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
    CLAUDE.md                     # Redirects to AGENTS.md
    AGENTS.md                     # Plugin-specific instructions for AI agents
    README.md                     # Plugin documentation
    skills/                       # Skill definitions
      <skill-name>/
        SKILL.md                  # Skill instructions (frontmatter + markdown)
        references/               # Detailed reference docs
        scripts/                  # Python scripts
        tests/                    # Unit tests (optional)
```

## Current Plugins

- **ultrathink**: Sequential thinking CLI for multi-step problem solving with confidence tracking and assumption management. Python-based, runs via `uv run`.
- **skill-creator**: Guide for creating effective skills that extend Claude's capabilities with specialized knowledge, workflows, or tool integrations. Includes utility scripts for initializing, validating, and packaging skills. Licensed under Apache 2.0.
- **database**: Unified access to MySQL, PostgreSQL, SQLite databases, and Redis key-value stores via CLI for querying, schema/key exploration, and data management. Auto-detects database type from context. Pure instruction-based skill (no scripts).
- **ideate**: Facilitation-first brainstorming skill that helps users unlock their own ideas through structured questioning (EECCA workflow) and expansion techniques. Pure instruction-based skill (no scripts).
- **code-review**: Iterative code-review toolkit bundling two skills. `code-review` itself finds gaps proactively (PR diff or holistic codebase), with business-logic awareness, end-to-end integration tracing (frontend → backend → database → external APIs), dependency grounding against pinned versions, and a tracked fix loop (TaskCreate/TaskUpdate). `address-pr-review` reacts to existing GitHub PR comments — validate (Valid / Partial / Invalid / Defer / Repeat), fix, reply, and resolve threads via `gh` GraphQL/REST. 10 gap categories. Pure instruction-based skills (no scripts).
- **interview**: Deep requirements gathering skill that interviews users through thoughtful, in-depth questions before implementation. Uses CDEEPER workflow (Contextualize, Discover, Explore, Edge, Prioritize, Experience, Ready) to uncover hidden requirements, edge cases, and trade-offs. Pure instruction-based skill (no scripts).

## Development Guidelines

### Adding a New Plugin

1. Create `plugins/<plugin-name>/` directory
2. Add `.claude-plugin/plugin.json` with metadata:
   ```json
   {
     "name": "<plugin-name>",
     "description": "...",
     "version": "1.0.0",
     "author": { "name": "...", "email": "..." },
     "license": "MIT"
   }
   ```
3. Add `CLAUDE.md` (redirects to AGENTS.md)
4. Add `AGENTS.md` for plugin-specific AI agent instructions
5. Add `README.md` for human documentation
6. Create `skills/<skill-name>/SKILL.md` for Claude Code skill instructions
7. Register in `.claude-plugin/marketplace.json` plugins array

### SKILL.md Format

Skills use YAML frontmatter followed by markdown instructions. `description` and `when_to_use` are the primary triggering fields Claude reads — keep them in frontmatter, **not** in the body. Triggering info in body (e.g., a `## When to Use` section) is invisible to Claude for routing decisions.

```markdown
---
name: skill-name
description: What this skill does (front-load the key use case)
when_to_use: Use when ... (natural language, generic — not POV-specific)
---

# Skill Title

## Instructions

...
```

Other optional frontmatter fields (consult `plugins/skill-creator/skills/skill-creator/SKILL.md` for the full list and validator rules): `argument-hint`, `disable-model-invocation`, `user-invocable`, `allowed-tools`, `model`, `effort`, `context`, `agent`, `paths`, `hooks`, `shell`. Combined `description` + `when_to_use` is capped at 1,536 characters in the listing.

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

**For CLI-based skills** (like ultrathink), run scripts directly:

```bash
uv run plugins/<plugin>/skills/<skill>/scripts/<script>.py --help
```

For ultrathink specifically:

```bash
uv run plugins/ultrathink/skills/ultrathink/scripts/ultrathink.py -t "Test thought" -n 3
```

**For documentation-based skills** (like skill-creator), test by invoking the skill in Claude Code and verifying the guidance is correct.

**For GitHub-integrated skills** (like `address-pr-review`), test against a real PR:

1. Push a branch with code that draws bot comments (or leave review comments manually)
2. Invoke `/address-pr-review <PR_NUMBER>`
3. Verify: the AskUserQuestion panel renders, the summary table classifies each thread, the fix loop runs only for valid/partial, replies cite real commit SHAs, threads are resolved, no force push happens

**Frontmatter validation** for any skill — run the validator before shipping:

```bash
uv run --with pyyaml python plugins/skill-creator/skills/skill-creator/scripts/quick_validate.py plugins/<plugin>/skills/<skill>/
```

CI runs this automatically (see `.github/workflows/ci.yml`).

## Version Management

- Each plugin has its own version in `plugin.json`
- Marketplace version in `marketplace.json` tracks the collection version
- Use semantic versioning (MAJOR.MINOR.PATCH)

## License

MIT - see LICENSE file
