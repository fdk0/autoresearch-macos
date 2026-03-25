# BD replay lab autoresearch program

This program is for **offline autoresearch on the BD workflow**, not for live task execution.

The source of truth is a **real Beads/Dolt workflow** (currently PolyTick), but the optimization loop runs only on extracted replay cases and prompt/rubric files in this repo.

## Goal

Improve the BD workflow significantly while keeping cost controlled by:

- extracting compact review/dispatcher decision packets from real history
- evaluating offline instead of replaying the full live agent stack
- mutating review/dispatcher prompt modules
- keeping only candidates that improve score without invariant violations

## Hard boundaries

- Never write to the source BD workspace during replay extraction.
- Always use `bd --readonly` when reading the source Beads state.
- Never mutate the live PolyTick repo or its `.beads` state.
- All edits happen only in this repo (`autoresearch-macos`) on the `bd-replay-lab` branch.
- The analysis clone exists only as a safe repo context for read-only inspection.

## Source layout

- Live source repo: real working BD repo
- Source Beads workspace: real `.beads` for that repo
- Analysis repo: sanitized clone with no active `.beads`
- Replay lab repo: this repo

## Setup flow

1. Validate the local PolyTick source + analysis clone configuration.
2. Extract draft review or dispatcher cases from the real Beads workspace.
3. Convert drafts into compact gold-set packets.
4. Run baseline evaluation.
5. Mutate prompt/rubric candidates.
6. Re-run offline evals.
7. Keep only candidates that improve score and preserve invariants.

## First target

Optimize **review lane** first.

Success means:

- better issue recall on real held-out review cases
- no invariant violations
- equal or better decision accuracy
- lower or comparable prompt token cost

## Core loop

LOOP:

1. Read current gold-set metrics.
2. Pick one narrow review or dispatcher rubric change.
3. Edit only candidate manifests / prompt modules in `bd_replay_lab/prompts/` and `bd_replay_lab/candidates/`.
4. Run offline evals.
5. Compare against incumbent.
6. If better, keep and commit.
7. If not better, revert and try another candidate.

Do not expand scope into full live-agent tuning unless offline replay evidence is already strong.

## Keep changes small

Good changes:

- reorder checks in the rubric
- tighten blocking conditions
- improve finding taxonomy
- shorten prompt modules without losing accuracy

Bad changes:

- giant monolithic prompt rewrites
- changing lane invariants
- changing schemas mid-loop without a migration reason

## Useful commands

Validate local PolyTick setup:

```bash
python3 bd_replay_lab/scripts/polytick_context.py
```

Prepare local runbook/output directories:

```bash
python3 bd_replay_lab/scripts/bootstrap_polytick_lab.py
```

Extract draft review cases:

```bash
python3 bd_replay_lab/scripts/extract_cases_from_bd.py \
  --lane review \
  --id <BD-ID> \
  --beads-dir /path/to/live/.beads \
  --repo-root /path/to/analysis-clone \
  --outdir bd_replay_lab/datasets/review_cases/drafts
```

Run baseline review eval:

```bash
python3 bd_replay_lab/scripts/eval_review.py \
  --cases bd_replay_lab/datasets/review_cases/examples \
  --candidate bd_replay_lab/candidates/review/review_baseline.json \
  --predictor-command "python3 bd_replay_lab/predictors/review_baseline.py"
```

Batch-rank review candidates:

```bash
python3 bd_replay_lab/scripts/run_batch.py \
  --lane review \
  --cases bd_replay_lab/datasets/review_cases/examples \
  --candidates-dir bd_replay_lab/candidates/review \
  --predictor-command "python3 bd_replay_lab/predictors/review_baseline.py"
```

## Stop condition

Stop when one of these is true:

- no candidate improves the held-out score
- gold set is too weak and needs more real cases
- invariants are at risk
- review lane improvements plateau and it is time to move to dispatcher
