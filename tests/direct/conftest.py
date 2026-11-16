import json
import re

import pytest

URL_A = "https://agency.example.org/evidence"
URL_B = "https://institute.example.net/evidence"
CLAIM = "The Aurora mission launched on 2024-01-15."
OBSERVED = "2024-01-16T00:00:00Z"
SUPPORT = "The Aurora mission launched on 2024-01-15."
REFUTE = "The Aurora mission did not launch on 2024-01-15; launch was cancelled."
CONFLICT = SUPPORT + " Correction: " + REFUTE


def make_policy():
    return {
        "version": "evidence-policy-v1",
        "min_support": 2,
        "min_refute": 2,
        "sources": [
            {
                "host": "agency.example.org",
                "group": "agency",
                "authoritative": True,
                "reference_url": URL_A,
            },
            {
                "host": "institute.example.net",
                "group": "institute",
                "authoritative": True,
                "reference_url": URL_B,
            },
        ],
    }


def mock_sources(
    vm, labels=("supports", "supports"), *, bodies=None, codes=(200, 200), grounded=True
):
    vm.clear_mocks()
    if bodies is None:
        quotes = {
            "supports": SUPPORT,
            "contradicts": REFUTE,
            "inconsistent": CONFLICT,
            "insufficient": "",
        }
        bodies = tuple(quotes.get(label, "") for label in labels)
    for source, label, body, code in zip((URL_A, URL_B), labels, bodies, codes):
        vm.mock_web(re.escape(source) + "$", {"status": code, "body": body})
        if (
            label != "unavailable"
            and code == 200
            and body
            and len(body.encode()) <= 48000
        ):
            quote = "" if label == "insufficient" else body
            # The source URL is unique in each extraction prompt.
            vm.mock_llm(
                r"(?s).*EVIDENCETRUST_EXTRACT_V1.*" + re.escape(source) + r".*",
                json.dumps(json.dumps({"label": label, "quote": quote})),
            )
    vm.mock_llm(
        r"(?s).*EVIDENCETRUST_GROUND_V1.*",
        json.dumps(json.dumps({"grounded": grounded})),
    )


@pytest.fixture
def policy():
    return make_policy()


@pytest.fixture
def contract(direct_deploy, direct_vm, policy):
    direct_vm.warp("2026-11-16T12:00:00+00:00")
    return direct_deploy(
        "contracts/evidence_trust.py", json.dumps(policy), sdk_version="v0.3.0-rc7"
    )


@pytest.fixture
def submitted(contract):
    record_id = contract.submit(CLAIM, [URL_A], OBSERVED, '{"category":"space"}')
    return contract, record_id
