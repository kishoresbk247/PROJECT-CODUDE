@echo off
echo ============================================
echo    DAILY PUSH - CoDude Project
echo ============================================
echo.

:: Check if Git is installed
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Git is not installed!
    pause
    exit /b 1
)

:: Show what changed
echo Files changed since last commit:
echo ---------------------------------
git status --short
echo ---------------------------------
echo.

:: Ask for commit message
set /p DAY_NUM="Enter the Day number (1-21): "
set /p COMMIT_MSG="What did you build today? : "
echo.

:: Stage all changes
echo Staging all changes...
git add .
echo [OK] All files staged
echo.

:: Commit
echo Committing...
git commit -m "Day %DAY_NUM%: %COMMIT_MSG%"
echo.

:: Push
echo Pushing to GitHub...
git push origin main
echo.

if %errorlevel%==0 (
    echo ============================================
    echo  PUSHED SUCCESSFULLY!
    echo  Day %DAY_NUM% commit is now on GitHub.
    echo  https://github.com/kishoresbk247/project-codude
    echo ============================================
) else (
    echo ============================================
    echo  PUSH FAILED! Try these:
    echo  1. Check internet connection
    echo  2. Run: git push origin main
    echo ============================================
)
echo.
pause
