"""Small reference model for the candidate KQL projection; NOT a Kusto executor.

Tests bind the exact compiled KQL to this restricted grammar and inject non-live
canaries into Log/extra fields. Azure schema/transform/ingestion tests remain C7.
Platform names/image/revision metadata must come from the reviewed deployment.
"""

import re


def project_candidate(query, row):
    pattern = r'source \| project (TimeGenerated, ContainerAppName, RevisionName(?:, ContainerImage)?), Log = case\((.*)\), _ResourceId'
    match = re.fullmatch(pattern, query)
    if not match:
        raise ValueError("Unsupported diagnostic projection; no pass-through fallback")
    comparisons = re.findall(r'Log contains "([A-Za-z_]+)", "([A-Z]+)", ', match[2])
    rebuilt = "".join(f'Log contains "{needle}", "{category}", ' for needle, category in comparisons) + '"REDACTED"'
    if match[2] != rebuilt or comparisons != [("ENOTFOUND", "DNS"), ("certificate", "TLS"), ("DATABASE_UNAVAILABLE", "SQL"), ("schema", "SCHEMA")]:
        raise ValueError("Unreviewed diagnostic classifier")
    result = {name: row.get(name) for name in match[1].split(", ") + ["_ResourceId"]}
    text = str(row.get("Log", "")).lower()
    result["Log"] = next((category for needle, category in comparisons if needle.lower() in text), "REDACTED")
    return result
