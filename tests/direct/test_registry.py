import json

import pytest
from conftest import CLAIM, OBSERVED, URL_A, URL_B


def test_submission_is_pending_and_auditable(contract, direct_vm):
    record_id = contract.submit(CLAIM, [URL_A], OBSERVED, '{"tag":"science"}')
    record = json.loads(contract.get_record(record_id))
    assert len(record_id) == 64
    assert record["claim"] == CLAIM
    assert record["status"] == "Pending"
    assert record["attempts"] == 0
    assert record["metadata"] == {"tag": "science"}
    assert record["observed_at"] == OBSERVED
    assert record["submitted_at"].startswith("2026-11-16")
    assert record["submitter"].lower() == "0x" + bytes(direct_vm.sender).hex()
    assert contract.list_records(0, 50) == [record_id]
    assert contract.list_records(1, 1) == []
    assert contract.get_history(record_id, 0, 8) == []


def test_duplicate_across_sender_urls_and_metadata(submitted, direct_vm, direct_bob):
    contract, record_id = submitted
    direct_vm.sender = direct_bob
    with direct_vm.expect_revert("Duplicate claim"):
        contract.submit(
            "  " + CLAIM.upper() + "  ", [URL_B], OBSERVED, '{"different":"yes"}'
        )
    assert contract.list_records(0, 50) == [record_id]


def test_distinct_observation_can_be_submitted(contract):
    first = contract.submit(CLAIM, [URL_A], OBSERVED, "{}")
    second = contract.submit(CLAIM, [URL_A], "2024-01-17T00:00:00Z", "{}")
    assert first != second


@pytest.mark.parametrize("claim", ["", "   ", "a" * 2001, "bad\nclaim", "bad\x7fclaim"])
def test_invalid_claim(contract, direct_vm, claim):
    with direct_vm.expect_revert():
        contract.submit(claim, [URL_A], OBSERVED, "{}")
    assert contract.list_records(0, 1) == []


@pytest.mark.parametrize(
    "source",
    [
        "http://agency.example.org/evidence",
        "https://user:pass@agency.example.org/evidence",
        "https://agency.example.org:443/evidence",
        "https://127.0.0.1/evidence",
        "https://[::1]/evidence",
        "https://localhost/evidence",
        "https://agency.example.org.evil.com/evidence",
        "https://agency.example.org/evidence#part",
        "https://agency.example.org/a/../evidence",
        "https://agency.example.org/%2e%2e/evidence",
        "https://agency.example.org/%252e/evidence",
        "https://agency.example.org/%0a",
        "https://agency.example.org/%QQ",
        "https://agency.example.org\\evil",
        "https://agency.example.org./evidence",
        "https://agency.example.org/évidence",
    ],
)
def test_unsafe_urls(contract, direct_vm, source):
    with direct_vm.expect_revert():
        contract.submit(CLAIM, [source], OBSERVED, "{}")


def test_canonical_host_and_duplicate_urls(contract, direct_vm):
    with direct_vm.expect_revert("Duplicate source"):
        contract.submit(
            CLAIM, [URL_A, URL_A.replace("agency", "AGENCY")], OBSERVED, "{}"
        )
    record_id = contract.submit(
        CLAIM, [URL_A.replace("agency", "AGENCY")], OBSERVED, "{}"
    )
    assert json.loads(contract.get_record(record_id))["source_urls"] == [URL_A]


@pytest.mark.parametrize("sources", [[], [URL_A] * 7])
def test_source_count_bounds(contract, direct_vm, sources):
    with direct_vm.expect_revert():
        contract.submit(CLAIM, sources, OBSERVED, "{}")


@pytest.mark.parametrize(
    "timestamp",
    [
        "2024-01-16",
        "2024-02-30T00:00:00Z",
        "2024-01-16T00:00:00+00:00",
        "9999-01-01T00:00:00Z",
    ],
)
def test_invalid_timestamp(contract, direct_vm, timestamp):
    with direct_vm.expect_revert():
        contract.submit(CLAIM, [URL_A], timestamp, "{}")


