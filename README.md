# Ekstend

A collection of plugins for [Claude Code](https://claude.com/claude-code).

## Plugins

### ultrathink

Sequential thinking CLI for multi-step problem solving. Use when breaking down complex problems into steps, planning implementations, debugging multi-layered issues, or when explicit step-by-step reasoning with confidence tracking and assumption management is beneficial.

**Features:**

- Sequential thinking with session management
- Confidence scoring (0.0-1.0 scale)
- Assumption tracking with dependencies
- Branching and revision support

[Learn more](./plugins/ultrathink/README.md)

### skill-creator

Guide for creating effective skills that extend Claude's capabilities with specialized knowledge, workflows, or tool integrations. Use when you want to create a new skill or update an existing one.

**Features:**

- Step-by-step skill creation guidance
- Best practices for context management
- Scripts for initializing, validating, and packaging skills
- Reference documentation for workflow and output patterns

[Learn more](./plugins/skill-creator/README.md)

### database

Access MySQL, PostgreSQL, and SQLite databases via CLI for querying, schema exploration, and data management. Auto-detects database type from context (connection strings, file extensions, config patterns) or asks when unclear.

**Features:**

- Multi-database support (MySQL, PostgreSQL, SQLite)
- Auto-detection of database type from context
- Credential management (manual input, .env, docker-compose.yml, connection strings)
- Safety confirmations for destructive operations
- Schema exploration commands
- Production/system database warnings
- Credential protection (passwords never shown in output)

[Learn more](./plugins/database/README.md)

### ideate

Facilitation-first brainstorming skill that helps users unlock their own ideas through structured questioning and expansion techniques. Use when you need to brainstorm, generate ideas, or think through options.

**Features:**

- EECCA workflow: Extract, Expand, Challenge, Cluster, Action
- AI as facilitator, not generator philosophy
- Session persistence via markdown files
- Technique deep-dives (SCAMPER, Six Thinking Hats)
- Provocative questions library

[Learn more](./plugins/ideate/README.md)

### code-review

Iterative code-review toolkit bundling two composable skills: `code-review` (proactively find gaps in a PR diff or a whole codebase) and `address-pr-review` (react to existing GitHub PR comments — validate, fix, reply, and resolve threads).

**Features:**

- Two review modes: PR diff review (auto-detects base branch via `gh` / `origin/HEAD`) and holistic codebase audit (ecosystem-aware source-root detection)
- Business logic awareness (understands domain rules, not just code)
- End-to-end integration tracing (frontend → backend → database → external APIs)
- Dependency grounding against pinned versions (Node, Python, Go, Java, Kotlin, Rust, Ruby, PHP, Elixir)
- 10 gap categories: Business Logic, Integration, Dependency Compatibility, Logic, Security, Performance, Error Handling, Style, Tests, Docs
- Tracked fix loop via TaskCreate/TaskUpdate with explicit post-fix verification and Failure/Retry/Skip/Abort protocol
- Human-gated loop: AskUserQuestion panel before every batch — fix menu, Next-Pass Gate, failure handling
- `address-pr-review`: fetch unresolved threads via GraphQL, reply via REST (`databaseId`), resolve via batched mutation; never force-pushes
- Subagent-aware: `subagent|no-subagent|auto` argument for both skills

[Learn more](./plugins/code-review/README.md)

### interview

Deep requirements gathering skill that interviews users through thoughtful, in-depth questions before implementation. Uses CDEEPER workflow to uncover hidden requirements, edge cases, and trade-offs.

**Features:**

- CDEEPER workflow: Contextualize, Discover, Explore, Edge, Prioritize, Experience, Ready
- Codebase exploration before questioning (avoids obvious questions)
- Skip-to-summary flow with configurable styles (Minimal/Inferred/Critical first)
- Question tracking and deduplication
- Confidence scoring (percentage-based on each requirement)
- Hybrid question ordering (domain-based + adaptive)
- Multi-session persistence with phase tracking

[Learn more](./plugins/interview/README.md)

## Installation

### From terminal (non-interactive)

```bash
claude plugin marketplace add husniadil/ekstend
claude plugin install ultrathink@ekstend
claude plugin install skill-creator@ekstend
claude plugin install database@ekstend
claude plugin install ideate@ekstend
claude plugin install code-review@ekstend
claude plugin install interview@ekstend
```

### From Claude Code session (interactive)

1. Add the marketplace:

```
/plugin marketplace add husniadil/ekstend
```

2. Install a plugin:

```
/plugin install ultrathink@ekstend
/plugin install skill-creator@ekstend
/plugin install database@ekstend
/plugin install ideate@ekstend
/plugin install code-review@ekstend
/plugin install interview@ekstend
```

Or browse available plugins interactively with `/plugin` and select "Browse Plugins".

## License

MIT

### Third-Party Licenses

- **skill-creator** plugin: Originally created by [Anthropic](https://github.com/anthropics/skills), licensed under Apache License 2.0. See [plugins/skill-creator/LICENSE.txt](./plugins/skill-creator/LICENSE.txt) for details.
