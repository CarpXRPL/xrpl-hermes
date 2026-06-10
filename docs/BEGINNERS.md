# New to XRPL and agent CLIs? Start here.

This guide assumes nothing: no XRPL background, no wallet, no agent experience. By the end you will have queried the live ledger, understood the four or five concepts that matter, and built (not sent) your first transaction — without ever touching a private key.

If you already know XRPL and just want to install fast, use [`QUICKSTART.md`](../QUICKSTART.md) instead.

## The one safety rule before anything else

**Never type, paste, or upload your wallet seed (the `s...` secret) anywhere in this toolkit, in an AI chat, or in an agent prompt.** Nothing in xrpl-hermes needs it. Every transaction tool here produces *unsigned* JSON that you sign yourself in your own wallet (Xaman, Crossmark, or a hardware-backed signer). If any tool, bot, or chat ever asks for your seed, stop — that is how funds get stolen.

## What is the XRPL, in five concepts

1. **Accounts and reserves.** An XRPL account is an `r...` address. Part of its XRP balance is locked as a *reserve* (a base reserve, plus a small amount per object the account owns — trust lines, offers, escrows). Reserved XRP is not spendable. The `account` command shows you `BalanceXRP`, `ReserveXRP`, and `SpendableXRP` so you never have to compute this yourself.

2. **Drops.** XRP amounts on the ledger are integers in *drops*: 1 XRP = 1,000,000 drops. When a command asks for `--amount 1000000`, that is 1 XRP.

3. **Trust lines and issued tokens.** Every token other than XRP (USD, RLUSD, meme tokens…) is an *issued token*: an IOU from a specific issuer account. To hold one you first create a *trust line* to that issuer — an explicit "I agree to hold up to N of this token from this issuer." A token is identified by its currency code **and** its issuer; "USD from Bitstamp" and "USD from anyone else" are different assets. Each trust line also raises your reserve slightly.

4. **Transactions and signing.** Every change to the ledger is a signed transaction. Building the transaction JSON requires no secrets; only *signing* it does. That split is the whole safety model of this toolkit: we build, your wallet signs.

5. **Amendments.** XRPL gains features through *amendments* that validators vote on. A feature can exist in documentation and on test networks but not be enabled on mainnet yet. The `amendment` command checks the live status, and the builders for newer features check it for you automatically.

## What is an "agent CLI"?

Two ways to use this repo, same tools underneath:

- **You drive:** run commands yourself in a terminal (`python3 -m scripts.xrpl_tools ...`). Good for learning — start here.
- **An agent drives:** an AI assistant (Hermes, Claude Code, Cursor, Codex, or any MCP client) calls the same commands through the bundled MCP server, reads the knowledge base, and explains results. See [`MCP-CLIENTS.md`](MCP-CLIENTS.md) when you're ready.

Either way, no secrets are involved: an agent using xrpl-hermes can research, build, and explain — it cannot spend your funds, because it never has your keys.

## Your first session (read-only, zero risk)

Install (see [`QUICKSTART.md`](../QUICKSTART.md) for details):

```bash
git clone https://github.com/CarpXRPL/xrpl-hermes.git
cd xrpl-hermes
pip install -r requirements.txt
```

These commands only *read* the public ledger. They cannot move funds, and you need no account of your own:

```bash
# Is the network up? Which ledger are we on?
python3 -m scripts.xrpl_tools server-info
python3 -m scripts.xrpl_tools ledger

# Look at a real account (balance, reserve, flags)
python3 -m scripts.xrpl_tools account rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh

# What trust lines does an account hold?
python3 -m scripts.xrpl_tools trustlines rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe

# Is a newer feature live on mainnet?
python3 -m scripts.xrpl_tools amendment MPTokensV1
```

Read the output of `account` carefully once — `BalanceXRP` vs `ReserveXRP` vs `SpendableXRP` is the single most common beginner confusion on XRPL, and the tool does the math for you.

## Build your first transaction (still zero risk)

`build-*` commands produce unsigned transaction JSON. Building is free, offline-safe, and touches no keys:

```bash
python3 -m scripts.xrpl_tools build-payment \
  --from rYOUR_ADDRESS --to rDEST_ADDRESS --amount 1000000
```

The output is signer-ready JSON. To actually send it you would paste it into a wallet you control — for example Xaman's Developer tab (xApps → Developer Console) — review it on your own screen, and sign there. The toolkit's job ends at the JSON.

## Practice safely: testnet

Real experiments belong on the XRPL **testnet**, where XRP is free and worthless:

1. Get a funded testnet account from the faucet: <https://faucet.altnet.rippletest.net/accounts>
2. The faucet gives you a testnet address and seed. Treat even this seed as practice for good hygiene: keep it in an environment variable, never in a command line or a chat.
3. The example scripts in [`examples/`](../examples/) run against testnet using `XRPL_SEED` from your environment.

When you graduate to mainnet, the habit is already formed: seeds live in your wallet, not in your tooling.

## Where to go next

| You want to… | Go to |
|---|---|
| See every command with examples | [`STANDALONE.md`](../STANDALONE.md) |
| Hook this up to Claude Code / Cursor / Hermes | [`docs/MCP-CLIENTS.md`](MCP-CLIENTS.md) |
| Find the right workflow per ecosystem (tokens, NFTs, AMMs, …) | [`docs/WORKFLOWS.md`](WORKFLOWS.md) |
| Understand a topic in depth | `knowledge/` — start with `01-xrpl-accounts.md`, `02-xrpl-payments.md`, `03-xrpl-trustlines.md` |
| Research whether a token is risky | `knowledge/64-token-intelligence-reports.md` |
| Contribute or extend the tools | [`docs/DEVELOPERS.md`](DEVELOPERS.md) |

## Glossary cheat sheet

| Term | Meaning |
|---|---|
| Drop | Smallest XRP unit; 1 XRP = 1,000,000 drops |
| Reserve | XRP locked by the network for your account and its objects; not spendable |
| Trust line | Your explicit opt-in to hold a specific issuer's token |
| Issuer | The account a token is an IOU from; part of the token's identity |
| Amendment | A protocol feature validators vote on; check live status before relying on it |
| Signer-ready JSON | A complete unsigned transaction; your wallet signs it, never this toolkit |
| Seed | Your secret key material (`s...`). Belongs in a wallet. Never in a prompt, chat, or CLI argument |
