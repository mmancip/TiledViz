#!/usr/bin/env python3
"""Helpers partages - normalisation de chemins et I/O JSON (stdlib only)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> Any:
    p = Path(path)
    with p.open(encoding="utf-8") as f:
        return json.load(f)


def dump_json(data: Any, path: str | Path | None) -> None:
    text = json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if path is None or path == "-":
        sys.stdout.write(text)
    else:
        Path(path).write_text(text, encoding="utf-8")


def write_text(text: str, path: str | Path | None) -> None:
    if not text.endswith("\n"):
        text += "\n"
    if path is None or path == "-":
        sys.stdout.write(text)
    else:
        Path(path).write_text(text, encoding="utf-8")


def norm_path(path: str) -> str:
    """Chemin stable pour comparaison (sans ./ initial)."""
    p = path.replace("\\", "/").strip()
    while p.startswith("./"):
        p = p[2:]
    return p


def sev_rank_bandit(sev: str) -> int:
    return {"HIGH": 3, "MEDIUM": 2, "LOW": 1, "UNDEFINED": 0}.get(
        (sev or "").upper(), 0
    )


def sev_rank_semgrep(sev: str) -> int:
    # Semgrep: ERROR / WARNING / INFO (parfois HIGH/MEDIUM via metadata)
    s = (sev or "").upper()
    return {
        "ERROR": 3,
        "HIGH": 3,
        "WARNING": 2,
        "MEDIUM": 2,
        "INFO": 1,
        "LOW": 1,
    }.get(s, 0)
