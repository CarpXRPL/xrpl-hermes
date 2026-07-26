"""Regression tests for strict experimental XRPL EVM helpers."""
import json

from scripts.tools import evm


def _output(capsys):
    return json.loads(capsys.readouterr().out)


def test_evm_balance_rejects_invalid_network_without_rpc(monkeypatch, capsys):
    monkeypatch.setattr(evm, "_rpc", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("RPC called")))
    evm.tool_evm_balance("0x" + "1" * 40, "nonsense")
    out = _output(capsys)
    assert out["Error"] == "ValueError"
    assert "mainnet or testnet" in out["Message"]


def test_evm_balance_rejects_malformed_address(monkeypatch, capsys):
    monkeypatch.setattr(evm, "_rpc", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("RPC called")))
    evm.tool_evm_balance("not-an-address", "mainnet")
    out = _output(capsys)
    assert out["Error"] == "ValueError"
    assert "20-byte EVM address" in out["Message"]


def test_evm_balance_reports_live_values(monkeypatch, capsys):
    def fake_rpc(_url, method, _params):
        return {"eth_getBalance": "0xde0b6b3a7640000", "eth_chainId": hex(1440000)}[method]

    monkeypatch.setattr(evm, "_rpc", fake_rpc)
    address = "0x" + "a" * 40
    evm.tool_evm_balance(address, "mainnet")
    out = _output(capsys)
    assert out["BalanceWei"] == "1000000000000000000"
    assert out["BalanceXRP"] == "1"
    assert out["ObservedChainID"] == 1440000
    assert out["Status"] == "experimental-read-only"


def test_evm_balance_rejects_chain_mismatch(monkeypatch, capsys):
    def fake_rpc(_url, method, _params):
        return {"eth_getBalance": "0x0", "eth_chainId": "0x1"}[method]

    monkeypatch.setattr(evm, "_rpc", fake_rpc)
    evm.tool_evm_balance("0x" + "a" * 40, "mainnet")
    out = _output(capsys)
    assert out["Error"] == "RuntimeError"
    assert "does not match" in out["Message"]


def test_evm_rpc_rejects_json_rpc_error(monkeypatch):
    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"jsonrpc": "2.0", "id": 1, "error": {"code": -32602, "message": "bad params"}}

    monkeypatch.setattr(evm.httpx, "post", lambda *args, **kwargs: Response())
    try:
        evm._rpc("https://example.invalid", "eth_getBalance", [])
    except RuntimeError as exc:
        assert "-32602" in str(exc)
        assert "bad params" in str(exc)
    else:
        raise AssertionError("RPC error was accepted")


def test_evm_contract_emits_explicit_experimental_envelope(capsys):
    evm.tool_evm_contract("0x" + "2" * 40, "6000", gas="53000", network="testnet")
    out = _output(capsys)
    assert out["Status"] == "experimental-build-only"
    assert out["ConfiguredChainID"] == 1449000
    assert out["UnsignedTransaction"] == {
        "from": "0x" + "2" * 40,
        "data": "0x6000",
        "value": "0x0",
        "gas": hex(53000),
        "chainId": 1449000,
    }
    assert "ABI" not in out["UnsignedTransaction"]


def test_evm_contract_rejects_abi_and_bad_inputs(capsys):
    sender = "0x" + "3" * 40
    evm.tool_evm_contract(sender, "6000", abi="[]")
    assert _output(capsys)["Error"] == "ValueError"
    evm.tool_evm_contract(sender, "xyz")
    assert _output(capsys)["Error"] == "ValueError"
    evm.tool_evm_contract(sender, "6000", gas="١٢٣")
    assert _output(capsys)["Error"] == "ValueError"
    evm.tool_evm_contract(sender, "6000", network="invalid")
    assert _output(capsys)["Error"] == "ValueError"


def test_evm_bridge_is_network_identity_only(monkeypatch, capsys):
    def fake_rpc(_url, method, _params):
        return {"eth_chainId": hex(1440000), "eth_blockNumber": "0x2a"}[method]

    monkeypatch.setattr(evm, "_rpc", fake_rpc)
    evm.tool_evm_bridge("mainnet")
    out = _output(capsys)
    assert out["ObservedChainID"] == 1440000
    assert out["LatestBlock"] == 42
    assert out["BridgeCertified"] is False
    assert out["Capability"] == "EVM network identity/status only"


def test_evm_bridge_rejects_chain_mismatch_and_invalid_network(monkeypatch, capsys):
    monkeypatch.setattr(
        evm,
        "_rpc",
        lambda _url, method, _params: hex(1) if method == "eth_chainId" else "0x2a",
    )
    evm.tool_evm_bridge("mainnet")
    out = _output(capsys)
    assert out["Error"] == "RuntimeError"
    assert "does not match" in out["Message"]

    evm.tool_evm_bridge("invalid")
    assert _output(capsys)["Error"] == "ValueError"
