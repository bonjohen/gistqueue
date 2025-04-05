"""
Command-line interface for GistQueue.

This module provides a command-line interface for interacting with the GistQueue application.
"""
import argparse
import sys
from gistqueue.main import check_environment, initialize_client

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
        "name", help="Name of the queue to create"
    )
    
    # 'list-queues' command
    list_queues_parser = subparsers.add_parser(
        "list-queues", help="List all available queues"
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
    elif not args.command:
        parser.print_help()
        return 0
    else:
        print(f"Command '{args.command}' not yet implemented.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
