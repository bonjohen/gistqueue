# GistQueue

A message queue system using GitHub Gists as the storage backend.

## Overview

GistQueue is a Python library that implements a simple message queue system using GitHub Gists for storage. It allows you to:

- Create and manage message queues as GitHub Gists
- Add, retrieve, update, and delete messages in the queues
- Handle concurrent access with conflict detection and resolution
- Automatically clean up processed messages

## Requirements

- Python 3.8 or higher
- A GitHub account
- A GitHub personal access token with the `gist` scope

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/example/gistqueue.git
   cd gistqueue
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv_gistqueue
   .\venv_gistqueue\Scripts\activate  # Windows
   source venv_gistqueue/bin/activate  # Linux/macOS
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up your GitHub token:
   - Create a GitHub personal access token with the `gist` scope at https://github.com/settings/tokens
   - Set the token as an environment variable:
     ```
     # Windows
     set GIST_TOKEN=your_github_token_here

     # Linux/macOS
     export GIST_TOKEN=your_github_token_here
     ```
   - Alternatively, create a `.env` file in the project root (copy from `.env.example`):
     ```
     GIST_TOKEN=your_github_token_here
     ```

5. Install the package in development mode:
   ```
   pip install -e .
   ```

## Usage

### Command Line Interface

GistQueue provides a command-line interface for common operations:

```
# Initialize and test your environment
gistqueue init

# Create a new queue
gistqueue create-queue orders

# List available queues
gistqueue list-queues
```

### Python API

```python
from gistqueue.github_client import GistClient

# Initialize the client
client = GistClient()

# Create a new queue
gist = client.create_gist(
    description="Queue: Orders",
    filename="orders_queue.json",
    content="[]"
)

# Get the queue content
content = client.get_gist_content(gist, "orders_queue.json")
queue_data = client.parse_json_content(content)
```

## Development

### Running Tests

```
pytest
```

### Building the Package

```
pip install build
python -m build
```
