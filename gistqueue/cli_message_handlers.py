"""
Message operation handler functions for the GistQueue CLI.
"""
import json
from tabulate import tabulate
from gistqueue.main import check_environment, initialize_client
from gistqueue.queue import QueueManager
from gistqueue.message import MessageManager, MessageStatus

def handle_create_message(args):
    """
    Handle the 'create-message' command.
    
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
    message_manager = MessageManager(queue_manager)
    
    message = message_manager.create_message(args.queue, args.content)
    
    if message:
        print(f"Message created with ID: {message['id']}")
        return 0
    else:
        return 1

def handle_list_messages(args):
    """
    Handle the 'list-messages' command.
    
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
    message_manager = MessageManager(queue_manager)
    
    messages = message_manager.list_messages(args.queue, args.status)
    
    if messages is None:
        return 1
    
    if not messages:
        print("No messages found.")
        return 0
    
    if args.format == "json":
        print(json.dumps(messages, indent=2))
    else:  # table format
        headers = ["ID", "Status", "Status Datetime", "Process", "Content"]
        table_data = [
            [
                msg.get("id", ""),
                msg.get("status", ""),
                msg.get("status_datetime", ""),
                msg.get("process", ""),
                str(msg.get("content", ""))[:50] + ("..." if len(str(msg.get("content", ""))) > 50 else "")
            ]
            for msg in messages
        ]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    return 0

def handle_get_next_message(args):
    """
    Handle the 'get-next-message' command.
    
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
    message_manager = MessageManager(queue_manager)
    
    message = message_manager.get_next_message(args.queue)
    
    if message is None:
        return 1
    
    if args.format == "json":
        print(json.dumps(message, indent=2))
    else:  # table format
        for key, value in message.items():
            print(f"{key.replace('_', ' ').title()}: {value}")
    
    return 0

def handle_update_message(args):
    """
    Handle the 'update-message' command.
    
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
    message_manager = MessageManager(queue_manager)
    
    message = message_manager.update_message(args.queue, args.message_id, args.content, args.status)
    
    if message is None:
        return 1
    
    if args.format == "json":
        print(json.dumps(message, indent=2))
    else:  # table format
        for key, value in message.items():
            print(f"{key.replace('_', ' ').title()}: {value}")
    
    return 0

def handle_delete_completed_messages(args):
    """
    Handle the 'delete-completed-messages' command.
    
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
    message_manager = MessageManager(queue_manager)
    
    deleted_count = message_manager.delete_completed_messages(args.queue)
    
    if deleted_count is None:
        return 1
    
    print(f"Deleted {deleted_count} completed messages.")
    return 0
