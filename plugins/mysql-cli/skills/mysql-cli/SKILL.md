---
name: mysql-cli
description: Access MySQL databases via CLI for querying, schema exploration, and data management. Use when working with MySQL databases to run queries, explore table structures, manage data, or perform database operations. Supports credentials from user input or config files (.env, docker-compose.yml). IMPORTANT - Always ask user for credentials or credential file location first; never use shell environment variables without explicit user permission.
---

# MySQL CLI

Access and manage MySQL databases using the `mysql` command-line client.

## Prerequisites

Verify mysql CLI is installed:

```bash
mysql --version
```

If not installed, inform user to install it via their package manager.

## Credential Acquisition

**CRITICAL: Never use environment variables from the shell without explicit user permission.**

When credentials are needed, ask the user using AskUserQuestion:

```
How would you like to provide MySQL credentials?

1. Enter credentials manually (host, user, password, database)
2. Read from a file (provide path to .env, docker-compose.yml, or config file)
```

### Option 1: Manual Input

Ask for each field:

- Host (default: localhost)
- Port (default: 3306)
- Username
- Password
- Database name

### Option 2: Read from File

Supported formats:

**.env file:**

```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=secret
DB_DATABASE=myapp
# Also supports: MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
```

**docker-compose.yml:**

```yaml
services:
  mysql:
    environment:
      MYSQL_ROOT_PASSWORD: secret
      MYSQL_DATABASE: myapp
      MYSQL_USER: user
      MYSQL_PASSWORD: pass
```

**Connection string:**

```
mysql://user:password@host:port/database
```

After reading the file, confirm with user before connecting.

## Connection Test

Before any operation, test the connection:

```bash
mysql -h HOST -P PORT -u USER -pPASSWORD -e "SELECT 1" 2>&1
```

Note: Password immediately follows `-p` with no space.

## Query Execution

### Read Operations (SELECT)

```bash
mysql -h HOST -P PORT -u USER -pPASSWORD DATABASE -e "QUERY" --table
```

Add `LIMIT 100` to large result sets by default. Use `--batch` for CSV-like output.

### Write Operations (INSERT, UPDATE, DELETE)

**ALWAYS require user confirmation before executing.**

For UPDATE/DELETE, first show affected rows:

```bash
mysql ... -e "SELECT COUNT(*) FROM table WHERE condition"
```

Then ask: "This will affect X rows. Proceed? (yes/no)"

## Schema Exploration

### List databases

```bash
mysql ... -e "SHOW DATABASES"
```

### List tables

```bash
mysql ... DATABASE -e "SHOW TABLES"
```

### Describe table structure

```bash
mysql ... DATABASE -e "DESCRIBE table_name"
```

### Show create statement

```bash
mysql ... DATABASE -e "SHOW CREATE TABLE table_name"
```

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

### Password Security

- NEVER echo password to terminal output
- NEVER include password in error messages shown to user
- Use `-p` flag (password prompted) or temporary config file if needed
- Do not log queries containing passwords

### Production Database Warning

If host contains these patterns, show warning:

- `prod`, `production`, `live`, `master`
- Cloud database hostnames (RDS, Cloud SQL, etc.)

## Output Formatting

### Table format (default for readability)

```bash
mysql ... -e "QUERY" --table
```

### JSON format (for data processing)

```bash
mysql ... -e "QUERY" --batch --raw | column -t -s $'\t'
```

### Export to file

```bash
mysql ... -e "QUERY" --batch > output.csv
```

## Common Tasks

| User Request           | Query                                                        |
| ---------------------- | ------------------------------------------------------------ |
| "Show all tables"      | `SHOW TABLES`                                                |
| "Describe users table" | `DESCRIBE users`                                             |
| "Find user by email"   | `SELECT * FROM users WHERE email LIKE '%pattern%' LIMIT 100` |
| "Count records"        | `SELECT COUNT(*) FROM table`                                 |
| "Recent records"       | `SELECT * FROM table ORDER BY created_at DESC LIMIT 10`      |

## Error Handling

| Error               | Likely Cause           | Suggestion               |
| ------------------- | ---------------------- | ------------------------ |
| Access denied       | Wrong credentials      | Verify username/password |
| Unknown database    | Database doesn't exist | Run `SHOW DATABASES`     |
| Can't connect       | Host/port issue        | Check host and port      |
| Table doesn't exist | Wrong table name       | Run `SHOW TABLES`        |
