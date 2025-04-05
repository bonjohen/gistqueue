@echo off
echo Checking for GIST_TOKEN environment variable...

if "%GIST_TOKEN%"=="" (
    echo GIST_TOKEN is NOT set in this environment
) else (
    echo GIST_TOKEN is set in this environment
    echo Token starts with: %GIST_TOKEN:~0,4%***
)

pause
