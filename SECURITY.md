# Security Policy

## Private Keys

This tool NEVER stores, transmits, or requests your private keys/seeds. All transaction building happens client-side. Signing requires your own wallet (Xaman, Crossmark, or xrpl-py with your own seed).

## API Keys

Any API keys you configure (`XRPLSCAN_API_KEY`, `XRPL_TO_API_KEY`, `CLIO_NODE_URL`) are stored in your environment only and never logged or transmitted outside of direct API calls.

## Reporting

Report vulnerabilities by opening a GitHub Issue tagged `security`.
