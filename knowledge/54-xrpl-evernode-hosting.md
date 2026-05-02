# XRPL Evernode Hosting Patterns — Tenants, Leases, Hooks, DNS, Costs

Evernode is a decentralized hosting network built around XRPL ecosystem primitives and Xahau Hooks-style automation.
This guide gives practical patterns for services that coordinate XRPL L1 accounts, Xahau public RPC, tenant accounting, lease negotiation, DNS, and deployment operations.
Public endpoints used here: `https://xrplcluster.com` for XRPL L1 reads and `https://xahau.network` for Xahau/Hook-style reads.

## Architecture overview
- Tenant account: XRPL or Xahau account representing the customer or application tenant.
- Host account: account controlled by the Evernode host or service operator.
- Lease object: off-ledger or Hook-mediated record describing CPU, memory, disk, duration, and price.
- Deployment artifact: container image, bundle hash, or release manifest stored off ledger.
- Hook controller: Xahau Hook or Hook-compatible workflow that validates lease payments and emits deployment state.
- DNS controller: service that maps tenant subdomains to active host endpoints.
- Billing worker: reconciles payments, lease renewals, refunds, and host settlement.
- Monitor: checks host liveness, ledger payment state, and DNS health.

## Query Xahau and XRPL health
```python
import httpx

ENDPOINTS = {
    "xrpl": "https://xrplcluster.com",
    "xahau": "https://xahau.network",
}

def rpc(endpoint: str, method: str, params: dict | None = None) -> dict:
    response = httpx.post(endpoint, json={"method": method, "params": [params or {}]}, timeout=20)
    response.raise_for_status()
    result = response.json()["result"]
    if result.get("status") == "error":
        raise RuntimeError(result)
    return result

for name, endpoint in ENDPOINTS.items():
    info = rpc(endpoint, "server_info")
    print(name, info.get("info", {}).get("validated_ledger"))
```

## Tenant account model
A tenant account can be a real funded XRPL/Xahau account or an application account linked to one or more ledger addresses.
```json
{
  "tenant_id": "tenant_018f7f8c4f",
  "xrpl_account": "rTenantClassicAddress",
  "xahau_account": "rTenantXahauAddress",
  "billing_currency": "XRP",
  "deployment_namespace": "tenant-018f7f8c4f",
  "dns_name": "tenant-018f7f8c4f.apps.example.com",
  "status": "active"
}
```

## Generate tenant wallets
```python
from xrpl.wallet import Wallet
from xrpl.core.keypairs import generate_seed

def new_tenant_wallet() -> dict:
    seed = generate_seed(algorithm="ed25519")
    wallet = Wallet.from_seed(seed)
    return {"address": wallet.classic_address, "seed": seed}

wallet = new_tenant_wallet()
print(wallet["address"])
```

## Lease negotiation JSON
```json
{
  "lease_id": "lease_2026_04_29_0001",
  "tenant": "rTenantClassicAddress",
  "host": "rHostClassicAddress",
  "network": "xahau",
  "region": "us-east",
  "resources": {
    "cpu_millicores": 1000,
    "memory_mb": 1024,
    "disk_mb": 10240,
    "egress_gb": 100
  },
  "term": {
    "starts_at": "2026-04-29T00:00:00Z",
    "ends_at": "2026-05-29T00:00:00Z"
  },
  "price": {
    "amount_drops": "25000000",
    "currency": "XRP",
    "interval": "month"
  },
  "artifact": {
    "image": "ghcr.io/example/app:1.2.3",
    "sha256": "ab93..."
  }
}
```

## Lease payment transaction
```python
import os
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import Payment
from xrpl.transaction import submit_and_wait
from xrpl.wallet import Wallet

client = JsonRpcClient(os.getenv("XAHAU_RPC", "https://xahau.network"))
tenant = Wallet.from_seed(os.environ["TENANT_SEED"])
lease_hook_account = os.environ["LEASE_HOOK_ACCOUNT"]

payment = Payment(
    account=tenant.classic_address,
    destination=lease_hook_account,
    amount="25000000",
    memos=[{
        "Memo": {
            "MemoType": "6c656173655f6964",
            "MemoData": "6c656173655f323032365f30345f32395f30303031"
        }
    }]
)

result = submit_and_wait(payment, client, tenant)
print(result.result["hash"])
```

