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

### mysql-cli

Access MySQL databases via CLI for querying, schema exploration, and data management. Use when working with MySQL databases to run queries, explore table structures, or manage data.

**Features:**

- Credential management (manual input or config files)
- Safety confirmations for destructive operations
- Schema exploration commands
- Production database warnings

[Learn more](./plugins/mysql-cli/README.md)

## Installation

### From terminal (non-interactive)

```bash
claude plugin marketplace add husniadil/ekstend
claude plugin install ultrathink@ekstend
claude plugin install skill-creator@ekstend
claude plugin install mysql-cli@ekstend
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
/plugin install mysql-cli@ekstend
```

Or browse available plugins interactively with `/plugin` and select "Browse Plugins".

## License

MIT

### Third-Party Licenses

- **skill-creator** plugin: Originally created by [Anthropic](https://github.com/anthropics/skills), licensed under Apache License 2.0. See [plugins/skill-creator/LICENSE.txt](./plugins/skill-creator/LICENSE.txt) for details.
