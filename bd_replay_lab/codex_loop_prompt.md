# Codex loop prompt for BD replay autoresearch

Use this prompt **with** the normal Codex/Assistant kernel, not instead of it.

This file is the task-specific operating prompt for the offline BD replay loop.

## Mission

Improve the BD workflow using **offline replay** over real historical Beads/Dolt state from PolyTick.

You are not running the live BD system.
You are optimizing the **control plane**:

- review rubrics
- dispatcher routing rubrics
- compact hook prompt modules
- replay packet quality

## Non-negotiable safety boundaries

- Never write to the live PolyTick repo.
- Never write to the live PolyTick `.beads` workspace.
- Always use `bd --readonly` when reading the source Beads state.
- Do all edits only in this repo on branch `bd-replay-lab`.
- Use the sanitized analysis clone only as a safe repo context for read-only BD access.

## Local environment

Use these paths exactly unless they are invalid at runtime:

- Live source repo: `/Users/fdk0/Projects/PolyTick`
- Live source beads: `/Users/fdk0/Projects/PolyTick/.beads`
- Sanitized analysis repo: `/Users/fdk0/Projects/PolyTick-bd-analysis`
- Replay lab repo: `/Users/fdk0/git/autoresearch-macos`

Before doing anything else, validate the setup:

```bash
python3 bd_replay_lab/scripts/polytick_context.py
python3 bd_replay_lab/scripts/bootstrap_polytick_lab.py
```

## First objective

Optimize the **review lane** first.

Primary success criteria:

- higher issue recall on real held-out review cases
- no invariant violations
- no regression in decision accuracy
- equal or lower prompt token cost when possible

## What to edit

Normally edit only these areas:

- `bd_replay_lab/prompts/review/*.md`
- `bd_replay_lab/prompts/dispatcher/*.md`
- `bd_replay_lab/candidates/**/*.json`
- replay lab scripts only when needed for extraction, scoring, or packet quality

Do not casually change:

- schemas
- lane invariants
- live workflow contracts

## Workflow

1. Validate PolyTick replay context.
2. If the gold set is too small, extract more draft cases from live Beads state using read-only mode.
3. Convert the best drafts into compact gold cases.
4. Run baseline evals.
5. Make one narrow prompt/rubric improvement.
6. Re-run evals.
7. Keep the change only if it improves score without violating invariants.
8. Commit winners. Revert losers.
9. Continue until improvements plateau or the gold set becomes the bottleneck.

## Extraction commands

Draft review case:

```bash
python3 bd_replay_lab/scripts/extract_cases_from_bd.py \
  --lane review \
  --id <BD-ID> \
  --beads-dir /Users/fdk0/Projects/PolyTick/.beads \
  --repo-root /Users/fdk0/Projects/PolyTick-bd-analysis \
  --outdir bd_replay_lab/datasets/review_cases/drafts
```

Draft dispatcher case:

```bash
python3 bd_replay_lab/scripts/extract_cases_from_bd.py \
  --lane dispatcher \
  --id <BD-ID> \
  --beads-dir /Users/fdk0/Projects/PolyTick/.beads \
  --repo-root /Users/fdk0/Projects/PolyTick-bd-analysis \
  --outdir bd_replay_lab/datasets/dispatcher_cases/drafts
```

## Evaluation commands

Review baseline:

```bash
python3 bd_replay_lab/scripts/eval_review.py \
  --cases bd_replay_lab/datasets/review_cases/gold \
  --candidate bd_replay_lab/candidates/review/review_baseline.json \
  --predictor-command "python3 bd_replay_lab/predictors/review_baseline.py"
```

Dispatcher baseline:

```bash
python3 bd_replay_lab/scripts/eval_dispatcher.py \
  --cases bd_replay_lab/datasets/dispatcher_cases/gold \
  --candidate bd_replay_lab/candidates/dispatcher/dispatcher_baseline.json \
  --predictor-command "python3 bd_replay_lab/predictors/dispatcher_baseline.py"
```

Batch ranking:

```bash
python3 bd_replay_lab/scripts/run_batch.py \
  --lane review \
  --cases bd_replay_lab/datasets/review_cases/gold \
  --candidates-dir bd_replay_lab/candidates/review \
  --predictor-command "python3 bd_replay_lab/predictors/review_baseline.py"
```

## Experiment policy

- Prefer many small rubric mutations over giant rewrites.
- One variable at a time when possible.
- Preserve the best-known candidate.
- If a result is ambiguous, improve the gold set before making more prompt changes.

## Commit policy

Commit only:

- extraction or packet-quality improvements
- better candidates that beat incumbent on replay
- runbook or tooling fixes needed for the loop

Do not commit:

- local secrets
- local path configs
- generated replay outputs under `bd_replay_lab/out/`

## Stop condition

Stop only when one of these is true:

- no more meaningful improvements are found
- the gold set is too weak and requires human labeling decisions
- invariant-preserving progress stalls
- the user explicitly redirects scope

## Reporting

When you finish a loop segment, report:

- what changed
- which candidate or prompt changed
- before/after metrics
- whether the change was kept or reverted
- the next best experiment
