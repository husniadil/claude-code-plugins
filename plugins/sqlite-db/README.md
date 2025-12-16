# sqlite-db

A Claude Code plugin for accessing SQLite databases via CLI.

## Features

- Query execution (SELECT, INSERT, UPDATE, DELETE)
- Schema exploration (list tables, indexes, views, describe tables)
- File-based database access (no credentials needed)
- Safety confirmations for destructive operations

## Installation

```bash
claude plugin install sqlite-db@ekstend
```

## Prerequisites

SQLite CLI client must be installed on your system:

```bash
# macOS (pre-installed)
sqlite3 --version

# Ubuntu/Debian
apt install sqlite3

# Check installation
sqlite3 --version
```

## Usage

Simply ask Claude to work with your SQLite database:

- "Open my SQLite database at ./data.db"
- "Show all tables in the database"
- "Find users with email containing gmail"
- "Update the status of order #123"

Claude will ask for the database file path before connecting.

## Safety

- Destructive operations (DROP, DELETE, UPDATE, TRUNCATE) require confirmation
- No credentials to protect (file-based database)
