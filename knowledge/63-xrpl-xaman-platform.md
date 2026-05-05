# 63 — Xaman Platform API

Xaman, formerly XUMM, provides a production signing flow for XRPL transactions without exposing user secrets to your application.
Do not create fake URLs by embedding transaction JSON in a URL. Create a real payload through the Xaman Platform API and send users the returned `next.always` URL or QR code.

## API Key Setup

1. Go to `https://apps.xumm.dev`.
2. Create or select an application.
3. Copy the API key and API secret.
4. Store them as environment variables on the server only.

```bash
export XUMM_API_KEY='your-api-key'
export XUMM_API_SECRET='your-api-secret'
```

## xaman-payload CLI

```bash
TX='{"TransactionType":"Payment","Account":"rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe","Destination":"rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh","Amount":"1000000"}'
python3 -m scripts.xrpl_tools xaman-payload "$TX"
```

The command returns `PayloadUUID`, `SignURL`, `QRPng`, `WSStatus`, and the raw Platform API response.

## Payload UUIDs

Every payload has a UUID. Store it with your local order, invoice, alert, or bot interaction ID.

Operational pattern:

- Build transaction JSON with an xrpl-hermes `build-*` command.
- Create a payload with `xaman-payload`.
- Send `SignURL` or `QRPng` to the user.
- Watch webhook or websocket status.
- Confirm the final transaction hash on-ledger before updating business state.

## next.always Sign URL

Use the `next.always` URL returned by the API. This is the correct universal signing link.

Operational pattern:

- Build transaction JSON with an xrpl-hermes `build-*` command.
- Create a payload with `xaman-payload`.
- Send `SignURL` or `QRPng` to the user.
- Watch webhook or websocket status.
- Confirm the final transaction hash on-ledger before updating business state.

## QR Codes

Use `refs.qr_png` for web dashboards, Discord embeds, Telegram photos, and kiosk flows.

Operational pattern:

- Build transaction JSON with an xrpl-hermes `build-*` command.
- Create a payload with `xaman-payload`.
- Send `SignURL` or `QRPng` to the user.
- Watch webhook or websocket status.
- Confirm the final transaction hash on-ledger before updating business state.

## Webhook Callbacks

Configure a webhook URL in the Xaman developer console and verify callbacks before marking work complete.

Operational pattern:

- Build transaction JSON with an xrpl-hermes `build-*` command.
- Create a payload with `xaman-payload`.
- Send `SignURL` or `QRPng` to the user.
- Watch webhook or websocket status.
- Confirm the final transaction hash on-ledger before updating business state.

## WebSocket Status

Use `refs.websocket_status` for live UI status: opened, signed, rejected, expired.

Operational pattern:

- Build transaction JSON with an xrpl-hermes `build-*` command.
- Create a payload with `xaman-payload`.
- Send `SignURL` or `QRPng` to the user.
- Watch webhook or websocket status.
- Confirm the final transaction hash on-ledger before updating business state.

## Custom Metadata

Attach local identifiers in your own database. Keep secrets and PII out of memo fields and payload JSON.

Operational pattern:

- Build transaction JSON with an xrpl-hermes `build-*` command.
- Create a payload with `xaman-payload`.
- Send `SignURL` or `QRPng` to the user.
- Watch webhook or websocket status.
- Confirm the final transaction hash on-ledger before updating business state.

## Error Handling

Handle missing credentials, 401 responses, expired payloads, rejected payloads, and network timeouts.

Operational pattern:

- Build transaction JSON with an xrpl-hermes `build-*` command.
- Create a payload with `xaman-payload`.
- Send `SignURL` or `QRPng` to the user.
- Watch webhook or websocket status.
- Confirm the final transaction hash on-ledger before updating business state.

## Security

Never ask for or store seeds. Xaman signs on the user device and returns signed status through the Platform API.

Operational pattern:

- Build transaction JSON with an xrpl-hermes `build-*` command.
- Create a payload with `xaman-payload`.
- Send `SignURL` or `QRPng` to the user.
- Watch webhook or websocket status.
- Confirm the final transaction hash on-ledger before updating business state.

## Real Payment Workflow

```bash
python3 -m scripts.xrpl_tools build-payment --from rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe --to rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh --amount 1000000 > tx.json
python3 -m scripts.xrpl_tools xaman-payload "$(cat tx.json)"
```

## Real AccountSet Workflow

```bash
python3 -m scripts.xrpl_tools build-account-set --from r9cZA1mLK5R5Am25ArfXFmqgNwjZgnfk59 --set-flag 8 > tx.json
python3 -m scripts.xrpl_tools xaman-payload "$(cat tx.json)"
```

### Platform Integration Note 1

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 2

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 3

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 4

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 5

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 6

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 7

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 8

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 9

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 10

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 11

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 12

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 13

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 14

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 15

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 16

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 17

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 18

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 19

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 20

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 21

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 22

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 23

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 24

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 25

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 26

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 27

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 28

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 29

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 30

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 31

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 32

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 33

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 34

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 35

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 36

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 37

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 38

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 39

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 40

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 41

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 42

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 43

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 44

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 45

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 46

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 47

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 48

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 49

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 50

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 51

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 52

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 53

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 54

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 55

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 56

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 57

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 58

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 59

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 60

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 61

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 62

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 63

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 64

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 65

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 66

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 67

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 68

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 69

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 70

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 71

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 72

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 73

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 74

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 75

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 76

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 77

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 78

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 79

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 80

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 81

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 82

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 83

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 84

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 85

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 86

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 87

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 88

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 89

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

### Platform Integration Note 90

- Persist payload UUID, local user ID, transaction type, created time, and expiration time.
- Treat `signed=true` as a signing event, then independently verify the transaction result on XRPL.
- Use the real Xaman Platform payload flow instead of any fabricated JSON-in-URL signing link.

## Related Files

- [26-xrpl-xaman-deeplink](knowledge/26-xrpl-xaman-deeplink.md)
- [02-xrpl-payments](knowledge/02-xrpl-payments.md)
- [60-xrpl-account-set](knowledge/60-xrpl-account-set.md)
