# Amendments

XRPL amendments are network feature flags. A public XRPL Mainnet server can understand an amendment without Mainnet having activated it.

## Read current status

```bash
xrpl-hermes amendments
xrpl-hermes amendment MPTokensV1
xrpl-hermes amendment-status MPTokensV1
```

The result distinguishes:

- `enabled`: active on the selected validated network;
- `supported`: understood by the queried server build;
- `vetoed`: the operator is not voting for activation.

A Mainnet server may know an amendment that Mainnet has not activated. This is network state, not an XRPL-Hermes capability label.

## Builder rule

A builder may exist only when XRPL-Hermes implements and tests it. If its transaction type depends on an amendment, the built-in command checks Mainnet; verify any other intended network directly before authorization.

The absence of a command means the feature is not shipped, regardless of amendment status.

## Activation

An amendment becomes enabled after the validator amendment process reaches and maintains the required consensus threshold. Activation is network-specific and permanent for that network.

Use current [XRPL amendment documentation](https://xrpl.org/resources/known-amendments) for protocol history and `amendment` for the network you are actually using.
