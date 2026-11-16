"""Scoped v2 checks use official SDK execution with mock transport/model results."""

import copy
import hashlib
import itertools
import json
import re
import sys

import pytest
from conftest import OBSERVED, URL_A, URL_B, make_policy

MODE = "all_required_subclaims"
CLAIMS = ("Agency A published document alpha.", "Institute B published document beta.")


@pytest.fixture
def scoped_policy():
    policy = make_policy()
    policy.update(version="scoped-test-v2", verification_mode=MODE)
    for source, source_id in zip(policy["sources"], ("agency_a", "institute_b")):
        source["source_id"] = source_id
    return policy


@pytest.fixture
def entries():
    return [
        {"source_id": source_id, "source_url": source_url, "claim": claim}
        for source_id, source_url, claim in zip(
            ("agency_a", "institute_b"), (URL_A, URL_B), CLAIMS
        )
    ]


@pytest.fixture
def scoped_contract(direct_vm, direct_deploy, scoped_policy):
    direct_vm.warp("2026-11-16T12:00:00+00:00")
    return direct_deploy(
        "contracts/evidence_trust.py",
        json.dumps(scoped_policy),
        sdk_version="v0.3.0-rc7",
    )


def mock_scoped(vm, labels=("supports", "supports"), *, grounded=True, changed=False):
    vm.clear_mocks()
    for index, (source_url, label) in enumerate(zip((URL_A, URL_B), labels)):
        body = (
            CLAIMS[index]
            if label == "supports"
            else "The submitted assertion is explicitly refuted by this document."
        )
        if label == "inconsistent":
            body = "This document confirms and explicitly denies the same assertion."
        if label == "insufficient":
            body = "An unrelated document with no relevant evidence."
        if label == "unavailable":
            body = ""
        if changed and index == 0:
            body += " Updated content."
        vm.mock_web(re.escape(source_url) + "$", {"status": 200, "body": body})
        if label != "unavailable":
            answer = {"label": label, "quote": "" if label == "insufficient" else body}
            vm.mock_llm(
                r"(?s).*EVIDENCETRUST_EXTRACT_SCOPED_V2.*" + re.escape(source_url),
                json.dumps(json.dumps(answer)),
            )
    vm.mock_llm(
        r"(?s).*EVIDENCETRUST_GROUND_SCOPED_V2.*",
        json.dumps(json.dumps({"grounded": grounded})),
    )


def submit(contract, entries):
    return contract.submit_scoped(
        json.dumps(entries), OBSERVED, '{"category":"scoped-test"}'
    )


def candidate(contract, record_id):
    history = json.loads(contract.get_history(record_id, 0, 1)[0])
    return {key: history[key] for key in ("status", "explanation", "findings", "mode")}


def test_scoped_identity_statement_and_history(
    scoped_contract, scoped_policy, entries, direct_vm
):
    record_id = submit(scoped_contract, list(reversed(entries)))
    record = json.loads(scoped_contract.get_record(record_id))
    assert record["mode"] == MODE
    assert record["subclaims"] == entries
    assert record["status"] == "Pending" and record["attempts"] == 0
    module = sys.modules["_contract_evidence_trust"]
    assert record["claim"] == module.scoped_statement(entries)
    assert len(record["claim"]) <= 2000
    material = {
        "mode": MODE,
        "policy_sha256": hashlib.sha256(
            scoped_contract.get_policy().encode()
        ).hexdigest(),
        "subclaims": entries,
        "observed_at": OBSERVED,
    }
    # Actual identity casefolds subclaim text, just like the v1 duplicate key.
    material["subclaims"] = [{**e, "claim": e["claim"].casefold()} for e in entries]
    assert record_id == hashlib.sha256(module.canonical(material).encode()).hexdigest()
    mock_scoped(direct_vm)
    assert scoped_contract.verify(record_id) == "Verified"
    assert direct_vm.run_validator() is True
    history = json.loads(scoped_contract.get_history(record_id, 0, 1)[0])
    assert history["mode"] == MODE and history["subclaims"] == entries
    assert history["previous_status"] == "Pending"
    assert history["policy_version"] == scoped_policy["version"]


