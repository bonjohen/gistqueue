"""
Command-line interface for GistQueue.

This module provides a command-line interface for interacting with the GistQueue application.
"""
import argparse
import sys
import json
from tabulate import tabulate
from gistqueue.main import check_environment, initialize_client, initialize_garbage_collector
from gistqueue.queue import QueueManager
from gistqueue.message import MessageManager, MessageStatus
from gistqueue.concurrency import ConcurrencyManager
from gistqueue.garbage_collection import GarbageCollector
from gistqueue.cli_message_handlers import (
    handle_create_message,
    handle_list_messages,
    handle_get_next_message,
    handle_update_message,
    handle_delete_completed_messages
)
from gistqueue.cli_garbage_collection_handlers import (
    handle_cleanup_all_queues,
    handle_start_cleanup_thread,
    handle_stop_cleanup_thread
)

def create_parser():
    """
    Create the command-line argument parser.

    Returns:
        argparse.ArgumentParser: The configured argument parser.
    """
    parser = argparse.ArgumentParser(
        description="GistQueue - A message queue system using GitHub Gists",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Add global options
    parser.add_argument(
        "--version", action="store_true",
        help="Show version information and exit"
    )

    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # 'init' command
    init_parser = subparsers.add_parser(
        "init", help="Initialize and test the GistQueue environment"
    )

    # 'create-queue' command
    create_queue_parser = subparsers.add_parser(
        "create-queue", help="Create a new message queue"
    )
    create_queue_parser.add_argument(
        "name", nargs="?", default=None,
        help="Name of the queue to create (default: use the default queue name)"
    )
    create_queue_parser.add_argument(
        "--public", action="store_true",
        help="Make the queue public (default: private)"
    )

    # 'list-queues' command
    list_queues_parser = subparsers.add_parser(
        "list-queues", help="List all available queues"
    )
    list_queues_parser.add_argument(
        "--format", choices=["table", "json"], default="table",
        help="Output format (default: table)"
    )

    # 'get-queue' command
    get_queue_parser = subparsers.add_parser(
        "get-queue", help="Get information about a queue"
    )
    get_queue_parser.add_argument(
        "name", nargs="?", default=None,
        help="Name of the queue (default: use the default queue name)"
    )
    get_queue_parser.add_argument(
        "--id", dest="gist_id",
        help="Gist ID of the queue (alternative to name)"
    )
    get_queue_parser.add_argument(
        "--format", choices=["table", "json"], default="table",
        help="Output format (default: table)"
    )

    # 'create-message' command
    create_message_parser = subparsers.add_parser(
        "create-message", help="Create a new message in a queue"
    )
    create_message_parser.add_argument(
        "queue", help="Name or ID of the queue"
    )
    create_message_parser.add_argument(
        "content", help="Content of the message"
    )

    # 'list-messages' command
    list_messages_parser = subparsers.add_parser(
        "list-messages", help="List messages in a queue"
    )
    list_messages_parser.add_argument(
        "queue", help="Name or ID of the queue"
    )
    list_messages_parser.add_argument(
        "--status", choices=["pending", "in_progress", "complete", "failed"],
        help="Filter messages by status"
    )
    list_messages_parser.add_argument(
        "--format", choices=["table", "json"], default="table",
        help="Output format (default: table)"
    )

    # 'get-next-message' command
    get_next_message_parser = subparsers.add_parser(
        "get-next-message", help="Get the next pending message from a queue and mark it as in progress"
    )
    get_next_message_parser.add_argument(
        "queue", help="Name or ID of the queue"
    )
    get_next_message_parser.add_argument(
        "--format", choices=["table", "json"], default="table",
        help="Output format (default: table)"
    )

    # 'update-message' command
    update_message_parser = subparsers.add_parser(
        "update-message", help="Update a message in a queue"
    )
    update_message_parser.add_argument(
        "queue", help="Name or ID of the queue"
    )
    update_message_parser.add_argument(
        "message_id", help="ID of the message to update"
    )
    update_message_parser.add_argument(
        "--content", help="New content of the message"
    )
    update_message_parser.add_argument(
        "--status", choices=["pending", "in_progress", "complete", "failed"],
        help="New status of the message"
    )
    update_message_parser.add_argument(
        "--format", choices=["table", "json"], default="table",
        help="Output format (default: table)"
    )

    # 'delete-completed-messages' command
    delete_completed_messages_parser = subparsers.add_parser(
        "delete-completed-messages", help="Delete completed messages that are older than the cleanup threshold"
    )
    delete_completed_messages_parser.add_argument(
        "queue", help="Name or ID of the queue"
    )

    # 'cleanup-all-queues' command
    cleanup_all_queues_parser = subparsers.add_parser(
        "cleanup-all-queues", help="Clean up completed messages in all queues"
    )
    cleanup_all_queues_parser.add_argument(
        "--format", choices=["table", "json"], default="table",
        help="Output format (default: table)"
    )

    # 'start-cleanup-thread' command
    start_cleanup_thread_parser = subparsers.add_parser(
        "start-cleanup-thread", help="Start the automatic cleanup thread"
    )

    # 'stop-cleanup-thread' command
    stop_cleanup_thread_parser = subparsers.add_parser(
        "stop-cleanup-thread", help="Stop the automatic cleanup thread"
    )
    stop_cleanup_thread_parser.add_argument(
        "--timeout", type=float, default=5.0,
        help="Maximum time to wait for the thread to stop, in seconds (default: 5.0)"
    )

    return parser

def handle_init():
    """
    Handle the 'init' command.

    Returns:
        int: Exit code (0 for success, non-zero for failure).
    """
    if not check_environment():
        return 1

    client = initialize_client()
    if not client:
        return 1

    print("GistQueue environment is properly configured.")
    return 0

def handle_create_queue(args):
    """
    Handle the 'create-queue' command.

    Args:
        args: Command-line arguments.

    Returns:
        int: Exit code (0 for success, non-zero for failure).
    """
    if not check_environment():
        return 1

    client = initialize_client()
    if not client:
        return 1

    queue_manager = QueueManager(client)
    gist = queue_manager.create_queue(args.name, args.public)

    if gist:
        print(f"Queue URL: {gist.html_url}")
        return 0
    else:
        return 1

def handle_list_queues(args):
    """
    Handle the 'list-queues' command.

    Args:
        args: Command-line arguments.

    Returns:
        int: Exit code (0 for success, non-zero for failure).
    """
    if not check_environment():
        return 1

    client = initialize_client()
    if not client:
        return 1

    queue_manager = QueueManager(client)
    queues = queue_manager.list_queues()

    if not queues:
        print("No queues found.")
        return 0

    if args.format == "json":
        print(json.dumps(queues, indent=2))
    else:  # table format
        headers = ["ID", "Name", "URL", "Created", "Updated"]
        table_data = [
            [q["id"], q["name"], q["url"], q["created_at"], q["updated_at"]]
            for q in queues
        ]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))

    return 0

