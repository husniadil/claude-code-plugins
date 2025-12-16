# AGENTS.md

Instructions for AI coding agents working on the sqlite-db plugin.

## Overview

SQLite DB is a skill that enables Claude Code to access and manage SQLite databases using the `sqlite3` command-line client. It provides safe database operations with destructive operation protection.

**Plugin structure:**

```
plugins/sqlite-db/
  .claude-plugin/plugin.json    # Plugin metadata
  CLAUDE.md                     # Redirects to AGENTS.md
  AGENTS.md                     # This file
  README.md                     # Human documentation
  skills/sqlite-db/
    SKILL.md                    # Claude Code skill instructions
```

## Tech Stack

- **Dependencies**: `sqlite3` CLI client (system)
- **No scripts**: Pure instruction-based skill

## Key Features

1. **Database Access**

   - File-based database (no credentials needed)
   - User provides database file path
   - Support for in-memory databases (`:memory:`)

2. **Safety Mechanisms**

   - Confirmation required for destructive operations (DROP, DELETE, UPDATE, TRUNCATE, ALTER)
   - Preview affected rows before write operations

3. **Schema Exploration**
   - List tables, indexes, triggers, views
   - Describe table structure
   - Show CREATE statements

## Development

### Testing the Skill

1. Install the plugin in Claude Code
2. Ask Claude to work with a SQLite database
3. Verify it asks for the database file path
4. Test various operations and safety confirmations

### Modifying the Skill

Edit `skills/sqlite-db/SKILL.md` directly. Key sections:

- Database Path Acquisition: How database path is obtained
- Safety Rules: Confirmation requirements
- Query Execution: How queries are run

## Related Files

- `SKILL.md`: Instructions shown to Claude Code when skill is invoked
- `README.md`: High-level plugin overview
