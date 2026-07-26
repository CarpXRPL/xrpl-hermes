# TX Ecosystem — External Dependency Card

## Status

XRPL-Hermes does not implement a TX Marketplace, TX Bridge, or TX-specific token metadata integration.

Use XRPL-native validated ledger methods for NFT state and unsigned NFT builders for intent. The user's wallet signs; Hermes verifies the validated result.

Before implementing a TX-specific integration, require current official documentation, exact network/issuer/contract identity, endpoint and schema fixtures, rate-limit/error semantics, custody/recovery terms and a current live acceptance test. Do not guess an API, bridge door, destination tag, memo or token issuer.
