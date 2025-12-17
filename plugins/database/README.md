# database

A Claude Code plugin for accessing MySQL, PostgreSQL, and SQLite databases via CLI.

## Features

- **Multi-database support**: MySQL, PostgreSQL, SQLite
- Query execution (SELECT, INSERT, UPDATE, DELETE)
- Schema exploration (list tables, describe structure)
- Credential management from user input or config files
- Safety confirmations for destructive operations
- Production/system database warnings
- Credential protection (passwords never shown in output)

## Installation

```bash
claude plugin install database@ekstend
```

## Prerequisites

Install the CLI client(s) for your database(s):

**MySQL:**

```bash
brew install mysql-client  # macOS
apt install mysql-client   # Ubuntu/Debian
mysql --version
```

**PostgreSQL:**

```bash
brew install postgresql    # macOS
apt install postgresql-client  # Ubuntu/Debian
psql --version
```

**SQLite:**

```bash
# Usually pre-installed on macOS/Linux
sqlite3 --version
```

## Usage

Simply ask Claude to work with your database:

- "Connect to my MySQL database"
- "Query the PostgreSQL users table"
- "Open my SQLite database at ./app.db"
- "Show all tables"
- "Find records where status is active"

Claude will detect the database type from context or ask you to specify.

## Safety

- Destructive operations require confirmation
- Credentials are never echoed or logged
- Production/system databases trigger warnings
