@echo off
echo ============================================
echo    SETTING UP GIT + GITHUB REPO
echo ============================================
echo.

:: Check if Git is installed
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Git is not installed!
    echo Please install Git first.
    pause
    exit /b 1
)

echo [OK] Git found:
git --version
echo.

:: Configure Git user
echo Setting up your Git identity...
git config --global user.name "kishoresbk247"
git config --global user.email "kishoresbk247@users.noreply.github.com"
echo [OK] Git user configured as: kishoresbk247
echo.

:: Initialize repo
echo Initializing Git repository...
git init
git branch -M main
echo [OK] Repository initialized with 'main' branch
echo.

:: Add remote
echo Connecting to GitHub...
git remote add origin https://github.com/kishoresbk247/project-codude.git 2>nul
if %errorlevel% neq 0 (
    echo [INFO] Remote 'origin' already exists. Updating...
    git remote set-url origin https://github.com/kishoresbk247/project-codude.git
)
echo [OK] Remote set to: https://github.com/kishoresbk247/project-codude.git
echo.

:: Make first commit
echo Making initial commit...
git add .
git commit -m "Day 1: Project setup - CoDude initialized"
echo.

:: Push
echo Pushing to GitHub...
echo.
echo =============================================
echo  IMPORTANT: If this is your first push, a
echo  browser window will open for GitHub login.
echo  Sign in with your GitHub account.
echo =============================================
echo.
git push -u origin main
echo.

if %errorlevel%==0 (
    echo ============================================
    echo  SUCCESS! Your project is now on GitHub!
    echo  https://github.com/kishoresbk247/project-codude
    echo ============================================
) else (
    echo ============================================
    echo  PUSH FAILED - See troubleshooting:
    echo.
    echo  Make sure the repo exists on GitHub:
    echo  https://github.com/kishoresbk247/project-codude
    echo.
    echo  Try pushing again:
    echo     git push -u origin main
    echo ============================================
)
echo.
pause
