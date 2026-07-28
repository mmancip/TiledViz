#!/usr/bin/env python3
"""
bandit_json.py - rendre lisible / normaliser / comparer des sorties Bandit JSON.

Inspiration : sort_json.py / compare_json.py (encadrant) - pattern normaliser puis comparer,
adapte aux findings Bandit (pas nodes.json TiledViz).

Exemples :
  ./bandit_json.py normalize bandit.json -o bandit.normalized.json
  ./bandit_json.py report bandit.json -o bandit.md
  ./bandit_json.py diff old.json new.json -o diff.md --fail-on-new
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
    sev_rank_bandit,
    write_text,
)


SCHEMA = "tiledviz.sast.bandit.normalized.v1"


def finding_key(r: dict[str, Any]) -> str:
    if r.get("key") and "test_id" in r and "issue_severity" not in r:
        return str(r["key"])
    return (
        f"{r.get('test_id', '')}::"
        f"{norm_path(str(r.get('filename', '')))}::"
        f"{r.get('line_number', '')}"
    )


def extract_results(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, dict) and data.get("schema") == SCHEMA:
        return list(data.get("findings") or [])
    if isinstance(data, dict) and "results" in data:
        return list(data["results"] or [])
    if isinstance(data, dict) and "findings" in data:
        return list(data["findings"] or [])
    if isinstance(data, list):
        return list(data)
    raise ValueError("JSON Bandit attendu : objet avec cle 'results' (ou liste de findings)")


def normalize_payload(data: Any) -> dict[str, Any]:
    if isinstance(data, dict) and data.get("schema") == SCHEMA:
        return data

    results = extract_results(data)
    findings: list[dict[str, Any]] = []
    seen: set[str] = set()
    collapsed = 0
    for r in results:
        key = finding_key(r)
        if key in seen:
            collapsed += 1
            continue
        seen.add(key)
        findings.append(
            {
                "key": key,
                "test_id": r.get("test_id"),
                "test_name": r.get("test_name"),
                "severity": (
                    r.get("issue_severity") or r.get("severity") or ""
                ).upper(),
                "confidence": (
                    r.get("issue_confidence") or r.get("confidence") or ""
                ).upper(),
                "filename": norm_path(str(r.get("filename", ""))),
                "line_number": r.get("line_number"),
                "issue_text": r.get("issue_text"),
                "more_info": r.get("more_info"),
                "code": r.get("code"),
            }
        )
    findings.sort(key=lambda x: (x["filename"], x["line_number"] or 0, x["test_id"] or ""))
    by_sev = Counter(f["severity"] for f in findings)
    out: dict[str, Any] = {
        "tool": "bandit",
        "schema": SCHEMA,
        "count": len(findings),
        "by_severity": dict(sorted(by_sev.items())),
        "findings": findings,
    }
    if collapsed:
        out["duplicates_collapsed"] = collapsed
    return out


def cmd_normalize(args: argparse.Namespace) -> int:
    data = load_json(args.input)
    dump_json(normalize_payload(data), args.out)
    return 0


def render_report(norm: dict[str, Any], source: str) -> str:
    lines: list[str] = []
    lines.append("# Rapport Bandit (lisible)")
    lines.append("")
    lines.append(f"- **Source** : `{source}`")
    lines.append(f"- **Findings** : {norm['count']}")
    lines.append(f"- **Par severite** : {norm.get('by_severity') or {}}")
    if norm.get("duplicates_collapsed"):
        lines.append(
            f"- **Doublons fusionnes** : {norm['duplicates_collapsed']}"
        )
    lines.append("")
    lines.append("| Severite | Confiance | ID | Fichier | Ligne | Message |")
    lines.append("|----------|-----------|----|---------|-------|---------|")
    for f in norm["findings"]:
        msg = (f.get("issue_text") or "").replace("|", "\\|").replace("\n", " ")
        if len(msg) > 80:
            msg = msg[:77] + "..."
        lines.append(
            f"| {f.get('severity','')} | {f.get('confidence','')} | `{f.get('test_id','')}` | "
            f"`{f.get('filename','')}` | {f.get('line_number','')} | {msg} |"
        )
    lines.append("")
    highs = [f for f in norm["findings"] if f.get("severity") == "HIGH"]
    if highs:
        lines.append("## Detail - HIGH")
        lines.append("")
        for f in highs:
            lines.append(f"### `{f.get('test_id')}` - `{f.get('filename')}:{f.get('line_number')}`")
            lines.append("")
            lines.append(f"{f.get('issue_text') or ''}")
            lines.append("")
            code = f.get("code") or ""
            if code:
                lines.append("```")
                lines.append(code.rstrip())
                lines.append("```")
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
    lines.append("# Diff Bandit")
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
        lines.append("| Severite | ID | Fichier | Ligne | Message |")
        lines.append("|----------|----|---------|-------|---------|")
        for k in keys:
            f = src[k]
            msg = (f.get("issue_text") or "").replace("|", "\\|").replace("\n", " ")
            if len(msg) > 60:
                msg = msg[:57] + "..."
            lines.append(
                f"| {f.get('severity','')} | `{f.get('test_id','')}` | `{f.get('filename','')}` | "
                f"{f.get('line_number','')} | {msg} |"
            )
        lines.append("")

    table("Nouveaux (dans B, absents de A)", new, ib)
    table("Resolus (dans A, absents de B)", resolved, ia)

    write_text("\n".join(lines), args.out)

    fail = False
    if args.fail_on_new and new:
        fail = True
    if args.fail_on_severity:
        thr = sev_rank_bandit(args.fail_on_severity)
        for k in new:
            if sev_rank_bandit(ib[k].get("severity", "")) >= thr:
                fail = True
                break

    print(
        f"bandit_diff: new={len(new)} resolved={len(resolved)} stable={len(stable)}",
        file=sys.stderr,
    )
    return 1 if fail else 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Bandit JSON : normalize / report / diff (compatible CI)."
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    n = sub.add_parser("normalize", help="JSON stable trie (cle d'identite)")
    n.add_argument("input", help="bandit.json brut")
    n.add_argument("-o", "--out", default="-", help="sortie (defaut: stdout)")
    n.set_defaults(func=cmd_normalize)

    r = sub.add_parser("report", help="Rapport Markdown lisible")
    r.add_argument("input", help="bandit.json brut ou normalise")
    r.add_argument("-o", "--out", default="-", help="sortie .md (defaut: stdout)")
    r.set_defaults(func=cmd_report)

    d = sub.add_parser("diff", help="Comparer deux analyses (A=baseline, B=courant)")
    d.add_argument("baseline", help="JSON A (reference)")
    d.add_argument("current", help="JSON B (nouveau run)")
    d.add_argument("-o", "--out", default="-", help="rapport diff .md")
    d.add_argument(
        "--fail-on-new",
        action="store_true",
        help="exit 1 si findings nouveaux dans B",
    )
    d.add_argument(
        "--fail-on-severity",
        metavar="LEVEL",
        help="exit 1 si un NOUVEAU finding >= LEVEL (HIGH|MEDIUM|LOW)",
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
