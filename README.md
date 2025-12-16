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

## Installation

### From terminal (non-interactive)

```bash
claude plugin marketplace add husniadil/ekstend
claude plugin install ultrathink@ekstend
```

### From Claude Code session (interactive)

1. Add the marketplace:

```
/plugin marketplace add husniadil/ekstend
```

2. Install a plugin:

```
/plugin install ultrathink@ekstend
```

Or browse available plugins interactively with `/plugin` and select "Browse Plugins".

## License

MIT
