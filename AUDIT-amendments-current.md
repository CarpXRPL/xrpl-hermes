# XRPL-Hermes amendment verification report

Generated: 2026-06-08 01:37:05 UTC

Source: live XRPL mainnet `feature` RPC via `https://s1.ripple.com:51234`, cross-checked against XRPL.org Known Amendments page during this update.

Counts: enabled 91, supported_not_enabled 13, vetoed 0, unsupported 0

## Builder-relevant status

| Feature | Mainnet status | Feature ID | XRPL-Hermes action |
|---|---|---|---|
| `AMM` | enabled | `8CC0774A3BF66D1D22E76BBDA8E8A232E6B6313834301B3B23E8601196AE6455` | live builder OK |
| `AMMClawback` | enabled | `726F944886BCDF7433203787E93DD9AA87FAB74DFE3AF4785BA03BEFC97ADA1F` | live builder OK |
| `Clawback` | enabled | `56B241D7A43D40354D02A9DC4C8DF5C7A1F930D92A9035C4E12291B3CA3E1C2B` | live builder OK |
| `Credentials` | enabled | `1CB67D082CF7D9102412D34258CEDB400E659352D3B207348889297A6D90F5EF` | live builder OK |
| `DID` | enabled | `DB432C3A09D9D5DFC7859F39AE5FF767ABC59AED0A9FB441E83B814D8946C109` | live builder OK |
| `MPTokensV1` | enabled | `950AE2EA4654E47F04AA8739C0B214E242097E802FD372D24047A89AB1F5EC38` | live builder OK |
| `PriceOracle` | enabled | `96FD2F293A519AE1DB6F8BED23E4AD9119342DA7CB6BAFD00953D16C54205D8B` | live builder OK |
| `TicketBatch` | enabled | `955DF3FA5891195A9DAEFA1DDC6BB244B545DDE1BAA84CBB25D5F12A8DA68A0C` | live builder OK |
| `TokenEscrow` | enabled | `138B968F25822EFBF54C00F97031221C47B1EAB8321D93C7C2AEAF85F04EC5DF` | live builder OK |
| `PermissionedDEX` | enabled | `677E401A423E3708363A36BA8B3A7D019D21AC5ABD00387BDBEA6BDE4C91247E` | live builder OK |
| `PermissionedDomains` | enabled | `A730EB18A9D4BB52502C898589558B4CCEB4BE10044500EE5581137A2E80E849` | live builder OK |
| `XRPFees` | enabled | `93E516234E35E08CA689FA33A6D38E103881F8DCB53023F728C307AA89D515A7` | live builder OK |
| `Batch` | supported, not enabled | `894646DD5284E97DECFE6674A6D6152686791C4A95F8C132CCA9BAF9E5812FB6` | security-retired; `build-batch` is unregistered |
| `PermissionDelegation` | supported, not enabled | `AE6AB9028EEB7299EBB03C7CBCC3F2A4F5FBE00EA28B8223AA3118A0B436C1C5` | build-only warning/gating required |
| `XChainBridge` | supported, not enabled | `C98D98EE9616ACD36E81FDEB8D41D349BF5F1B41DD64A0ABC1FE9AA5EA267E9C` | build-only warning/gating required |
| `DynamicMPT` | supported, not enabled | `58E92F338758479C06084E1B6BA366BAD8F75E5329A7F0EEAFFFDA51E5106B7F` | build-only warning/gating required |
| `LendingProtocol` | supported, not enabled | `565B90CA1AB2B9D42208ED10884188C64F9E19083DECB9634AAF06EB03299509` | build-only warning/gating required |
| `SingleAssetVault` | supported, not enabled | `81BD2619B6B3C8625AC5D0BC01DE17F06C3F0AB95C7C87C93715B87A4FD240D8` | build-only warning/gating required |
| `fixTokenEscrowV1` | enabled | `32B8614321F7E070419115ABEAB1742EA20F3E3AF34432B5E2F474F8083260DC` | live builder OK |
| `fixAMMClawbackRounding` | enabled | `5E9586DB3D765B4C5794658FB6BB385071E9838DF4016027E6E26820C8526724` | live builder OK |
| `fixAMMv1_3` | enabled | `7CA70A7674A26FA517412858659EBC7EDEEF7D2D608824464E6FDEFD06854E14` | live builder OK |
| `fixPriceOracleOrder` | enabled | `FF2D1E13CF6D22427111B967BD504917F63A900CECD320D6FD3AC9FA90344631` | live builder OK |

## Supported but not enabled on mainnet

- `Batch` — `894646DD5284E97DECFE6674A6D6152686791C4A95F8C132CCA9BAF9E5812FB6`
- `CryptoConditionsSuite` — `86E83A7D2ECE3AD5FA87AB2195AE015C950469ABF0B72EAACED318F74886AE90`
- `DynamicMPT` — `58E92F338758479C06084E1B6BA366BAD8F75E5329A7F0EEAFFFDA51E5106B7F`
- `fixDelegateV1_1` — `58CAABE561CD53D8EC9BD3EFDFD70E092B40F80F221430004603F7ECEFFEA56B`
- `fixNFTokenDirV1` — `0285B7E5E08E1A8E4C15636F0591D87F73CB6A7B6452A932AD72BBC8E5D1CBE3`
- `fixNFTokenNegOffer` — `36799EA497B1369B170805C078AEFE6188345F9B3E324C21E9CA3FF574E3C3D6`
- `fixXChainRewardRounding` — `2BF037D90E1B676B17592A8AF55E88DB465398B4B597AE46EECEE1399AB05699`
- `InvariantsV1_1` — `D8ED3BE0B2673496CB49DE8B5588C8805DF7B1DE203F38FE0367ACE703D36C0F`
- `LendingProtocol` — `565B90CA1AB2B9D42208ED10884188C64F9E19083DECB9634AAF06EB03299509`
- `NonFungibleTokensV1` — `3C43D9A973AA4443EF3FC38E42DD306160FBFFDAB901CD8BAA15D09F2597EB87`
- `PermissionDelegation` — `AE6AB9028EEB7299EBB03C7CBCC3F2A4F5FBE00EA28B8223AA3118A0B436C1C5`
- `SingleAssetVault` — `81BD2619B6B3C8625AC5D0BC01DE17F06C3F0AB95C7C87C93715B87A4FD240D8`
- `XChainBridge` — `C98D98EE9616ACD36E81FDEB8D41D349BF5F1B41DD64A0ABC1FE9AA5EA267E9C`

## Notes

- `Batch` is supported by current servers but not enabled on XRPL mainnet. XRPL-Hermes has security-retired and unregistered `build-batch`; amendment status does not make it an available capability.
- `MPTokensV1`, `Credentials`, `DID`, `PriceOracle`, `AMMClawback`, `TokenEscrow`, `PermissionedDEX`, `PermissionedDomains`, and `XRPFees` returned enabled on the live mainnet feature endpoint.
- `XChainBridge`, `PermissionDelegation`, `DynamicMPT`, `LendingProtocol`, and `SingleAssetVault` returned supported/not enabled and must not be documented as production mainnet features.
- Hooks remain Xahau-specific in this skill unless XRPL mainnet feature status changes.
