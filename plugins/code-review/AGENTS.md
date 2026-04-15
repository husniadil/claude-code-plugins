# AGENTS.md

Instructions for AI coding agents working on this plugin.

## Plugin Overview

This is the **code-review** plugin — an iterative code-review toolkit that bundles two composable skills:

1. **`code-review`** — proactively find gaps in a PR diff or across a codebase, then fix them in a tracked loop
2. **`address-pr-review`** — react to existing GitHub PR comments (bot or human), validate each, fix where valid, reply with reasoning, and resolve threads

Both skills share reference material via `skills/code-review/references/` so they stay consistent (dependency grounding, integration tracing, failure resumption, gap categories).

## Key Design Principles

- **Human-in-loop**: every destructive action (fix, reply, resolve, push) is gated behind `AskUserQuestion`
- **Tracked fix loop**: batch edits go through `TaskCreate`/`TaskUpdate` with explicit post-fix verification; `completed` means verified, `deleted` means explicit skip, `in_progress` on a halted task means a blocker
- **Iterative**: Review → Fix → Next-Pass Gate → Re-review, until the user stops
- **Grounded**: library / API claims are verified against the exact pinned version in the project's manifests, not against latest-release knowledge
- **Subagent-aware**: both skills accept a `subagent|no-subagent|auto` argument; default is `auto`

## File Structure

```
plugins/code-review/
├── .claude-plugin/plugin.json    # Plugin metadata
├── AGENTS.md                     # This file
├── CLAUDE.md                     # Redirects to AGENTS.md
├── README.md                     # Human documentation
└── skills/
    ├── code-review/              # Skill 1 — find gaps
    │   ├── SKILL.md
    │   └── references/
    │       ├── gap-categories.md         # 10 gap category definitions
    │       ├── integration-tracing.md    # End-to-end integration tracing
    │       ├── dependency-grounding.md   # Version-pinned library grounding
    │       └── failure-resumption.md     # Failure protocol for tracked fix loop
    └── address-pr-review/        # Skill 2 — respond to PR comments
        └── SKILL.md              # Reuses references from ../code-review/references/
```

## Development Guidelines

- Both skills are pure instruction-based (no scripts)
- Orchestrates via Claude Code built-ins:
  - `Bash` — git + `gh` CLI (diff, PR metadata, GraphQL, REST replies)
  - `AskUserQuestion` — user decisions (fix all / done / apply actions / next pass)
  - `Task` — parallel scans (Explore) and complex multi-file fixes (general-purpose)
  - `Read`, `Edit` — code modifications
  - `TaskCreate`, `TaskUpdate` — tracked fix loop bookkeeping
- `address-pr-review` extends `code-review` — do not duplicate references. Link them via relative paths (`../code-review/references/...`)
- Soft target: keep each `SKILL.md` body under 500 lines (per official skill-creator guidance) and split detailed material to `references/`. The current `code-review/SKILL.md` is over this limit because it bundles a multi-step orchestration; treat 700 lines as a hard ceiling and refactor before exceeding it.
- When adding a new gap category, update BOTH `skills/code-review/SKILL.md` Step 2f AND `references/gap-categories.md`

## Testing

### `code-review`

1. Create a branch with intentional issues across several categories (security, dep-compat, integration, style)
2. Invoke: "review my PR"
3. Verify gap list, Apply all fixes, Next-Pass Gate, iteration loop

### `address-pr-review`

1. Push a branch with code that will draw comments from a bot (or leave review comments manually)
2. Invoke: `/address-pr-review <PR_NUMBER>`
3. Verify: summary table classifies each thread, fix loop runs only for valid/partial, replies cite real commits, threads resolved, no force push