@pytest.mark.parametrize(
    "labels",
    list(
        itertools.product(
            ("supports", "contradicts", "insufficient", "inconsistent", "unavailable"),
            repeat=2,
        )
    ),
)
def test_scoped_decision_matrix(scoped_contract, entries, direct_vm, labels):
    record_id = submit(scoped_contract, entries)
    mock_scoped(direct_vm, labels)
    if "inconsistent" in labels or set(labels) == {"supports", "contradicts"}:
        expected = "Disputed"
    elif set(labels) & {"insufficient", "unavailable"}:
        expected = "Pending"
    elif labels == ("supports", "supports"):
        expected = "Verified"
    elif labels == ("contradicts", "contradicts"):
        expected = "Rejected"
    else:
        expected = "Pending"
    assert scoped_contract.verify(record_id) == expected
    assert direct_vm.run_validator() is True


@pytest.mark.parametrize(
    "change",
    [
        lambda e: e.pop(),
        lambda e: e.append(copy.deepcopy(e[0])),
        lambda e: e.__setitem__(1, copy.deepcopy(e[0])),
        lambda e: e[0].update(source_id="unknown"),
        lambda e: e[0].update(source_url=URL_B),
        lambda e: e[0].update(source_url=URL_A + "/replacement"),
        lambda e: e[0].update(source_url="http://agency.example.org/evidence"),
        lambda e: e[0].update(source_url="https://evil.example.org/evidence"),
        lambda e: e[0].update(authoritative=True),
        lambda e: e[0].update(claim=""),
        lambda e: e[0].update(claim="bad\nclaim"),
        lambda e: e[0].update(claim="x" * 2001),
        lambda e: [item.update(claim="x" * 1100) for item in e],
        lambda e: [
            item.update(claim="x" * 900) for item in e
        ],  # structured statement > 2000
    ],
)
def test_scoped_submission_mapping_and_limits(
    scoped_contract, entries, direct_vm, change
):
    change(entries)
    with direct_vm.expect_revert():
        submit(scoped_contract, entries)
    assert scoped_contract.list_records(0, 50) == []


def test_swapped_source_ids_and_urls_rejected(scoped_contract, entries, direct_vm):
    entries[0]["source_url"], entries[1]["source_url"] = (
        entries[1]["source_url"],
        entries[0]["source_url"],
    )
    with direct_vm.expect_revert("mapping mismatch"):
        submit(scoped_contract, entries)


@pytest.mark.parametrize(
    "raw", ["{}", '[{"source_id":"agency_a","source_id":"institute_b"}]', "x" * 12001]
)
def test_scoped_raw_payload_rejected(scoped_contract, direct_vm, raw):
    with direct_vm.expect_revert():
        scoped_contract.submit_scoped(raw, OBSERVED, "{}")


@pytest.mark.parametrize(
    "timestamp,metadata",
    [
        ("2099-01-01T00:00:00Z", "{}"),
        ("2024-02-30T00:00:00Z", "{}"),
        ("2024-01-16", "{}"),
        (OBSERVED, '{"x":2}'),
        (OBSERVED, "[]"),
    ],
)
def test_scoped_common_validation(
    scoped_contract, entries, direct_vm, timestamp, metadata
):
    with direct_vm.expect_revert():
        scoped_contract.submit_scoped(json.dumps(entries), timestamp, metadata)
    assert scoped_contract.list_records(0, 50) == []


def test_mode_entrypoints_do_not_bypass_policy(scoped_contract, direct_vm):
    with direct_vm.expect_revert("Use submit_scoped"):
        scoped_contract.submit(CLAIMS[0], [URL_A], OBSERVED, "{}")


def test_scoped_rejected_under_legacy_policy(contract, entries, direct_vm):
    with direct_vm.expect_revert("Scoped policy required"):
        submit(contract, entries)