## Hook deployment signal
Hooks run on Xahau, so application code generally sends a transaction carrying deployment metadata and a Hook validates it.
```json
{
  "TransactionType": "Payment",
  "Account": "rTenantXahauAddress",
  "Destination": "rLeaseHookAccount",
  "Amount": "25000000",
  "Memos": [
    {
      "Memo": {
        "MemoType": "657665726e6f64655f6c65617365",
        "MemoFormat": "6170706c69636174696f6e2f6a736f6e",
        "MemoData": "7b226c656173655f6964223a226c656173655f323032365f30345f32395f30303031227d"
      }
    }
  ]
}
```

## Deployment worker
```python
from dataclasses import dataclass
import httpx

@dataclass
class Lease:
    lease_id: str
    namespace: str
    image: str
    domain: str
    port: int = 8080

def deploy_container(lease: Lease, host_controller_url: str, token: str) -> dict:
    response = httpx.post(
        f"{host_controller_url.rstrip('/')}/deployments",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "lease_id": lease.lease_id,
            "namespace": lease.namespace,
            "image": lease.image,
            "domain": lease.domain,
            "port": lease.port,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()

# The host controller can map this HTTPS request to Kubernetes, Nomad, Docker, or Firecracker.
```

## DNS management with a public HTTPS API pattern
The provider varies. The workflow is stable: create a CNAME or A record after lease activation and remove it on lease expiry.
```python
import os
import httpx

def upsert_dns_record(zone_id: str, name: str, target: str) -> dict:
    token = os.environ["DNS_API_TOKEN"]
    response = httpx.post(
        f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records",
        headers={"Authorization": f"Bearer {token}"},
        json={"type": "CNAME", "name": name, "content": target, "ttl": 120, "proxied": True},
        timeout=20,
    )
    response.raise_for_status()
    return response.json()
```

## Cost structure
- **Base ledger reserve**: Tenant and host accounts need network reserve on XRPL/Xahau.
- **Owner reserve**: Hooks, trust lines, signer lists, and other objects increase reserve.
- **Transaction fees**: Lease payments, renewal signals, and settlement transactions destroy small fees.
- **Host compute**: CPU, memory, disk, and bandwidth charged by host policy.
- **Artifact storage**: Container registry, IPFS pinning, Arweave, or S3-compatible storage.
- **DNS**: Hosted zone and query charges if using a managed DNS provider.
- **Monitoring**: External uptime checks and log retention.
- **Bridge costs**: If funding from EVM sidechain or another chain, include bridge and gas fees.

## Lease lifecycle
1. Tenant chooses host offer.
2. Application builds lease proposal JSON.
3. Tenant signs payment or lease transaction.
4. Hook or backend validates payment, term, and resource limits.
5. Deployment worker pulls artifact and starts workload.
6. DNS worker points tenant domain at the selected host.
7. Monitor records health and ledger renewal deadlines.
8. Renewal worker requests the next payment before expiration.
9. Expiry worker stops workload and removes DNS when grace period ends.
10. Settlement worker reports host revenue and tenant usage.

## Practical Hosting Notes

### Tenant Readiness Check
Before presenting a lease offer, verify the tenant account has enough XRP/XAH for reserve (2 XRP base + 0.2 per owner object) and tx fee for the full lease term.

### Hook Optimization
Keep Hook parameters under 256 bytes total. Put large manifests in content-addressed storage (Arweave, IPFS) and reference by hash in the hook state.

### DNS Migration
Use low TTL records (120s) during host migration. Only raise TTL (3600s) after host health is stable for 24+ hours.

### Cost Transparency
Separate ledger fees (reserve + tx costs), host resource charges (CPU/memory/disk), bandwidth (egress), and support margin in invoices. Avoid bundling.

