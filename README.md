# autoresearch-macos

![teaser](progress.png)

*One day, frontier AI research used to be done by meat computers in between eating, sleeping, having other fun, and synchronizing once in a while using sound wave interconnect in the ritual of "group meeting". That era is long gone. Research is now entirely the domain of autonomous swarms of AI agents running across compute cluster megastructures in the skies. The agents claim that we are now in the 10,205th generation of the code base, in any case no one could tell if that's right or wrong as the "code" is now a self-modifying binary that has grown beyond human comprehension. This repo is the story of how it all began. -@karpathy, March 2026*.

The idea: give an AI agent a small but real LLM training setup and let it experiment autonomously overnight. It modifies the code, trains for 5 minutes, checks if the result improved, keeps or discards, and repeats. You wake up in the morning to a log of experiments and (hopefully) a better model. The training code here is a simplified single-GPU implementation of [nanochat](https://github.com/karpathy/nanochat). The core idea is that you're not touching any of the Python files like you normally would as a researcher. Instead, you are programming the `program.md` Markdown files that provide context to the AI agents and set up your autonomous research org. The default `program.md` in this repo is intentionally kept as a bare bones baseline, though it's obvious how one would iterate on it over time to find the "research org code" that achieves the fastest research progress, how you'd add more agents to the mix, etc. A bit more context on this project is here in this [tweet](https://x.com/karpathy/status/2029701092347630069) and [this tweet](https://x.com/karpathy/status/2031135152349524125).

This fork tracks [`karpathy/autoresearch`](https://github.com/karpathy/autoresearch) and keeps a small compatibility patchset on the **`macos`** branch so the project remains usable on Apple Silicon / MPS without giving up straightforward upstream syncs.

## Open source project worth to look at

Open source collabaration platform for agentic swarms in organizations and communityies. 

[SentientWave Automata](https://github.com/sentientwave/automata)

## How it works

The repo is deliberately kept small and only really has three files that matter:

- **`prepare.py`** — fixed constants, one-time data prep (downloads training data, trains a BPE tokenizer), and runtime utilities (dataloader, evaluation). In this fork it also centralizes backend detection helpers.
- **`train.py`** — the single file the agent edits. Contains the full GPT model, optimizer (Muon + AdamW), and training loop. Everything is fair game: architecture, hyperparameters, optimizer, batch size, etc. **This file is edited and iterated on by the agent**.
- **`program.md`** — baseline instructions for one agent. Point your agent here and let it go. **This file is edited and iterated on by the human**.

By design, training runs for a **fixed 5-minute time budget** (wall clock, excluding startup/compilation), regardless of the details of your compute. The metric is **val_bpb** (validation bits per byte) — lower is better, and vocab-size-independent so architectural changes are fairly compared.

If you are new to neural networks, this ["Dummy's Guide"](https://x.com/hooeem/status/2030720614752039185) looks pretty good for a lot more context.

## Quick start

**Requirements:** Apple Silicon Mac (M1/M2/M3/M4 with Metal/MPS support) or a single NVIDIA GPU, Python 3.10+, [uv](https://docs.astral.sh/uv/).

**Recommended branch:** use `macos`. It is the maintained branch that rebases/merges onto `karpathy/autoresearch` and carries the macOS compatibility delta.

```bash

# 1. Install uv project manager (if you don't already have it)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install dependencies
uv sync

# 3. Download data and train tokenizer (one-time, ~2 min)
uv run prepare.py

# 4. Manually run a single training experiment (~5 min)
uv run train.py
```

If the above commands all work ok, your setup is working and you can go into autonomous research mode.

**Platform support.** This fork targets **macOS (Apple Silicon / MPS)** first, while keeping CUDA support intact and retaining a CPU fallback path for setup/smoke testing. Compared with upstream, it:

- auto-detects `cuda` / `mps` / `cpu`
- uses FlashAttention on CUDA when the optional kernels stack is available
- falls back to PyTorch SDPA when FlashAttention is unavailable
- avoids `torch.compile` paths that are unstable on MPS
- uses smaller default training settings that fit typical Apple Silicon machines better

## Running the agent

Simply spin up your Claude/Codex or whatever you want in this repo (and disable all permissions), then you can prompt something like:

```
Hi have a look at program.md and let's kick off a new experiment! let's do the setup first.
```

The `program.md` file is essentially a super lightweight "skill".

### Codex stop guard for unattended runs

This repo includes a repo-local Codex hook configuration in `.codex/hooks.json` so unattended autoresearch sessions do not stop after a single completed experiment.

Arm it when you start an `autoresearch/<tag>` branch:

```bash
python3 scripts/codex_hooks/autoresearch_guard.py arm --branch autoresearch/<tag>
```

Check status:

```bash
python3 scripts/codex_hooks/autoresearch_guard.py status
```

When you explicitly want Codex to stop or pause the loop, disarm it first:

```bash
python3 scripts/codex_hooks/autoresearch_guard.py disarm
```

## BD replay lab

This repo also includes a `bd_replay_lab/` scaffold for improving Beads/Codex BD workflows using **offline replay** instead of full live-agent loops on every experiment.

It is aimed at:

- review rubric tuning
- dispatcher routing tuning
- hook/context compression experiments
- direct case extraction from local Beads state using the `bd` CLI

Start here:

```bash
sed -n '1,220p' bd_replay_lab/README.md
```

Example baseline evaluations:

```bash
python3 bd_replay_lab/scripts/eval_review.py \
  --cases bd_replay_lab/datasets/review_cases/examples \
  --candidate bd_replay_lab/candidates/review/review_baseline.json \
  --predictor-command "python3 bd_replay_lab/predictors/review_baseline.py"

python3 bd_replay_lab/scripts/eval_dispatcher.py \
  --cases bd_replay_lab/datasets/dispatcher_cases/examples \
  --candidate bd_replay_lab/candidates/dispatcher/dispatcher_baseline.json \
  --predictor-command "python3 bd_replay_lab/predictors/dispatcher_baseline.py"
```

## Project structure

```
prepare.py      — constants, data prep + runtime utilities
train.py        — model, optimizer, training loop (agent modifies this)
program.md      — agent instructions
pyproject.toml  — dependencies
```

## Design choices

- **Single file to modify.** The agent only touches `train.py`. This keeps the scope manageable and diffs reviewable.
- **Fixed time budget.** Training always runs for exactly 5 minutes, regardless of your specific platform. This means you can expect approx 12 experiments/hour and approx 100 experiments while you sleep. There are two upsides of this design decision. First, this makes experiments directly comparable regardless of what the agent changes (model size, batch size, architecture, etc). Second, this means that autoresearch will find the most optimal model for your platform in that time budget. The downside is that your runs (and results) become not comparable to other people running on other compute platforms.
- **Self-contained.** No external dependencies beyond PyTorch and a few small packages. No distributed training, no complex configs. One GPU, one file, one metric.

## Platform support notes

Upstream is optimized around a single NVIDIA GPU and FlashAttention-oriented kernels. This fork keeps closer to upstream than a full rewrite, but carries a narrow portability layer so it also works on Apple Silicon.

The intended maintenance model is:

- `upstream/master` = source of truth from `karpathy/autoresearch`
- `macos` = maintained branch in this repo
- small compatibility patchset on top for MPS / generic SDPA fallback / smaller-device defaults

If you're going to try running autoresearch on smaller computers (MacBooks etc.), these are still the main knobs worth tuning:

1. To get half-decent results I'd use a dataset with a lot less entropy, e.g. this [TinyStories dataset](https://huggingface.co/datasets/karpathy/tinystories-gpt4-clean). These are GPT-4 generated short stories. Because the data is a lot narrower in scope, you will see reasonable results with a lot smaller models (if you try to sample from them after training).
2. You might experiment with decreasing `vocab_size`, e.g. from 8192 down to 4096, 2048, 1024, or even - simply byte-level tokenizer with 256 possibly bytes after utf-8 encoding.
3. In `prepare.py`, you'll want to lower `MAX_SEQ_LEN` a lot, depending on the computer even down to 256 etc. As you lower `MAX_SEQ_LEN`, you may want to experiment with increasing `DEVICE_BATCH_SIZE` in `train.py` slightly to compensate. The number of tokens per fwd/bwd pass is the product of these two.
4. Also in `prepare.py`, you'll want to decrease `EVAL_TOKENS` so that your validation loss is evaluated on a lot less data.
5. In `train.py`, the primary single knob that controls model complexity is the `DEPTH` (default 4 on the `macos` branch). A lot of variables are just functions of this, so e.g. lower it down even further if needed.
6. You'll want to most likely use `WINDOW_PATTERN` of just "L", because "SSSL" uses alternating banded attention pattern that may be very inefficient for you. Try it.
7. You'll want to lower `TOTAL_BATCH_SIZE` a lot, but keep it powers of 2, e.g. down to `2**14` (~16K) or so even, hard to tell.

I think these are the most reasonable hyperparameters to play with. Ask your favorite coding agent for help and copy-paste this guide together with the source.

## Notable forks

- [miolini/autoresearch-macos](https://github.com/miolini/autoresearch-macos) (MacOS)
- [trevin-creator/autoresearch-mlx](https://github.com/trevin-creator/autoresearch-mlx) (MacOS)
- [jsegov/autoresearch-win-rtx](https://github.com/jsegov/autoresearch-win-rtx) (Windows)
- [andyluo7/autoresearch](https://github.com/andyluo7/autoresearch) (AMD)

## License

MIT
