@echo off
REM ============================================================================
REM AI ADVISOR - PREPARE FILES FOR CLAUDE PROJECT
REM ============================================================================

color 0E
cls

echo.
echo ============================================================================
echo    AI ADVISOR - CLAUDE PROJECT PREPARATION
echo ============================================================================
echo.
echo This script will:
echo   1. Create "Claude-Project-Upload" folder
echo   2. Copy 20 most important files
echo   3. Ready for upload to Claude Project in 1 folder!
echo.
echo ============================================================================
echo.

pause

echo.
echo [1/2] Creating upload folder...
echo.

REM Create upload folder
mkdir "Claude-Project-Upload" 2>nul
cd "Claude-Project-Upload"

echo [OK] Folder created!
echo.

echo [2/2] Copying essential files...
echo.

REM ============================================================================
REM MASTER INDEX (MUST HAVE!)
REM ============================================================================
echo Copying: MASTER_INDEX.md
copy "..\MASTER_INDEX.md" . >nul 2>&1

REM ============================================================================
REM BACKEND FILES
REM ============================================================================
echo Copying: Backend files...
copy "..\backend\admin_api.py" . >nul 2>&1
copy "..\backend\admin_api_simple.py" . >nul 2>&1
copy "..\backend\telegram_notifier.py" . >nul 2>&1
copy "..\backend\.env.example" . >nul 2>&1
copy "..\backend\requirements.txt" . >nul 2>&1
copy "..\backend\Procfile" . >nul 2>&1
copy "..\backend\HEROKU_DEPLOYMENT_GUIDE.md" . >nul 2>&1

REM ============================================================================
REM FRONTEND FILES
REM ============================================================================
echo Copying: Frontend files...
copy "..\admin\AdminSignalDashboard.jsx" . >nul 2>&1
copy "..\admin\AdminSignalDashboard.css" . >nul 2>&1

REM ============================================================================
REM NOTIFICATION FILES
REM ============================================================================
echo Copying: Notification guides...
copy "..\TELEGRAM_SETUP_GUIDE.md" . >nul 2>&1

REM ============================================================================
REM STRATEGY FILES
REM ============================================================================
echo Copying: Strategy docs...
copy "..\FINAL_STRATEGY_COMPARISON.md" . >nul 2>&1
copy "..\BREAKOUT_STRATEGY.md" . >nul 2>&1
copy "..\STRATEGY_2_BREAKOUT_CONFIRMATION.md" . >nul 2>&1
copy "..\STRATEGY_3_TREND_PULLBACK.md" . >nul 2>&1

REM ============================================================================
REM BACKTEST FILES
REM ============================================================================
echo Copying: Backtest files...
copy "..\OFFLINE_BACKTEST_GUIDE.md" . >nul 2>&1
copy "..\BACKTEST_COMPLETE_SUMMARY.md" . >nul 2>&1

REM ============================================================================
REM DEPLOYMENT FILES
REM ============================================================================
echo Copying: Deployment guides...
copy "..\DEPLOYMENT_GUIDE.md" . >nul 2>&1
copy "..\QUICKSTART.md" . >nul 2>&1

REM ============================================================================
REM DOCUMENTATION
REM ============================================================================
echo Copying: README...
copy "..\README.md" . >nul 2>&1

echo.
echo [OK] Files copied!
echo.

REM Count files
set count=0
for %%f in (*.*) do set /a count+=1

echo.
echo ============================================================================
echo    PREPARATION COMPLETE!
echo ============================================================================
echo.
echo Files ready: %count%
echo Location: %cd%
echo.
echo ============================================================================
echo    NEXT STEPS:
echo ============================================================================
echo.
echo 1. Open Claude.ai (web or app)
echo.
echo 2. Click "Projects" in left sidebar
echo.
echo 3. Click "+ New Project"
echo.
echo 4. Name: "AI Advisor - Full Stack"
echo    Description: "Complete AI trading advisor system"
echo.
echo 5. Click "Add content" or drag files
echo.
echo 6. Select ALL files in this folder:
echo    %cd%
echo.
echo 7. Upload (may take 1-2 minutes for 20 files)
echo.
echo 8. Done! Start chatting in the project!
echo.
echo ============================================================================
echo    TIPS:
echo ============================================================================
echo.
echo - Upload MASTER_INDEX.md first (most important!)
echo - Other files in any order
echo - Can upload more files later if needed
echo - Use [BACKEND], [FRONTEND] prefixes in messages
echo.
echo ============================================================================
echo.

pause

REM Open folder
explorer .

echo.
echo Folder opened! Ready to upload to Claude Project!
echo.
pause
