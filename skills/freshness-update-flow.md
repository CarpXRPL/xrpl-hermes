# Freshness update flow

Use this when checking whether XRPL-Hermes claims still match current networks, SDKs, or external providers.

## 1. Gather current evidence

- XRPL server and amendments: `server-info`, `amendments`, `amendment NAME`
- xrpl-py: current PyPI release and compatibility tests
- xrpl.js: current npm release and example tests
- External integrations: current first-party Xaman, Xahau, XRPL EVM, Flare, Axelar, and Arweave documentation plus live read fixtures

Record the source, observed value, and affected file. If evidence conflicts or cannot be reproduced, remove the claim or mark it unavailable rather than guessing.

## 2. Update durable guidance

- Prefer query instructions over copied current values.
- Keep network amendment status separate from product capability.
- Keep external credentials and signing outside MCP.
- Do not add an implementation to the advertised capability map until the command and tests exist.
- Update dependency pins only after compatibility passes.

## 3. Verify

```bash
python3 -m pytest -q
python3 scripts/dev_test_matrix.py
python3 scripts/audit_project_quality.py
python3 -m scripts.package_acceptance
python3 -m scripts.xrpl_tools server-info
git diff --check
```

If JavaScript examples changed:

```bash
cd examples/js
npm install
node --check *.js
```

## 4. Review the public surface

Read the README, quick start, capability map, limitations, security policy, and release notes as a new user. Remove internal audit narration, generated timestamps, tombstones, and roadmap items presented as features.

Commit only after the exact candidate passes and the public capability table maps to reachable commands or a concrete external-setup path.
