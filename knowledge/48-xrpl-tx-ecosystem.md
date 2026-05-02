# TX Ecosystem — XRPL Multi-Chain Settlement Protocol

## Overview

TX (tx.money) is the XRP Ledger ecosystem's multi-chain settlement protocol and NFT marketplace. It provides infrastructure connecting XRPL L1, the XRPL EVM Sidechain, and other chains through a native bridge, along with a fully-featured NFT marketplace and portfolio dashboard.

**Core products:**
- **TX Marketplace** — NFT marketplace supporting XLS-20 NFTs natively with creator royalties
- **TX Bridge** — Cross-chain bridge between XRPL L1, EVM sidechain, and other chains
- **TX Portal** — Web dashboard for wallet connect, portfolio tracking, NFT gallery

**Native token:** TX (used for marketplace fees, bridge fees, staking, governance)

---

## Architecture

```
┌───────────────────────────────────────────────────────┐
│                    TX Ecosystem                        │
│                                                       │
│  ┌─────────────┐  ┌───────────────┐  ┌───────────┐   │
│  │ TX          │  │ TX Bridge     │  │ TX Portal │   │
│  │ Marketplace │  │ (federator)   │  │ (dashboard│   │
│  │ (XLS-20)    │  │               │  │  wallet)  │   │
│  └──────┬──────┘  └───────┬───────┘  └─────┬─────┘   │
│         │                 │                │          │
└─────────┼─────────────────┼────────────────┼──────────┘
          │                 │                │
     XRPL L1          XRPL L1 ←→         Xaman /
   NFTokenOfferCreate  EVM Sidechain    MetaMask
   NFTokenAcceptOffer  + Other chains   connect
```

### TX Token

The TX token is the ecosystem's native utility token:
- **Currency code**: `TX` on XRPL L1 (verify issuer address from official tx.money site)
- **ERC-20**: TX token on XRPL EVM Sidechain
- **Uses**: marketplace listing fees, bridge transaction fees, governance voting, staking rewards

---

## TX Marketplace

The TX Marketplace is a primary NFT marketplace for XLS-20 tokens on XRPL, offering:
- Buy, sell, auction listings
- Creator royalties enforced via TransferFee
- Rarity tracking and trait filtering
- Collection analytics and floor price

### How XLS-20 Offers Work on Marketplace

```
Seller creates NFTokenCreateOffer (sell offer)
    ↓
TX Marketplace indexes the offer
    ↓
Buyer calls NFTokenAcceptOffer via TX Marketplace UI
    ↓
On-ledger atomic swap: NFT changes hands, XRP/tokens transferred
    ↓
Creator royalty (TransferFee) automatically deducted by protocol
```

---

## Python: Interact with TX Marketplace via XRPL

