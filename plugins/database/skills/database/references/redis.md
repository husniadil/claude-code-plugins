# Redis CLI Reference

Redis-specific CLI instructions using the `redis-cli` command-line client.

**Important:** Redis is a key-value store, not a SQL database. It uses Redis commands instead of SQL queries. For complete command documentation, see: https://redis.io/docs/latest/commands/

## Prerequisites

Verify redis-cli is installed:

```bash
redis-cli --version
```

If not installed, inform user to install it via their package manager.

## Credential Acquisition

### Manual Input

Ask for each field:

- Host (default: 127.0.0.1)
- Port (default: 6379)
- Password (optional, for AUTH)
- Username (optional, for ACL authentication)
- Database number (default: 0, range 0-15)

### Read from File

**.env file:**

```
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=secret
REDIS_DB=0
# Also supports: REDIS_URL, REDIS_USER (for ACL)
```

**docker-compose.yml:**

```yaml
services:
  redis:
    environment:
      REDIS_PASSWORD: secret
    # Or with command-line args:
    command: redis-server --requirepass secret
```

**Connection string (REDIS_URL):**

```
redis://[[username:]password@]host[:port][/database]
redis://:password@localhost:6379/0
rediss://user:password@host:6379/0  # TLS
```

After reading the file, confirm with user before connecting.

## TLS/SSL Connections

For secure connections (Redis Cloud, AWS ElastiCache with in-transit encryption):

```bash
redis-cli -h HOST -p PORT --tls [-a PASSWORD] COMMAND
```

With client certificates:

```bash
redis-cli -h HOST -p PORT --tls --cert client.crt --key client.key --cacert ca.crt COMMAND
```

## Connection Test

```bash
redis-cli -h HOST -p PORT [-a PASSWORD] [-n DB] PING
```

Expected response: `PONG`

Note: Password follows `-a` flag. Use `--no-auth-warning` to suppress password warning:

```bash
redis-cli -h HOST -p PORT -a PASSWORD --no-auth-warning PING
```

For ACL authentication (Redis 6+):

```bash
redis-cli -h HOST -p PORT --user USERNAME --pass PASSWORD PING
```

## Command Execution

### Basic Command Pattern

```bash
redis-cli -h HOST -p PORT [-a PASSWORD] [-n DB] COMMAND [ARGS...]
```

### Read Operations

```bash
# Get a key value
redis-cli ... GET key_name

# Get multiple keys
redis-cli ... MGET key1 key2 key3

# Check if key exists
redis-cli ... EXISTS key_name

# Get key type
redis-cli ... TYPE key_name

# Get TTL (time to live)
redis-cli ... TTL key_name
```

### Write Operations

**ALWAYS require user confirmation before executing destructive operations.**

```bash
# Set a key
redis-cli ... SET key_name "value"

# Set with expiration (seconds)
redis-cli ... SET key_name "value" EX 3600

# Delete key(s) - REQUIRES CONFIRMATION
redis-cli ... DEL key_name
```

## Key/Namespace Exploration

Redis keys often use naming conventions like `namespace:subtype:id`. Use SCAN for production-safe iteration.

### List all keys (USE SCAN for production)

**WARNING:** `KEYS *` blocks the server. Use SCAN instead:

```bash
# Safe key iteration (non-blocking)
redis-cli ... --scan --pattern "*"

# With pattern matching
redis-cli ... --scan --pattern "user:*"
redis-cli ... --scan --pattern "*:session:*"

# Count matching keys
redis-cli ... --scan --pattern "user:*" | wc -l
```

### Get key type

```bash
redis-cli ... TYPE key_name
```

### Key introspection

```bash
# String length
redis-cli ... STRLEN key_name

# List length
redis-cli ... LLEN list_name

# Set cardinality
redis-cli ... SCARD set_name

# Hash field count
redis-cli ... HLEN hash_name

# Sorted set cardinality
redis-cli ... ZCARD zset_name
```

## Data Structure Operations

### Strings

```bash
redis-cli ... GET key
redis-cli ... SET key "value"
redis-cli ... INCR counter
redis-cli ... APPEND key "more"
```

### Hashes (like objects/dictionaries)

```bash
redis-cli ... HGET hash_name field
redis-cli ... HGETALL hash_name
redis-cli ... HSET hash_name field "value"
redis-cli ... HMSET hash_name field1 "v1" field2 "v2"
redis-cli ... HDEL hash_name field
```

### Lists (ordered, duplicates allowed)

```bash
redis-cli ... LRANGE list_name 0 -1   # All elements
redis-cli ... LRANGE list_name 0 99   # First 100
redis-cli ... LPUSH list_name "value"
redis-cli ... RPUSH list_name "value"
redis-cli ... LPOP list_name
redis-cli ... RPOP list_name
```

### Sets (unordered, unique)

```bash
redis-cli ... SMEMBERS set_name
redis-cli ... SADD set_name "member"
redis-cli ... SREM set_name "member"
redis-cli ... SISMEMBER set_name "member"
```

