# C5-F1 Semgrep CE control fixtures

Synthetic, intentionally unsafe and safe code used **only** as local control
inputs for [`scripts/sast/feasibility.py`](../../../../scripts/sast/feasibility.py).
None of these files is imported, built, executed or deployed. They contain no
real credentials, hosts or tokens; placeholder values are deliberately inert.

Annotations follow the Semgrep test convention and apply to the next code line:

| Annotation | Meaning in the harness |
| --- | --- |
| `ruleid: <id>` | Rule must report a finding on the next line (positive control) |
| `ok: <id>` | Rule must not report on the next line (negative/safe control) |
| `todoruleid: <id>` | Known CE/rule blind spot: expected miss, recorded as a coverage gap |

Any finding without a matching `ruleid` is counted as a false positive. Files in
`malformed/` must produce a parse error; they are never counted as clean.
Production scans exclude this directory by explicit classification, not by an
ignore file. Original work under the repository [MIT license](../../../../LICENSE).
