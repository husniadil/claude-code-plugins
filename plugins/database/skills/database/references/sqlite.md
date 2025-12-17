# SQLite CLI Reference

SQLite-specific CLI instructions using the `sqlite3` command-line client.

## Prerequisites

Verify sqlite3 CLI is installed:

```bash
sqlite3 --version
```

If not installed, inform user to install it via their package manager (usually pre-installed on macOS/Linux).

## Database Path Acquisition

### Manual Input

Ask for the database file path directly.

### Read from File

**.env file:**

```
SQLITE_DATABASE=./data.db
# Also supports: DATABASE_PATH, DB_PATH, DB_DATABASE, DATABASE_URL
```

**Connection string (DATABASE_URL):**

```
sqlite:///path/to/database.db
sqlite:///:memory:
```

After reading the file, confirm with user before connecting.

### Supported Path Formats

- Relative path: `./data.db`, `../databases/app.sqlite`
- Absolute path: `/home/user/data.db`, `/var/lib/app/database.sqlite`
- In-memory: `:memory:` (temporary, data lost on close)
- URI format: `file:path/to/db?mode=ro` (read-only), `file::memory:?cache=shared`
- Common extensions: `.db`, `.sqlite`, `.sqlite3`, `.db3`

### URI Format Options

SQLite supports URI filenames with query parameters:

```bash
# Read-only mode
sqlite3 "file:data.db?mode=ro"

# Read-write, create if not exists (default)
sqlite3 "file:data.db?mode=rwc"

# Shared cache for in-memory
sqlite3 "file::memory:?cache=shared"
```

After receiving the path, verify the file exists (unless creating new):

```bash
ls -la DATABASE_PATH 2>&1
```

## Connection Test

```bash
sqlite3 DATABASE_PATH "SELECT 1" 2>&1
```

If the file doesn't exist, SQLite will create it. Warn the user if this happens.

## Query Execution

### Read Operations (SELECT)

```bash
sqlite3 -header -column DATABASE_PATH "QUERY"
```

Add `LIMIT 100` to large result sets by default.

### Write Operations (INSERT, UPDATE, DELETE)

For UPDATE/DELETE, first show affected rows:

```bash
sqlite3 DATABASE_PATH "SELECT COUNT(*) FROM table WHERE condition"
```

Then ask: "This will affect X rows. Proceed? (yes/no)"

## Schema Exploration

### List tables

```bash
sqlite3 DATABASE_PATH ".tables"
```

Or with more detail:

```bash
sqlite3 -header -column DATABASE_PATH "SELECT name, type FROM sqlite_master WHERE type='table' ORDER BY name"
```

### Describe table structure

```bash
sqlite3 -header -column DATABASE_PATH "PRAGMA table_info(table_name)"
```

### Show CREATE statement

```bash
sqlite3 DATABASE_PATH ".schema table_name"
```

Or for all objects:

```bash
sqlite3 DATABASE_PATH ".schema"
```

### List indexes

```bash
sqlite3 DATABASE_PATH ".indexes"
```

Or for a specific table:

```bash
sqlite3 DATABASE_PATH ".indexes table_name"
```

### List all indexes with details

```bash
sqlite3 -header -column DATABASE_PATH "SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index' ORDER BY tbl_name"
```

### List views

```bash
sqlite3 -header -column DATABASE_PATH "SELECT name, sql FROM sqlite_master WHERE type='view'"
```

### List triggers

```bash
sqlite3 -header -column DATABASE_PATH "SELECT name, tbl_name, sql FROM sqlite_master WHERE type='trigger'"
```

### Show database info

```bash
sqlite3 DATABASE_PATH "PRAGMA database_list"
```

### Show table row count

```bash
sqlite3 DATABASE_PATH "SELECT COUNT(*) FROM table_name"
```

## Protected Database Warning

If database path matches these patterns, show warning and require confirmation:

**System databases:**

- Browser databases: `*/Chrome/*`, `*/Firefox/*`, `*/Safari/*`, `places.sqlite`, `cookies.sqlite`
- macOS system: `/Library/`, `~/Library/`
- Linux system: `/var/lib/`, `/etc/`

**Application databases:**

- `*.sqlite-shm`, `*.sqlite-wal` (active database files)
- Paths containing `prod`, `production`, `live`

