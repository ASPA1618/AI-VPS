#!/usr/bin/env python3
"""Build a sanitised ASPA light snapshot for GitHub/VPS read access.

The collector is allowlist-only. It does not read PostgreSQL, environment
variables, raw logs or legacy source files directly. Optional JSON inputs must
already contain aggregate values only.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

SCHEMA_VERSION = "aspa-light-snapshot-v1"
MAX_BYTES = 512 * 1024

ALLOWED = {
    "runtime": {
        "wsl_status",
        "last_worker_heartbeat",
        "queue_depth",
        "running_task_count",
        "failed_task_count",
        "last_successful_task_at",
    },
    "business_aggregates": {
        "customer_count",
        "vehicle_count",
        "request_count",
        "offer_count",
        "order_count",
        "open_order_count",
        "legacy_import_status",
    },
    "suppliers": {
        "registered_count",
        "enabled_count",
        "healthy_count",
        "degraded_count",
        "offline_count",
        "last_probe_at",
    },
    "versions": {
        "business_schema",
        "legacy_import_contract",
        "supplier_registry",
        "search_envelope",
        "snapshot_publisher",
    },
}

FORBIDDEN_KEY = re.compile(
    r"(?:name|phone|email|address|vin|plate|registration|balance|payment|"
    r"token|secret|password|cookie|authorization|api[_-]?key|credential)",
    re.IGNORECASE,
)
EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
VIN = re.compile(r"\b[A-HJ-NPR-Z0-9]{17}\b")
PHONE = re.compile(r"(?<!\d)(?:\+?\d[\s().-]*){9,15}(?!\d)")
SECRET = re.compile(
    r"(?:sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|"
    r"Bearer\s+[A-Za-z0-9._~-]{16,}|BEGIN\s+(?:RSA|OPENSSH|EC)\s+PRIVATE\s+KEY)",
    re.IGNORECASE,
)
REPO_SLUG = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.strip()


def normalise_remote(remote: str) -> str:
    """Convert Git remote URLs to a non-sensitive owner/repository slug."""
    value = remote.strip()
    if value.startswith("git@") and ":" in value:
        value = value.split(":", 1)[1]
    elif "://" in value:
        parsed = urlparse(value)
        value = parsed.path.lstrip("/")
    value = value.removesuffix(".git").strip("/")
    if not REPO_SLUG.fullmatch(value):
        raise ValueError("Git remote cannot be reduced to a safe owner/repository slug")
    return value


def git_state(repo: Path) -> dict[str, Any]:
    return {
        "repository": normalise_remote(run_git(repo, "config", "--get", "remote.origin.url")),
        "branch": run_git(repo, "branch", "--show-current") or "detached",
        "commit": run_git(repo, "rev-parse", "HEAD"),
        "dirty": bool(run_git(repo, "status", "--porcelain")),
    }


def load_json(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return value


def allowlist(section: str, value: dict[str, Any]) -> dict[str, Any]:
    unknown = sorted(set(value) - ALLOWED[section])
    if unknown:
        raise ValueError(f"Unsupported keys in {section}: {', '.join(unknown)}")
    return {key: value[key] for key in sorted(value)}


def validate(value: Any, path: str = "snapshot") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if FORBIDDEN_KEY.search(str(key)):
                raise ValueError(f"Forbidden key at {path}.{key}")
            validate(child, f"{path}.{key}")
        return
    if isinstance(value, list):
        if len(value) > 200:
            raise ValueError(f"List too long at {path}")
        for index, child in enumerate(value):
            validate(child, f"{path}[{index}]")
        return
    if value is None or isinstance(value, (bool, int, float)):
        return
    if not isinstance(value, str):
        raise ValueError(f"Unsupported type at {path}: {type(value).__name__}")
    if len(value) > 512:
        raise ValueError(f"String too long at {path}")
    for pattern, label in ((EMAIL, "email"), (VIN, "VIN"), (PHONE, "phone"), (SECRET, "secret")):
        if pattern.search(value):
            raise ValueError(f"Forbidden {label}-like value at {path}")


def semantic_sha(snapshot: dict[str, Any]) -> str:
    stable = dict(snapshot)
    stable.pop("generated_at", None)
    stable.pop("evidence", None)
    raw = json.dumps(stable, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def render_markdown(snapshot: dict[str, Any]) -> str:
    lines = [
        "# ASPA Current Light Snapshot",
        "",
        f"Generated: `{snapshot['generated_at']}`",
        f"Source host: `{snapshot['source_host']}`",
        f"Semantic SHA-256: `{snapshot['evidence']['semantic_sha256']}`",
        "",
        "## Repository",
        "",
        f"- Repository: `{snapshot['repo']['repository']}`",
        f"- Branch: `{snapshot['repo']['branch']}`",
        f"- Commit: `{snapshot['repo']['commit']}`",
        f"- Dirty: `{str(snapshot['repo']['dirty']).lower()}`",
    ]
    for title, key in (
        ("Runtime", "runtime"),
        ("Business aggregates", "business_aggregates"),
        ("Supplier aggregates", "suppliers"),
        ("Versions", "versions"),
    ):
        lines += ["", f"## {title}", ""]
        for item, value in snapshot[key].items():
            lines.append(f"- {item}: `{value}`")
    lines += [
        "",
        "## Work references",
        "",
        f"- Active issues: `{snapshot['work']['active_issue_numbers']}`",
        f"- Active PRs: `{snapshot['work']['active_pr_numbers']}`",
        f"- Last completed task: `{snapshot['work']['last_completed_task']}`",
        "",
        "> Sanitised operational snapshot; not a CRM or database backup.",
        "",
    ]
    return "\n".join(lines)


def write_if_changed(path: Path, data: bytes) -> bool:
    if path.exists() and path.read_bytes() == data:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_bytes(data)
    temp.replace(path)
    return True


def positive_numbers(values: list[str]) -> list[int]:
    numbers = sorted({int(value) for value in values})
    if any(number <= 0 for number in numbers):
        raise ValueError("Issue and PR numbers must be positive")
    return numbers


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--source-host", default="ROBOT-OMNI")
    parser.add_argument("--runtime-json", type=Path)
    parser.add_argument("--business-json", type=Path)
    parser.add_argument("--suppliers-json", type=Path)
    parser.add_argument("--versions-json", type=Path)
    parser.add_argument("--active-issue", action="append", default=[])
    parser.add_argument("--active-pr", action="append", default=[])
    parser.add_argument("--last-completed-task")
    args = parser.parse_args()

    snapshot: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "source_host": args.source_host,
        "repo": git_state(args.repo_root.resolve()),
        "runtime": allowlist("runtime", load_json(args.runtime_json)),
        "business_aggregates": allowlist("business_aggregates", load_json(args.business_json)),
        "suppliers": allowlist("suppliers", load_json(args.suppliers_json)),
        "versions": allowlist("versions", load_json(args.versions_json)),
        "work": {
            "active_issue_numbers": positive_numbers(args.active_issue),
            "active_pr_numbers": positive_numbers(args.active_pr),
            "last_completed_task": args.last_completed_task,
        },
    }
    validate(snapshot)
    snapshot["evidence"] = {
        "semantic_sha256": semantic_sha(snapshot),
        "source_commit": snapshot["repo"]["commit"],
    }

    json_bytes = (json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    if len(json_bytes) > MAX_BYTES:
        raise ValueError(f"Snapshot exceeds {MAX_BYTES} bytes")
    markdown_bytes = render_markdown(snapshot).encode()
    sums = (
        f"{hashlib.sha256(json_bytes).hexdigest()}  current.json\n"
        f"{hashlib.sha256(markdown_bytes).hexdigest()}  CURRENT.md\n"
    ).encode()

    changed = False
    changed |= write_if_changed(args.output_dir / "current.json", json_bytes)
    changed |= write_if_changed(args.output_dir / "CURRENT.md", markdown_bytes)
    changed |= write_if_changed(args.output_dir / "SHA256SUMS", sums)
    print(json.dumps({"changed": changed, "semantic_sha256": snapshot["evidence"]["semantic_sha256"]}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"snapshot_error: {exc}", file=sys.stderr)
        raise SystemExit(2)