### Lease Audit Trail
Store the signed transaction hash with the lease record before deploying any workload. This is critical for dispute resolution.

---

## The Sashimi Hook

Evernode's core infrastructure is the **Sashimi Hook** — a Xahau Hook that manages the entire host lifecycle directly on-ledger.

### Sashimi Hook Architecture

```
Sashimi Hook (installed on host's Xahau account)
        │
        ├── Handles: HostRegistration, LeaseOffer, LeasePayment
        ├── Validates: payment amounts, lease terms, resource limits
        ├── Emits: deployment signals, renewal notifications, expiry flags
        └── Stores: host capacity, lease contracts, tenant mappings in HookState
```

### What Sashimi Does On-Chain

1. **Host Registration** — A new host sends a `Payment` tx with a registration memo to their own account. The Sashimi Hook intercepts it, validates the bond amount, and writes host metadata (CPU cores, RAM GB, disk GB, region) to HookState.

2. **Lease Offer** — A tenant sends a `Payment` with lease terms in the memo. Sashimi validates the offer, checks the host has capacity, and writes the lease contract to state.

3. **Lease Payment** — Tenant sends the lease fee. Sashimi credits the payment, increments the lease period, and sets a deployment flag for the off-chain worker.

4. **Expiry** — Sashimi checks lease deadlines on every triggering tx. Expired leases are flagged; the off-chain worker reads the flag and stops the workload.

### Sashimi Hook State Schema

```c
// Sashimi Hook state keys (32 bytes each, truncated for display)
uint8_t KEY_HOST_REG[] = "host_registry_v1";       // → host capacity JSON
uint8_t KEY_LEASE_NS[] = "lease_";                  // → lease contract JSON (prefix + lease_id)
uint8_t KEY_TENANT_NS[] = "tenant_";                // → tenant lease list (prefix + tenant_address)
```

### Deploying a Host with Sashimi

```python
import os, json, httpx
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.transactions import Payment
from xrpl.transaction import submit_and_wait

XAHAU_RPC = "https://xahau.network"
client = JsonRpcClient(XAHAU_RPC)
host_wallet = Wallet.from_seed(os.environ["HOST_SEED"])

# Register as host via Sashimi Hook
host_spec = json.dumps({
    "action": "register_host",
    "cpu_millicores": 4000,
    "memory_mb": 8192,
    "disk_mb": 102400,
    "region": "us-east",
    "bond_xah": "1000"
})

register_tx = Payment(
    account=host_wallet.classic_address,
    destination=host_wallet.classic_address,  # Self-payment triggers Sashimi
    amount="1000000000",  # 1000 XAH bond
    memos=[{
        "Memo": {
            "MemoData": host_spec.encode().hex().upper(),
            "MemoType": "657665726e6f64652f686f737400",  # "evernode/host"
        }
    }]
)

result = submit_and_wait(register_tx, client, host_wallet)
print(f"Host registered: {result.result['hash']}")
```

### Deploying a Tenant Application

```python
def deploy_tenant_app(
    tenant_wallet: Wallet,
    lease_terms: dict,
    lease_hook_account: str,
    xahau_client: JsonRpcClient
) -> dict:
    """
    Deploy an application via Evernode/Sashimi.
    lease_terms: {
        cpu_millicores, memory_mb, disk_mb,
        duration_days, artifact_image, artifact_hash
    }
    """
    lease_payload = json.dumps({
        "action": "request_lease",
        **lease_terms
    })

    # Calculate lease cost (example: 25 XAH/month per GB RAM)
    monthly_xah = (lease_terms["memory_mb"] / 1024) * 25
    total_xah = monthly_xah * (lease_terms["duration_days"] / 30)
    total_drops = str(int(total_xah * 1_000_000))

    lease_tx = Payment(
        account=tenant_wallet.classic_address,
        destination=lease_hook_account,
        amount=total_drops,
        memos=[{
            "Memo": {
                "MemoData": lease_payload.encode().hex().upper(),
                "MemoType": "657665726e6f64652f6c6561736500",  # "evernode/lease"
            }
        }]
    )

    result = submit_and_wait(lease_tx, xahau_client, tenant_wallet)
    return {
        "tx_hash": result.result["hash"],
        "lease_id": f"lease_{result.result['hash'][:12]}",
        "status": "pending_deployment",
        "note": "Off-chain worker picks up deployment flag from Sashimi state"
    }
```