```python
import httpx
import asyncio
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import (
    NFTokenCreateOffer, NFTokenAcceptOffer, NFTokenBurn
)
from xrpl.models.requests import AccountNFTs
from xrpl.wallet import Wallet
from xrpl.transaction import submit_and_wait
from xrpl.utils import xrp_to_drops

XRPL_RPC = "https://s1.ripple.com:51234"

def list_nft_for_sale(
    wallet: Wallet,
    nft_token_id: str,
    price_xrp: float,
    expiration_seconds: int = None
) -> dict:
    """
    Create an NFTokenSellOffer. TX Marketplace will index it automatically.
    """
    client = JsonRpcClient(XRPL_RPC)

    tx_params = dict(
        account=wallet.classic_address,
        nftoken_id=nft_token_id,
        amount=str(xrp_to_drops(price_xrp)),
        flags=1  # tfSellNFToken
    )
    if expiration_seconds:
        # XRPL uses seconds since Ripple epoch (Jan 1 2000)
        import time
        ripple_epoch_offset = 946684800
        tx_params["expiration"] = int(time.time()) - ripple_epoch_offset + expiration_seconds

    tx = NFTokenCreateOffer(**tx_params)
    result = submit_and_wait(tx, client, wallet)

    # Extract offer index from metadata
    offer_index = None
    for node in result.result.get("meta", {}).get("AffectedNodes", []):
        created = node.get("CreatedNode", {})
        if created.get("LedgerEntryType") == "NFTokenOffer":
            offer_index = created.get("LedgerIndex")

    return {
        "offer_index": offer_index,
        "nft_token_id": nft_token_id,
        "price_xrp": price_xrp,
        "xrpl_tx_hash": result.result["hash"],
        "status": result.result["meta"]["TransactionResult"],
        "marketplace_url": f"https://marketplace.tx.money/nft/{nft_token_id}"
    }

def buy_nft(
    buyer_wallet: Wallet,
    sell_offer_index: str
) -> dict:
    """Accept an existing sell offer, completing the purchase."""
    client = JsonRpcClient(XRPL_RPC)

    tx = NFTokenAcceptOffer(
        account=buyer_wallet.classic_address,
        nftoken_sell_offer=sell_offer_index
    )
    result = submit_and_wait(tx, client, buyer_wallet)

    return {
        "xrpl_tx_hash": result.result["hash"],
        "status": result.result["meta"]["TransactionResult"]
    }

async def get_nft_floor_price(collection_taxon: int, issuer: str) -> dict:
    """
    Get the floor price for an NFT collection from XRPSCAN.
    TX Marketplace uses on-chain offers — we query XRPSCAN API.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.xrpscan.com/api/v1/account/{issuer}/nfts",
            params={"taxon": collection_taxon, "limit": 100}
        )
        nfts = response.json().get("nfts", [])

    # Get sell offers for each NFT and find the floor
    floor_price = None
    for nft in nfts:
        token_id = nft.get("nft_id") or nft.get("NFTokenID")
        if not token_id:
            continue
        async with httpx.AsyncClient() as client:
            offers_resp = await client.post(
                XRPL_RPC,
                json={
                    "method": "nft_sell_offers",
                    "params": [{"nft_id": token_id}]
                }
            )
            offers = offers_resp.json().get("result", {}).get("offers", [])
            for offer in offers:
                amount = offer.get("amount")
                if isinstance(amount, str):  # XRP in drops
                    xrp_price = int(amount) / 1_000_000
                    if floor_price is None or xrp_price < floor_price:
                        floor_price = xrp_price

    return {
        "issuer": issuer,
        "taxon": collection_taxon,
        "floor_price_xrp": floor_price,
        "total_nfts_checked": len(nfts)
    }
```

---

## Python: TX Bridge (XRPL ↔ EVM Sidechain)

The TX Bridge operates similarly to the official XRPL EVM Sidechain bridge. For exact endpoints and contract addresses, always verify from tx.money official docs.

```python
import httpx
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import Payment
from xrpl.wallet import Wallet
from xrpl.transaction import submit_and_wait
from xrpl.utils import xrp_to_drops

TX_BRIDGE_L1_ACCOUNT = "rTxBridgeGatewayAddress"  # verify from tx.money

def bridge_to_evm(
    wallet: Wallet,
    amount_xrp: float,
    destination_evm_address: str
) -> dict:
    """
    Bridge XRP from XRPL L1 to EVM sidechain via TX Bridge.
    The EVM address is encoded in the destination tag or memo.
    """
    client = JsonRpcClient("https://s1.ripple.com:51234")

    # TX Bridge uses destination tag to route to EVM address
    # Exact encoding — verify from tx.money bridge docs
    dest_tag = int(destination_evm_address.replace("0x", "")[:8], 16)

    tx = Payment(
        account=wallet.classic_address,
        destination=TX_BRIDGE_L1_ACCOUNT,
        amount=str(xrp_to_drops(amount_xrp)),
        destination_tag=dest_tag
    )
    result = submit_and_wait(tx, client, wallet)
    return {
        "xrpl_tx_hash": result.result["hash"],
        "status": result.result["meta"]["TransactionResult"],
        "bridge_ui": "https://bridge.tx.money"
    }

async def get_bridge_transaction_status(xrpl_tx_hash: str) -> dict:
    """
    Query bridge status. TX Bridge may expose a REST API.
    Fallback: check EVM sidechain for the corresponding mint.
    """
    # Check XRPSCAN for outgoing bridge transactions
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.xrpscan.com/api/v1/transaction/{xrpl_tx_hash}"
        )
        tx_data = response.json()

    return {
        "source_tx": xrpl_tx_hash,
        "type": tx_data.get("TransactionType"),
        "result": tx_data.get("meta", {}).get("TransactionResult"),
        "ledger": tx_data.get("ledger_index"),
        "bridge_ui": f"https://bridge.tx.money"
    }
```

