# Release Workflow

Execute the full release workflow for ekstend plugins.

## Steps

### 1. Version Check and Bump

Check if versions need to be bumped across all version files:

- `pyproject.toml` - root project version
- `.claude-plugin/marketplace.json` - marketplace version
- `plugins/*/. claude-plugin/plugin.json` - individual plugin versions (only if plugin was modified)

Ask the user:

```
What type of version bump is needed?
1. Patch (bug fixes) - e.g., 1.7.0 -> 1.7.1
2. Minor (new features) - e.g., 1.7.0 -> 1.8.0
3. Major (breaking changes) - e.g., 1.7.0 -> 2.0.0
4. No bump needed (versions already updated)
```

If bump is needed, update all relevant version files consistently.

### 2. Documentation Check

Review and update documentation if needed:

- `README.md` - root readme (plugin list, installation commands)
- `AGENTS.md` - current plugins list
- `plugins/*/README.md` - individual plugin readmes

Verify:

- All plugins listed in marketplace.json are documented
- Installation commands match available plugins
- No stale references to removed plugins

### 3. Pre-commit Hooks

Run all pre-commit hooks manually:

```bash
uv run --with pre-commit pre-commit run --all-files
```

This runs:

- ruff (lint and format)
- mypy (type checking, may update uv.lock)
- prettier (JSON, YAML, Markdown formatting)

If any files are modified, stage them for commit.

### 4. Commit Changes

Stage all changes and create a commit:

```bash
git add -A
git status
```

Ask user to confirm the changes look correct, then commit with a release message:

```
Release vX.Y.Z

- [Summary of changes]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

### 5. Tag the Commit

Create an annotated tag:

```bash
git tag -a vX.Y.Z -m "vX.Y.Z - [Brief description]"
```

### 6. Push to Remotes

Push both the commit and the tag:

```bash
git push origin main
git push origin vX.Y.Z
```

### 7. Create GitHub Release

Create a new release using GitHub CLI:

```bash
gh release create vX.Y.Z --title "vX.Y.Z" --notes "[Release notes]"
```

The release notes should include:

- Summary of changes
- List of new/modified plugins
- Breaking changes (if any)
- Migration notes (if any)

## Usage

Run this command when you're ready to release a new version of ekstend.