@pytest.mark.parametrize(
    "change",
    [
        lambda p: p.update(verification_mode="unknown"),
        lambda p: p["sources"][0].update(authoritative=False),
        lambda p: p["sources"][0].update(reference_url=""),
        lambda p: p["sources"][1].update(source_id="agency_a"),
        lambda p: p["sources"][0].update(source_id="bad id"),
        lambda p: p["sources"][0].pop("source_id"),
        lambda p: p.update(min_support=1),
        lambda p: p.update(min_refute=1),
        lambda p: p["sources"][1].update(group="agency"),
    ],
)
def test_scoped_policy_validation(direct_deploy, scoped_policy, change):
    change(scoped_policy)
    with pytest.raises(Exception) as caught:
        direct_deploy(
            "contracts/evidence_trust.py",
            json.dumps(scoped_policy),
            sdk_version="v0.3.0-rc7",
        )
    assert type(caught.value).__name__ == "UserError"


def test_canonical_duplicate_and_mapping_identity(
    scoped_contract, entries, direct_vm, direct_bob
):
    first = submit(scoped_contract, entries)
    reordered = list(reversed(copy.deepcopy(entries)))
    for entry in reordered:
        entry["claim"] = " " + entry["claim"].upper() + " "
    direct_vm.sender = direct_bob
    with direct_vm.expect_revert("Duplicate scoped"):
        scoped_contract.submit_scoped(
            json.dumps(reordered), OBSERVED, '{"other":"metadata"}'
        )
    entries[0]["claim"], entries[1]["claim"] = entries[1]["claim"], entries[0]["claim"]
    second = submit(scoped_contract, entries)
    assert (
        first != second
    )  # Swapping text defines different assertions, not a URL binding bypass.


def test_assessment_and_grounding_are_source_specific(
    scoped_contract, entries, direct_vm, monkeypatch
):
    record_id = submit(scoped_contract, entries)
    module = sys.modules["_contract_evidence_trust"]
    documents = {URL_A: CLAIMS[0], URL_B: CLAIMS[1]}
    calls = []
    monkeypatch.setattr(
        module, "fetch", lambda source_url: (documents[source_url], "ok")
    )

    def prompt_fn(prompt):
        payload = json.loads(prompt.splitlines()[-1])
        calls.append(payload)
        if prompt.startswith("EVIDENCETRUST_EXTRACT_SCOPED_V2"):
            assert payload["claim"] == documents[payload["url"]]
            return json.dumps({"label": "supports", "quote": payload["source"]})
        assert payload["claim"] == documents[payload["url"]]
        assert payload["quote"] == payload["source"]
        return '{"grounded":true}'

    monkeypatch.setattr(module.gl.nondet, "exec_prompt", prompt_fn)
    assert scoped_contract.verify(record_id) == "Verified"
    assert direct_vm.run_validator() is True
    assert (
        len(calls) == 6
    )  # two leader extractions + two independent extractions + two groundings


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_id", "institute_b"),
        ("subclaim", "A substituted assertion."),
        ("url", URL_B),
        ("host", "evil.example.org"),
        ("group", "fake"),
        ("authoritative", 1),
        ("retrieval", "fetch_error"),
        ("content_sha256", "f" * 64),
        ("quote", "A fabricated quotation from another source."),
    ],
)
def test_scoped_tampering_rejected(scoped_contract, entries, direct_vm, field, value):
    record_id = submit(scoped_contract, entries)
    mock_scoped(direct_vm)
    scoped_contract.verify(record_id)
    proposed = candidate(scoped_contract, record_id)
    proposed["findings"][0][field] = value
    assert direct_vm.run_validator(leader_result=proposed) is False


@pytest.mark.parametrize("mutation", ["omit", "duplicate", "reorder", "mode", "status"])
def test_scoped_result_coverage_rejected(scoped_contract, entries, direct_vm, mutation):
    record_id = submit(scoped_contract, entries)
    mock_scoped(direct_vm)
    scoped_contract.verify(record_id)
    proposed = candidate(scoped_contract, record_id)
    if mutation == "omit":
        proposed["findings"].pop()
    elif mutation == "duplicate":
        proposed["findings"][1] = copy.deepcopy(proposed["findings"][0])
    elif mutation == "reorder":
        proposed["findings"].reverse()
    elif mutation == "mode":
        proposed["mode"] = "legacy"
    else:
        proposed["status"] = "Pending"
    assert direct_vm.run_validator(leader_result=proposed) is False