**Example warning:**

```
WARNING: This appears to be a system/application database.
Path: ~/Library/Application Support/Firefox/places.sqlite
Modifying this database may cause application issues.
Are you sure you want to proceed? (yes/no)
```

## Output Formatting

### Table format (default for readability)

```bash
sqlite3 -header -column DATABASE_PATH "QUERY"
```

### CSV format (for data export)

```bash
sqlite3 -header -csv DATABASE_PATH "QUERY"
```

### JSON format (for data processing)

```bash
sqlite3 -json DATABASE_PATH "QUERY"
```

### Line format (one value per line)

```bash
sqlite3 -line DATABASE_PATH "QUERY"
```

### Export to file

```bash
sqlite3 -header -csv DATABASE_PATH "QUERY" > output.csv
```

## Backup and Export

### Dump entire database

```bash
sqlite3 DATABASE_PATH ".dump" > backup.sql
```

### Dump specific table

```bash
sqlite3 DATABASE_PATH ".dump table_name" > table_backup.sql
```

### Dump schema only (no data)

```bash
sqlite3 DATABASE_PATH ".schema" > schema.sql
```

### Restore from dump

```bash
sqlite3 NEW_DATABASE < backup.sql
```

## Import Data

### Import CSV file

```bash
sqlite3 DATABASE_PATH <<EOF
.mode csv
.import file.csv table_name
EOF
```

For CSV with headers (skip first row):

```bash
sqlite3 DATABASE_PATH <<EOF
.mode csv
.import --skip 1 file.csv table_name
EOF
```

### Import from SQL file

```bash
sqlite3 DATABASE_PATH < data.sql
```

## SQLite-Specific Features

### PRAGMA commands

Common PRAGMA commands for database inspection:

```sql
PRAGMA table_info(table_name);      -- Column details
PRAGMA foreign_key_list(table_name); -- Foreign keys
PRAGMA index_list(table_name);       -- Indexes on table
PRAGMA index_info(index_name);       -- Index columns
PRAGMA integrity_check;              -- Check database integrity
PRAGMA quick_check;                  -- Fast integrity check
PRAGMA database_list;                -- Attached databases
PRAGMA table_xinfo(table_name);      -- Extended column info (includes hidden)
```

### Attach multiple databases

```sql
ATTACH DATABASE 'other.db' AS other;
SELECT * FROM other.table_name;
DETACH DATABASE other;
```

## Common Tasks

| User Request               | Query/Command                                                    |
| -------------------------- | ---------------------------------------------------------------- |
| "Show all tables"          | `.tables` or `SELECT name FROM sqlite_master WHERE type='table'` |
| "Describe users table"     | `PRAGMA table_info(users)`                                       |
| "Find user by email"       | `SELECT * FROM users WHERE email LIKE '%pattern%' LIMIT 100`     |
| "Count records"            | `SELECT COUNT(*) FROM table`                                     |
| "Recent records"           | `SELECT * FROM table ORDER BY created_at DESC LIMIT 10`          |
| "Show indexes"             | `.indexes` or `.indexes table_name`                              |
| "Show create statement"    | `.schema table_name`                                             |
| "Database file size"       | Use `ls -lh DATABASE_PATH` via bash                              |
| "Check database integrity" | `PRAGMA integrity_check`                                         |
| "List foreign keys"        | `PRAGMA foreign_key_list(table_name)`                            |
| "Enable foreign keys"      | `PRAGMA foreign_keys = ON`                                       |
| "Backup database"          | `.dump > backup.sql`                                             |
| "Import CSV"               | `.mode csv` then `.import file.csv table`                        |
| "Export to CSV"            | `-header -csv "SELECT ..." > output.csv`                         |

## Error Handling

| Error                        | Likely Cause              | Suggestion                       |
| ---------------------------- | ------------------------- | -------------------------------- |
| unable to open database file | Wrong path or permissions | Verify path and file permissions |
| no such table                | Table doesn't exist       | Run `.tables` to list tables     |
| database is locked           | Another process using it  | Close other connections          |
| SQLITE_CORRUPT               | Database corrupted        | Run `PRAGMA integrity_check`     |
| SQLITE_READONLY              | No write permission       | Check file permissions           |
| near "X": syntax error       | SQL syntax error          | Check query syntax               |
