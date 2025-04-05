@echo off
echo ===== GistQueue Operations Script =====

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
echo ===== Listing all queues =====
gistqueue list-queues
set LIST_RESULT=%ERRORLEVEL%
if %LIST_RESULT% neq 0 (
    echo WARNING: Failed to list queues.
    echo Command exited with code: %LIST_RESULT%
) else (
    echo Successfully listed queues.
    echo Command exited with code: %LIST_RESULT%
)

echo.
echo ===== Creating a queue named 'john' =====
gistqueue create-queue john
set CREATE_RESULT=%ERRORLEVEL%
if %CREATE_RESULT% neq 0 (
    echo WARNING: Failed to create queue 'john'. This may be normal if the queue already exists.
    echo Command exited with code: %CREATE_RESULT%
) else (
    echo Queue 'john' created successfully.
    echo Command exited with code: %CREATE_RESULT%
)

echo.
echo ===== Listing all queues again =====
gistqueue list-queues
set LIST2_RESULT=%ERRORLEVEL%
if %LIST2_RESULT% neq 0 (
    echo WARNING: Failed to list queues.
    echo Command exited with code: %LIST2_RESULT%
) else (
    echo Successfully listed queues.
    echo Command exited with code: %LIST2_RESULT%
)

echo.
echo ===== Getting information about queue 'john' =====
gistqueue get-queue john
set INFO_RESULT=%ERRORLEVEL%
if %INFO_RESULT% neq 0 (
    echo WARNING: Failed to get information about queue 'john'. This may be normal if the queue doesn't exist.
    echo Command exited with code: %INFO_RESULT%
) else (
    echo Successfully retrieved information about queue 'john'.
    echo Command exited with code: %INFO_RESULT%
)

echo.
echo ===== Script completed =====
echo Summary:
echo - First list operation: %LIST_RESULT% (0=success)
echo - Create queue operation: %CREATE_RESULT% (0=success, 1=may already exist)
echo - Second list operation: %LIST2_RESULT% (0=success)
echo - Get queue info operation: %INFO_RESULT% (0=success, 1=may not exist)

echo.
echo NOTE: Non-zero exit codes may be normal if the queue already exists or doesn't exist.

REM Deactivate virtual environment
call deactivate