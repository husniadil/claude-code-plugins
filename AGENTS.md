# AGENTS.md

Instructions for AI coding agents working on this project.

## Project Overview

This is a Claude Code plugins repository containing reusable plugins that extend Claude Code's capabilities. Plugins are installed via the Claude Code plugin marketplace system.

**Repository structure:**

```
.claude-plugin/marketplace.json   # Marketplace metadata (lists all plugins)
plugins/
  <plugin-name>/
    .claude-plugin/plugin.json    # Plugin metadata
    README.md                     # Plugin documentation
    skills/                       # Skill definitions
      <skill-name>/
        SKILL.md                  # Skill instructions (frontmatter + markdown)
        REFERENCE.md              # Detailed reference docs
        *.py                      # Skill implementation
```

## Current Plugins

- **ultrathink**: Sequential thinking CLI for multi-step problem solving with confidence tracking and assumption management. Python-based, runs via `uv run`.
- **skill-creator**: Guide for creating effective skills that extend Claude's capabilities with specialized knowledge, workflows, or tool integrations. Includes utility scripts for initializing, validating, and packaging skills. Licensed under Apache 2.0.

## Development Guidelines

### Adding a New Plugin

1. Create `plugins/<plugin-name>/` directory
2. Add `.claude-plugin/plugin.json` with metadata:
   ```json
   {
     "name": "<plugin-name>",
     "description": "...",
     "version": "1.0.0",
     "author": { "name": "...", "email": "..." }
   }
   ```
3. Add `README.md` for human documentation
4. Create `skills/<skill-name>/SKILL.md` for Claude Code skill instructions
5. Register in `.claude-plugin/marketplace.json` plugins array

### SKILL.md Format

Skills use YAML frontmatter followed by markdown instructions:

```markdown
---
name: skill-name
description: When to use this skill (shown to Claude)
---

# Skill Title

## When to Use

...

## Instructions

...
```

### Code Style

- Python: Use `uv` for dependency management and execution
- Follow PEP 8 conventions
- Include type hints where practical
- Keep skills self-contained (minimal external dependencies)

### Code Quality Tools

This repository uses pre-commit hooks and CI to enforce code quality. The same
tools can be run manually:

**Python Linting (ruff):**

```bash
# Check for issues
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .

# Check formatting only
ruff format --check .
```

**Python Type Checking (mypy):**

```bash
mypy .
```

**Prettier (JSON, YAML, Markdown):**

```bash
# Check formatting
npx prettier --check "**/*.{json,yaml,yml,md}"

# Auto-fix formatting
npx prettier --write "**/*.{json,yaml,yml,md}"
```

**Pre-commit Hooks:**

```bash
# Install hooks (run once)
uv run --with pre-commit pre-commit install

# Run all hooks manually
uv run --with pre-commit pre-commit run --all-files

# Run specific hook
uv run --with pre-commit pre-commit run ruff --all-files
uv run --with pre-commit pre-commit run mypy --all-files
uv run --with pre-commit pre-commit run prettier --all-files
```

### Testing

Run Python skills directly:

```bash
uv run plugins/<plugin>/skills/<skill>/<script>.py --help
```

For ultrathink specifically:

```bash
uv run plugins/ultrathink/skills/ultrathink/scripts/ultrathink.py -t "Test thought" -n 3
```

## Version Management

- Each plugin has its own version in `plugin.json`
- Marketplace version in `marketplace.json` tracks the collection version
- Use semantic versioning (MAJOR.MINOR.PATCH)

## License

MIT - see LICENSE file
