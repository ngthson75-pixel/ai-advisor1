@echo off
REM ============================================================================
REM DAILY SCANNER - WINDOWS TASK SCHEDULER
REM Run daily at 3:45 PM to generate trading signals
REM ============================================================================

echo ======================================================================
echo AI ADVISOR - DAILY SCANNER
echo ======================================================================
echo Start Time: %date% %time%
echo.

REM Change to scripts directory
cd /d C:\ai-advisor1\scripts

REM Activate virtual environment if exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Run scanner
echo Running scanner...
python run_daily_scanner.py

REM Check exit code
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ======================================================================
    echo SUCCESS - Signals generated!
    echo ======================================================================
) else (
    echo.
    echo ======================================================================
    echo ERROR - Scanner failed with code %ERRORLEVEL%
    echo ======================================================================
)

echo.
echo End Time: %date% %time%
echo ======================================================================

REM Keep window open if run manually (optional)
REM pause

REM Auto-close after 5 seconds if scheduled
timeout /t 5
