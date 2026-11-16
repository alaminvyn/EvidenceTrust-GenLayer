"""Use official direct-mode fixtures and project-local, pinned SDK artifacts."""

import sys
from pathlib import Path

import pytest
from gltest.direct import sdk_loader

sdk_loader.CACHE_DIR = Path(__file__).resolve().parents[1] / ".cache" / "genvm"


@pytest.fixture(autouse=True)
def isolate_sdk_contract_registration():
    # GenVM imports one contract per process. gltest 0.29.2 re-imports contracts
    # in the same pytest process but does not reset this SDK registration.
    # Reset only that registry between tests; execution/storage remain official.
    module = sys.modules.get("genlayer.gl.genvm_contracts")
    if module is not None:
        module.__known_contract__ = None


def pytest_sessionstart(session):
    archive = sdk_loader.CACHE_DIR / "genvm-universal-v0.3.0-rc7.tar.xz"
    if not archive.is_file():
        raise pytest.UsageError(
            "Pinned SDK cache missing. Run: python scripts/prepare_sdk.py"
        )
