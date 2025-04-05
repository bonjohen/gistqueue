# GistQueue Usage Documentation

## Overview

GistQueue is a message queue system that uses GitHub Gists as the storage backend. This document provides comprehensive syntax and usage examples for all available commands and operations.

## Installation

```bash
# Install from source
git clone https://github.com/yourusername/gistqueue.git
cd gistqueue
pip install -e .

# Or install from PyPI (if available)
pip install gistqueue
```

## Authentication

GistQueue requires a GitHub personal access token with the `gist` scope. Set this token as an environment variable:

```bash
# Windows (Command Prompt)
set GIST_TOKEN=your_github_token

# Windows (PowerShell)
$env:GIST_TOKEN="your_github_token"

# Linux/macOS
export GIST_TOKEN=your_github_token
```

For permanent configuration, add the token to your system environment variables or create a `.env` file in your project directory:

```
GIST_TOKEN=your_github_token
```

## Command Line Interface

### Basic Syntax

```bash
gistqueue [command] [options]
```

### Global Options

- `--version`: Show version information
- `--help` or `-h`: Show help message

### Environment and Initialization

#### Initialize and Test Environment

```bash
gistqueue init
```

### Queue Management

#### Create Queue

```bash
# Create a queue with the default name
gistqueue create-queue

# Create a named queue
gistqueue create-queue [queue_name]

# Create a public queue
gistqueue create-queue [queue_name] --public
```

#### List Queues

```bash
# List all queues in table format (default)
gistqueue list-queues

# List all queues in JSON format
gistqueue list-queues --format json
```

#### Get Queue Information

```bash
# Get information about a queue by name
gistqueue get-queue [queue_name]

# Get information about a queue by ID
gistqueue get-queue --id [gist_id]

# Get information in JSON format
gistqueue get-queue [queue_name] --format json
```

### Message Operations

#### Create Message

```bash
# Create a message in a queue
gistqueue create-message [queue_name] [content]

# Example with JSON content (use quotes)
gistqueue create-message orders "{'order_id': 123, 'customer': 'John Doe'}"
```

#### List Messages

```bash
# List all messages in a queue
gistqueue list-messages [queue_name]

# List messages with a specific status
gistqueue list-messages [queue_name] --status pending
gistqueue list-messages [queue_name] --status in_progress
gistqueue list-messages [queue_name] --status complete
gistqueue list-messages [queue_name] --status failed

# List messages in JSON format
gistqueue list-messages [queue_name] --format json
```

#### Get Next Message

```bash
# Get the next pending message and mark it as in progress
gistqueue get-next-message [queue_name]

# Get the next message in JSON format
gistqueue get-next-message [queue_name] --format json
```

#### Update Message

```bash
# Update a message's content
gistqueue update-message [queue_name] [message_id] --content [new_content]

# Update a message's status
gistqueue update-message [queue_name] [message_id] --status pending
gistqueue update-message [queue_name] [message_id] --status in_progress
gistqueue update-message [queue_name] [message_id] --status complete
gistqueue update-message [queue_name] [message_id] --status failed

# Update both content and status
gistqueue update-message [queue_name] [message_id] --content [new_content] --status complete

# Update in JSON format
gistqueue update-message [queue_name] [message_id] --content [new_content] --format json
```

#### Delete Completed Messages

```bash
# Delete completed messages older than the cleanup threshold
gistqueue delete-completed-messages [queue_name]
```

### Garbage Collection

#### Clean Up All Queues

```bash
# Clean up completed messages in all queues
gistqueue cleanup-all-queues

# Clean up and output results in JSON format
gistqueue cleanup-all-queues --format json
```

#### Automatic Cleanup

```bash
# Start the automatic cleanup thread
gistqueue start-cleanup-thread

# Stop the automatic cleanup thread
gistqueue stop-cleanup-thread

# Stop with custom timeout (in seconds)
gistqueue stop-cleanup-thread --timeout 10.0
```

## Configuration Options