---

## JSON: TX Ecosystem Transaction Examples

### XLS-20 NFT Sell Offer (for TX Marketplace)

```json
{
  "TransactionType": "NFTokenCreateOffer",
  "Account": "rSellerAddress",
  "NFTokenID": "000800004B9A9E67A78A79F5DE2B9A1C9C9F0A4B",
  "Amount": "5000000",
  "Flags": 1,
  "Fee": "12",
  "Sequence": 12345
}
```

### Accept NFT Offer (Buy)

```json
{
  "TransactionType": "NFTokenAcceptOffer",
  "Account": "rBuyerAddress",
  "NFTokenSellOffer": "OFFER_INDEX_HEX",
  "Fee": "12",
  "Sequence": 67890
}
```

### Payment to TX Bridge

```json
{
  "TransactionType": "Payment",
  "Account": "rSender",
  "Destination": "rTxBridgeAccount",
  "Amount": "10000000",
  "DestinationTag": 12345678,
  "Fee": "12",
  "Memos": [
    {
      "Memo": {
        "MemoType": "65766D5F61646472657373",
        "MemoData": "307861626364656600000000000000000000000000000000000000"
      }
    }
  ]
}
```

---

## REST API Usage

TX Marketplace likely exposes a REST API for listing/searching NFTs. Until official docs publish endpoints, use XRPSCAN for on-chain data:

```python
async def search_tx_marketplace_listings(
    issuer: str = None,
    min_price_xrp: float = None,
    max_price_xrp: float = None
) -> list:
    """
    Search NFT sell offers. On-chain data via XRPSCAN.
    """
    params = {"limit": 50}
    if issuer:
        params["issuer"] = issuer

    async with httpx.AsyncClient() as client:
        # XRPSCAN nft search
        response = await client.get(
            "https://api.xrpscan.com/api/v1/nfts/offers",
            params=params
        )
        offers = response.json().get("offers", [])

    # Filter by price
    filtered = []
    for offer in offers:
        amount = offer.get("Amount")
        if isinstance(amount, str):
            price_xrp = int(amount) / 1_000_000
            if min_price_xrp and price_xrp < min_price_xrp:
                continue
            if max_price_xrp and price_xrp > max_price_xrp:
                continue
            filtered.append({**offer, "price_xrp": price_xrp})

    return sorted(filtered, key=lambda x: x["price_xrp"])

async def get_account_nft_portfolio(account: str) -> dict:
    """Get all NFTs owned by an account (for TX Portal equivalent)."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.xrpscan.com/api/v1/account/{account}/nfts"
        )
        nfts = response.json().get("nfts", [])

    return {
        "account": account,
        "total_nfts": len(nfts),
        "nfts": nfts,
        "tx_portal": f"https://tx.money/portfolio/{account}"
    }
```

---

## TX Token Integration

```python
async def get_tx_token_info() -> dict:
    """
    Get TX token issuer and current price.
    Always verify issuer from official tx.money sources.
    """
    # Query xrpl.to for TX token market data
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.xrpl.to/v1/token/TX",
            params={"search": "TX"}
        )
        return response.json()

async def check_tx_balance(account: str) -> dict:
    """Check TX token balance for an account."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://s1.ripple.com:51234",
            json={
                "method": "account_lines",
                "params": [{
                    "account": account,
                    "ledger_index": "validated"
                }]
            }
        )
        lines = response.json()["result"].get("lines", [])

    tx_lines = [l for l in lines if l.get("currency") == "TX"]
    return {
        "account": account,
        "tx_balances": tx_lines,
        "total_tx": sum(float(l["balance"]) for l in tx_lines)
    }

async def trust_tx_token(wallet: Wallet) -> dict:
    """Set up trust line for TX token (required before receiving TX)."""
    from xrpl.models.transactions import TrustSet

    # Verify the correct TX issuer from tx.money
    TX_ISSUER = "rTxTokenIssuerAddress"  # replace with verified issuer

    client = JsonRpcClient(XRPL_RPC)
    tx = TrustSet(
        account=wallet.classic_address,
        limit_amount={
            "currency": "TX",
            "issuer": TX_ISSUER,
            "value": "1000000000"
        }
    )
    result = submit_and_wait(tx, client, wallet)
    return {
        "status": result.result["meta"]["TransactionResult"],
        "tx_hash": result.result["hash"]
    }
```

