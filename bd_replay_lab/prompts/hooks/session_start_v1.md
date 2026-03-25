# Hook session_start v1

Inject only the current lane, current state warnings, and the smallest relevant reminders.

Do not restate large prompt bodies when:

- lane is already known
- no drift flags are present
- no continuity/freshness warning is active
