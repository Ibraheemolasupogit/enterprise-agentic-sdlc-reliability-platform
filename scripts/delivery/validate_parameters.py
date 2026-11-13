"""Offline C4 review-manifest validation. Never authenticates, resolves DNS or applies ARM.

Bicep cannot express CIDR overlap, full digest syntax or cross-file OIDC trust.
This preflight is mandatory for any future parameter handoff, not Azure authorization.
No real parameter file is provided. Errors name rules, never supplied values.
"""

from datetime import datetime, timezone
import ipaddress
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit
import uuid


def require(condition, rule):
    if not condition:
        raise ValueError(rule)


def validate(values, templates, now=None):
    now = now or datetime.now(timezone.utc)
    definitions = [(name, spec) for t in templates.values() for name, spec in t.get("parameters", {}).items()]
    names = {name for name, _ in definitions}
    context = {"reservedNetworks", "reservedNetworksReviewed"}
    required = {name for name, spec in definitions if "defaultValue" not in spec} | context
    require(isinstance(values, dict) and required <= values.keys() <= names | context, "Missing/unknown review-manifest field")
    effective = {name: spec["defaultValue"] for name, spec in definitions if "defaultValue" in spec}
    effective.update(values)
    for name, spec in definitions:
        value = effective[name]
        kinds = {"string": str, "int": int, "bool": bool, "array": list, "object": dict}
        require(spec["type"] in kinds and type(value) is kinds[spec["type"]], "Parameter type: " + name)
        for bound, operation in (("minLength", lambda a, b: len(a) >= b), ("maxLength", lambda a, b: len(a) <= b),
                                 ("minValue", lambda a, b: a >= b), ("maxValue", lambda a, b: a <= b)):
            if bound in spec:
                require(operation(value, spec[bound]), "Parameter bound: " + name)
        if "allowedValues" in spec:
            require(value in spec["allowedValues"], "Parameter allowed values: " + name)

    def match(name, pattern):
        require(re.fullmatch(pattern, effective[name]) is not None, "Parameter format: " + name)

    match("location", r"[a-z][a-z0-9]{1,30}")
    match("prefix", r"[a-z][a-z0-9]{2,15}")
    match("registryName", r"[a-z][a-z0-9]{4,49}")
    match("ownerTag", r"[A-Za-z0-9_.-]{1,64}")
    match("sqlServerName", r"[a-z][a-z0-9-]{1,48}[a-z0-9]")
    match("sqlDatabase", r"[A-Za-z][A-Za-z0-9_-]{0,49}")
    match("sqlAdminGroupName", r"[A-Za-z0-9_.-]{1,128}")
    try:
        group_id = uuid.UUID(effective["sqlAdminGroupObjectId"])
    except (ValueError, AttributeError):
        raise ValueError("Admin group object ID format") from None
    require(group_id.int != 0, "Admin group must be explicitly selected")
    for field, length in (("apiDigest", 64), ("frontendDigest", 64), ("releaseSha", 40), ("configSha256", 64)):
        match(field, (r"sha256:" if field.endswith("Digest") else "") + r"[a-f0-9]{" + str(length) + "}")
        require(set(effective[field].split(":")[-1]) != {"0"}, "Unselected digest/hash: " + field)

    def https(name, origin_only=False):
        value = effective[name]
        try:
            url = urlsplit(value)
            require(url.scheme == "https" and url.hostname and url.port in (None, 443) and not url.username and not url.password
                    and not url.query and not url.fragment and not re.search(r"[\s\\'\"]", value), "HTTPS trust: " + name)
            require(re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?", url.hostname) is not None, "Hostname format: " + name)
            if origin_only:
                require(value == "https://" + url.hostname, "Exact origin required: " + name)
            return "https://" + url.hostname
        except (ValueError, AttributeError):
            raise ValueError("HTTPS trust: " + name) from None

    https("publicOrigin", True)
    try:
        client = ipaddress.ip_network(effective["frontendClientCidr"], strict=True)
    except ValueError:
        raise ValueError("Aligned frontend client CIDR") from None
    require(client.version == 4 and 24 <= client.prefixlen <= 32 and not client.is_loopback and not client.is_multicast
            and not client.is_link_local and not any(client.subnet_of(ipaddress.ip_network(p)) for p in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")), "Bounded public frontend client CIDR")
    issuer_origin = https("oidcIssuer")
    require(https("oidcJwksUri") == issuer_origin == https("oidcConnectOrigin", True), "Single approved identity origin")
    require(not re.search(r"/(common|organizations|consumers)(/|$)", effective["oidcIssuer"], re.I), "Tenant-specific issuer required")
    for field in ("oidcAudience", "oidcRequiredRole", "oidcRequiredScope", "oidcSpaClientId"):
        match(field, r"[A-Za-z0-9_./:-]{1,200}")
    scopes = effective["oidcSpaScopes"].split(" ")
    require(2 <= len(scopes) <= 8 and len(set(scopes)) == len(scopes) and all(re.fullmatch(r"[A-Za-z0-9_./:-]{1,200}", s) for s in scopes)
            and "openid" in scopes and effective["oidcRequiredScope"] in scopes and "offline_access" not in scopes, "Explicit SPA scopes; no refresh/offline grant")
    require(effective["dnsResolver"] == "168.63.129.16", "Azure-provided DNS required by this topology")
    require(effective["diagnosticExportEnabled"] is False, "C4 diagnostic export must stay disabled pending live transform proof")

    networks = []
    private = [ipaddress.ip_network(s) for s in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")]
    for name in ("vnetCidr", "acaSubnetCidr", "privateEndpointSubnetCidr"):
        try:
            network = ipaddress.ip_network(effective[name], strict=True)
        except ValueError:
            raise ValueError("Aligned IPv4 CIDR required: " + name) from None
        require(network.version == 4 and any(network.subnet_of(p) for p in private), "RFC1918 network required: " + name)
        networks.append(network)
    vnet, aca, endpoint = networks
    require(aca.subnet_of(vnet) and endpoint.subnet_of(vnet) and not aca.overlaps(endpoint), "Separate contained ACA/endpoint subnets")
    require(16 <= vnet.prefixlen <= 24 and vnet.prefixlen < aca.prefixlen <= 27 and vnet.prefixlen < endpoint.prefixlen <= 28, "Reviewed network/subnet capacity")
    # ACA platform ranges cannot overlap a custom VNet; surrounding/peered ranges need owner inventory.
    reserved = [ipaddress.ip_network(n) for n in ("169.254.0.0/16", "172.30.0.0/16", "172.31.0.0/16", "192.0.2.0/24", "100.64.0.0/10")]
    require(effective["reservedNetworksReviewed"] is True and isinstance(effective["reservedNetworks"], list), "Surrounding-network inventory review required")
    try:
        reserved += [ipaddress.ip_network(n, strict=True) for n in effective["reservedNetworks"]]
    except (ValueError, TypeError):
        raise ValueError("Invalid surrounding-network CIDR") from None
    require(all(n.version == 4 and not vnet.overlaps(n) for n in reserved), "VNet overlaps platform/surrounding network")

    try:
        expiry = datetime.strptime(effective["expiresAt"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        raise ValueError("UTC expiry format") from None
    require(0 < (expiry - now).total_seconds() <= 48 * 3600, "Reviewed expiry must be future and within 48 hours; not spend authorization")
    require(effective["identityName"] in (effective["prefix"] + "-publisher", effective["prefix"] + "-release"), "Federation limited to publisher/release")
    match("verifiedSubject", r"[A-Za-z0-9_:/@.-]{10,512}")
    match("credentialName", r"[a-z][a-z0-9-]{2,63}")
    return effective


if __name__ == "__main__":
    # Only an explicitly supplied manifest; no environment/credential/account discovery.
    try:
        from policy import load_templates
        validate(json.loads(Path(sys.argv[1]).read_text()), load_templates())
    except (ValueError, KeyError, IndexError, OSError, TypeError):
        raise SystemExit("BLOCKED: invalid/missing local review manifest; no supplied values printed.") from None
    print("PASS: offline parameter contract only; authorization and live integration remain unverified.")
