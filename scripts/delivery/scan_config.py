"""Run Trivy's ARM and Dockerfile rules against exactly our deployment/build inputs."""

from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def main():
    for folder in ("artifacts/m3/infra", "apps/octocat-supply/api", "apps/octocat-supply/frontend"):
        report = ROOT / "artifacts/m3" / (Path(folder).name + "-configuration.json")
        subprocess.run([
            "trivy", "config", "--skip-version-check", "--exit-code", "1", "--severity", "HIGH,CRITICAL",
            "--misconfig-scanners", "azure-arm,dockerfile", "--format", "json", "--output", str(report), str(ROOT / folder)
        ], check=True)
        results = json.loads(report.read_text()).get("Results", [])
        print(f"Trivy evaluated {folder}: {[r['Target'] for r in results]}")
    print("Coverage limit: Trivy may not evaluate all ARM resource types; compiled-template policy tests are mandatory for all four templates.")


if __name__ == "__main__":
    main()
