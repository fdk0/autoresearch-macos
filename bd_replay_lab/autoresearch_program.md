# BD replay autoresearch program

This file defines the **true autoresearch harness** for BD replay optimization.
It is intended to be loaded directly by the dedicated Codex profile for one-cycle `exec` runs.

Unlike the interactive loop prompt, this program is for **one bounded experiment cycle per process**.

## Goal

Use the real PolyTick BD workflow as source material and optimize the replay lab by repeating:

1. inspect current loop state
2. make one narrow change
3. run one evaluation cycle
4. keep only improvements; otherwise revert
5. update results/state
6. exit

The outer shell loop is responsible for repeating cycles.

## Core invariant

One process = one experiment cycle.

The process must exit after finishing exactly one of:

- one bootstrap case-extraction cycle
- one gold-set improvement cycle
- one prompt/rubric mutation + evaluation cycle

## Non-negotiable safety

- Never write to `/Users/fdk0/Projects/PolyTick`
- Never write to `/Users/fdk0/Projects/PolyTick/.beads`
- Always use `bd --readonly` when reading source BD state
- Only edit files in this repo on branch `bd-replay-lab`
- The sanitized analysis repo is read-only context only

## Loop artifacts

### State file

`bd_replay_lab/state/loop_state.json`

Tracks:

- active lane
- incumbent candidate
- best score
- next cycle index
- source paths
- latest cycle outcome

### Results ledger

`bd_replay_lab/results.tsv`

Columns:

```text
commit	lane	candidate	score	prompt_tokens	invariant_violations	status	description
```

Statuses:

- `keep`
- `discard`
- `bootstrap`
- `blocked`

## Cycle policy

Each cycle must:

1. read:
   - `bd_replay_lab/autoresearch_program.md`
   - `bd_replay_lab/state/loop_state.json`
   - `bd_replay_lab/results.tsv`
   - `bd_replay_lab/out/polytick_runbook.md`
2. decide the smallest valid next step
3. do exactly one step of meaningful progress
4. write a concise summary to `bd_replay_lab/out/last_cycle_summary.md`
5. update `loop_state.json`
6. append one row to `results.tsv`
7. exit

## Phase order

### Phase 1: bootstrap real data

If the review gold set is too small:

- extract or improve one real review case
- prefer review over dispatcher until review baseline is meaningful

### Phase 2: establish incumbent

Run the baseline candidate on the current gold set and record it.

### Phase 3: optimize

Make one narrow rubric/candidate change and evaluate it.

If better and invariant-safe:

- keep
- commit

Else:

- revert
- record discard

## Narrow-change rule

Allowed experiment types:

- reorder one rubric section
- add one blocking rule
- shorten one prompt section
- improve one finding taxonomy item
- improve one extraction/scoring script only if it unblocks evaluation quality

Disallowed experiment types:

- giant monolithic prompt rewrite
- schema churn without necessity
- changing several unrelated things in one cycle

## Commit rule

Commit only if the cycle is a real improvement or a necessary bootstrap/tooling improvement.

Suggested format:

- `autoresearch(review): <short description>`
- `autoresearch(dispatcher): <short description>`
- `autoresearch(tooling): <short description>`

## Stop rule

The one-cycle process must exit after recording exactly one cycle.

The outer shell loop decides whether to start the next cycle.