def handle_get_queue(args):
    """
    Handle the 'get-queue' command.

    Args:
        args: Command-line arguments.

    Returns:
        int: Exit code (0 for success, non-zero for failure).
    """
    if not check_environment():
        return 1

    client = initialize_client()
    if not client:
        return 1

    queue_manager = QueueManager(client)

    gist = None
    if args.gist_id:
        gist = queue_manager.get_queue_by_id(args.gist_id)
    else:
        gist = queue_manager.get_queue(args.name)

    if not gist:
        print("Queue not found.")
        return 1

    # Get queue information
    queue_name = args.name or queue_manager.default_queue
    filename = queue_manager._get_queue_filename(queue_name)
    content = queue_manager.get_queue_content(gist, queue_name)

    queue_info = {
        "id": gist.id,
        "name": queue_name,
        "description": gist.description,
        "url": gist.html_url,
        "created_at": gist.created_at.isoformat(),
        "updated_at": gist.updated_at.isoformat(),
        "filename": filename,
        "message_count": len(content) if content else 0
    }

    if args.format == "json":
        print(json.dumps(queue_info, indent=2))
    else:  # table format
        for key, value in queue_info.items():
            print(f"{key.replace('_', ' ').title()}: {value}")

    return 0

def main():
    """
    Main entry point for the CLI.

    Returns:
        int: Exit code (0 for success, non-zero for failure).
    """
    parser = create_parser()
    args = parser.parse_args()

    # Handle version flag
    if args.version:
        from gistqueue import __version__
        print(f"GistQueue version {__version__}")
        return 0

    # Handle commands
    if args.command == "init":
        return handle_init()
    elif args.command == "create-queue":
        return handle_create_queue(args)
    elif args.command == "list-queues":
        return handle_list_queues(args)
    elif args.command == "get-queue":
        return handle_get_queue(args)
    elif args.command == "create-message":
        return handle_create_message(args)
    elif args.command == "list-messages":
        return handle_list_messages(args)
    elif args.command == "get-next-message":
        return handle_get_next_message(args)
    elif args.command == "update-message":
        return handle_update_message(args)
    elif args.command == "delete-completed-messages":
        return handle_delete_completed_messages(args)
    elif args.command == "cleanup-all-queues":
        return handle_cleanup_all_queues(args)
    elif args.command == "start-cleanup-thread":
        return handle_start_cleanup_thread(args)
    elif args.command == "stop-cleanup-thread":
        return handle_stop_cleanup_thread(args)
    elif not args.command:
        parser.print_help()
        return 0
    else:
        print(f"Command '{args.command}' not yet implemented.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
