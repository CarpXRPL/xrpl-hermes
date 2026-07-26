# Arweave Cost — Narrow Read Card

## Certified surface

`arweave-cost SIZE` requests a base-network storage quote from a public Arweave gateway and reads gateway network information.

```bash
python3 scripts/xrpl_tools.py arweave-cost 1MB
```

The tool never uploads and never handles wallet keys. Treat the result as a point-in-time base fee estimate excluding bundler/service margins.

## Not certified

- upload or deployment;
- Bundlr/Irys integration;
- wallet/JWK signing;
- ArNS/ArkB routes;
- retrieval from every gateway;
- absolute “permanent availability” guarantees.

Upload support requires current first-party tooling, user-controlled signing, fee separation, a confirmed test upload and multi-gateway retrieval evidence.

Official sources:

- https://docs.arweave.org/
- https://arweave.net/info