@pytest.mark.parametrize(
    "change", ["disagree", "body", "grounding", "malformed", "exception"]
)
def test_scoped_independent_failures(scoped_contract, entries, direct_vm, change):
    record_id = submit(scoped_contract, entries)
    mock_scoped(direct_vm)
    scoped_contract.verify(record_id)
    if change == "disagree":
        mock_scoped(direct_vm, ("contradicts", "contradicts"))
    elif change == "body":
        mock_scoped(direct_vm, changed=True)
    elif change == "grounding":
        mock_scoped(direct_vm, grounded=False)
    elif change == "malformed":
        direct_vm.clear_mocks()
        direct_vm.mock_web(r".*", {"status": 200, "body": CLAIMS[0]})
        direct_vm.mock_llm(r"(?s).*", json.dumps('{"label":"supports"}'))
    else:
        assert direct_vm.run_validator(leader_error=RuntimeError("failed")) is False
        return
    assert direct_vm.run_validator() is False


def test_scoped_failed_leader_does_not_write_history(
    scoped_contract, entries, direct_vm
):
    record_id = submit(scoped_contract, entries)
    direct_vm.mock_web(r".*", {"status": 200, "body": CLAIMS[0]})
    direct_vm.mock_llm(r"(?s).*", json.dumps("not JSON"))
    with direct_vm.expect_revert():
        scoped_contract.verify(record_id)
    assert scoped_contract.get_history(record_id, 0, 8) == []
    assert json.loads(scoped_contract.get_record(record_id))["attempts"] == 0


def test_scoped_history_limits_and_auth(
    scoped_contract, entries, direct_vm, direct_bob
):
    record_id = submit(scoped_contract, entries)
    original = scoped_contract.get_record(record_id)
    owner = direct_vm.sender
    direct_vm.sender = direct_bob
    with direct_vm.expect_revert("Only submitter"):
        scoped_contract.verify(record_id)
    assert scoped_contract.get_record(record_id) == original
    direct_vm.sender = owner
    mock_scoped(direct_vm)
    scoped_contract.verify(record_id)
    first = scoped_contract.get_history(record_id, 0, 1)[0]
    mock_scoped(direct_vm, ("insufficient", "supports"))
    for _ in range(7):
        assert scoped_contract.verify(record_id) == "Pending"
    assert scoped_contract.get_history(record_id, 0, 1)[0] == first
    assert json.loads(scoped_contract.get_record(record_id))["subclaims"] == entries
    assert len(scoped_contract.get_history(record_id, 0, 8)) == 8
    with direct_vm.expect_revert("attempt limit"):
        scoped_contract.verify(record_id)


def test_scoped_all_required_even_after_support_quorum(
    direct_deploy, direct_vm, scoped_policy, entries
):
    third = {
        "host": "third.example.org",
        "group": "third",
        "authoritative": True,
        "reference_url": "https://third.example.org/doc",
        "source_id": "third",
    }
    scoped_policy["sources"].append(third)
    scoped = direct_deploy(
        "contracts/evidence_trust.py",
        json.dumps(scoped_policy),
        sdk_version="v0.3.0-rc7",
    )
    entries.append(
        {
            "source_id": "third",
            "source_url": third["reference_url"],
            "claim": "Third publisher confirms item gamma.",
        }
    )
    record_id = submit(scoped, entries)
    mock_scoped(direct_vm)
    direct_vm.mock_web(
        re.escape(third["reference_url"]) + "$",
        {"status": 200, "body": "Unrelated information."},
    )
    direct_vm.mock_llm(
        r"(?s).*EVIDENCETRUST_EXTRACT_SCOPED_V2.*" + re.escape(third["reference_url"]),
        json.dumps('{"label":"insufficient","quote":""}'),
    )
    assert scoped.verify(record_id) == "Pending"
    assert direct_vm.run_validator() is True


