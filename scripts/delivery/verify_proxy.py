"""Real local TLS proxy checks using published Node test fixtures, never credentials/accounts."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
IMAGE = "morrow-supply-web:m3-verify"
API_IMAGE = "morrow-supply-api:m3-verify"
NETWORK = "morrow-m4b-proxy-check"
NAMES = ["morrow-m4b-tls-peer", "morrow-m4b-proxy"]
FIXTURES = [
    ("agent1-cert.pem", "5968cc95396f7a49d0fccaee6cf2c6b8a2f66b907efa21531c4c98d20962783c"),
    ("agent1-key.pem",
     "2b75ca8377f0963f5ce0d47a416b9d40de09dbd6e128ffe6e00af0e52be0eda9"),
    ("ca1-cert.pem", "cfc60db87bd758cd89e69973484b60a14fb2f3d9cf798bb4ce0dcc17e59643b6"),
]


def docker(*args, check=True):
    result = subprocess.run(["docker", *args], capture_output=True, text=True, timeout=120)
    if check:
        if result.returncode:
            raise RuntimeError(f"Docker {args[0]} failed ({result.returncode}): {result.stderr[-4000:]}")
    return result


def allow_peer_fixture_reads(folder):
    # TemporaryDirectory is 0700; native Linux preserves its runner UID on bind mount.
    # Only published, non-live vectors and the test server are made readable, never secrets.
    for name in [name for name, _ in FIXTURES] + ["peer.mjs"]:
        (folder / name).chmod(0o644)
    folder.chmod(0o755)


def safe(value):
    return value.replace("Bearer public-non-live-fixture", "[non-live bearer redacted]")


def collect_diagnostics():
    commands = {
        **{f"{name}-state": ["inspect", "--format", "{{json .State}} user={{.Config.User}}", name] for name in NAMES},
        **{f"{name}-logs": ["logs", "--tail", "40", name] for name in NAMES},
        "nginx-config": ["exec", NAMES[1], "nginx", "-T", "-c", "/app/nginx.conf"],
        "resolver": ["exec", NAMES[1], "cat", "/etc/resolv.conf"],
        "network": ["network", "inspect", "--format", "{{json .Containers}}", NETWORK],
        "peer-files": ["exec", NAMES[0], "sh", "-c", "id; ls -ld /fixtures /fixtures/*"],
    }
    result = {}
    for label, command in commands.items():
        try:
            response = docker(*command, check=False)
            result[label] = {"exitCode": response.returncode, "output": safe((response.stdout + response.stderr)[-12000:])}
        except Exception as error:
            result[label] = {"error": safe(str(error))}
    return result


def write_record(record):
    output = ROOT / "artifacts/m4b"
    output.mkdir(parents=True, exist_ok=True)
    record["finished"] = datetime.now(timezone.utc).isoformat()
    rendered = safe(json.dumps(record, indent=2))
    (output / "proxy.json").write_text(rendered + "\n")
    print(rendered, flush=True)


def get(path):
    req = urllib.request.Request("http://127.0.0.1:18081" + path, headers={
        "Authorization": "Bearer public-non-live-fixture", "X-MS-CLIENT-PRINCIPAL": "forged-user",
        "X-Forwarded-Proto": "untrusted", "X-Forwarded-For": "untrusted",
    })
    try:
        response = urllib.request.urlopen(req, timeout=3)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        return response.status, response.read()


def wait_status(path, expected, attempts=40):
    last = "No HTTP response"
    for _ in range(attempts):
        try:
            status, data = get(path)
            if status == expected:
                return data
            last = f"HTTP {status}: {safe(data.decode(errors='replace')[:512])}"
        except OSError as error:
            last = safe(str(error))
        for name in NAMES:
            state = docker("inspect", "--format", "{{json .State}}", name, check=False)
            if state.returncode == 0:
                details = json.loads(state.stdout)
                if not details["Running"]:
                    raise RuntimeError(f"{name} exited ({details['ExitCode']}); {path}: {last}")
        time.sleep(0.25)
    raise RuntimeError(f"{path} never reached {expected}; last response: {last}")


def main():
    for name in [*NAMES, NETWORK]:
        kind = "network" if name == NETWORK else "container"
        if docker(kind, "inspect", name, check=False).returncode == 0:
            raise RuntimeError("Proxy verification state exists; inspect it manually before testing")
    record = {"started": datetime.now(timezone.utc).isoformat(), "actor": "local deterministic TLS fixture test", "checks": []}
    with tempfile.TemporaryDirectory(prefix="morrow-tls-fixture-") as folder:
        temp = Path(folder)
        for name, digest in FIXTURES:
            url = "https://raw.githubusercontent.com/nodejs/node/v24.22.2/test/fixtures/keys/" + name
            data = subprocess.check_output(["curl", "--fail", "--silent", "--show-error", "--location", "--max-time", "60", url])
            assert hashlib.sha256(data).hexdigest() == digest
            (temp / name).write_bytes(data)
        # This key is already public in Node's test repository, not generated or registered anywhere.
        (temp / "peer.mjs").write_text('''import https from 'node:https';import fs from 'node:fs';
https.createServer({key:fs.readFileSync('/fixtures/agent1-key.pem'),cert:fs.readFileSync('/fixtures/agent1-cert.pem')},(req,res)=>{
 res.setHeader('Content-Type','application/json');res.end(JSON.stringify({host:req.headers.host,
 authorization:req.headers.authorization,principal:req.headers['x-ms-client-principal']??null,
 forwarded:req.headers['x-forwarded-for']??null,proto:req.headers['x-forwarded-proto']}));
}).listen(443,'0.0.0.0');\n''')
        allow_peer_fixture_reads(temp)
        docker("network", "create", NETWORK)
        try:
            docker("run", "-d", "--name", NAMES[0], "--network", NETWORK,
                   "--network-alias", "agent1", "--network-alias", "wrong-name",
                   "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges:true",
                   "-v", f"{temp}:/fixtures:ro", API_IMAGE, "node", "/fixtures/peer.mjs")
            common = ["run", "-d", "--name", NAMES[1], "--network", NETWORK,
                      "--read-only", "--tmpfs", "/tmp", "--cap-drop", "ALL",
                      "--security-opt", "no-new-privileges:true", "-p", "127.0.0.1:18081:8080",
                      "-v", f"{temp / 'ca1-cert.pem'}:/fixtures/ca1-cert.pem:ro"]

            def start(host, extra=None):
                env = {"AUTH_MODE": "oidc", "PROXY_MODE": "https", "API_ORIGIN": "https://" + host,
                       "TRUSTED_API_HOST": host, "DNS_RESOLVER": "127.0.0.11",
                       "PROXY_CA_FILE": "/fixtures/ca1-cert.pem", "OIDC_ISSUER": "https://issuer.example.test",
                       "OIDC_CLIENT_ID": "public-test-client", "OIDC_SCOPES": "openid cart",
                       "PUBLIC_ORIGIN": "https://shop.example.test", **(extra or {})}
                args = common.copy()
                for key, value in env.items():
                    args += ["-e", key + "=" + value]
                docker(*args, IMAGE)

            start("agent1")
            data = json.loads(wait_status("/api/echo", 200))
            assert data == {"host": "agent1", "authorization": "Bearer public-non-live-fixture", "principal": None,
                            "forwarded": None, "proto": "https"}
            wait_status("/health/ready", 200)
            assert json.loads(get("/auth-config.json")[1])["mode"] == "oidc"
            with urllib.request.urlopen("http://127.0.0.1:18081/", timeout=3) as response:
                csp = response.headers["Content-Security-Policy"]
                assert "connect-src 'self' https://issuer.example.test;" in csp
                assert "script-src 'self';" in csp and "unsafe-inline" not in csp
            record["checks"].append("verified HTTPS/SNI/CA; bearer forwarded, spoofed identity/forwarding stripped; dependency readiness 200")
            docker("rm", "-f", NAMES[1])
            start("wrong-name")
            wait_status("/health/ready", 503)
            assert get("/api/echo")[0] == 503 and get("/")[0] == 200
            tls_logs = docker("logs", "--tail", "20", NAMES[1]).stderr
            assert 'certificate does not match "wrong-name"' in tls_logs, "Expected TLS hostname rejection, not another upstream failure"
            record["checks"].append("wrong TLS peer name rejected: static 200, API/readiness 503; no TLS bypass")
            docker("rm", "-f", NAMES[1])
            for invalid in ({"TRUSTED_API_HOST": "other"}, {"API_ORIGIN": "http://agent1"}, {"OIDC_SCOPES": 'openid"; malicious'}, {"DNS_RESOLVER": "999.0.0.1"}, {"API_ORIGIN": "https://agent1:444"}, {"OIDC_CONNECT_ORIGIN": 'https://issuer.example.test; unsafe-inline'}, {"OIDC_CONNECT_ORIGIN": 'https://issuer.example.test\nmalicious'}):
                start("agent1", invalid)
                code = docker("wait", NAMES[1]).stdout.strip()
                assert code == "1", "Unsafe proxy configuration did not fail startup"
                docker("rm", NAMES[1])
            record["checks"].append("seven unsafe proxy/auth/DNS/port/CSP configurations rejected before startup")
            record["result"] = "PASS"
        except Exception as error:
            record.update(result="FAIL", error=safe(str(error)), diagnostics=collect_diagnostics())
            write_record(record)  # Existing always-upload step retains evidence before cleanup.
            raise
        finally:
            for name in reversed(NAMES):
                docker("rm", "-f", name, check=False)
            docker("network", "rm", NETWORK)
    write_record(record)


if __name__ == "__main__":
    main()
