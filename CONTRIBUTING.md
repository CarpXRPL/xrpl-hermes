# Contributing to xrpl-hermes

Thanks for helping build the definitive XRPL knowledge base. ☤

## Ways to Contribute

### 1. Add Knowledge Files

New files go in `knowledge/` with the next available number:

```
knowledge/56-xrpl-your-topic.md
```

File format: standard markdown with a `# Title` header and practical Python/Solidity code examples. Use real public endpoints (xrplcluster.com, xrpl.to). Keep internal API keys out.

### 2. Improve Tools

The CLI tools live in `scripts/xrpl_tools.py`. Each tool is a function registered in the TOOLS dict. Add new tools following the existing pattern.

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