def test_swapping_claim_text_is_not_automatically_supported(
    scoped_contract, entries, direct_vm, monkeypatch
):
    entries[0]["claim"], entries[1]["claim"] = entries[1]["claim"], entries[0]["claim"]
    record_id = submit(scoped_contract, entries)
    module = sys.modules["_contract_evidence_trust"]
    documents = {URL_A: CLAIMS[0], URL_B: CLAIMS[1]}
    monkeypatch.setattr(
        module, "fetch", lambda source_url: (documents[source_url], "ok")
    )

    def prompt_fn(prompt):
        payload = json.loads(prompt.splitlines()[-1])
        assert payload["claim"] != documents[payload["url"]]
        return '{"label":"insufficient","quote":""}'

    monkeypatch.setattr(module.gl.nondet, "exec_prompt", prompt_fn)
    assert scoped_contract.verify(record_id) == "Pending"
    assert direct_vm.run_validator() is True


def test_scoped_closure_and_calldata_roundtrip(scoped_contract, entries, direct_vm):
    from gltest.direct import sdk_loader

    extracted = sdk_loader.extract_runner(
        sdk_loader.CACHE_DIR / "genvm-universal-v0.3.0-rc7.tar.xz",
        "py-lib-cloudpickle",
        "1dlk6mnfabi0z7r39635amyfzw8xb6rm8bv4pmgv6ji1bfx9hghd",
        "v0.3.0-rc7",
    )
    sys.path.insert(0, str(extracted / "src"))
    import cloudpickle
    from genlayer import gl
    from genlayer.py import calldata

    record_id = submit(scoped_contract, entries)
    mock_scoped(direct_vm)
    scoped_contract.verify(record_id)
    result, leader, validator = direct_vm._captured_validators[-1]
    restored_leader = cloudpickle.loads(cloudpickle.dumps(leader))
    restored_validator = cloudpickle.loads(cloudpickle.dumps(validator))
    assert restored_leader() == result
    wire = calldata.decode(calldata.encode(result))
    assert restored_validator(gl.vm.Return(calldata=wire)) is True


def test_scoped_six_source_limit(direct_deploy, direct_vm, scoped_policy, entries):
    for i in range(2, 6):
        source = {
            "source_id": f"source_{i}",
            "host": f"source{i}.example.org",
            "group": f"group_{i}",
            "authoritative": True,
            "reference_url": f"https://source{i}.example.org/evidence",
        }
        scoped_policy["sources"].append(source)
        entries.append(
            {
                "source_id": source["source_id"],
                "source_url": source["reference_url"],
                "claim": "The document confirms a specific fact.",
            }
        )
    scoped = direct_deploy(
        "contracts/evidence_trust.py",
        json.dumps(scoped_policy),
        sdk_version="v0.3.0-rc7",
    )
    record_id = submit(scoped, entries)
    direct_vm.mock_web(
        r".*", {"status": 200, "body": "The document confirms a specific fact."}
    )
    direct_vm.mock_llm(
        r"(?s).*EXTRACT_SCOPED.*",
        json.dumps(
            '{"label":"supports","quote":"The document confirms a specific fact."}'
        ),
    )
    direct_vm.mock_llm(r"(?s).*GROUND_SCOPED.*", json.dumps('{"grounded":true}'))
    assert scoped.verify(record_id) == "Verified"
    assert direct_vm.run_validator() is True
    assert len(json.loads(scoped.get_history(record_id, 0, 1)[0])["findings"]) == 6


def test_studio_v2_inputs_match_sdk_ids(direct_deploy, direct_vm):
    from pathlib import Path

    folder = Path("examples/studio/v2")
    policy = json.loads((folder / "policy.json").read_text())
    args = json.loads((folder / "constructor-args.json").read_text())
    assert len(args) == 1 and json.loads(args[0]) == policy
    direct_vm.warp("2026-11-16T12:00:00+00:00")
    scoped = direct_deploy(
        "contracts/evidence_trust.py", *args, sdk_version="v0.3.0-rc7"
    )
    for case in json.loads((folder / "cases.json").read_text())["cases"]:
        record_id = scoped.submit_scoped(*case["submit_scoped_args"])
        assert record_id == case["expected_record_id"]
        record = json.loads(scoped.get_record(record_id))
        assert record["subclaims"] == case["subclaims"]
        assert record["status"] == "Pending" and record["attempts"] == 0
        assert scoped.get_history(record_id, 0, 8) == []
    assert len(scoped.list_records(0, 50)) == 4
    assert (
        not direct_vm._captured_validators
    )  # No live or mocked verification in this test.