---

## Error Handling Patterns

```python
class TXMarketplaceError(Exception):
    pass

class NFTOfferExpiredError(TXMarketplaceError):
    pass

class InsufficientFundsError(TXMarketplaceError):
    pass

def handle_nft_tx_error(tx_result: str, context: str = "") -> None:
    """Map XRPL transaction result codes to marketplace errors."""
    errors = {
        "tecNO_ENTRY": "NFT offer not found — may have been accepted or cancelled",
        "tecINSUFFICIENT_FUNDS": "Insufficient XRP balance to complete purchase",
        "tecEXPIRED": "NFT offer has expired",
        "tecNO_PERMISSION": "Account not authorized to accept this offer",
        "tefNFTOKEN_IS_NOT_TRANSFERABLE": "This NFT is marked as non-transferable",
        "temBAD_AMOUNT": "Invalid price amount",
    }
    error_msg = errors.get(tx_result, f"Unknown error: {tx_result}")
    if context:
        error_msg = f"{context}: {error_msg}"

    if "EXPIRED" in tx_result:
        raise NFTOfferExpiredError(error_msg)
    elif "FUNDS" in tx_result:
        raise InsufficientFundsError(error_msg)
    else:
        raise TXMarketplaceError(error_msg)

def safe_list_nft(wallet: Wallet, nft_id: str, price_xrp: float) -> dict:
    """List NFT for sale with error handling."""
    try:
        return list_nft_for_sale(wallet, nft_id, price_xrp)
    except Exception as e:
        if hasattr(e, 'result'):
            handle_nft_tx_error(e.result, f"Listing NFT {nft_id}")
        raise TXMarketplaceError(f"Failed to list NFT: {e}") from e
```

---

## Practical Workflow: Full NFT Sale on TX Marketplace

```python
async def complete_nft_sale_workflow(
    seller_seed: str,
    nft_token_id: str,
    price_xrp: float
) -> dict:
    """
    Complete workflow for listing and selling an NFT on TX Marketplace.
    """
    seller_wallet = Wallet.from_seed(seller_seed)

    # 1. Verify NFT ownership
    async with httpx.AsyncClient() as client:
        nfts_resp = await client.post(
            XRPL_RPC,
            json={
                "method": "account_nfts",
                "params": [{"account": seller_wallet.classic_address}]
            }
        )
        nfts = nfts_resp.json()["result"].get("account_nfts", [])

    owned_ids = [n["NFTokenID"] for n in nfts]
    if nft_token_id not in owned_ids:
        raise TXMarketplaceError(f"NFT {nft_token_id} not owned by seller")

    # 2. Create sell offer
    print(f"Creating sell offer for {price_xrp} XRP...")
    offer_result = list_nft_for_sale(seller_wallet, nft_token_id, price_xrp)

    if offer_result["status"] != "tesSUCCESS":
        handle_nft_tx_error(offer_result["status"], "Creating sell offer")

    print(f"Offer created: {offer_result['offer_index']}")
    print(f"View on TX Marketplace: {offer_result['marketplace_url']}")

    return {
        "offer_index": offer_result["offer_index"],
        "price_xrp": price_xrp,
        "listing_url": offer_result["marketplace_url"],
        "xrpl_tx": offer_result["xrpl_tx_hash"]
    }
```

---

## Resources

- TX Ecosystem website: https://tx.money
- TX Marketplace: https://marketplace.tx.money
- TX Bridge: https://bridge.tx.money
- TX Portal: https://tx.money (portal section)

---

## Related Files

- `52-xrpl-l1-reference.md` — XLS-20 NFT transaction types and AMM
- `50-xrpl-evm-sidechain.md` — EVM Sidechain (TX Bridge connects here)
- `53-xrpl-wallets-auth.md` — Xaman wallet integration for TX Marketplace
- `55-xrpl-sidechain-interop.md` — Cross-chain bridge patterns
- `46-xrpl-axelar-bridge.md` — Alternative cross-chain bridge (Axelar)