### Sorted Sets (ordered by score)

```bash
redis-cli ... ZRANGE zset_name 0 -1              # By index
redis-cli ... ZRANGE zset_name 0 -1 WITHSCORES   # With scores
redis-cli ... ZRANGEBYSCORE zset_name 0 100      # By score range
redis-cli ... ZADD zset_name 1.5 "member"
redis-cli ... ZREM zset_name "member"
```

### Streams (append-only log)

```bash
redis-cli ... XLEN stream_name
redis-cli ... XRANGE stream_name - +             # All entries
redis-cli ... XRANGE stream_name - + COUNT 10   # Last 10
redis-cli ... XADD stream_name "*" field "value"
```

## Output Formatting

### Raw output (for scripting)

```bash
redis-cli ... --raw GET key_name
```

### CSV output

```bash
redis-cli ... --csv HGETALL hash_name
```

### JSON output (Redis 7.0+)

```bash
redis-cli ... --json HGETALL hash_name
```

### Pipe output to file

```bash
redis-cli ... --scan --pattern "user:*" > keys.txt
redis-cli ... HGETALL hash_name > hash_data.txt
```

## Server Information

### Get server info

```bash
redis-cli ... INFO
redis-cli ... INFO server
redis-cli ... INFO memory
redis-cli ... INFO replication
redis-cli ... INFO stats
```

### Database size (key count per DB)

```bash
redis-cli ... DBSIZE
redis-cli ... INFO keyspace
```

### Current database

```bash
redis-cli ... CONFIG GET databases
```

### Memory usage

```bash
redis-cli ... INFO memory
redis-cli ... MEMORY USAGE key_name
```

## Backup and Export

### Trigger RDB snapshot

```bash
redis-cli ... BGSAVE
```

### Check save status

```bash
redis-cli ... LASTSAVE
```

### Export keys to file (using --scan for safety)

```bash
# Export all keys and values (custom script approach)
redis-cli ... --scan --pattern "*" | while read key; do
  echo "$key $(redis-cli ... GET "$key")"
done > export.txt
```

### Dump single key (binary format)

```bash
redis-cli ... DUMP key_name | xxd > key_dump.hex
```

### Restore from dump

```bash
redis-cli ... RESTORE key_name 0 "SERIALIZED_VALUE"
```

### Copy RDB file

The RDB file location can be found with:

```bash
redis-cli ... CONFIG GET dir
redis-cli ... CONFIG GET dbfilename
```

## Common Tasks

| User Request              | Command                                      |
| ------------------------- | -------------------------------------------- |
| "List all keys"           | `--scan --pattern "*"` (NOT `KEYS *`)        |
| "Find keys matching user" | `--scan --pattern "user:*"`                  |
| "Get key value"           | `GET key_name`                               |
| "Set key value"           | `SET key_name "value"`                       |
| "Delete key"              | `DEL key_name` (requires confirmation)       |
| "Key count"               | `DBSIZE`                                     |
| "Check key type"          | `TYPE key_name`                              |
| "Get hash fields"         | `HGETALL hash_name`                          |
| "List all hash keys"      | `HKEYS hash_name`                            |
| "Get list items"          | `LRANGE list_name 0 99`                      |
| "Memory usage"            | `INFO memory` or `MEMORY USAGE key_name`     |
| "Server info"             | `INFO`                                       |
| "Check TTL"               | `TTL key_name`                               |
| "Set expiration"          | `EXPIRE key_name 3600`                       |
| "Flush database"          | `FLUSHDB` (CRITICAL - requires confirmation) |
| "Trigger backup"          | `BGSAVE`                                     |

## Redis Command Reference

For complete command documentation, including syntax and examples:

- **All commands**: https://redis.io/docs/latest/commands/
- **Grouped by category**: https://redis.io/docs/latest/commands/?group=string (change group parameter)

## Error Handling

| Error                     | Likely Cause             | Suggestion                          |
| ------------------------- | ------------------------ | ----------------------------------- |
| NOAUTH Authentication req | Server requires password | Add `-a PASSWORD` flag              |
| ERR invalid password      | Wrong password           | Verify password                     |
| WRONGTYPE Operation error | Wrong data type for key  | Check key type with `TYPE key_name` |
| ERR unknown command       | Command not supported    | Check Redis version                 |
| OOM command not allowed   | Memory limit reached     | Check `maxmemory` config            |
| Connection refused        | Server not running       | Start Redis server                  |
| MOVED/ASK                 | Redis Cluster redirect   | Use `redis-cli -c` for cluster mode |
| READONLY                  | Replica node (read-only) | Connect to primary node             |

## Redis Cluster Mode

For Redis Cluster, use `-c` flag to enable cluster mode (follows redirects):

```bash
redis-cli -c -h HOST -p PORT [-a PASSWORD] COMMAND
```

## Sentinel Mode

To connect via Sentinel:

```bash
redis-cli -h SENTINEL_HOST -p SENTINEL_PORT SENTINEL get-master-addr-by-name MASTER_NAME
```

Then connect to the returned master address.
