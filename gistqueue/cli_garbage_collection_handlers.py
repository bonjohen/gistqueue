"""
Garbage collection handler functions for the GistQueue CLI.
"""
import json
from tabulate import tabulate
from gistqueue.main import check_environment, initialize_client, initialize_garbage_collector

def handle_cleanup_all_queues(args):
    """
    Handle the 'cleanup-all-queues' command.
    
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
    
    garbage_collector = initialize_garbage_collector(client)
    if not garbage_collector:
        print("ERROR: Failed to initialize garbage collector.")
        return 1
    
    results = garbage_collector.cleanup_all_queues()
    
    if not results:
        print("No queues found or all cleanup operations failed.")
        return 1
    
    if args.format == "json":
        print(json.dumps(results, indent=2))
    else:  # table format
        headers = ["Queue", "Messages Deleted"]
        table_data = [
            [queue_name, deleted_count]
            for queue_name, deleted_count in results.items()
        ]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    total_deleted = sum(count for count in results.values() if count > 0)
    print(f"Total messages deleted: {total_deleted}")
    
    return 0

def handle_start_cleanup_thread(args):
    """
    Handle the 'start-cleanup-thread' command.
    
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
    
    garbage_collector = initialize_garbage_collector(client)
    if not garbage_collector:
        print("ERROR: Failed to initialize garbage collector.")
        return 1
    
    if garbage_collector.start_cleanup_thread():
        print(f"Cleanup thread started. Cleanup interval: {garbage_collector.cleanup_interval_seconds} seconds")
        print("The thread will run in the background as long as the process is running.")
        print("Use 'stop-cleanup-thread' to stop the thread.")
        return 0
    else:
        print("ERROR: Failed to start cleanup thread.")
        return 1

def handle_stop_cleanup_thread(args):
    """
    Handle the 'stop-cleanup-thread' command.
    
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
    
    garbage_collector = initialize_garbage_collector(client)
    if not garbage_collector:
        print("ERROR: Failed to initialize garbage collector.")
        return 1
    
    if garbage_collector.stop_cleanup_thread(args.timeout):
        print("Cleanup thread stopped.")
        return 0
    else:
        print(f"ERROR: Failed to stop cleanup thread within {args.timeout} seconds.")
        return 1
