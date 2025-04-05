@REM echo off
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

REM Check for GitHub token
if "%GIST_TOKEN%"=="" (
    echo WARNING: GIST_TOKEN environment variable is not set
    echo Setting up a temporary token for this session...
    
    set /p GIST_TOKEN=Enter your GitHub token with gist scope: 
    if "%GIST_TOKEN%"=="" (
        echo ERROR: GitHub token is required
        exit /b 1
    )
)

echo.
echo ===== Environment setup complete =====
echo.

REM Initialize GistQueue
echo ===== Initializing GistQueue =====
gistqueue init
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to initialize GistQueue
    exit /b 1
)

echo.
echo ===== Listing all queues =====
gistqueue list-queues
set LIST_RESULT=%ERRORLEVEL%
echo Command exited with code: %LIST_RESULT%

echo.
echo ===== Creating a queue named 'john' =====
gistqueue create-queue john
set CREATE_RESULT=%ERRORLEVEL%
echo Command exited with code: %CREATE_RESULT%

echo.
echo ===== Listing all queues again =====
gistqueue list-queues
set LIST2_RESULT=%ERRORLEVEL%
echo Command exited with code: %LIST2_RESULT%

echo.
echo ===== Getting information about queue 'john' =====
gistqueue get-queue john
set INFO_RESULT=%ERRORLEVEL%
echo Command exited with code: %INFO_RESULT%

echo.
echo ===== Script completed =====
echo Summary:
echo - First list operation: %LIST_RESULT%
echo - Create queue operation: %CREATE_RESULT%
echo - Second list operation: %LIST2_RESULT%
echo - Get queue info operation: %INFO_RESULT%

REM Deactivate virtual environment
call deactivate