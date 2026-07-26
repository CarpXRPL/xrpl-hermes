# XRPL amendments

Amendments introduce protocol behavior through network activation. They are not a product roadmap and they do not automatically create XRPL-Hermes commands.

## Live commands

```bash
xrpl-hermes amendments
xrpl-hermes amendment FEATURE_NAME_OR_ID
xrpl-hermes amendment-status OPTIONAL_FILTER
```

Each response reports the queried network and endpoint plus the server’s `enabled`, `supported`, and `vetoed` fields.

## Interpret the fields

- **Enabled:** active in the validated ledger on that network.
- **Supported:** the queried server build contains code for the amendment.
- **Vetoed:** the server operator is not voting to enable it.
- **Known to the server, inactive on the network:** the server understands it, but XRPL Mainnet has not activated it.

None of these fields says whether XRPL-Hermes implements a builder. Product capability comes from the installed command registry.

## Safe build sequence

1. Query XRPL Mainnet with the commands above.
2. For another network, query that network directly; these commands do not switch networks.
3. Confirm `enabled: true` when the transaction type requires it.
4. Confirm the matching builder exists in `xrpl_list_commands` or CLI command discovery.
5. Build unsigned JSON.
6. Review and authorize it in the user-controlled wallet.
7. Verify the resulting transaction from validated ledger state.

A builder warning is not network authorization. A server reporting `supported: true` is not activation.

## Activation model

Validators vote on amendments. Activation requires the protocol-defined consensus threshold to remain satisfied for the required period. Once enabled, an amendment becomes part of that network’s ledger rules.

For protocol history and validator details, use current first-party sources:

- https://xrpl.org/docs/concepts/networks-and-servers/amendments
- https://xrpl.org/resources/known-amendments
