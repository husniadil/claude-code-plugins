# PostgreSQL CLI Reference

PostgreSQL-specific CLI instructions using the `psql` command-line client.

## Prerequisites

Verify psql CLI is installed:

```bash
psql --version
```

If not installed, inform user to install it via their package manager.

## Credential Acquisition

### Manual Input

Ask for each field:

- Host (default: localhost)
- Port (default: 5432)
- Username
- Password
- Database name

### Read from File

**.env file:**

```
PGHOST=localhost
PGPORT=5432
PGUSER=postgres
PGPASSWORD=secret
PGDATABASE=myapp
# Also supports: DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_DATABASE
# Also supports: POSTGRES_HOST, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
```

**docker-compose.yml:**

```yaml
services:
  postgres:
    environment:
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: myapp
      POSTGRES_USER: user
```

**Connection string:**

```
postgresql://user:password@host:port/database
postgres://user:password@host:port/database
```

**.pgpass file** (native PostgreSQL password file):

Location: `~/.pgpass` (Linux/macOS) or `%APPDATA%\postgresql\pgpass.conf` (Windows)

Format (one entry per line):

```
hostname:port:database:username:password
```

Example:

```
localhost:5432:myapp:postgres:secret
*.example.com:5432:*:admin:adminpass
```

Note: File must have permissions `600` (`chmod 600 ~/.pgpass`).

After reading the file, confirm with user before connecting.

## SSL/TLS Connections

For secure connections (especially cloud databases), use `PGSSLMODE`:

```bash
PGPASSWORD=PASSWORD PGSSLMODE=require psql -h HOST -p PORT -U USER -d DATABASE -c "QUERY"
```

SSL modes:

| Mode          | Description                                    |
| ------------- | ---------------------------------------------- |
| `disable`     | No SSL                                         |
| `allow`       | Try non-SSL first, then SSL                    |
| `prefer`      | Try SSL first, then non-SSL (default)          |
| `require`     | SSL required, no certificate verification      |
| `verify-ca`   | SSL required, verify server certificate        |
| `verify-full` | SSL required, verify server certificate + host |

For cloud databases (RDS, Cloud SQL, Azure), typically use `require` or `verify-full`.

Connection string with SSL:

```
postgresql://user:password@host:port/database?sslmode=require
```

## Connection Test

```bash
PGPASSWORD=PASSWORD psql -h HOST -p PORT -U USER -d DATABASE -c "SELECT 1" 2>&1
```

Note: Password is passed via `PGPASSWORD` environment variable (set inline for single command).

## Query Execution

### Read Operations (SELECT)

```bash
PGPASSWORD=PASSWORD psql -h HOST -p PORT -U USER -d DATABASE -c "QUERY"
```

Add `LIMIT 100` to large result sets by default. Use `--csv` for CSV output.

### Write Operations (INSERT, UPDATE, DELETE)

For UPDATE/DELETE, first show affected rows:

```bash
PGPASSWORD=PASSWORD psql ... -c "SELECT COUNT(*) FROM table WHERE condition"
```

Then ask: "This will affect X rows. Proceed? (yes/no)"

## Schema Exploration

### List databases

```bash
PGPASSWORD=PASSWORD psql -h HOST -p PORT -U USER -d DATABASE -c "\l"
```

### List tables

```bash
PGPASSWORD=PASSWORD psql ... -c "\dt"
```

### List tables with schema

```bash
PGPASSWORD=PASSWORD psql ... -c "\dt schema_name.*"
```

### Describe table structure

```bash
PGPASSWORD=PASSWORD psql ... -c "\d table_name"
```

### Show detailed table info (with indexes, constraints)

```bash
PGPASSWORD=PASSWORD psql ... -c "\d+ table_name"
```

### List schemas

```bash
PGPASSWORD=PASSWORD psql ... -c "\dn"
```

### Show create statement

```bash
PGPASSWORD=PASSWORD pg_dump -h HOST -p PORT -U USER -d DATABASE -t table_name --schema-only
```

### List indexes

```bash
PGPASSWORD=PASSWORD psql ... -c "\di"
```

### List functions