### Reading Sashimi State (Lease Verification)

```python
async def check_hook_state(
    account: str,
    namespace_id: str,
    key: str
) -> dict:
    """Read a value from the Sashimi Hook's state."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            XAHAU_RPC,
            json={
                "method": "ledger_entry",
                "params": [{
                    "hook_state": {
                        "account": account,
                        "key": key.encode().hex(),
                        "namespace_id": namespace_id
                    }
                }]
            }
        )
        result = response.json()["result"]
        return result.get("node", {}).get("HookStateData", {})

# Verify a lease is active
state = await check_hook_state(
    lease_hook_account,
    "0000000000000000000000000000000000000000000000000000000000000000",
    "lease_abc123"
)
```

---

## Evernode Runtime

The off-chain runtime that reads Sashimi state and manages containers:

```python
# Pseudocode showing the worker loop
import asyncio, httpx, docker  # docker-py

EVERNODE_WORKER_INTERVAL = 30  # seconds

async def evernode_worker_loop(lease_hook_account: str):
    """Poll Sashimi state, deploy/stop containers based on hook flags."""
    docker_client = docker.from_env()

    while True:
        # 1. Get active leases from Sashimi
        # (via account_objects or ledger_entry on the hook account)

        # 2. Compare with running containers
        running = {c.name for c in docker_client.containers.list()}

        # 3. Deploy new leases
        for lease in active_leases:
            if lease["id"] not in running:
                deploy_container(lease)

        # 4. Stop expired leases
        for container_name in running:
            if container_name not in {l["id"] for l in active_leases}:
                stop_container(container_name)

        await asyncio.sleep(EVERNODE_WORKER_INTERVAL)
```

---

## Evers (EVR) Token Integration

EVR is the Evernode governance and utility token.

```python
# EVR is an issued currency on Xahau
EVR_CURRENCY = "EVR"
EVR_ISSUER = os.environ.get("EVR_ISSUER")  # Verify from evernode.io

async def get_evr_price() -> dict:
    """Query EVR price from FTSO or market data API."""
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.xrpl.to/v1/token/EVR")
        return response.json()

def get_evr_balance(wallet: Wallet, client: JsonRpcClient) -> float:
    """Get EVR token balance for a wallet."""
    from xrpl.models.requests import AccountLines
    resp = client.request(AccountLines(account=wallet.classic_address))
    for line in resp.result.get("lines", []):
        if line["currency"] == EVR_CURRENCY and line["account"] == EVR_ISSUER:
            return float(line["balance"])
    return 0.0
```

---

## Known Limitations & Production Notes

### Sashimi Hook Limits
- Max 256 state keys per hook namespace
- Max 128 bytes per state value
- Emit limit: 16 emitted transactions per hook execution
- Max lease contract JSON payload: ~4 KB (fits in multi-page memo)

### Host Infrastructure
- Each host runs a Docker daemon + Sashimi-aware worker
- Host must have a funded Xahau account with sufficient XAH for hook fees
- Recommended: 4+ CPU cores, 8 GB RAM, 100 GB SSD per host
- Host bond: typically 1000 XAH (slashed if host goes offline without notice)

### Tenant Considerations
- App must be containerized (Docker image)
- Recommended to use health check endpoints for the Sashimi worker to monitor
- Upgrade path: send a new lease tx with updated artifact hash, worker performs rolling update
- Backup: tenant should store their app image in a registry they control, not rely on host's registry cache

---

## Related Files

- `knowledge/51-xrpl-xahau-hooks.md` — Xahau hook host network
- `knowledge/17-xrpl-private-node.md` — alternative self-hosting
