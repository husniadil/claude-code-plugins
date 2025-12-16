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

### mysql-db

Access MySQL databases via CLI for querying, schema exploration, and data management. Use when working with MySQL databases to run queries, explore table structures, or manage data.

**Features:**

- Credential management (manual input or config files)
- Safety confirmations for destructive operations
- Schema exploration commands
- Production database warnings

[Learn more](./plugins/mysql-db/README.md)

### postgres-db

Access PostgreSQL databases via CLI for querying, schema exploration, and data management. Use when working with PostgreSQL databases to run queries, explore table structures, or manage data.

**Features:**

- Credential management (manual input, config files, or .pgpass)
- SSL/TLS connection support
- Safety confirmations for destructive operations
- Schema exploration with meta-commands
- Production database warnings

[Learn more](./plugins/postgres-db/README.md)

### sqlite-db

Access SQLite databases via CLI for querying, schema exploration, and data management. Use when working with SQLite databases to run queries, explore table structures, or manage data.

**Features:**

- File-based database access (no credentials needed)
- Path from manual input or .env files
- Safety confirmations for destructive operations
- Backup/dump and CSV import support
- Protected database warnings (system/browser DBs)

[Learn more](./plugins/sqlite-db/README.md)

### ideate

Facilitation-first brainstorming skill that helps users unlock their own ideas through structured questioning and expansion techniques. Use when you need to brainstorm, generate ideas, or think through options.

**Features:**

- EECCA workflow: Extract, Expand, Challenge, Cluster, Action
- AI as facilitator, not generator philosophy
- Session persistence via markdown files
- Technique deep-dives (SCAMPER, Six Thinking Hats)
- Provocative questions library

[Learn more](./plugins/ideate/README.md)

## Installation

### From terminal (non-interactive)

```bash
claude plugin marketplace add husniadil/ekstend
claude plugin install ultrathink@ekstend
claude plugin install skill-creator@ekstend
claude plugin install mysql-db@ekstend
claude plugin install postgres-db@ekstend
claude plugin install sqlite-db@ekstend
claude plugin install ideate@ekstend
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
/plugin install mysql-db@ekstend
/plugin install postgres-db@ekstend
/plugin install sqlite-db@ekstend
/plugin install ideate@ekstend
```

Or browse available plugins interactively with `/plugin` and select "Browse Plugins".

## License

MIT

### Third-Party Licenses

- **skill-creator** plugin: Originally created by [Anthropic](https://github.com/anthropics/skills), licensed under Apache License 2.0. See [plugins/skill-creator/LICENSE.txt](./plugins/skill-creator/LICENSE.txt) for details.
