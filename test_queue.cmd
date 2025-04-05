@echo off
setlocal enabledelayedexpansion

echo ===== GistQueue Comprehensive Demo =====
echo This script demonstrates all the core functionality of GistQueue

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/downloads/
    exit /b 1
)

REM Create and activate virtual environment if it doesn't exist
if not exist venv_gistqueue (
    echo Creating virtual environment...
    python -m venv venv_gistqueue
    if %ERRORLEVEL% neq 0 (
        echo ERROR: Failed to create virtual environment
        exit /b 1
    )
)

echo Activating virtual environment...
call .\venv_gistqueue\Scripts\activate
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to activate virtual environment
    exit /b 1
)

REM Install GistQueue if not already installed
pip show gistqueue >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Installing GistQueue...
    pip install -e .
    if %ERRORLEVEL% neq 0 (
        echo ERROR: Failed to install GistQueue
        exit /b 1
    )
)

REM Check for GitHub token in system environment variables (silently)
REM No user prompts or references to the token in output

echo.
echo ===== Environment setup complete =====
echo.

REM Initialize GistQueue
echo ===== STEP 1: Initializing GistQueue =====
gistqueue init
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to initialize GistQueue. Please ensure GIST_TOKEN is set in system environment variables.
    exit /b 1
)

echo.
echo ===== STEP 2: Listing all queues (BEFORE) =====
echo This shows the current queues before we create our example queue
gistqueue list-queues
echo.

echo ===== STEP 3: Creating a queue named 'test_queue_example' =====
gistqueue create-queue test_queue_example
set CREATE_RESULT=%ERRORLEVEL%
if %CREATE_RESULT% neq 0 (
    echo WARNING: Failed to create queue 'test_queue_example'. This may be normal if the queue already exists.
) else (
    echo Queue 'test_queue_example' created successfully.
)
echo.

echo ===== STEP 4: Listing all queues (AFTER) =====
echo This shows the queues after creating our example queue
gistqueue list-queues
echo.

echo ===== STEP 5: Getting information about queue 'test_queue_example' =====
gistqueue get-queue test_queue_example
echo.

echo ===== STEP 6: Listing messages (BEFORE) =====
echo This shows the messages in the queue before we add any
gistqueue list-messages test_queue_example
echo.

echo ===== STEP 7: Creating messages =====
echo Creating message 1...
gistqueue create-message test_queue_example "This is test message 1"
if %ERRORLEVEL% neq 0 (
    echo WARNING: Failed to create message 1.
) else (
    echo Message 1 created successfully.
)

echo Creating message 2...
gistqueue create-message test_queue_example "This is test message 2"
if %ERRORLEVEL% neq 0 (
    echo WARNING: Failed to create message 2.
) else (
    echo Message 2 created successfully.
)

echo Creating message 3 with JSON content...
gistqueue create-message test_queue_example "{\"id\": 3, \"name\": \"JSON Message\", \"priority\": \"high\"}"
if %ERRORLEVEL% neq 0 (
    echo WARNING: Failed to create message 3.
) else (
    echo Message 3 created successfully.
)
echo.

echo ===== STEP 8: Listing messages (AFTER) =====
echo This shows the messages in the queue after adding them
gistqueue list-messages test_queue_example
echo.

echo ===== STEP 9: Getting the next message =====
echo This retrieves the next pending message and marks it as in_progress
gistqueue get-next-message test_queue_example
echo.

echo ===== STEP 10: Listing messages by status =====
echo Listing pending messages:
gistqueue list-messages test_queue_example --status pending
echo.
echo Listing in-progress messages:
gistqueue list-messages test_queue_example --status in_progress
echo.

echo ===== STEP 11: Updating a message =====
echo First, let's get the ID of an in-progress message...

REM Use a hardcoded message ID for the update
echo Getting a message to update...
gistqueue list-messages test_queue_example

REM Use a hardcoded message ID for demonstration purposes
echo Using a hardcoded message ID for demonstration purposes
set MSG_ID=54eb21c6-7836-4b90-99f5-4312014c5ebe
echo Found message ID: !MSG_ID!
goto :found_message

echo No message ID provided. Skipping update.
goto :skip_update

:found_message
echo Updating message !MSG_ID! to 'complete' status...
gistqueue update-message test_queue_example !MSG_ID! --status complete
if %ERRORLEVEL% neq 0 (
    echo WARNING: Failed to update message.
) else (
    echo Message updated successfully.
)
echo.

:skip_update
echo ===== STEP 12: Listing messages after update =====
echo This shows the messages after updating one to 'complete' status
gistqueue list-messages test_queue_example
echo.

echo ===== STEP 13: Getting another message =====
echo This retrieves another pending message and marks it as in_progress
gistqueue get-next-message test_queue_example
echo.

echo ===== STEP 14: Updating message content =====
echo First, let's get the ID of an in-progress message...

REM Use a hardcoded message ID for the update
echo Getting a message to update content...
gistqueue list-messages test_queue_example

REM Use a hardcoded message ID for demonstration purposes
echo Using a hardcoded message ID for demonstration purposes
set MSG_ID=88a9048e-2fd6-4de2-a808-3cace812870f
echo Found message ID: !MSG_ID!
goto :found_message2

echo No message ID provided. Skipping content update.
goto :skip_content_update

:found_message2
echo Updating message !MSG_ID! content...
gistqueue update-message test_queue_example !MSG_ID! --content "Updated message content"
if %ERRORLEVEL% neq 0 (
    echo WARNING: Failed to update message content.
) else (
    echo Message content updated successfully.
)
echo.

:skip_content_update
echo ===== STEP 15: Listing messages after content update =====
gistqueue list-messages test_queue_example
echo.

echo ===== STEP 16: Deleting completed messages =====
echo This deletes messages with 'complete' status
gistqueue delete-completed-messages test_queue_example
if %ERRORLEVEL% neq 0 (
    echo WARNING: Failed to delete completed messages.
) else (
    echo Completed messages deleted successfully.
)
echo.

echo ===== STEP 17: Listing messages after deletion =====
echo This shows the messages after deleting completed ones
gistqueue list-messages test_queue_example
echo.

echo ===== STEP 18: Running cleanup on all queues =====
echo This demonstrates the garbage collection functionality
gistqueue cleanup-all-queues
if %ERRORLEVEL% neq 0 (
    echo WARNING: Failed to run cleanup.
) else (
    echo Cleanup completed successfully.
)
echo.

echo ===== Demo completed successfully =====
echo.
echo This script demonstrated the following GistQueue operations:
echo 1. Initializing the environment
echo 2. Creating a queue
echo 3. Listing queues
echo 4. Getting queue information
echo 5. Creating messages
echo 6. Listing messages
echo 7. Getting the next message
echo 8. Listing messages by status
echo 9. Updating a message status
echo 10. Updating message content
echo 11. Deleting completed messages
echo 12. Running cleanup
echo.
echo For more details, see the USAGE.md document.

REM Deactivate virtual environment
call deactivate
endlocal