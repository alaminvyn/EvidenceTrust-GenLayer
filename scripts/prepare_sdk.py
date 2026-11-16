"""Cache the unmodified official runner bundle under the legacy gltest filename."""

import argparse
import hashlib
import shutil
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "v0.3.0-rc7"
SHA256 = "e218a1854214681560351051f76fe2b878545cf3409455ef372d57014a88ca67"
CACHE = ROOT / ".cache" / "genvm"
ARCHIVE = CACHE / f"genvm-universal-{VERSION}.tar.xz"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--archive", type=Path, help="Use an already downloaded official bundle"
    )
    args = parser.parse_args()
    CACHE.mkdir(parents=True, exist_ok=True)
    if not ARCHIVE.exists():
        if args.archive:
            shutil.copyfile(args.archive, ARCHIVE)
        else:
            remote = f"https://github.com/genlayerlabs/genvm/releases/download/{VERSION}/genvm-runners-all.tar.xz"
            print(f"Downloading {remote}")
            with (
                urllib.request.urlopen(remote, timeout=60) as source,
                ARCHIVE.open("wb") as target,
            ):
                shutil.copyfileobj(source, target)
    actual = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
    if actual != SHA256:
        ARCHIVE.unlink()
        raise SystemExit("Runner checksum mismatch; cache file removed")
    print(f"Verified official {VERSION} runner bundle: {actual}")


if __name__ == "__main__":
    main()
