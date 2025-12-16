# mysql-cli

A Claude Code plugin for accessing MySQL databases via CLI.

## Features

- Query execution (SELECT, INSERT, UPDATE, DELETE)
- Schema exploration (SHOW DATABASES, SHOW TABLES, DESCRIBE)
- Credential management from user input or config files (.env, docker-compose.yml)
- Safety confirmations for destructive operations
- Production database warnings

## Installation

```bash
claude plugin install mysql-cli@ekstend
```

## Prerequisites

MySQL CLI client must be installed on your system:

```bash
# macOS
brew install mysql-client

# Ubuntu/Debian
apt install mysql-client

# Check installation
mysql --version
```

## Usage

Simply ask Claude to work with your MySQL database:

- "Connect to my MySQL database"
- "Show all tables in the database"
- "Find users with email containing gmail"
- "Update the status of order #123"

Claude will ask for credentials or a config file path before connecting.

## Safety

- Destructive operations (DROP, DELETE, UPDATE, TRUNCATE) require confirmation
- Password is never echoed to terminal or logged
- Production databases trigger warnings
