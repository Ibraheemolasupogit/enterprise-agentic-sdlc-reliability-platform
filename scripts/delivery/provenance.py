"""Unsigned local/CI evidence, not a signed attestation or release authorization."""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "artifacts/m3"


def main():
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    expected = os.environ.get("GITHUB_SHA")
    if expected and expected != head:
        raise ValueError("Checked-out revision differs from GitHub event revision")
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT))
    images = {}
    for name, image in (("api", "morrow-supply-api:m3-verify"), ("frontend", "morrow-supply-web:m3-verify")):
        info = json.loads(subprocess.check_output(["docker", "image", "inspect", image]))[0]
        report = json.loads((OUTPUT / f"{name}-vulnerabilities.json").read_text())
        if report["Metadata"]["ImageID"] != info["Id"]:
            raise ValueError("Image changed after scanning; refusing stale provenance")
        sbom = json.loads((OUTPUT / f"{name}-sbom.cdx.json").read_text())
        properties = sbom["metadata"]["component"]["properties"]
        if not any(p["name"] == "aquasecurity:trivy:ImageID" and p["value"] == info["Id"] for p in properties):
            raise ValueError("SBOM image identity is stale or missing")
        images[name] = {"localImageId": info["Id"], "descriptorMediaType": info.get("Descriptor", {}).get("mediaType"),
                        "os": info["Os"], "architecture": info["Architecture"]}
    paths = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
    prefixes = ("apps/octocat-supply/", ".github/", "infra/", "security/", "scripts/delivery/", "tests/delivery/")
    files = [ROOT / p for p in sorted(set(paths)) if p.startswith(prefixes) and (ROOT / p).is_file()]
    files.append(ROOT / "requirements-delivery.txt")
    files += sorted(OUTPUT.glob("*-sbom.cdx.json")) + sorted(OUTPUT.glob("*-vulnerabilities.json"))
    record = {"created": datetime.now(timezone.utc).isoformat(), "sourceHead": head,
              "dirtyWorkingTree": dirty, "githubRunId": os.environ.get("GITHUB_RUN_ID"),
              "releaseEligible": False, "signedAttestation": False, "images": images,
              "files": [{"path": str(p.relative_to(ROOT)), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]}
    (OUTPUT / "provenance.json").write_text(json.dumps(record, indent=2) + "\n")
    print("Recorded source/lock/tool/Dockerfile/SBOM/report hashes and local image identities; not release approval")


if __name__ == "__main__":
    main()
