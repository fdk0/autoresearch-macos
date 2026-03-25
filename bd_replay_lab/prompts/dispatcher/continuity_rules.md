# Dispatcher continuity rules

Prefer `reuse_review` when:

- same PR is open
- review requested changes
- remediation is pending

Prefer `reuse_worker` when:

- same BD has active worker continuity
- worktree/branch continuity is still valid

Do not spawn fresh work when:

- stale base blocks the branch
- dispatchability seal is missing
- remediation chain should continue instead
