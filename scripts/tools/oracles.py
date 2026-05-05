#!/usr/bin/env python3
"""Oracle Set tool (XLS-47)."""
from ._shared import (
    json_out, note_out, json_tx_out, _dispatch_build,
    OracleSet, PriceData,
)

def tool_build_set_oracle(frm: str, oracle_doc_id: str, provider: str,
                           asset_class: str, last_update_time: str,
                           price_data: str = None, uri: str = None):
    if not price_data:
        print("Error: --price-data is required for OracleSet (XLS-47).")
        print("Format: BASE/QUOTE:PRICE:SCALE  (comma-separated for multiple feeds)")
        return
    price_data_series = []
    for entry in price_data.split(","):
        entry = entry.strip()
        parts = entry.split(":")
        if len(parts) >= 3:
            pair, price_val, scale = parts[0], parts[1], parts[2]
            pair_parts = pair.split("/")
            base_asset = pair_parts[0] if len(pair_parts) >= 1 else pair
            quote_asset = pair_parts[1] if len(pair_parts) >= 2 else "USD"
            price_data_series.append(PriceData(
                base_asset=base_asset, quote_asset=quote_asset,
                asset_price=int(price_val), scale=int(scale),
            ))
    if not price_data_series:
        print("Error: --price-data could not be parsed. Use BASE/QUOTE:PRICE:SCALE format.")
        return
    kwargs: dict = dict(account=frm, oracle_document_id=int(oracle_doc_id), provider=provider,
                        asset_class=asset_class, last_update_time=int(last_update_time),
                        price_data_series=price_data_series)
    if uri: kwargs["uri"] = uri
    tx = OracleSet(**kwargs)
    note_out("# OracleSet TX JSON - signer-ready JSON")
    json_tx_out(tx)

COMMANDS = {
    "build-set-oracle": lambda: _dispatch_build(5, tool_build_set_oracle),
}
