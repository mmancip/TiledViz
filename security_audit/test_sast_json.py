#!/usr/bin/env python3
"""
Tests unitaires - bandit_json.py / semgrep_json.py

Usage (depuis ce dossier) :
  python3 test_sast_json.py
  python3 -m unittest test_sast_json -v
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
PREUVES_SAST = SCRIPTS.parent.parent / "06_preuves" / "figement_toe" / "sast"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import bandit_json as bj
import semgrep_json as sj


BANDIT_RAW = {
    "results": [
        {
            "test_id": "B605",
            "test_name": "start_process_with_a_shell",
            "issue_severity": "HIGH",
            "issue_confidence": "HIGH",
            "filename": "./TVConnections/TVConnection.py",
            "line_number": 63,
            "issue_text": "Starting a process with a shell",
            "code": "os.system(cmd)",
        },
        {
            "test_id": "B307",
            "test_name": "blacklist",
            "issue_severity": "MEDIUM",
            "issue_confidence": "HIGH",
            "filename": "TVConnections/TVConnection.py",
            "line_number": 183,
            "issue_text": "Use of possibly insecure function",
            "code": "eval(x)",
        },
        {
            "test_id": "B605",
            "test_name": "start_process_with_a_shell",
            "issue_severity": "HIGH",
            "issue_confidence": "HIGH",
            "filename": "TVConnections/TVConnection.py",
            "line_number": 63,
            "issue_text": "Starting a process with a shell (dup)",
            "code": "os.system(cmd)",
        },
    ]
}

SEMGREP_RAW = {
    "version": "1.0.0",
    "engine_requested": "OSS",
    "results": [
        {
            "check_id": "python.lang.security.audit.subprocess-shell-true.subprocess-shell-true",
            "path": "TVConnections/TileServer.py",
            "start": {"line": 488},
            "end": {"line": 488},
            "extra": {
                "severity": "ERROR",
                "message": "Found subprocess with shell=True",
                "fingerprint": "requires login",
                "lines": "Popen(cmd, shell=True)",
            },
        },
        {
            "check_id": "python.lang.security.audit.avoid-bind-to-all-interfaces.avoid-bind-to-all-interfaces",
            "path": "./TVConnections/TileServer.py",
            "start": {"line": 131},
            "end": {"line": 131},
            "extra": {
                "severity": "INFO",
                "message": "bind to 0.0.0.0",
                "fingerprint": "requires login",
                "lines": "sock.bind(('0.0.0.0', 80))",
            },
        },
    ],
}


def _write_json(path: Path, data: object) -> Path:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


class TestBanditJson(unittest.TestCase):
    def test_normalize_collapses_duplicates_and_paths(self) -> None:
        norm = bj.normalize_payload(BANDIT_RAW)
        self.assertEqual(norm["schema"], bj.SCHEMA)
        self.assertEqual(norm["count"], 2)
        self.assertEqual(norm.get("duplicates_collapsed"), 1)
        keys = {f["key"] for f in norm["findings"]}
        self.assertIn("B605::TVConnections/TVConnection.py::63", keys)
        self.assertTrue(all(not f["filename"].startswith("./") for f in norm["findings"]))

    def test_normalize_idempotent(self) -> None:
        n1 = bj.normalize_payload(BANDIT_RAW)
        n2 = bj.normalize_payload(n1)
        self.assertEqual(n1, n2)
        self.assertEqual(n2["findings"][0]["severity"], "HIGH")

    def test_diff_same_exit_0(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            a = _write_json(t / "a.json", BANDIT_RAW)
            out = t / "diff.md"
            code = bj.main(["diff", str(a), str(a), "-o", str(out), "--fail-on-new"])
            self.assertEqual(code, 0)
            text = out.read_text(encoding="utf-8")
            self.assertIn("**Nouveaux** : 0", text)

    def test_diff_new_finding_fail_on_new(self) -> None:
        baseline = bj.normalize_payload(BANDIT_RAW)
        current = bj.normalize_payload(BANDIT_RAW)
        extra = dict(current["findings"][0])
        extra["line_number"] = 999
        extra["key"] = f"{extra['test_id']}::{extra['filename']}::999"
        extra["issue_text"] = "FAKE NEW"
        current["findings"] = list(current["findings"]) + [extra]
        current["count"] = len(current["findings"])

        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            a = _write_json(t / "a.json", baseline)
            b = _write_json(t / "b.json", current)
            out = t / "diff.md"
            code = bj.main(["diff", str(a), str(b), "-o", str(out), "--fail-on-new"])
            self.assertEqual(code, 1)
            self.assertIn("FAKE NEW", out.read_text(encoding="utf-8"))

    def test_report_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            src = _write_json(t / "bandit.json", BANDIT_RAW)
            out = t / "report.md"
            code = bj.main(["report", str(src), "-o", str(out)])
            self.assertEqual(code, 0)
            text = out.read_text(encoding="utf-8")
            self.assertIn("# Rapport Bandit", text)
            self.assertIn("B605", text)
            self.assertIn("Doublons fusionnes", text)


class TestSemgrepJson(unittest.TestCase):
    def test_normalize_ignores_fake_fingerprint(self) -> None:
        norm = sj.normalize_payload(SEMGREP_RAW)
        self.assertEqual(norm["count"], 2)
        for f in norm["findings"]:
            self.assertFalse(f["key"].startswith("fp::"), f["key"])
            self.assertIn("::", f["key"])

    def test_normalize_idempotent(self) -> None:
        n1 = sj.normalize_payload(SEMGREP_RAW)
        n2 = sj.normalize_payload(n1)
        self.assertEqual(n1["count"], n2["count"])
        self.assertEqual(
            [f["key"] for f in n1["findings"]],
            [f["key"] for f in n2["findings"]],
        )
        sevs = {f["severity"] for f in n2["findings"]}
        self.assertEqual(sevs, {"ERROR", "INFO"})

    def test_diff_new_finding_fail_on_new(self) -> None:
        baseline = sj.normalize_payload(SEMGREP_RAW)
        current = sj.normalize_payload(SEMGREP_RAW)
        extra = dict(current["findings"][0])
        extra["start_line"] = 999
        extra["key"] = f"{extra['check_id']}::{extra['path']}::999"
        extra["message"] = "FAKE NEW SEMGREP"
        current["findings"] = list(current["findings"]) + [extra]
        current["count"] = len(current["findings"])

        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            a = _write_json(t / "a.json", baseline)
            b = _write_json(t / "b.json", current)
            out = t / "diff.md"
            code = sj.main(["diff", str(a), str(b), "-o", str(out), "--fail-on-new"])
            self.assertEqual(code, 1)
            self.assertIn("FAKE NEW SEMGREP", out.read_text(encoding="utf-8"))

    def test_report_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            src = _write_json(t / "semgrep.json", SEMGREP_RAW)
            out = t / "report.md"
            code = sj.main(["report", str(src), "-o", str(out)])
            self.assertEqual(code, 0)
            text = out.read_text(encoding="utf-8")
            self.assertIn("# Rapport Semgrep", text)
            self.assertIn("subprocess-shell-true", text)


@unittest.skipUnless(
    (PREUVES_SAST / "bandit.json").is_file()
    and (PREUVES_SAST / "semgrep_security.json").is_file(),
    "preuves figement_toe absentes",
)
class TestAgainstLabEvidence(unittest.TestCase):
    def test_bandit_self_diff(self) -> None:
        path = PREUVES_SAST / "bandit.json"
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "d.md"
            code = bj.main(["diff", str(path), str(path), "-o", str(out), "--fail-on-new"])
            self.assertEqual(code, 0)

    def test_semgrep_self_diff(self) -> None:
        path = PREUVES_SAST / "semgrep_security.json"
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "d.md"
            code = sj.main(["diff", str(path), str(path), "-o", str(out), "--fail-on-new"])
            self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
