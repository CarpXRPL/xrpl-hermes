# xrpl.js with XRPL-Hermes

XRPL-Hermes emits standard unsigned XRPL transaction JSON. JavaScript and TypeScript applications can inspect or hand off that JSON with current `xrpl.js` tooling without moving key material into Hermes.

## Connect and read

```javascript
import xrpl from "xrpl"

const client = new xrpl.Client("wss://xrplcluster.com")
await client.connect()

const response = await client.request({
  command: "account_info",
  account: "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
  ledger_index: "validated"
})

console.log(response.result.account_data)
await client.disconnect()
```

## Consume an unsigned builder

```javascript
import { execFileSync } from "node:child_process"

const stdout = execFileSync("xrpl-hermes", [
  "build-payment",
  "--from", "rSOURCE",
  "--to", "rDESTINATION",
  "--amount", "1000000"
], { encoding: "utf8" })

const json = stdout
  .split("\n")
  .filter(line => !line.startsWith("#"))
  .join("\n")

const unsigned = JSON.parse(json)
console.log(unsigned)
```

## Wallet boundary

Use a current user-selected wallet/provider to display and authorize the complete decoded transaction. Do not pass seeds or private keys through environment snippets, chat, MCP arguments, or XRPL-Hermes.

After authorization and broadcast by the external wallet:

```bash
xrpl-hermes tx-info TX_HASH
```

Require validated ledger state before updating balances, ownership, orders, or application receipts.

## Network separation

XRPL Mainnet/Testnet, Xahau, and the XRPL EVM Sidechain are distinct networks. Use network-appropriate clients, addresses, transaction types, and wallet support. A JSON shape accepted by one network is not proof it is valid on another.