```bash
PGPASSWORD=PASSWORD psql ... -c "\df"
```

### List views

```bash
PGPASSWORD=PASSWORD psql ... -c "\dv"
```

### List sequences

```bash
PGPASSWORD=PASSWORD psql ... -c "\ds"
```

### List roles/users

```bash
PGPASSWORD=PASSWORD psql ... -c "\du"
```

## Output Formatting

### Default format (aligned tables)

```bash
PGPASSWORD=PASSWORD psql ... -c "QUERY"
```

### CSV format (for data processing)

```bash
PGPASSWORD=PASSWORD psql ... --csv -c "QUERY"
```

### Tuples only (no headers/footers)

```bash
PGPASSWORD=PASSWORD psql ... -t -c "QUERY"
```

### Export to file

```bash
PGPASSWORD=PASSWORD psql ... --csv -c "QUERY" > output.csv
```

### Expanded display (vertical format for wide tables)

```bash
PGPASSWORD=PASSWORD psql ... -x -c "QUERY"
```

## Backup and Export

### Dump entire database

```bash
PGPASSWORD=PASSWORD pg_dump -h HOST -p PORT -U USER -d DATABASE > backup.sql
```

### Dump specific table

```bash
PGPASSWORD=PASSWORD pg_dump -h HOST -p PORT -U USER -d DATABASE -t table_name > table_backup.sql
```

### Dump schema only (no data)

```bash
PGPASSWORD=PASSWORD pg_dump -h HOST -p PORT -U USER -d DATABASE --schema-only > schema.sql
```

### Dump data only (no schema)

```bash
PGPASSWORD=PASSWORD pg_dump -h HOST -p PORT -U USER -d DATABASE --data-only > data.sql
```

### Custom format (for pg_restore)

```bash
PGPASSWORD=PASSWORD pg_dump -h HOST -p PORT -U USER -d DATABASE -Fc > backup.dump
```

### Restore from SQL dump

```bash
PGPASSWORD=PASSWORD psql -h HOST -p PORT -U USER -d DATABASE < backup.sql
```

### Restore from custom format

```bash
PGPASSWORD=PASSWORD pg_restore -h HOST -p PORT -U USER -d DATABASE backup.dump
```

## Common Tasks

| User Request           | Query/Command                                                 |
| ---------------------- | ------------------------------------------------------------- |
| "Show all tables"      | `\dt` or `\dt *.*` for all schemas                            |
| "Describe users table" | `\d users` or `\d+ users` for detailed                        |
| "Find user by email"   | `SELECT * FROM users WHERE email LIKE '%pattern%' LIMIT 100`  |
| "Count records"        | `SELECT COUNT(*) FROM table`                                  |
| "Recent records"       | `SELECT * FROM table ORDER BY created_at DESC LIMIT 10`       |
| "List schemas"         | `\dn`                                                         |
| "Show table in schema" | `\dt schema_name.table_name`                                  |
| "Current database"     | `SELECT current_database()`                                   |
| "Current user"         | `SELECT current_user`                                         |
| "List indexes"         | `\di` or `\di table_name`                                     |
| "List functions"       | `\df`                                                         |
| "List views"           | `\dv`                                                         |
| "Show table size"      | `SELECT pg_size_pretty(pg_total_relation_size('table'))`      |
| "Database size"        | `SELECT pg_size_pretty(pg_database_size(current_database()))` |
| "Active connections"   | `SELECT * FROM pg_stat_activity`                              |
| "Backup database"      | `pg_dump ... -d DATABASE > backup.sql`                        |
| "Export to CSV"        | `psql ... --csv -c "SELECT ..." > output.csv`                 |

## Error Handling

| Error                   | Likely Cause            | Suggestion                 |
| ----------------------- | ----------------------- | -------------------------- |
| password authentication | Wrong credentials       | Verify username/password   |
| database does not exist | Database doesn't exist  | Run `\l` to list databases |
| could not connect       | Host/port issue         | Check host and port        |
| relation does not exist | Wrong table name        | Run `\dt` to list tables   |
| permission denied       | Insufficient privileges | Check user permissions     |
| connection refused      | PostgreSQL not running  | Start PostgreSQL service   |
