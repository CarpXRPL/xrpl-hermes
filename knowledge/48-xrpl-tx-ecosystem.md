# TX Ecosystem — External Dependency Boundary

## Status

**Not implemented.** XRPL-Hermes has no TX-specific marketplace, bridge, token-metadata, wallet, or custody integration.

XRPL-Hermes does not currently certify:

- a TX Marketplace API;
- a TX Bridge route, door account, destination tag, asset mapping or status API;
- TX token issuer/market metadata;
- direct marketplace or bridge signing/submission;
- any provider's current fee, custody or recovery behavior.

## Safe approach

For NFT state, use XRPL-native validated ledger methods and unsigned builders:

- `nft-info`
- `nft-offers`
- `build-nft-create-offer`
- `build-nft-accept-offer`
- `build-nft-cancel-offer`
- `build-nft-burn`

The user's wallet signs; Hermes verifies the validated transaction and resulting NFT/offer state.

For any TX-specific integration, require current official documentation, exact endpoint/schema fixtures, network and issuer identity, rate-limit/error behavior, license/terms and a current live acceptance test. If an official source is unavailable, report the integration as unavailable rather than guessing.

Third-party explorer/API output is supplementary and must not replace validated ledger evidence.
