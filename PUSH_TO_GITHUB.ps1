# Scholar's Terminal - Push to GitHub Script
# This script will commit your changes and push to GitHub

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  Scholar's Terminal - GitHub Push" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check current status
Write-Host "[Step 1/5] Checking git status..." -ForegroundColor Yellow
git status

Write-Host ""
Write-Host "Press any key to continue with commit..." -ForegroundColor Green
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Step 2: Add all files
Write-Host ""
Write-Host "[Step 2/5] Adding all files..." -ForegroundColor Yellow
git add .

# Step 3: Commit
Write-Host ""
Write-Host "[Step 3/5] Creating commit..." -ForegroundColor Yellow
git commit -m "chore: Prepare for initial GitHub release

- Updated requirements.txt with complete dependencies
- Made paths configurable via environment variables  
- Added .env.example for configuration reference
- Updated LICENSE to Scholar's Terminal
- Created setup.py for Python packaging
- Added CONTRIBUTING.md for contributors
- Removed all hardcoded absolute paths
- Updated documentation for public release"

# Step 4: Add remote (if not already added)
Write-Host ""
Write-Host "[Step 4/5] Setting up GitHub remote..." -ForegroundColor Yellow
$remoteExists = git remote | Select-String -Pattern "origin"
if ($remoteExists) {
    Write-Host "Remote 'origin' already exists. Skipping..." -ForegroundColor Gray
} else {
    git remote add origin https://github.com/Vincent1949/scholars-terminal.git
    Write-Host "Added remote: https://github.com/Vincent1949/scholars-terminal.git" -ForegroundColor Green
}

# Step 5: Push to GitHub
Write-Host ""
Write-Host "[Step 5/5] Pushing to GitHub..." -ForegroundColor Yellow
Write-Host ""
Write-Host "IMPORTANT: You need to create the repository on GitHub first!" -ForegroundColor Red
Write-Host "1. Go to: https://github.com/new" -ForegroundColor White
Write-Host "2. Repository name: scholars-terminal" -ForegroundColor White
Write-Host "3. Make it PUBLIC" -ForegroundColor White
Write-Host "4. DO NOT initialize with README" -ForegroundColor White
Write-Host "5. Click 'Create repository'" -ForegroundColor White
Write-Host ""
Write-Host "Have you created the repository on GitHub? (Y/N)" -ForegroundColor Green
$response = Read-Host

if ($response -eq "Y" -or $response -eq "y") {
    Write-Host ""
    Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
    git branch -M main
    git push -u origin main
    
    # Create tag
    Write-Host ""
    Write-Host "Creating release tag v2.0.0..." -ForegroundColor Yellow
    git tag -a v2.0.0 -m "Initial public release - Scholar's Terminal v2.0.0"
    git push origin v2.0.0
    
    Write-Host ""
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host "  SUCCESS! Your project is on GitHub!" -ForegroundColor Green
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "View it at: https://github.com/Vincent1949/scholars-terminal" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Go to your repository on GitHub" -ForegroundColor White
    Write-Host "2. Click 'Releases' on the right sidebar" -ForegroundColor White
    Write-Host "3. Click 'Draft a new release'" -ForegroundColor White
    Write-Host "4. Choose tag: v2.0.0" -ForegroundColor White
    Write-Host "5. Add release notes and publish" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "No problem! Here's what to do:" -ForegroundColor Yellow
    Write-Host "1. Go to https://github.com/new" -ForegroundColor White
    Write-Host "2. Create the repository named: scholars-terminal" -ForegroundColor White
    Write-Host "3. Then run this script again!" -ForegroundColor White
    Write-Host ""
}

Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
