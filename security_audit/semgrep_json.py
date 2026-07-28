#!/usr/bin/env python3
"""
semgrep_json.py - rendre lisible / normaliser / comparer des sorties Semgrep JSON.

Meme pattern que bandit_json.py (inspiration sort/compare nodes.json de l'encadrant).

Exemples :
  ./semgrep_json.py normalize semgrep_security.json -o semgrep.normalized.json
  ./semgrep_json.py report semgrep_security.json -o semgrep.md
  ./semgrep_json.py diff old.json new.json -o diff.md --fail-on-new
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from typing import Any

from _sast_json_common import (
    dump_json,
    load_json,
    norm_path,
    sev_rank_semgrep,
    write_text,
)


SCHEMA = "tiledviz.sast.semgrep.normalized.v1"


def _looks_like_fingerprint(fp: str) -> bool:
    """Semgrep OSS peut mettre un libelle (ex. 'requires login') dans fingerprint."""
    s = str(fp).strip()
    if len(s) < 16 or " " in s:
        return False
    return True


def finding_key(r: dict[str, Any]) -> str:
    if r.get("key") and "start_line" in r:
        return str(r["key"])
    extra = r.get("extra") or {}
    fp = extra.get("fingerprint") or r.get("fingerprint")
    if fp and _looks_like_fingerprint(str(fp)):
        return f"fp::{fp}"
    path = norm_path(str(r.get("path", "")))
    start = r.get("start") or {}
    line = start.get("line") if start else r.get("start_line", "")
    return f"{r.get('check_id', '')}::{path}::{line}"


def extract_results(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, dict) and data.get("schema") == SCHEMA:
        return list(data.get("findings") or [])
    if isinstance(data, dict) and "results" in data:
        return list(data["results"] or [])
    if isinstance(data, dict) and "findings" in data:
        return list(data["findings"] or [])
    if isinstance(data, list):
        return list(data)
    raise ValueError("JSON Semgrep attendu : objet avec cle 'results'")


def short_rule(check_id: str) -> str:
    if not check_id:
        return ""
    return check_id.rsplit(".", 1)[-1]


def normalize_payload(data: Any) -> dict[str, Any]:
    if isinstance(data, dict) and data.get("schema") == SCHEMA:
        return data

    results = extract_results(data)
    findings: list[dict[str, Any]] = []
    seen: set[str] = set()
    collapsed = 0
    for r in results:
        extra = r.get("extra") or {}
        start = r.get("start") or {}
        end = r.get("end") or {}
        key = finding_key(r)
        if key in seen:
            collapsed += 1
            continue
        seen.add(key)
        sev = (extra.get("severity") or r.get("severity") or "").upper()
        path = norm_path(str(r.get("path", "")))
        start_line = start.get("line") if start else r.get("start_line")
        end_line = end.get("line") if end else r.get("end_line")
        findings.append(
            {
                "key": key,
                "check_id": r.get("check_id"),
                "rule_short": short_rule(str(r.get("check_id") or "")),
                "severity": sev,
                "path": path,
                "start_line": start_line,
                "end_line": end_line,
                "message": extra.get("message") or r.get("message"),
                "fingerprint": extra.get("fingerprint") or r.get("fingerprint"),
                "lines": extra.get("lines") or r.get("lines"),
            }
        )
    findings.sort(
        key=lambda x: (x["path"], x["start_line"] or 0, x["check_id"] or "")
    )
    by_sev = Counter(f["severity"] for f in findings)
    meta: dict[str, Any] = {}
    if isinstance(data, dict) and "version" in data:
        meta = {"version": data.get("version"), "engine": data.get("engine_requested")}
    elif isinstance(data, dict) and data.get("meta"):
        meta = dict(data["meta"])
    out: dict[str, Any] = {
        "tool": "semgrep",
        "schema": SCHEMA,
        "meta": meta,
        "count": len(findings),
        "by_severity": dict(sorted(by_sev.items())),
        "findings": findings,
    }
    if collapsed:
        out["duplicates_collapsed"] = collapsed
    return out


def cmd_normalize(args: argparse.Namespace) -> int:
    dump_json(normalize_payload(load_json(args.input)), args.out)
    return 0


def render_report(norm: dict[str, Any], source: str) -> str:
    lines: list[str] = []
    lines.append("# Rapport Semgrep (lisible)")
    lines.append("")
    lines.append(f"- **Source** : `{source}`")
    if norm.get("meta"):
        lines.append(f"- **Meta** : {norm['meta']}")
    lines.append(f"- **Findings** : {norm['count']}")
    lines.append(f"- **Par severite** : {norm.get('by_severity') or {}}")
    if norm.get("duplicates_collapsed"):
        lines.append(
            f"- **Doublons fusionnes** : {norm['duplicates_collapsed']}"
        )
    lines.append("")
    lines.append("| Severite | Regle | Fichier | Ligne | Message |")
    lines.append("|----------|-------|---------|-------|---------|")
    for f in norm["findings"]:
        msg = (f.get("message") or "").replace("|", "\\|").replace("\n", " ")
        if len(msg) > 80:
            msg = msg[:77] + "..."
        rule = f.get("rule_short") or f.get("check_id") or ""
        lines.append(
            f"| {f.get('severity','')} | `{rule}` | `{f.get('path','')}` | "
            f"{f.get('start_line','')} | {msg} |"
        )
    lines.append("")
    errs = [f for f in norm["findings"] if f.get("severity") in ("ERROR", "HIGH")]
    if errs:
        lines.append("## Detail - ERROR / HIGH")
        lines.append("")
        for f in errs:
            lines.append(
                f"### `{f.get('rule_short')}` - `{f.get('path')}:{f.get('start_line')}`"
            )
            lines.append("")
            lines.append(f"{f.get('message') or ''}")
            lines.append("")
            snippet = f.get("lines") or ""
            if snippet:
                lines.append("```")
                lines.append(str(snippet).rstrip())
                lines.append("```")
                lines.append("")
            lines.append(f"- check_id : `{f.get('check_id')}`")
            lines.append("")
    return "\n".join(lines)


def cmd_report(args: argparse.Namespace) -> int:
    norm = normalize_payload(load_json(args.input))
    write_text(render_report(norm, str(args.input)), args.out)
    return 0


def index_by_key(norm: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {f["key"]: f for f in norm["findings"]}


def cmd_diff(args: argparse.Namespace) -> int:
    a = normalize_payload(load_json(args.baseline))
    b = normalize_payload(load_json(args.current))
    ia, ib = index_by_key(a), index_by_key(b)
    keys_a, keys_b = set(ia), set(ib)
    new = sorted(keys_b - keys_a)
    resolved = sorted(keys_a - keys_b)
    stable = sorted(keys_a & keys_b)

    lines: list[str] = []
    lines.append("# Diff Semgrep")
    lines.append("")
    lines.append(f"- **Baseline (A)** : `{args.baseline}` - {a['count']} findings")
    lines.append(f"- **Courant (B)** : `{args.current}` - {b['count']} findings")
    lines.append(f"- **Nouveaux** : {len(new)}")
    lines.append(f"- **Resolus** : {len(resolved)}")
    lines.append(f"- **Stables** : {len(stable)}")
    lines.append("")

    def table(title: str, keys: list[str], src: dict[str, dict[str, Any]]) -> None:
        lines.append(f"## {title} ({len(keys)})")
        lines.append("")
        if not keys:
            lines.append("*(aucun)*")
            lines.append("")
            return
        lines.append("| Severite | Regle | Fichier | Ligne | Message |")
        lines.append("|----------|-------|---------|-------|---------|")
        for k in keys:
            f = src[k]
            msg = (f.get("message") or "").replace("|", "\\|").replace("\n", " ")
            if len(msg) > 60:
                msg = msg[:57] + "..."
            rule = f.get("rule_short") or ""
            lines.append(
                f"| {f.get('severity','')} | `{rule}` | `{f.get('path','')}` | "
                f"{f.get('start_line','')} | {msg} |"
            )
        lines.append("")

    table("Nouveaux (dans B, absents de A)", new, ib)
    table("Resolus (dans A, absents de B)", resolved, ia)

    write_text("\n".join(lines), args.out)

    fail = False
    if args.fail_on_new and new:
        fail = True
    if args.fail_on_severity:
        thr = sev_rank_semgrep(args.fail_on_severity)
        for k in new:
            if sev_rank_semgrep(ib[k].get("severity", "")) >= thr:
                fail = True
                break

    print(
        f"semgrep_diff: new={len(new)} resolved={len(resolved)} stable={len(stable)}",
        file=sys.stderr,
    )
    return 1 if fail else 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Semgrep JSON : normalize / report / diff (compatible CI)."
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    n = sub.add_parser("normalize", help="JSON stable trie")
    n.add_argument("input")
    n.add_argument("-o", "--out", default="-")
    n.set_defaults(func=cmd_normalize)

    r = sub.add_parser("report", help="Rapport Markdown lisible")
    r.add_argument("input")
    r.add_argument("-o", "--out", default="-")
    r.set_defaults(func=cmd_report)

    d = sub.add_parser("diff", help="Comparer deux analyses")
    d.add_argument("baseline")
    d.add_argument("current")
    d.add_argument("-o", "--out", default="-")
    d.add_argument("--fail-on-new", action="store_true")
    d.add_argument(
        "--fail-on-severity",
        metavar="LEVEL",
        help="seuil sur NOUVEAUX (ERROR|WARNING|INFO)",
    )
    d.set_defaults(func=cmd_diff)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
