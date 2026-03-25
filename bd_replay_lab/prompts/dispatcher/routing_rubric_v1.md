# Dispatcher routing rubric v1

Choose in this order:

1. if remediation is pending on the same PR, prefer continuity reuse
2. if review is ready, send to review
3. if freshness or dispatchability is broken, reconcile
4. if runnable work exists on a fresh base, spawn worker
5. otherwise idle