GistQueue can be configured using environment variables or a `.env` file:

| Environment Variable | Description | Default Value |
|----------------------|-------------|---------------|
| `GIST_TOKEN` | GitHub personal access token | (Required) |
| `GIST_DESCRIPTION_PREFIX` | Prefix for Gist descriptions | "Queue:" |
| `DEFAULT_QUEUE_NAME` | Default queue name | "default" |
| `DEFAULT_FILE_EXTENSION` | File extension for queue files | "json" |
| `API_RETRY_COUNT` | Number of API retry attempts | 3 |
| `API_RETRY_DELAY` | Delay between retries (seconds) | 1 |
| `CLEANUP_THRESHOLD_DAYS` | Age threshold for message cleanup (days) | 1 |
| `CLEANUP_INTERVAL_SECONDS` | Interval for automatic cleanup (seconds) | 3600 |
| `CLEANUP_AUTO_START` | Auto-start cleanup thread | False |
| `CONCURRENCY_MAX_RETRIES` | Max retries for concurrent operations | 3 |
| `CONCURRENCY_RETRY_DELAY_BASE` | Base delay for retries (seconds) | 1.0 |
| `CONCURRENCY_RETRY_DELAY_MAX` | Maximum delay for retries (seconds) | 5.0 |
| `CONCURRENCY_JITTER_FACTOR` | Jitter factor for retry delays | 0.1 |

## Scripting Examples

### Basic Queue Operations

```bash
# Create a queue and add a message
gistqueue create-queue orders
gistqueue create-message orders "{'order_id': 123, 'product': 'Widget'}"

# Process messages
message=$(gistqueue get-next-message orders --format json)
message_id=$(echo $message | jq -r '.id')
gistqueue update-message orders $message_id --status complete
```

### Batch Processing

```bash
# Process all pending messages in a queue
for message_id in $(gistqueue list-messages orders --status pending --format json | jq -r '.[].id'); do
    gistqueue update-message orders $message_id --status in_progress
    # Process the message...
    gistqueue update-message orders $message_id --status complete
done
```

### Scheduled Cleanup

```bash
# Windows Task Scheduler or Linux cron job
gistqueue cleanup-all-queues
```

## Error Handling

GistQueue provides detailed error messages and exit codes:

- Exit code 0: Success
- Exit code 1: Error (check error message)

Common error scenarios:

- Authentication errors: Check your GIST_TOKEN
- Queue not found: Verify the queue name or ID
- Message not found: Verify the message ID
- API rate limiting: Wait and retry
- Network issues: Check your internet connection

## Troubleshooting

### Authentication Issues

```bash
# Verify your token
gistqueue init
```

### Queue Operations

```bash
# Check if a queue exists
gistqueue list-queues

# Get detailed information about a queue
gistqueue get-queue [queue_name]
```

### Message Operations

```bash
# Check message status
gistqueue list-messages [queue_name] --status [status]
```

## Best Practices

1. Use descriptive queue names for different types of messages
2. Implement proper error handling in your scripts
3. Regularly clean up completed messages
4. Use the automatic cleanup thread for long-running applications
5. Set appropriate retry counts and delays for your use case
6. Use JSON for structured message content
7. Store the GitHub token securely as an environment variable

## Advanced Usage

### Custom Queue Files

By default, GistQueue creates queue files with names like `[queue_name]_queue.json`. You can customize this by setting the `DEFAULT_FILE_EXTENSION` environment variable.

### Concurrency Control

GistQueue implements atomic operations and conflict resolution to handle concurrent access to queues. The `get-next-message` and `update-message` operations are designed to be thread-safe.

### Process Identification

Each message in progress includes a process identifier to track which process is handling it. This helps with debugging and conflict resolution.

## Limitations

- GitHub API rate limits apply
- Maximum Gist file size is 100 MB
- Not recommended for high-throughput applications
- Network latency affects performance

## Support

For issues and feature requests, please open an issue on the GitHub repository.
