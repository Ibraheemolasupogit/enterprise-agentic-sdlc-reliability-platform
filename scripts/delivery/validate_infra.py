"""Compile/lint locally with Bicep; never invokes az, ARM validate or what-if."""

import json
import hashlib
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def main():
    output = ROOT / "artifacts/m3/infra"
    output.mkdir(parents=True, exist_ok=True)
    sources = sorted((ROOT / "infra").glob("*.bicep"))
    expected = {"apps", "foundation", "registry-access", "federation", "network", "sql", "migrator", "diagnostics"}
    if {p.stem for p in sources} != expected or {p.stem for p in output.glob("*.json")} - expected:
        raise ValueError("Missing/unknown Bicep source or stale compiled template; review coverage first")
    for source in sources:
        formatted = subprocess.run(["bicep", "format", str(source), "--stdout"], text=True, capture_output=True, check=True)
        if formatted.stdout != source.read_text():
            raise ValueError(f"Bicep formatting required: {source.name}")
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
    paths = sources + sorted((ROOT / "infra").glob("*.kql")) + [ROOT / "infra/bicepconfig.json"]
    paths += sorted(output.glob("*.json"))
    bindings = [{"path": str(p.relative_to(ROOT)), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]
    (output.parent / "infra-bindings.json").write_text(json.dumps(bindings, indent=2) + "\n")
    print(f"PASS: all {len(sources)} Bicep templates format/lint/build and source/output bindings; no Azure connection or deployment validation performed")


if __name__ == "__main__":
    main()
