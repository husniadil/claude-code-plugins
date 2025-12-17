---
name: database
description: Use this skill when the user asks to connect to, query, access, or work with a database (MySQL, PostgreSQL/Postgres, or SQLite). Also use when the user mentions database tables, schemas, or wants to run SQL queries. Supports credentials from user input or config files (.env, docker-compose.yml). For MySQL and PostgreSQL - always ask user for credentials or credential file location first; never use shell environment variables without explicit user permission. For SQLite - always ask user for the database file path first.
---

# Database CLI

Access and manage MySQL, PostgreSQL, and SQLite databases using their respective command-line clients.

## Database Type Detection

Determine the database type from context:

| Signal                                         | Database Type |
| ---------------------------------------------- | ------------- |
| User says "MySQL", "mysql"                     | MySQL         |
| User says "PostgreSQL", "Postgres", "psql"     | PostgreSQL    |
| User says "SQLite", "sqlite3"                  | SQLite        |
| File path ends in `.db`, `.sqlite`, `.sqlite3` | SQLite        |
| Connection string starts with `mysql://`       | MySQL         |
| Connection string starts with `postgresql://`  | PostgreSQL    |
| Connection string starts with `postgres://`    | PostgreSQL    |
| Connection string starts with `sqlite:///`     | SQLite        |
| Config has `MYSQL_*` variables                 | MySQL         |
| Config has `PG*` or `POSTGRES_*` variables     | PostgreSQL    |
| Config has `SQLITE_*` or `DATABASE_PATH`       | SQLite        |
| Port 3306 mentioned                            | MySQL         |
| Port 5432 mentioned                            | PostgreSQL    |

If database type cannot be determined, ask using AskUserQuestion:

```
Which database are you working with?
1. MySQL
2. PostgreSQL
3. SQLite
```

## Prerequisites

Verify the appropriate CLI is installed:

| Database   | Command             |
| ---------- | ------------------- |
| MySQL      | `mysql --version`   |
| PostgreSQL | `psql --version`    |
| SQLite     | `sqlite3 --version` |

If CLI is not installed, offer to help install it:

1. Detect the OS using `uname -s` (Darwin=macOS, Linux=Linux)
2. Ask the user using AskUserQuestion:

```
The [DATABASE] CLI is not installed. Would you like me to install it?

I detected you're on [OS]. I would run:
- [INSTALL_COMMAND]

1. Yes, install it for me
2. No, I'll install it myself
```

Installation commands by OS:

| Database   | macOS (Homebrew)            | Ubuntu/Debian                        | Arch Linux                  |
| ---------- | --------------------------- | ------------------------------------ | --------------------------- |
| MySQL      | `brew install mysql-client` | `sudo apt install mysql-client`      | `sudo pacman -S mysql`      |
| PostgreSQL | `brew install libpq`        | `sudo apt install postgresql-client` | `sudo pacman -S postgresql` |
| SQLite     | `brew install sqlite`       | `sudo apt install sqlite3`           | `sudo pacman -S sqlite`     |

For macOS with Homebrew, after installing mysql-client or libpq, the user may need to add to PATH:

- MySQL: `echo 'export PATH="/opt/homebrew/opt/mysql-client/bin:$PATH"' >> ~/.zshrc`
- PostgreSQL: `echo 'export PATH="/opt/homebrew/opt/libpq/bin:$PATH"' >> ~/.zshrc`

## Credential/Path Acquisition

**CRITICAL: Never use environment variables from the shell without explicit user permission.**

Ask the user using AskUserQuestion:

**For MySQL/PostgreSQL:**

```
How would you like to provide database credentials?
1. Enter credentials manually (host, user, password, database)
2. Read from a file (provide path to .env, docker-compose.yml, or config file)
```

**For SQLite:**

```
How would you like to provide the SQLite database path?
1. Enter the file path manually (e.g., ./data.db, /path/to/database.sqlite)
2. Read from a file (provide path to .env or config file)
3. Use in-memory database (:memory:)
```

After reading any config file, confirm with user before connecting.

For detailed credential formats and CLI syntax, see the database-specific references:

