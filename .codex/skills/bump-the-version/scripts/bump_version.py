#!/usr/bin/env python3
"""Bump this repository's plugin version, changelog, commit, and tag."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path


MANIFEST = Path("plugin/.claude-plugin/plugin.json")
CHANGELOG = Path("CHANGELOG.md")
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bump plugin/.claude-plugin/plugin.json, update CHANGELOG.md, commit, and tag."
    )
    parser.add_argument("version", help="New semantic version, for example 2.10.2")
    parser.add_argument(
        "--note",
        action="append",
        default=[],
        help="Release note bullet text. Repeat for multiple bullets.",
    )
    args = parser.parse_args()

    version = args.version.strip()
    if not SEMVER.fullmatch(version):
        raise SystemExit(f"invalid semantic version: {version}")

    require_repo_root()
    require_clean_worktree()
    require_tag_absent(version)

    previous = update_manifest(version)
    update_changelog(version, args.note or [f"Bumped plugin version from {previous} to {version}."])

    run(["git", "add", str(MANIFEST), str(CHANGELOG)])
    run(["git", "commit", "-m", f"Bump version to {version}"])
    version_commit = git(["rev-parse", "HEAD"]).strip()

    run(["git", "tag", f"v{version}", version_commit])

    replace_pending_commit(version, version_commit[:7])
    run(["git", "add", str(CHANGELOG)])
    run(["git", "commit", "-m", "Update changelog version reference"])

    print(f"Bumped version {previous} -> {version}")
    print(f"Tagged v{version} at {version_commit[:7]}")
    return 0


def require_repo_root() -> None:
    root = git(["rev-parse", "--show-toplevel"]).strip()
    if Path(root).resolve() != Path.cwd().resolve():
        raise SystemExit(f"run this script from the repository root: {root}")
    if not MANIFEST.is_file():
        raise SystemExit(f"missing manifest: {MANIFEST}")
    if not CHANGELOG.is_file():
        raise SystemExit(f"missing changelog: {CHANGELOG}")


def require_clean_worktree() -> None:
    status = git(["status", "--porcelain"])
    if status.strip():
        raise SystemExit("worktree must be clean before bumping the version")


def require_tag_absent(version: str) -> None:
    tag = f"v{version}"
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"refs/tags/{tag}"],
        text=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode == 0:
        raise SystemExit(f"tag already exists: {tag}")


def update_manifest(version: str) -> str:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    previous = str(data.get("version") or "")
    if previous == version:
        raise SystemExit(f"manifest is already at version {version}")
    data["version"] = version
    MANIFEST.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return previous


def update_changelog(version: str, notes: list[str]) -> None:
    text = CHANGELOG.read_text(encoding="utf-8")
    heading = f"## {version} - {date.today().isoformat()}"
    if heading in text:
        raise SystemExit(f"changelog already contains {heading}")

    lines = text.splitlines()
    insert_at = next(
        (index for index, line in enumerate(lines) if line.startswith("## ")),
        len(lines),
    )
    section = [
        heading,
        "",
        f"Commit: pending - `Bump version to {version}`",
        "",
        *[f"- {note.strip()}" for note in notes if note.strip()],
        "",
    ]
    updated = lines[:insert_at] + section + lines[insert_at:]
    CHANGELOG.write_text("\n".join(updated).rstrip() + "\n", encoding="utf-8")


def replace_pending_commit(version: str, short_hash: str) -> None:
    text = CHANGELOG.read_text(encoding="utf-8")
    pending = f"Commit: pending - `Bump version to {version}`"
    resolved = f"Commit: `{short_hash}` - `Bump version to {version}`"
    if pending not in text:
        raise SystemExit("pending changelog commit marker not found")
    CHANGELOG.write_text(text.replace(pending, resolved, 1), encoding="utf-8")


def git(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], text=True)


def run(args: list[str]) -> None:
    subprocess.run(args, check=True)


if __name__ == "__main__":
    sys.exit(main())
