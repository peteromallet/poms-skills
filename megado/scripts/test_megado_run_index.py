#!/usr/bin/env python3

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("megado_run_index.py")


class RunIndexTest(unittest.TestCase):
    def test_register_is_idempotent_and_handoff_links_cloud(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            index = root / "run-index.json"
            command = [
                "python3",
                str(SCRIPT),
                "--index",
                str(index),
                "register",
                "--run-id",
                "run-1",
                "--project-root",
                str(root / "repo"),
                "--otto-dir",
                str(root / "repo/.otto/runs/run-1"),
                "--worktree",
                str(root / "repo/.otto/worktrees/run-1"),
                "--source-ref",
                "main",
                "--base-sha",
                "abc123",
                "--parent-source",
                "codex",
                "--parent-session-id",
                "session-1",
            ]
            first = json.loads(subprocess.check_output(command, text=True))
            second_command = [
                item
                for position, item in enumerate(command)
                if position not in {command.index("--parent-source"), command.index("--parent-source") + 1,
                                    command.index("--parent-session-id"), command.index("--parent-session-id") + 1}
            ]
            second = json.loads(subprocess.check_output(second_command, text=True))
            self.assertEqual(first["logical_run_key"], second["logical_run_key"])
            self.assertEqual(first["registered_at"], second["registered_at"])
            self.assertEqual(second["parent"]["session_id"], "session-1")
            self.assertEqual(len(json.loads(index.read_text())["runs"]), 1)

            handoff = json.loads(
                subprocess.check_output(
                    [
                        "python3",
                        str(SCRIPT),
                        "--index",
                        str(index),
                        "handoff",
                        "--logical-run-key",
                        first["logical_run_key"],
                        "--project-id",
                        "agentbox-project-7",
                        "--evidence",
                        "AgentBox ledger registration receipt 7.",
                    ],
                    text=True,
                )
            )
            self.assertEqual(handoff["owner_hint"], "agentbox:agentbox-project-7")
            self.assertEqual(handoff["local_role"], "observer")

            conflicting = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "--index",
                    str(index),
                    "handoff",
                    "--logical-run-key",
                    first["logical_run_key"],
                    "--project-id",
                    "agentbox-project-8",
                    "--evidence",
                    "unrelated receipt",
                ],
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(conflicting.returncode, 0)
            self.assertIn("refusing to relink", conflicting.stderr)

    def test_unknown_run_update_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            completed = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "--index",
                    str(Path(temp_dir) / "index.json"),
                    "set-hint",
                    "--logical-run-key",
                    "missing",
                    "--lifecycle-hint",
                    "completed",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("unknown logical run", completed.stderr)


if __name__ == "__main__":
    unittest.main()