- **MySQL**: See [references/mysql.md](references/mysql.md)
- **PostgreSQL**: See [references/postgres.md](references/postgres.md)
- **SQLite**: See [references/sqlite.md](references/sqlite.md)

## Connection Test

Before any operation, test the connection using the appropriate command from the reference docs.

## Query Execution

### Read Operations (SELECT)

Add `LIMIT 100` to large result sets by default unless user specifies otherwise.

### Write Operations (INSERT, UPDATE, DELETE)

**ALWAYS require user confirmation before executing.**

For UPDATE/DELETE, first show affected rows count, then ask: "This will affect X rows. Proceed? (yes/no)"

## Schema Exploration

Common operations (see reference docs for exact syntax):

| Operation      | Description              |
| -------------- | ------------------------ |
| List databases | Show available databases |
| List tables    | Show tables in database  |
| Describe table | Show column structure    |
| Show create    | Show CREATE statement    |
| List indexes   | Show indexes on table    |

## Safety Rules

### Destructive Operations - REQUIRE CONFIRMATION

These operations MUST show a warning and require explicit user confirmation:

| Operation              | Risk Level | Action Before Execute                     |
| ---------------------- | ---------- | ----------------------------------------- |
| `DROP TABLE/DATABASE`  | CRITICAL   | Show what will be dropped, require "yes"  |
| `TRUNCATE TABLE`       | CRITICAL   | Show row count, require "yes"             |
| `DELETE` without WHERE | CRITICAL   | Refuse or require explicit confirmation   |
| `UPDATE` without WHERE | CRITICAL   | Refuse or require explicit confirmation   |
| `DELETE` with WHERE    | HIGH       | Show affected count, require confirmation |
| `UPDATE` with WHERE    | HIGH       | Show affected count, require confirmation |
| `ALTER TABLE`          | MEDIUM     | Describe changes, require confirmation    |
| `VACUUM` (SQLite)      | LOW        | Inform user (compacts database)           |

### Password/Credential Security

- NEVER echo password to terminal output
- NEVER include password in error messages shown to user
- NEVER print or show the full command that contains passwords to the user
- When executing commands, do NOT display the command itself - only show the query results
- Do not log queries containing passwords

### Production/System Database Warning

Show warning if:

- Host/path contains: `prod`, `production`, `live`, `master`
- Cloud database hostnames (RDS, Cloud SQL, Azure)
- System databases (browser DBs, `/Library/`, `/var/lib/`)

### SQLite File Safety

- Verify database path before operations
- Warn if creating a new database file
- Don't modify system SQLite databases without explicit permission (browser DBs, OS DBs)

## Common SQL Operations

These work across all three databases:

```sql
-- List all records (with limit)
SELECT * FROM table_name LIMIT 100;

-- Find by condition
SELECT * FROM table_name WHERE column = 'value' LIMIT 100;

-- Count records
SELECT COUNT(*) FROM table_name;

-- Recent records
SELECT * FROM table_name ORDER BY created_at DESC LIMIT 10;

-- Insert
INSERT INTO table_name (col1, col2) VALUES ('val1', 'val2');

-- Update (show count first, then confirm)
UPDATE table_name SET col1 = 'value' WHERE condition;

-- Delete (show count first, then confirm)
DELETE FROM table_name WHERE condition;
```

## Database-Specific References

For detailed CLI commands, credential formats, and database-specific features:

- **MySQL**: [references/mysql.md](references/mysql.md) - CLI syntax, credential formats, SHOW commands
- **PostgreSQL**: [references/postgres.md](references/postgres.md) - psql meta-commands, SSL/TLS, pg_dump
- **SQLite**: [references/sqlite.md](references/sqlite.md) - PRAGMA commands, backup/import, file formats

## Error Handling

Common errors across databases:

| Error Type         | Likely Cause            | Suggestion                   |
| ------------------ | ----------------------- | ---------------------------- |
| Connection refused | Service not running     | Check if database is running |
| Access denied      | Wrong credentials       | Verify username/password     |
| Database not found | Wrong database name     | List available databases     |
| Table not found    | Wrong table name        | List tables in database      |
| Permission denied  | Insufficient privileges | Check user permissions       |
| Syntax error       | Invalid SQL             | Check query syntax           |

See database-specific references for detailed error handling.
