# Review rubric v1

Check in this order:

1. required verify evidence exists and passes
2. worker STATUS v2 is present and consistent
3. changed files are within scope
4. mergeability / stale-base / cleanup blockers
5. only then consider approval

High-severity findings usually block approval:

- missing required verify evidence
- missing worker STATUS v2
- scope violations

Medium-severity findings usually request changes:

- stale base
- missing cleanup or merge hygiene follow-through

If there are no blocking findings, approve.
