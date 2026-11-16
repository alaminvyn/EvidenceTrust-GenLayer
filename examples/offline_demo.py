"""Synthetic SDK-only demonstration. No network, credentials or on-chain deployment."""

import json
import re
from pathlib import Path

from gltest.direct import sdk_loader
from gltest.direct.loader import create_address, deploy_contract
from gltest.direct.vm import VMContext

ROOT = Path(__file__).resolve().parents[1]
sdk_loader.CACHE_DIR = ROOT / ".cache" / "genvm"


def main():
    policy = json.loads((ROOT / "examples/policy.json").read_text())
    scenarios = json.loads((ROOT / "examples/scenarios.json").read_text())
    vm = VMContext()
    vm.sender = create_address("offline-demo")
    vm.warp("2026-11-16T12:00:00+00:00")
    with vm.activate():
        # deploy_contract is the official in-memory test helper; no RPC is used.
        contract = deploy_contract(
            ROOT / "contracts/evidence_trust.py",
            vm,
            json.dumps(policy),
            sdk_version="v0.3.0-rc7",
        )
        record_id = contract.submit(
            "The Aurora mission launched on 2024-01-15.",
            [policy["sources"][0]["reference_url"]],
            "2024-01-16T00:00:00Z",
            '{"demo":"synthetic"}',
        )
        for scenario in scenarios:
            vm.clear_mocks()
            for source, label, body in zip(
                policy["sources"], scenario["labels"], scenario["bodies"]
            ):
                source_url = source["reference_url"]
                vm.mock_web(re.escape(source_url) + "$", {"status": 200, "body": body})
                if label != "unavailable":
                    # gltest 0.29.2 auto-parses mock JSON even in text mode.
                    response = json.dumps(
                        {
                            "label": label,
                            "quote": "" if label == "insufficient" else body,
                        }
                    )
                    vm.mock_llm(
                        r"(?s).*EVIDENCETRUST_EXTRACT_V1.*"
                        + re.escape(source_url)
                        + r".*",
                        json.dumps(response),
                    )
            vm.mock_llm(
                r"(?s).*EVIDENCETRUST_GROUND_V1.*", json.dumps('{"grounded":true}')
            )
            status = contract.verify(record_id)
            assert status == scenario["expected_mock_status"]
            assert vm.run_validator() is True
            print(f"{scenario['name']}: {status} (mocked leader and validator)")
        print(f"Retained history entries: {len(contract.get_history(record_id, 0, 8))}")


if __name__ == "__main__":
    main()
