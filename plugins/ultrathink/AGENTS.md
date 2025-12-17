# AGENTS.md

Instructions for AI coding agents working on the ultrathink plugin.

## Overview

UltraThink is a sequential thinking CLI tool for multi-step problem solving. It provides structured reasoning with confidence tracking, assumption management, branching, and revision support.

**Plugin structure:**

```
plugins/ultrathink/
  .claude-plugin/plugin.json    # Plugin metadata
  CLAUDE.md                     # Redirects to AGENTS.md
  AGENTS.md                     # This file
  README.md                     # Human documentation
  skills/ultrathink/
    SKILL.md                    # Claude Code skill instructions
    references/
      REFERENCE.md              # Complete CLI reference
    scripts/
      ultrathink.py             # Main implementation (~980 lines)
    tests/
      test_ultrathink.py        # Unit tests (134 tests, 97% coverage)
```

## Tech Stack

- **Language**: Python 3.12+
- **Dependencies**: typer, pydantic (inline script dependencies via PEP 723)
- **Runtime**: `uv run` (no virtual environment setup needed)
- **Output**: JSON to stdout, errors to stderr

## Architecture

The codebase follows a layered design:

1. **Models** (`scripts/ultrathink.py:36-378`)

   - `Assumption`: Tracks assumptions with confidence, verification status
   - `Thought`: Single thinking step with revision/branching support
   - `ThoughtRequest`: CLI input model
   - `ThoughtResponse`: JSON output model

2. **Session** (`scripts/ultrathink.py:381-503`)

   - `ThinkingSession`: In-memory session state
   - Manages thoughts, branches, assumptions
   - Validates references and dependencies

3. **Storage** (`scripts/ultrathink.py:506-610`)

   - File-based persistence in `<tempdir>/ultrathink/sessions/`
   - JSON serialization with path traversal protection
   - Auto-creates session directory

4. **Service** (`scripts/ultrathink.py:613-712`)

   - `UltraThinkService`: Orchestrates request processing
   - Session creation/loading/saving
   - Cross-session assumption resolution

5. **CLI** (`scripts/ultrathink.py:715-937`)
   - Typer-based interface
   - All options documented in docstring

## Development

### Running the CLI

```bash
# Show help
uv run plugins/ultrathink/skills/ultrathink/scripts/ultrathink.py --help

# Basic usage
uv run plugins/ultrathink/skills/ultrathink/scripts/ultrathink.py -t "Test thought" -n 3

# With session continuation
uv run plugins/ultrathink/skills/ultrathink/scripts/ultrathink.py -t "Next thought" -n 3 -s <session-id>
```

### Code Style

- Strict Pydantic models (`model_config = {"strict": True}`)
- Type hints throughout with `Annotated` for field metadata
- Validators use `@field_validator` decorators
- JSON parsing helpers for CLI string inputs

### Code Quality

Before committing, ensure code passes all checks:

```bash
# Run from repository root

# Python linting
ruff check plugins/ultrathink/
ruff format --check plugins/ultrathink/

# Type checking
mypy plugins/ultrathink/

# Or run all pre-commit hooks
uv run --with pre-commit pre-commit run --all-files
```

### Running Tests

Unit tests are located in `skills/ultrathink/tests/test_ultrathink.py`:

```bash
# Run from repository root

# Run all tests
uv run --with pytest --with pytest-cov --with typer --with pydantic \
  pytest plugins/ultrathink/skills/ultrathink/tests/test_ultrathink.py -v

# Run with coverage report
uv run --with pytest --with pytest-cov --with typer --with pydantic \
  pytest plugins/ultrathink/skills/ultrathink/tests/test_ultrathink.py \
  --cov=plugins/ultrathink/skills/ultrathink/scripts/ultrathink \
  --cov-report=term-missing

# Run specific test class
uv run --with pytest --with pytest-cov --with typer --with pydantic \
  pytest plugins/ultrathink/skills/ultrathink/tests/test_ultrathink.py::TestThinkingSession -v

# Run specific test
uv run --with pytest --with pytest-cov --with typer --with pydantic \
  pytest plugins/ultrathink/skills/ultrathink/tests/test_ultrathink.py::TestThinkingSession::test_add_thought -v
```

Or run from the skill directory:

```bash
cd plugins/ultrathink/skills/ultrathink/tests

# Run all tests
uv run --with pytest --with pytest-cov --with typer --with pydantic pytest test_ultrathink.py -v

# Run with coverage
uv run --with pytest --with pytest-cov --with typer --with pydantic \
  pytest test_ultrathink.py --cov=ultrathink --cov-report=term-missing
```

Test coverage target: **97%+**

### Testing Changes

1. Run basic invocation:

   ```bash
   uv run plugins/ultrathink/skills/ultrathink/scripts/ultrathink.py -t "Test" -n 1
   ```

2. Test session persistence:

   ```bash
   # Create session
   SESSION=$(uv run plugins/ultrathink/skills/ultrathink/scripts/ultrathink.py -t "Step 1" -n 3 | jq -r '.session_id')

   # Continue session
   uv run plugins/ultrathink/skills/ultrathink/scripts/ultrathink.py -t "Step 2" -n 3 -s "$SESSION"
   ```

3. Test assumptions:

   ```bash
   uv run plugins/ultrathink/skills/ultrathink/scripts/ultrathink.py -t "Test" -n 3 \
     --assumptions '[{"id":"A1","text":"Test assumption"}]'
   ```

4. Test error handling:

   ```bash
   # Should fail: empty thought
   uv run plugins/ultrathink/skills/ultrathink/scripts/ultrathink.py -t "" -n 3

   # Should fail: invalid session ID
   uv run plugins/ultrathink/skills/ultrathink/scripts/ultrathink.py -t "Test" -n 3 -s "../../../etc/passwd"
   ```

### Key Validation Rules

- `thought`: Non-empty string required
- `total_thoughts`: Positive integer required
- `confidence`: Float 0.0-1.0
- `session_id`: Alphanumeric + hyphens/underscores, max 128 chars
- `assumption.id`: Pattern `^(A\d+|[\w-]+:A\d+)$`
- References (revises, branches, depends_on) must exist in session

## Important Behaviors

### Risky Assumptions

An assumption is "risky" when:

- `critical == true` AND
- `confidence < 0.7` AND
- `verification_status != "verified_true"`

### Auto-Adjustments

- `thought_number` auto-increments if not provided
- `total_thoughts` auto-adjusts upward if `thought_number` exceeds it
- `next_thought_needed` defaults to `thought_number < total_thoughts`

### Cross-Session References

- Format: `session-id:A1`
- Read-only: can depend on, cannot invalidate
- Unresolved refs tracked in `unresolved_references`

## Common Tasks

### Adding a New CLI Option

1. Add to `main_callback()` parameters in `scripts/ultrathink.py:739`
2. Add to `ThoughtRequest` model if needed
3. Pass through to `Thought` model if it affects thought state
4. Update `ThoughtResponse` if it affects output

### Adding a New Assumption Field

1. Add to `Assumption` model (`scripts/ultrathink.py:36-104`)
2. Update `save_session()` serialization
3. Update `load_session()` deserialization
4. Add to response if needed

### Modifying Session Storage

- Storage functions: `scripts/ultrathink.py:506-610`
- Session file path: `<tempdir>/ultrathink/sessions/<session_id>.json`
- Always validate session_id before file operations

## Related Files

- `SKILL.md`: Instructions shown to Claude Code when skill is invoked
- `references/REFERENCE.md`: Full CLI documentation for users
- `README.md`: High-level plugin overview
