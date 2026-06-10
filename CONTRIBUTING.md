# Contributing to xrpl-hermes

Thanks for helping build the definitive XRPL knowledge base. ☤

## Ways to Contribute

### 1. Add Knowledge Files

New files go in `knowledge/` with the next available number (currently `66`):

```
knowledge/66-xrpl-your-topic.md
```

File format: standard markdown with a `# Title` header and practical Python/Solidity code examples. Use real public endpoints (xrplcluster.com, xrpl.to). Keep internal API keys out.

### 2. Improve Tools

Tool logic lives in domain modules under `scripts/tools/` — each module exports a `COMMANDS` dict that the thin dispatcher `scripts/xrpl_tools.py` merges. To add a command: implement it in the right module using the `_shared.py` helpers, add a safe invocation to `scripts/dev_test_matrix.py`, add pytest coverage, and document it in `STANDALONE.md`. Full walkthrough: [`docs/DEVELOPERS.md`](docs/DEVELOPERS.md).

Before opening a PR, run:

```bash
python3 -m pytest -q
python3 scripts/dev_test_matrix.py
```

### 3. Fix a Bug or Docs Error

- Open an issue or submit a PR.
- Keep titles descriptive: "Fix AMM pool discovery fallback" not "Fix bug."

### 4. Suggest a Feature

Open a GitHub issue describing the feature and what problem it solves. XRPL ecosystem coverage (Flare, Axelar, Xahau, EVM) is especially welcome.

## Pull Request Process

1. Fork the repo.
2. Create a branch: `git checkout -b feat/your-change`.
3. Commit with clear messages: `feat: add Xahau hook deployment example`.
4. Push and open a PR against `main`.
5. Keep changes focused — one PR per topic.

## Style Guide

- Python: 4-space indentation, type hints on public functions.
- Markdown: ATX headers (`##`), fenced code blocks with language tags.
- Solidity: pragma `^0.8.20`, OpenZeppelin imports where applicable.
- Addresses: use `rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe` (testnet) for examples. Never include personal wallet addresses.

## Code of Conduct

Be respectful. Assume good faith. This is community knowledge — build it together.

---
