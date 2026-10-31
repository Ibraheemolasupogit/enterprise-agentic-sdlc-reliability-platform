"""Fail on every reported HIGH/CRITICAL image finding; no ignore-unfixed bypass."""

from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "artifacts/m3"


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    failed = False
    for name, image in (("api", "morrow-supply-api:m3-verify"), ("frontend", "morrow-supply-web:m3-verify")):
        result = subprocess.run([
            "trivy", "image", "--quiet", "--skip-version-check", "--scanners", "vuln", "--timeout", "15m",
            "--severity", "HIGH,CRITICAL", "--exit-code", "1", "--format", "json",
            "--output", str(OUTPUT / f"{name}-vulnerabilities.json"), image
        ])
        failed |= result.returncode != 0
        subprocess.run([
            "trivy", "image", "--quiet", "--skip-version-check", "--format", "cyclonedx",
            "--output", str(OUTPUT / f"{name}-sbom.cdx.json"), image
        ], check=True)
    if failed:
        raise SystemExit("Image gate BLOCKED: scanner error or HIGH/CRITICAL findings. Review retained reports; no automatic exception.")


if __name__ == "__main__":
    main()
