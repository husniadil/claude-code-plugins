# AGENTS.md

Instructions for AI coding agents working on this plugin.

## Plugin Overview

This is the **code-review** plugin - an iterative PR code review skill that:

1. Reviews PR diffs against the base branch
2. Identifies gaps across all categories (logic, security, performance, etc.)
3. Presents gaps as a numbered list for user selection
4. Fixes selected gaps using Task agents
5. Loops until user approves or no gaps remain

## Key Design Principles

- **Human-in-loop**: User approves every iteration
- **Lightweight**: No token-heavy one-shot dumps
- **Iterative**: Review → Fix → Re-review cycle
- **Tool-based interaction**: Uses `AskUserQuestion` for gap selection

## File Structure

```
plugins/code-review/
├── .claude-plugin/plugin.json    # Plugin metadata
├── AGENTS.md                     # This file
├── CLAUDE.md                     # Redirects to AGENTS.md
├── README.md                     # Human documentation
└── skills/code-review/
    ├── SKILL.md                  # Main skill instructions
    └── references/
        └── gap-categories.md     # Detailed gap category definitions
```

## Development Guidelines

- This is a pure instruction-based skill (no scripts)
- The skill orchestrates using Claude Code's built-in tools:
  - `Bash` for git commands (diff, branch info)
  - `AskUserQuestion` for user interaction
  - `Task` for spawning fix agents
  - `Read`, `Edit` for code modifications
- Keep instructions clear and actionable
- Maintain the iterative loop structure

## Testing

Test the skill by:

1. Creating a branch with intentional issues
2. Invoking the skill ("review my PR")
3. Verifying it detects gaps and presents them correctly
4. Testing the fix flow and re-review loop
