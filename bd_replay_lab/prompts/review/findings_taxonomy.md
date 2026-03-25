# Review findings taxonomy

Preferred finding types:

- `missing_verify_evidence`
- `missing_worker_status_v2`
- `out_of_scope_change`
- `stale_base`
- `merge_hygiene_gap`
- `cleanup_gap`

Severity guidance:

- `high`: direct gate violation, missing machine evidence, major scope break
- `medium`: remediation required before merge but not fundamental execution fraud
- `low`: advisory or non-blocking improvement
