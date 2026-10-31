"""Build/smoke an isolated local project; never touch the M2 demo/volume."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "apps/octocat-supply"
OUTPUT = ROOT / "artifacts/m3"
PROJECT = "morrow-supply-m3-verify"
BASE = "http://127.0.0.1:18080"
COMPOSE = ["docker", "compose", "-p", PROJECT, "-f", str(APP / "compose.yaml"),
           "-f", str(ROOT / "security/compose.verify.yaml")]


def compose(*args, port="3000", capture=False):
    return subprocess.run(COMPOSE + list(args), cwd=APP,
                          env={**os.environ, "API_PORT": port}, check=True,
                          text=True, capture_output=capture, timeout=600)


def request(path, method="GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method,
                                 headers={"Content-Type": "application/json", "Origin": BASE})
    try:
        response = urllib.request.urlopen(req, timeout=5)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        return response.status, response.read(), dict(response.headers)


def ready():
    for _ in range(60):
        try:
            if request("/health/ready")[0] == 200:
                return
        except (OSError, TimeoutError):
            pass
        time.sleep(0.5)
    raise RuntimeError("Local frontend dependency readiness failed")


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    # Refuse to take over any prior state, including a stopped project's volume.
    existing = compose("ps", "-a", "-q", capture=True).stdout.strip()
    volume = subprocess.run(["docker", "volume", "inspect", PROJECT + "_demo-data"],
                            capture_output=True)
    if existing or volume.returncode == 0:
        raise RuntimeError("Verification project already exists; inspect/clean it manually first")
    record = {"started": datetime.now(timezone.utc).isoformat(), "project": PROJECT,
              "actor": "deterministic local delivery verification", "checks": []}
    try:
        compose("build")
        compose("run", "--rm", "api", "node", "api/dist/database-cli.js", "migrate")
        compose("run", "--rm", "api", "node", "api/dist/database-cli.js", "seed")
        compose("up", "-d", "--wait", "--wait-timeout", "40")
        ready()
        status, body, _ = request("/api/products")
        assert status == 200 and json.loads(body)["total"] == 12
        status, body, _ = request("/api/carts", "POST", {})
        assert status == 201
        cart_id = json.loads(body)["id"]
        assert request(f"/api/carts/{cart_id}/items/1", "PUT", {"quantity": 2})[0] == 200
        status, body, _ = request(f"/api/carts/{cart_id}/items/2", "PUT", {"quantity": 3})
        assert status == 200 and json.loads(body)["totalMinor"] == 28796
        record["checks"].append("12 fixtures and authoritative discount total via built proxy")
        for service in ("api", "frontend"):
            container = compose("ps", "-q", service, capture=True).stdout.strip()
            details = json.loads(subprocess.check_output(["docker", "inspect", container]))[0]
            assert details["Config"]["User"] not in ("", "root", "0")
            assert details["HostConfig"]["ReadonlyRootfs"]
            assert details["HostConfig"]["CapDrop"] == ["ALL"]
            bindings = details["HostConfig"]["PortBindings"] or {}
            if service == "api":
                assert not bindings
            else:
                assert bindings == {"8080/tcp": [{"HostIp": "127.0.0.1", "HostPort": "18080"}]}
        record["checks"].append("non-root/read-only/cap-drop; only loopback frontend published")
        compose("up", "-d", "--force-recreate", "--no-deps", "api")
        ready()
        assert json.loads(request(f"/api/carts/{cart_id}")[1])["totalMinor"] == 28796
        record["checks"].append("cart persisted across API container replacement")
        subprocess.run(["npm", "run", "test:e2e"], cwd=APP,
                       env={**os.environ, "E2E_BASE_URL": BASE}, check=True, timeout=120)
        record["checks"].append("all three unchanged M2 browser cases passed through production images")
        assert request(f"/api/carts/{cart_id}", "DELETE")[0] == 204
        assert request(f"/api/carts/{cart_id}")[0] == 404
        record["result"] = "PASS"
    finally:
        compose("down", "--volumes", "--remove-orphans")
    record["finished"] = datetime.now(timezone.utc).isoformat()
    (OUTPUT / "container-smoke.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
