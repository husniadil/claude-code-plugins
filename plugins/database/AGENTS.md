# AGENTS.md

Instructions for AI coding agents working on the database plugin.

## Overview

Database is a unified skill that enables Claude Code to access and manage MySQL, PostgreSQL, and SQLite databases using their respective command-line clients. It provides safe database operations with credential management and destructive operation protection.

**Plugin structure:**

```
plugins/database/
  .claude-plugin/plugin.json    # Plugin metadata
  CLAUDE.md                     # Redirects to AGENTS.md
  AGENTS.md                     # This file
  README.md                     # Human documentation
  skills/database/
    SKILL.md                    # Claude Code skill instructions
    references/
      mysql.md                  # MySQL-specific CLI instructions
      postgres.md               # PostgreSQL-specific CLI instructions
      sqlite.md                 # SQLite-specific CLI instructions
```

## Tech Stack

- **Dependencies**: `mysql`, `psql`, `sqlite3` CLI clients (system)
- **No scripts**: Pure instruction-based skill

## Key Features

1. **Database Type Detection**

   - Auto-detect from context clues (file extensions, connection strings, config patterns)
   - Explicit user selection when unclear

2. **Credential Management**

   - Manual input via AskUserQuestion
   - Read from .env, docker-compose.yml, or connection strings
   - NEVER use shell environment variables without explicit permission

3. **Safety Mechanisms**

   - Confirmation required for destructive operations
   - Preview affected rows before write operations
   - Production/system database warnings

4. **Password Security**
   - Never echo credentials to terminal
   - Never include credentials in error messages

## Development

### Testing the Skill

1. Install the plugin in Claude Code
2. Test each database type connection
3. Verify credential prompts and safety confirmations

### Modifying the Skill

- Main workflow in `skills/database/SKILL.md`
- Database-specific details in `skills/database/references/`
