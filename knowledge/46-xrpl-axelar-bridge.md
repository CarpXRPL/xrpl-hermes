# Axelar and XRPL — Certification Boundary

## Release status

**Registration lookup: narrow read-only. GMP search: partial. Transfers: not implemented.**

XRPL-Hermes provides public Axelar status lookups only. It does not build, sign, submit, recover, or certify an XRPL/Axelar transfer.

## What the tools actually do

### `bridge-status [CHAIN ...]`

Reads Axelarscan's chain-registration API and returns selected chain metadata and the gateway field supplied by that API.

A registration record does **not** prove:

- a route is operational;
- a specific asset or amount is supported;
- liquidity is available;
- fees/minimums are acceptable;
- contracts are unpaused;
- a transfer will complete.

### `bridge-tx TXHASH`

Searches Axelarscan's **GMP index** for a source transaction hash. It is not a general ITS token-transfer receipt checker. “Not found” can mean non-GMP activity, an unknown hash, or indexing delay.

## Transfer boundary

Current Axelar XRPL ITS documentation requires an exact memo schema, including operation-specific fields such as:

- `type=interchain_transfer` for ITS transfer intents;
- destination chain and destination address;
- gas fee amount;
- operation-specific fields defined by the current official schema.

GMP contract calls use a different operation type such as `type=call_contract`. Do not infer either schema from generic bridge examples. Malformed gateway payments can strand funds and may not be automatically refunded.

Before supporting a transfer, independently establish all of the following from current first-party sources:

1. exact source/destination network identities;
2. current gateway/contract addresses;
3. supported asset identity and representation;
4. exact memo/schema and encoding;
5. minimum, fee, gas and recovery behavior;
6. pause/status checks;
7. Testnet round-trip and malformed-input recovery evidence;
8. external-wallet decoded preview and signing;
9. destination-side finalized receipt verification.

Until those gates pass, XRPL-Hermes may research and review an unsigned intent but must not label it ready to transfer.

## Official sources

Re-check before every implementation:

- https://docs.axelar.dev/
- https://docs.axelar.dev/dev/send-tokens/interchain-tokens/xrpl/
- https://axelarscan.io/
