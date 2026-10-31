"""Install reviewed public tools into an explicit local directory; no cloud login."""

import hashlib
import io
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[2]


def main():
    destination = Path(sys.argv[1]).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((ROOT / "security/tools.json").read_text())
    host = f"{platform.system()}-{platform.machine()}"
    requested = sys.argv[2:] or list(manifest)
    for name in requested:
        entry = manifest[name]["platforms"][host]
        # Use system CA trust on macOS/Linux; never disable certificate verification.
        data = subprocess.run([
            "curl", "--fail", "--location", "--silent", "--show-error", "--proto", "=https",
            "--tlsv1.2", "--max-time", "180", entry["url"]
        ], check=True, capture_output=True).stdout
        if hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise ValueError(f"Checksum mismatch for {name}; nothing executed")
        if entry["url"].endswith(".tar.gz"):
            # Extract exactly the named binary, never arbitrary archive paths.
            with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
                member = archive.getmember(name)
                if not member.isfile():
                    raise ValueError("Tool archive member is not a regular file")
                data = archive.extractfile(member).read()
        target = destination / name
        target.write_bytes(data)
        os.chmod(target, 0o755)
        print(f"Installed {name} {manifest[name]['version']} (SHA-256 verified)")


if __name__ == "__main__":
    main()
