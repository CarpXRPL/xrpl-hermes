# Arweave Storage — Cost-Estimate Boundary

## Release status

**Base-network fee estimate: narrow read-only. Upload/deployment: quarantined.**

XRPL-Hermes can ask a public Arweave gateway for the current base-network price of storing a byte count and can report gateway network information. It never uploads content and never handles an Arweave/JWK wallet.

```bash
python3 scripts/xrpl_tools.py arweave-cost 1MB
```

The output includes:

- requested byte count;
- quoted Winston and AR;
- gateway URL;
- gateway-reported network/height when available;
- fetch time;
- an explicit statement that bundler/service fees are excluded.

## What the estimate does not prove

A price response does not prove:

- successful transaction creation or upload;
- bundler/Irys pricing or availability;
- transaction confirmation;
- content retrievability from every gateway;
- content-policy acceptance;
- ArNS resolution;
- indefinite availability from a specific URL.

Avoid absolute “stored forever” or “permanent availability” guarantees. Arweave is designed for durable storage, while retrieval remains dependent on network/gateway behavior and content policies.

## Upload boundary

The former Bundlr, direct HTTP upload, JWK signing, ArkB, ArNS, and deployment snippets were removed because they were stale, unsafe, or not reproduced.

Before restoring upload support, require:

1. current first-party SDK/tool and endpoint;
2. isolated user-controlled wallet/signing;
3. exact base fee versus service/bundler fee;
4. a small Testnet or deliberately funded production upload;
5. confirmed transaction ID and network inclusion;
6. retrieval checks from multiple gateways;
7. documented content type, hash, size and provenance;
8. failure/retry behavior without secret exposure.

## Official sources

- https://docs.arweave.org/
- https://arweave.net/info

Source review date: **2026-07-26**.
