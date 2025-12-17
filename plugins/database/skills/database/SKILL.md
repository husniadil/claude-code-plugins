---
name: database
description: ALWAYS USE THIS SKILL when user mentions ANY database-related keywords including "db", "database", "SQL", "query", "PostgreSQL", "Postgres", "psql", "MySQL", "SQLite", "Redis", "orders", "users", "tables", "records", "data", "check data", "get data", "fetch data", "select", "insert", "update", "delete", "from database", "in database", "query table", "check records", "look up", "retrieve". This skill provides safe database access with mandatory schema exploration before queries. Supports MySQL, PostgreSQL, SQLite, and Redis via CLI.
---

# Database CLI

Access and manage MySQL, PostgreSQL, SQLite databases, and Redis key-value stores using their respective command-line clients.

## Critical Rules

**NEVER** do the following:

- **NEVER** guess or assume table names - always list tables first with `SHOW TABLES`, `\dt`, or `.tables`
- **NEVER** guess or assume column names - always describe the table first with `DESCRIBE`, `\d`, or `PRAGMA table_info`
- **NEVER** run SELECT queries on an unfamiliar database without exploring the schema first
- **NEVER** assume ORM naming conventions (e.g., `Order` vs `orders`, `userId` vs `user_id`) - verify with schema

**ALWAYS** follow the Query Workflow below when querying data the user asks for.

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
| User says "Redis", "redis-cli"                 | Redis         |
| Connection string starts with `redis://`       | Redis         |
| Connection string starts with `rediss://`      | Redis         |
| Config has `REDIS_*` variables                 | Redis         |
| Port 3306 mentioned                            | MySQL         |
| Port 5432 mentioned                            | PostgreSQL    |
| Port 6379 mentioned                            | Redis         |

If database type cannot be determined, ask using AskUserQuestion:

```
Which database are you working with?
1. MySQL
2. PostgreSQL
3. SQLite
4. Redis
```

## Prerequisites

Verify the appropriate CLI is installed:

| Database   | Command               |
| ---------- | --------------------- |
| MySQL      | `mysql --version`     |
| PostgreSQL | `psql --version`      |
| SQLite     | `sqlite3 --version`   |
| Redis      | `redis-cli --version` |

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
| Redis      | `brew install redis`        | `sudo apt install redis-tools`       | `sudo pacman -S redis`      |

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

**For Redis:**

```
How would you like to provide Redis connection details?
1. Enter connection details manually (host, port, password, database number)
2. Read from a file (provide path to .env, docker-compose.yml, or config file)
```

After reading any config file, confirm with user before connecting.

For detailed credential formats and CLI syntax, see the database-specific references:

- **MySQL**: See [references/mysql.md](references/mysql.md)
- **PostgreSQL**: See [references/postgres.md](references/postgres.md)
- **SQLite**: See [references/sqlite.md](references/sqlite.md)
- **Redis**: See [references/redis.md](references/redis.md)

## Connection Test

Before any operation, test the connection using the appropriate command from the reference docs.

## Query Workflow (For Unfamiliar Databases)

When user asks to query or check data, follow these steps **in order**:

### Step 1: List Tables

First, discover what tables exist:

| Database   | Command                                                          |
| ---------- | ---------------------------------------------------------------- |
| MySQL      | `SHOW TABLES`                                                    |
| PostgreSQL | `\dt` or `\dt *.*` (all schemas)                                 |
| SQLite     | `.tables` or `SELECT name FROM sqlite_master WHERE type='table'` |

### Step 2: Identify Target Table

Match user's intent to actual table name:

- User says "order" → look for `orders`, `order`, `Order`, `tbl_orders`, etc.
- User says "user" → look for `users`, `user`, `accounts`, `members`, etc.
- **Do NOT assume** - pick from the actual table list

### Step 3: Describe Table Structure

Get actual column names before querying:

| Database   | Command                         |
| ---------- | ------------------------------- |
| MySQL      | `DESCRIBE table_name`           |
| PostgreSQL | `\d table_name`                 |
| SQLite     | `PRAGMA table_info(table_name)` |

### Step 4: Build and Execute Query

Now build the SELECT using **actual column names** from Step 3:

```sql
-- Use real columns, not guessed ones
SELECT actual_col1, actual_col2, actual_col3
FROM actual_table_name
ORDER BY created_at DESC
LIMIT 10;
```

## Query Execution

### Read Operations (SELECT)

Add `LIMIT 100` to large result sets by default unless user specifies otherwise.

### Write Operations (INSERT, UPDATE, DELETE)

**ALWAYS require user confirmation before executing.**

For UPDATE/DELETE, first show affected rows count, then ask: "This will affect X rows. Proceed? (yes/no)"

## Redis Operations

Redis uses commands, not SQL queries. See [references/redis.md](references/redis.md) for:

- Key-value operations (GET, SET, DEL)
- Data structure operations (lists, sets, hashes, sorted sets)
- Key pattern exploration (SCAN, KEYS)
- Official command reference: https://redis.io/docs/latest/commands/

## Schema Exploration (SQL Databases)

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

### Redis Destructive Operations - REQUIRE CONFIRMATION

| Operation              | Risk Level | Action Before Execute                         |
| ---------------------- | ---------- | --------------------------------------------- |
| `FLUSHDB`              | CRITICAL   | Show database number, warn all keys deleted   |
| `FLUSHALL`             | CRITICAL   | Warn ALL databases cleared, require "yes"     |
| `DEL` with pattern     | CRITICAL   | Show matching key count first, require "yes"  |
| `UNLINK` with pattern  | CRITICAL   | Show matching key count first, require "yes"  |
| `KEYS *` on production | HIGH       | Warn about blocking, suggest SCAN instead     |
| `CONFIG SET`           | HIGH       | Show what will change, require confirmation   |
| `DEBUG *`              | CRITICAL   | Refuse unless explicit permission             |
| `SHUTDOWN`             | CRITICAL   | Warn server will stop, require explicit "yes" |

### Password/Credential Security

- NEVER echo password to terminal output
- NEVER include password in error messages shown to user
- NEVER print or show the full command that contains passwords to the user
- When executing commands, do NOT display the command itself - only show the query results
- Do not log queries containing passwords

### Production/System Database Warning

Show warning if:

- Host/path contains: `prod`, `production`, `live`, `master`
- Cloud database hostnames (RDS, Cloud SQL, Azure, Redis Cloud, ElastiCache)
- System databases (browser DBs, `/Library/`, `/var/lib/`)

### SQLite File Safety

- Verify database path before operations
- Warn if creating a new database file
- Don't modify system SQLite databases without explicit permission (browser DBs, OS DBs)

## Common SQL Operations

These work across MySQL, PostgreSQL, and SQLite (Redis uses commands, not SQL):

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
- **Redis**: [references/redis.md](references/redis.md) - CLI syntax, key operations, data structures, SCAN patterns

## Error Handling

Common errors across databases:

| Error Type         | Likely Cause            | Suggestion                       |
| ------------------ | ----------------------- | -------------------------------- |
| Connection refused | Service not running     | Check if database is running     |
| Access denied      | Wrong credentials       | Verify username/password         |
| Database not found | Wrong database name     | List available databases         |
| Table not found    | Wrong table name        | List tables in database          |
| Permission denied  | Insufficient privileges | Check user permissions           |
| Syntax error       | Invalid SQL             | Check query syntax               |
| NOAUTH (Redis)     | Redis requires password | Add `-a PASSWORD` flag           |
| WRONGTYPE (Redis)  | Wrong Redis data type   | Check key type with TYPE command |

See database-specific references for detailed error handling.
