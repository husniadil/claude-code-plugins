# AGENTS.md

Instructions for AI coding agents working on the mysql-cli plugin.

## Overview

MySQL CLI is a skill that enables Claude Code to access and manage MySQL databases using the `mysql` command-line client. It provides safe database operations with credential management and destructive operation protection.

**Plugin structure:**

```
plugins/mysql-cli/
  .claude-plugin/plugin.json    # Plugin metadata
  CLAUDE.md                     # Redirects to AGENTS.md
  AGENTS.md                     # This file
  README.md                     # Human documentation
  skills/mysql-cli/
    SKILL.md                    # Claude Code skill instructions
```

## Tech Stack

- **Dependencies**: `mysql` CLI client (system)
- **No scripts**: Pure instruction-based skill

## Key Features

1. **Credential Management**

   - Manual input via AskUserQuestion
   - Read from .env, docker-compose.yml, or connection string
   - NEVER use shell environment variables without explicit permission

2. **Safety Mechanisms**

   - Confirmation required for destructive operations (DROP, DELETE, UPDATE, TRUNCATE, ALTER)
   - Preview affected rows before write operations
   - Production database warnings

3. **Password Security**
   - Never echo password to terminal
   - Never include password in error messages

## Development

### Testing the Skill

1. Install the plugin in Claude Code
2. Ask Claude to connect to a MySQL database
3. Verify it asks for credentials (doesn't use env vars automatically)
4. Test various operations and safety confirmations

### Modifying the Skill

Edit `skills/mysql-cli/SKILL.md` directly. Key sections:

- Credential Acquisition: How credentials are obtained
- Safety Rules: Confirmation requirements
- Query Execution: How queries are run

## Related Files

- `SKILL.md`: Instructions shown to Claude Code when skill is invoked
- `README.md`: High-level plugin overview
