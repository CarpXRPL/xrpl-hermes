# Contributing to xrpl-hermes

Thanks for helping improve the verified, model-agnostic XRPL capability layer. ☤

## Ways to Contribute

### 1. Add Knowledge Files

New files go in `knowledge/` with the next available number (currently `66`):

```
knowledge/66-xrpl-your-topic.md
```

File format: standard markdown with a `# Title` header. Prefer signer-separated, test-backed examples.
Do not add seeds/private keys, direct signing/submission, guessed wallet APIs, or third-party routes
without current first-party documentation, contract tests, provenance and explicit certification status.

### 2. Improve Tools

Tool logic lives in domain modules under `scripts/tools/` — each module exports a `COMMANDS` dict that the thin dispatcher `scripts/xrpl_tools.py` merges. To add a command: implement it using `_shared.py`, add a safe matrix invocation, add pytest coverage, classify its MCP status, and update the canonical README/SKILL/knowledge surfaces. Do not revive the retired duplicated `STANDALONE.md` bundle. Full walkthrough: [`docs/DEVELOPERS.md`](docs/DEVELOPERS.md).

Before opening a PR, run:

```bash
python3 -m pytest -q
python3 scripts/dev_test_matrix.py
```

### 3. Fix a Bug or Docs Error

- Open an issue or submit a PR.
- Keep titles descriptive: "Fix AMM pool discovery fallback" not "Fix bug."

### 4. Suggest a Feature

Open a GitHub issue describing the feature, supported network, intended certification status, first-party sources, and acceptance evidence. External ecosystem integrations must remain explicitly separated from XRPL L1.

## Pull Request Process

1. Fork the repo.
2. Create a branch: `git checkout -b feat/your-change`.
3. Commit with clear messages: `feat: add validated XRPL read helper`.
4. Push and open a PR against `main`.
5. Keep changes focused — one PR per topic.

## Style Guide

- Python: 4-space indentation, type hints on public functions.
- Markdown: ATX headers (`##`), fenced code blocks with language tags.
- Addresses: use `rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe` (testnet) for examples. Never include personal wallet addresses.

## Code of Conduct

Be respectful. Assume good faith. This is community knowledge — build it together.

---
