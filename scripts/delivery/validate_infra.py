"""Compile/lint locally with Bicep; never invokes az, ARM validate or what-if."""

import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def main():
    output = ROOT / "artifacts/m3/infra"
    output.mkdir(parents=True, exist_ok=True)
    for source in sorted((ROOT / "infra").glob("*.bicep")):
        for command in (["bicep", "lint", str(source)], [
            "bicep", "build", str(source), "--outfile", str(output / f"{source.stem}.json")
        ]):
            result = subprocess.run(command, text=True, capture_output=True)
            print(result.stdout + result.stderr, end="")
            result.check_returncode()
            if ": Warning " in result.stderr:
                raise ValueError("Unresolved Bicep warning; fix before validation passes")
        template = json.loads((output / f"{source.stem}.json").read_text())
        assert template["resources"], f"Empty template: {source}"
    print("PASS: local Bicep lint/build; no Azure connection or deployment validation performed")


if __name__ == "__main__":
    main()
