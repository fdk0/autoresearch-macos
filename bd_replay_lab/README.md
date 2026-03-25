# BD Replay Lab

This directory scaffolds an offline replay harness for improving the BD workflow without paying full live-agent cost on every experiment.

The lab is designed around **decision-point replay**, not transcript replay.

## Why this exists

Tuning the full planner/driver/dispatcher/worker/review stack end-to-end is expensive and noisy.

This lab instead optimizes:

- **review rubrics** against issue-detection accuracy and token cost
- **dispatcher routing rubrics** against next-action accuracy and continuity/freshness correctness
- **hook prompt modules** against compactness and relevant warning coverage

The workflow is:

1. build compact cases from historical BD truth
2. render candidate prompts/rubrics
3. run an offline predictor
4. score quality + invariants + prompt cost
5. promote only strong candidates to live canaries

## Directory layout

```text
bd_replay_lab/
  candidates/
  datasets/
  predictors/
  prompts/
  schemas/
  scripts/
```

## Main concepts

### Cases

A case is one decision point.

- `review_cases/*` represent review decisions
- `dispatcher_cases/*` represent dispatcher decisions

### Candidates

A candidate manifest points at the prompt modules that define a rubric variant.

Candidates are cheap to diff and easy for autoresearch to edit.

### Predictors

The lab is model-agnostic. Evaluation scripts call an external predictor command that:

1. reads JSON from stdin
2. returns JSON to stdout

For now, this scaffold includes simple deterministic baseline predictors so the pipeline is runnable immediately.

## Example usage

### Review baseline

```bash
python3 bd_replay_lab/scripts/eval_review.py \
  --cases bd_replay_lab/datasets/review_cases/examples \
  --candidate bd_replay_lab/candidates/review/review_baseline.json \
  --predictor-command "python3 bd_replay_lab/predictors/review_baseline.py"
```

### Dispatcher baseline

```bash
python3 bd_replay_lab/scripts/eval_dispatcher.py \
  --cases bd_replay_lab/datasets/dispatcher_cases/examples \
  --candidate bd_replay_lab/candidates/dispatcher/dispatcher_baseline.json \
  --predictor-command "python3 bd_replay_lab/predictors/dispatcher_baseline.py"
```

### Batch ranking

```bash
python3 bd_replay_lab/scripts/run_batch.py \
  --lane review \
  --cases bd_replay_lab/datasets/review_cases/examples \
  --candidates-dir bd_replay_lab/candidates/review \
  --predictor-command "python3 bd_replay_lab/predictors/review_baseline.py"
```

## Direct Beads integration

If you are in a repo with an active Beads context, or you have `BEADS_DIR` pointing at the relevant local Beads workspace, you can draft replay cases directly from local `bd` state.

Example:

```bash
python3 bd_replay_lab/scripts/extract_cases_from_bd.py \
  --lane review \
  --id BD-123 \
  --id BD-124 \
  --outdir bd_replay_lab/datasets/review_cases/drafts
```

The extractor uses:

- `bd show --json --long <ID>`
- `bd comments --json <ID>`

and writes draft case JSON with:

- raw issue/comments payload
- heuristic tags
- a TODO list for completing the compact packet and expected output

This is the recommended bridge from live BD history into replay-ready datasets.

## Preparing real data

Build cases from historical BD runs, not free-form transcripts.

### Review case inputs

Keep only fields that affect review:

- PR metadata
- diff summary
- verify summary
- worker STATUS v2 summary
- DoD/scope checklist
- merge/cleanup state

### Dispatcher case inputs

Keep only fields that affect routing:

- queue snapshot
- latest worker truth
- latest review truth
- PR continuity state
- freshness/base state
- dispatchability flags

## What to optimize first

Start with **review lane issue detection**.

Why:

- high leverage
- relatively easy to label
- expensive when wrong
- more state-machine-like than worker coding behavior

Then optimize **dispatcher routing**.

## Suggested success criteria

### Review

- higher issue recall on held-out cases
- no invariant violations
- equal or better decision precision
- lower prompt token footprint

### Dispatcher

- higher next-action accuracy
- no continuity/freshness violations
- lower prompt token footprint

## Case-writing guidance

- Keep cases decision-centric and compact.
- Label expected outputs explicitly.
- Include difficulty metadata.
- Prefer real historical failures over synthetic easy wins.
- Maintain a small hard-negative gold set for promotion gates.

## Output contract

Predictors receive a payload of the form:

```json
{
  "lane": "review",
  "candidate": { "...": "..." },
  "prompt_text": "...",
  "case": { "...": "..." }
}
```

Predictors must return:

### Review

```json
{
  "decision": "approve",
  "findings": [
    { "type": "missing_verify_evidence", "severity": "high" }
  ],
  "notes": "optional"
}
```

### Dispatcher

```json
{
  "next_action": "reuse_review",
  "reason_tags": ["same_pr_remediation"]
}
```

## Notes

- JSON schemas are stored under `schemas/`.
- Prompt modules live under `prompts/`.
- This scaffold intentionally uses only the Python standard library.
