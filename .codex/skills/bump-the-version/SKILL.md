---
name: bump-the-version
description: Repo-local release workflow for this Ailtir plugin repository. Use when the user asks to bump the plugin version, update plugin/.claude-plugin/plugin.json, update CHANGELOG.md, create the version bump commit, and tag that version commit.
---

# Bump The Version

## Workflow

Use `scripts/bump_version.py` from this skill. Run it from the repository root.

```bash
python3 .codex/skills/bump-the-version/scripts/bump_version.py 2.10.2 \
  --note "Fixed telemetry reporting when Claude invokes plugin helper scripts by absolute path."
```

The script performs the repo-specific release sequence:

1. Require a clean worktree before changing files.
2. Update `plugin/.claude-plugin/plugin.json`.
3. Insert a newest-first section in `CHANGELOG.md`.
4. Commit the manifest and changelog with `Bump version to X.Y.Z`.
5. Tag that version-bump commit as `vX.Y.Z`.
6. Replace the changelog `pending` marker with the version commit hash.
7. Commit the changelog reference as `Update changelog version reference`.

The tag must point to the version bump commit, not the changelog-reference
follow-up commit.

## Release Notes

Pass one or more `--note` values when the release has specific user-visible
changes:

```bash
python3 .codex/skills/bump-the-version/scripts/bump_version.py 2.10.2 \
  --note "Fixed telemetry reporting for installed plugin helpers." \
  --note "Kept plugin runtime variables out of user-facing configuration."
```

If the user only asks for a version bump and gives no release-note text, let the
script use its default note. Do not invent detailed release notes without
inspecting the commits since the previous version.

## Pushing

The script creates local commits and a local tag by default. If the user asks to
push too, run:

```bash
git push
git push origin vX.Y.Z
```

Do not use `git push --tags` unless the user explicitly asks to push every local
tag.
