# MySQL CLI Reference

MySQL-specific CLI instructions using the `mysql` command-line client.

## Prerequisites

Verify mysql CLI is installed:

```bash
mysql --version
```

If not installed, inform user to install it via their package manager.

## Credential Acquisition

### Manual Input

Ask for each field:

- Host (default: localhost)
- Port (default: 3306)
- Username
- Password
- Database name

### Read from File

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

## Output Formatting

### Table format (default for readability)

```bash
mysql ... -e "QUERY" --table
```

### Batch format (for data processing)

```bash
mysql ... -e "QUERY" --batch --raw | column -t -s $'\t'
```

### Export to file

```bash
mysql ... -e "QUERY" --batch > output.csv
```

## Backup and Export

### Dump entire database

```bash
mysqldump -h HOST -P PORT -u USER -pPASSWORD DATABASE > backup.sql
```

### Dump specific table

```bash
mysqldump -h HOST -P PORT -u USER -pPASSWORD DATABASE table_name > table_backup.sql
```

### Dump schema only (no data)

```bash
mysqldump -h HOST -P PORT -u USER -pPASSWORD --no-data DATABASE > schema.sql
```

### Dump data only (no schema)

```bash
mysqldump -h HOST -P PORT -u USER -pPASSWORD --no-create-info DATABASE > data.sql
```

### Restore from dump

```bash
mysql -h HOST -P PORT -u USER -pPASSWORD DATABASE < backup.sql
```

## Common Tasks

| User Request           | Query                                                        |
| ---------------------- | ------------------------------------------------------------ |
| "Show all tables"      | `SHOW TABLES`                                                |
| "Describe users table" | `DESCRIBE users`                                             |
| "Find user by email"   | `SELECT * FROM users WHERE email LIKE '%pattern%' LIMIT 100` |
| "Count records"        | `SELECT COUNT(*) FROM table`                                 |
| "Recent records"       | `SELECT * FROM table ORDER BY created_at DESC LIMIT 10`      |
| "Backup database"      | `mysqldump ... DATABASE > backup.sql`                        |
| "Export to CSV"        | `mysql ... -e "SELECT ..." --batch > output.csv`             |

## Error Handling

| Error               | Likely Cause           | Suggestion               |
| ------------------- | ---------------------- | ------------------------ |
| Access denied       | Wrong credentials      | Verify username/password |
| Unknown database    | Database doesn't exist | Run `SHOW DATABASES`     |
| Can't connect       | Host/port issue        | Check host and port      |
| Table doesn't exist | Wrong table name       | Run `SHOW TABLES`        |
