@echo off
setlocal enabledelayedexpansion
echo ===== GistQueue Comprehensive Demo Script =====

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
echo ===== Initializing GistQueue =====
gistqueue init
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to initialize GistQueue. Please ensure GIST_TOKEN is set in system environment variables.
    exit /b 1
)

echo.
echo ===== STEP 1: Listing all queues (BEFORE) =====
echo This shows the current queues before we create our example queue
gistqueue list-queues
echo.

echo ===== STEP 2: Creating a queue named 'test_queue_example' =====
gistqueue create-queue test_queue_example
if %ERRORLEVEL% neq 0 (
    echo WARNING: Failed to create queue 'test_queue_example'. This may be normal if the queue already exists.
) else (
    echo Queue 'test_queue_example' created successfully.
)
echo.

echo ===== STEP 3: Listing all queues (AFTER) =====
echo This shows the queues after creating our example queue
gistqueue list-queues
echo.

echo ===== STEP 4: Getting information about queue 'test_queue_example' =====
gistqueue get-queue test_queue_example
if %ERRORLEVEL% neq 0 (
    echo WARNING: Failed to get information about queue 'test_queue_example'.
    exit /b 1
)
echo.

echo ===== STEP 5: Demonstrating queue operations =====
echo This script has demonstrated the following operations:
echo - Initializing the environment
echo - Creating a queue
echo - Listing queues
echo - Getting queue information
echo.
echo For more advanced operations like message handling, please refer to the USAGE.md document.
echo.

echo ===== Demo completed successfully =====
echo.
echo This script demonstrated the following GistQueue operations:
echo 1. Initializing the environment
echo 2. Creating a queue
echo 3. Listing queues
echo 4. Getting queue information
echo.
echo For more details, see the USAGE.md document.

REM Deactivate virtual environment
call deactivate

endlocal
