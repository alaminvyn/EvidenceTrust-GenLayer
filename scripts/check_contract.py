"""Run official lint and SDK semantic checks using the pinned project cache."""

import os
from pathlib import Path

from genvm_linter.cli import main
from genvm_linter.validate import artifacts

ROOT = Path(__file__).resolve().parents[1]
artifacts.CACHE_DIR = ROOT / ".cache" / "genvm"
os.environ["GENVM_VERSION"] = "v0.3.0-rc7"
if __name__ == "__main__":
    main(["check", str(ROOT / "contracts" / "evidence_trust.py")])
