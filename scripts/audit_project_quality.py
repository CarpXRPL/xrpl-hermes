#!/usr/bin/env python3
"""Project quality audit for XRPL-Hermes.

Offline regression checks that keep the repo honest as it grows:

1. no-seeds          — no decodable XRPL family seed appears anywhere in the repo
2. neutral-language  — no hostile competitor wording in public docs
3. command-count     — every "N commands" claim in docs matches the dispatcher
4. version-sync      — pyproject, SKILL.md, MCP SERVER_INFO, and CHANGELOG agree
5. currency-literals — no raw 4-20 char currency literals passed to xrpl-py
                       models without normalize_currency_code (long codes must
                       be 160-bit hex on-ledger)

Exit 0 = clean, exit 1 = findings (printed as JSON).
"""
from __future__ import annotations
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TEXT_SUFFIXES = {".py", ".md", ".toml", ".txt", ".sh", ".json", ".yml", ".yaml", ".js"}


def _tracked_files() -> list[Path]:
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, text=True, capture_output=True, check=True)
    return [ROOT / line for line in out.stdout.splitlines()
            if (ROOT / line).suffix in TEXT_SUFFIXES and (ROOT / line).is_file()]


def check_no_seeds(files) -> list[str]:
    """Flag only strings that actually decode as XRPL seeds — zero false positives."""
    from xrpl.core.addresscodec import decode_seed
    candidate = re.compile(r"\bs[1-9A-HJ-NP-Za-km-z]{20,40}\b")
    findings = []
    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace")
        for match in candidate.finditer(text):
            token = match.group(0)
            try:
                decode_seed(token)
            except Exception:
                continue
            line = text.count("\n", 0, match.start()) + 1
            findings.append(f"{f.relative_to(ROOT)}:{line}: decodable XRPL seed-shaped string '{token[:4]}…'")
    return findings


def check_neutral_language(files) -> list[str]:
    banned = [
        re.compile("(?i)" + "xrpl" + "claw"),
        re.compile(r"(?i)\b(crush|destroy|kill|obliterate)\s+(the\s+)?competit"),
        re.compile(r"(?i)\bunlike\s+(the\s+)?(broken|inferior|garbage)\b"),
    ]
    findings = []
    for f in files:
        if f.suffix != ".md" and f.name not in ("pyproject.toml",):
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        for pat in banned:
            for match in pat.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                findings.append(f"{f.relative_to(ROOT)}:{line}: hostile/competitor wording '{match.group(0)}'")
    return findings


def check_command_count(files) -> list[str]:
    from scripts.xrpl_tools import COMMANDS
    actual = len(COMMANDS)
    claim = re.compile(r"\b(\d{2,3})(?:-command\b|\s+(?:CLI\s+)?commands\b)")
    findings = []
    for f in files:
        if f.suffix not in (".md", ".py"):
            continue
        # CHANGELOG entries record the count at release time; AUDIT files are generated.
        if f.name in (Path(__file__).name, "CHANGELOG.md") or f.name.startswith("AUDIT-"):
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        for match in claim.finditer(text):
            n = int(match.group(1))
            if n != actual:
                line = text.count("\n", 0, match.start()) + 1
                findings.append(f"{f.relative_to(ROOT)}:{line}: claims {n} commands, dispatcher has {actual}")
    return findings


def check_version_sync(files) -> list[str]:
    findings = []
    versions = {}
    pyproject = (ROOT / "pyproject.toml").read_text()
    m = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.M)
    versions["pyproject.toml"] = m.group(1) if m else None
    skill = (ROOT / "SKILL.md").read_text()
    m = re.search(r"^version:\s*(\S+)", skill, re.M)
    versions["SKILL.md"] = m.group(1) if m else None
    mcp = (ROOT / "scripts" / "mcp_server.py").read_text()
    m = re.search(r'"version":\s*"([^"]+)"', mcp)
    versions["mcp_server.py"] = m.group(1) if m else None
    changelog = (ROOT / "CHANGELOG.md").read_text()
    m = re.search(r"^##\s*v?(\d+\.\d+\.\d+)", changelog, re.M)
    versions["CHANGELOG.md (latest entry)"] = m.group(1) if m else None
    distinct = {v for v in versions.values()}
    if None in distinct or len(distinct) != 1:
        findings.append(f"version mismatch: {versions}")
    return findings


def check_currency_literals(files) -> list[str]:
    """xrpl-py model calls with a literal 4-20 char currency must use hex/normalization."""
    pat = re.compile(r"currency\s*=\s*[\"']([A-Za-z0-9]{4,20})[\"']")
    findings = []
    for f in files:
        if f.suffix != ".py":
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        for match in pat.finditer(text):
            code = match.group(1)
            try:
                bytes.fromhex(code)
                continue  # 40-char hex literals are fine (none shorter can be hex+valid)
            except ValueError:
                pass
            line = text.count("\n", 0, match.start()) + 1
            findings.append(
                f"{f.relative_to(ROOT)}:{line}: literal currency '{code}' is {len(code)} chars — "
                "long codes must be 160-bit hex on-ledger; use normalize_currency_code()")
    return findings


CHECKS = [
    ("no-seeds", check_no_seeds),
    ("neutral-language", check_neutral_language),
    ("command-count", check_command_count),
    ("version-sync", check_version_sync),
    ("currency-literals", check_currency_literals),
]


def main() -> int:
    files = _tracked_files()
    report = {}
    failed = False
    for name, fn in CHECKS:
        findings = fn(files)
        report[name] = {"status": "PASS" if not findings else "FAIL", "findings": findings}
        failed = failed or bool(findings)
    print(json.dumps(report, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