@pytest.mark.parametrize(
    "metadata",
    [
        "[]",
        '{"a":1}',
        '{"a":"x","a":"y"}',
        "{",
        json.dumps({"a": "x" * 513}),
        json.dumps({str(i): "x" for i in range(17)}),
        "x" * 4001,
    ],
)
def test_invalid_metadata(contract, direct_vm, metadata):
    with direct_vm.expect_revert():
        contract.submit(CLAIM, [URL_A], OBSERVED, metadata)


@pytest.mark.parametrize("offset,limit", [(-1, 1), (0, 0), (0, 51)])
def test_pagination_bounds(submitted, direct_vm, offset, limit):
    contract, record_id = submitted
    with direct_vm.expect_revert():
        contract.list_records(offset, limit)
    with direct_vm.expect_revert():
        contract.get_history(record_id, offset, limit)


def test_missing_record(contract, direct_vm):
    for action in [
        lambda: contract.get_record("missing"),
        lambda: contract.verify("missing"),
        lambda: contract.get_history("missing", 0, 1),
    ]:
        with direct_vm.expect_revert("Unknown evidence"):
            action()


def test_policy_immutable(contract, policy):
    assert json.loads(contract.get_policy()) == policy


@pytest.mark.parametrize(
    "change",
    [
        lambda p: p.update(min_support=1),
        lambda p: p.update(min_refute=True),
        lambda p: p.update(extra="value"),
        lambda p: p["sources"][1].update(group="agency"),
        lambda p: p["sources"][1].update(host="agency.example.org"),
        lambda p: p["sources"][1].update(reference_url=URL_A),
        lambda p: [s.update(reference_url="") for s in p["sources"]],
        lambda p: p["sources"][0].update(authoritative="true"),
    ],
)
def test_policy_validation(direct_deploy, direct_vm, policy, change):
    change(policy)
    with pytest.raises(Exception) as caught:
        direct_deploy(
            "contracts/evidence_trust.py", json.dumps(policy), sdk_version="v0.3.0-rc7"
        )
    assert type(caught.value).__name__ == "UserError", (
        "Constructor must fail on policy validation, not import/runtime setup"
    )


def test_combined_source_budget_rejected_at_submission(contract, direct_vm):
    extra = [f"https://agency.example.org/item{i}" for i in range(5)]
    with direct_vm.expect_revert("Combined source limit"):
        contract.submit(CLAIM, extra, OBSERVED, "{}")
    assert contract.list_records(0, 50) == []


def test_non_string_policy_host_is_user_error(direct_deploy, policy):
    policy["sources"][0]["host"] = 42
    with pytest.raises(Exception) as caught:
        direct_deploy(
            "contracts/evidence_trust.py", json.dumps(policy), sdk_version="v0.3.0-rc7"
        )
    assert type(caught.value).__name__ == "UserError"


def test_exact_source_budget_is_usable(contract, direct_vm):
    urls = [URL_A, URL_B] + [f"https://agency.example.org/item{i}" for i in range(4)]
    record_id = contract.submit(CLAIM, urls, OBSERVED, "{}")
    direct_vm.mock_web(r".*", {"status": 200, "body": ""})
    assert contract.verify(record_id) == "Pending"
    result = json.loads(contract.get_history(record_id, 0, 1)[0])
    assert len(result["findings"]) == 6


def test_policy_hostname_cannot_include_path(direct_deploy, policy):
    policy["sources"][0]["host"] += "/ignored-path"
    with pytest.raises(Exception) as caught:
        direct_deploy(
            "contracts/evidence_trust.py", json.dumps(policy), sdk_version="v0.3.0-rc7"
        )
    assert type(caught.value).__name__ == "UserError"
    assert "only a hostname" in str(caught.value)
