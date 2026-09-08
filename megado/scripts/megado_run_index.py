#!/usr/bin/env python3
"""Maintain a lightweight discovery index for Megado runs.

The index is a hint for fleet discovery. Repository .otto state and the
AgentBox operation ledger remain authoritative.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VALID_HINTS = {"created", "planning", "executing", "reviewing", "blocked", "completed"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def logical_key(project_root: str, run_id: str) -> str:
    digest = hashlib.sha256(f"{Path(project_root).resolve()}\0{run_id}".encode()).hexdigest()[:16]
    return f"megado:{run_id}:{digest}"


def ensure_private_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.chmod(0o700)


def read_index(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": 1, "updated_at": None, "runs": {}}
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict) or not isinstance(value.get("runs"), dict):
        raise ValueError("run index is not a valid object with a runs map")
    return value


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    ensure_private_dir(path.parent)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
        path.chmod(0o600)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def mutate(index_path: Path, callback) -> dict[str, Any]:
    ensure_private_dir(index_path.parent)
    lock_path = index_path.with_suffix(index_path.suffix + ".lock")
    with lock_path.open("a+") as lock:
        lock_path.chmod(0o600)
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        index = read_index(index_path)
        result = callback(index)
        index["updated_at"] = now_iso()
        atomic_write(index_path, index)
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
    return result


def register(args: argparse.Namespace) -> dict[str, Any]:
    key = logical_key(args.project_root, args.run_id)

    def apply(index: dict[str, Any]) -> dict[str, Any]:
        existing = index["runs"].get(key, {})
        registered_at = existing.get("registered_at", now_iso())
        parent = dict(existing.get("parent") or {})
        supplied_parent = {
            "source": args.parent_source,
            "session_id": args.parent_session_id,
            "transcript_path": args.transcript_path,
            "resume_command": args.resume_command,
            "cwd": args.parent_cwd,
        }
        for parent_key, value in supplied_parent.items():
            if value is not None:
                parent[parent_key] = value
        record = {
            **existing,
            "logical_run_key": key,
            "run_id": args.run_id,
            "project_root": str(Path(args.project_root).resolve()),
            "otto_dir": str(Path(args.otto_dir).resolve()),
            "worktree": str(Path(args.worktree).resolve()),
            "source_ref": args.source_ref,
            "base_sha": args.base_sha,
            "registered_at": registered_at,
            "last_declared_at": now_iso(),
            "lifecycle_hint": existing.get("lifecycle_hint", "created"),
            "owner_hint": existing.get("owner_hint", "local"),
            "parent": parent,
        }
        index["runs"][key] = record
        return record

    return mutate(args.index, apply)


def set_hint(args: argparse.Namespace) -> dict[str, Any]:
    if args.lifecycle_hint not in VALID_HINTS:
        raise ValueError(f"lifecycle hint must be one of {sorted(VALID_HINTS)}")

    def apply(index: dict[str, Any]) -> dict[str, Any]:
        record = index["runs"].get(args.logical_run_key)
        if not record:
            raise ValueError(f"unknown logical run: {args.logical_run_key}")
        record["lifecycle_hint"] = args.lifecycle_hint
        record["phase_hint"] = args.phase
        record["candidate_sha_hint"] = args.candidate_sha
        record["last_declared_at"] = now_iso()
        if args.evidence:
            record["last_hint_evidence"] = args.evidence
        return record

    return mutate(args.index, apply)


def handoff(args: argparse.Namespace) -> dict[str, Any]:
    def apply(index: dict[str, Any]) -> dict[str, Any]:
        record = index["runs"].get(args.logical_run_key)
        if not record:
            raise ValueError(f"unknown logical run: {args.logical_run_key}")
        previous_project_id = record.get("cloud_project_id")
        if previous_project_id and previous_project_id != args.project_id:
            raise ValueError(
                "run is already linked to AgentBox project "
                f"{previous_project_id}; refusing to relink it to {args.project_id}"
            )
        record.update(
            {
                "owner_hint": f"agentbox:{args.project_id}",
                "cloud_project_id": args.project_id,
                "local_role": "observer",
                "handoff_at": now_iso(),
                "handoff_evidence": args.evidence,
                "last_declared_at": now_iso(),
            }
        )
        return record

    return mutate(args.index, apply)


def list_runs(args: argparse.Namespace) -> dict[str, Any]:
    return read_index(args.index)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--index",
        type=Path,
        default=Path.home() / ".local" / "state" / "megado" / "run-index.json",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    register_parser = subparsers.add_parser("register")
    register_parser.add_argument("--run-id", required=True)
    register_parser.add_argument("--project-root", required=True)
    register_parser.add_argument("--otto-dir", required=True)
    register_parser.add_argument("--worktree", required=True)
    register_parser.add_argument("--source-ref", required=True)
    register_parser.add_argument("--base-sha", required=True)
    register_parser.add_argument("--parent-source")
    register_parser.add_argument("--parent-session-id")
    register_parser.add_argument("--transcript-path")
    register_parser.add_argument("--resume-command")
    register_parser.add_argument("--parent-cwd")
    register_parser.set_defaults(handler=register)

    hint_parser = subparsers.add_parser("set-hint")
    hint_parser.add_argument("--logical-run-key", required=True)
    hint_parser.add_argument("--lifecycle-hint", required=True)
    hint_parser.add_argument("--phase")
    hint_parser.add_argument("--candidate-sha")
    hint_parser.add_argument("--evidence")
    hint_parser.set_defaults(handler=set_hint)

    handoff_parser = subparsers.add_parser("handoff")
    handoff_parser.add_argument("--logical-run-key", required=True)
    handoff_parser.add_argument("--project-id", required=True)
    handoff_parser.add_argument("--evidence", required=True)
    handoff_parser.set_defaults(handler=handoff)

    list_parser = subparsers.add_parser("list")
    list_parser.set_defaults(handler=list_runs)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        result = args.handler(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
