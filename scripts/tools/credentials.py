#!/usr/bin/env python3
"""Credential tools (XLS-70 DID)."""
from ._shared import (
    note_out, json_tx_out, _dispatch_build,
    CredentialCreate, CredentialAccept, CredentialDelete,
)

def tool_build_credential_create(frm: str, subject: str, credential_type: str,
                                  uri: str = None, expiration: str = None):
    kwargs: dict = dict(account=frm, subject=subject, credential_type=credential_type)
    if uri: kwargs["uri"] = uri
    if expiration: kwargs["expiration"] = int(expiration)
    tx = CredentialCreate(**kwargs)
    note_out("# CredentialCreate TX JSON - signer-ready JSON")
    json_tx_out(tx)

def tool_build_credential_accept(frm: str, issuer: str, credential_type: str):
    tx = CredentialAccept(account=frm, issuer=issuer, credential_type=credential_type)
    note_out("# CredentialAccept TX JSON - signer-ready JSON")
    json_tx_out(tx)

def tool_build_credential_delete(frm: str, credential_type: str,
                                  subject: str = None, issuer: str = None):
    kwargs: dict = dict(account=frm, credential_type=credential_type)
    if subject: kwargs["subject"] = subject
    if issuer: kwargs["issuer"] = issuer
    tx = CredentialDelete(**kwargs)
    note_out("# CredentialDelete TX JSON - signer-ready JSON")
    json_tx_out(tx)

COMMANDS = {
    "build-credential-create": lambda: _dispatch_build(3, tool_build_credential_create),
    "build-credential-accept": lambda: _dispatch_build(3, tool_build_credential_accept),
    "build-credential-delete": lambda: _dispatch_build(2, tool_build_credential_delete),
}
