# OPTION 1: BOOKS ONLY (RECOMMENDED)
# Run time: 4-6 hours

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   SCHOLAR'S TERMINAL RE-INDEX" -ForegroundColor Cyan  
Write-Host "   OPTION 1: BOOKS ONLY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "This will:" -ForegroundColor Yellow
Write-Host "  - Index 13,742 book files" -ForegroundColor Yellow
Write-Host "  - Skip GitHub (982,143 files)" -ForegroundColor Yellow
Write-Host "  - Take 4-6 hours" -ForegroundColor Yellow
Write-Host "  - Create ~45,000 document chunks" -ForegroundColor Yellow
Write-Host ""

$confirm = Read-Host "Continue? (yes/no)"
if ($confirm -ne "yes") {
    Write-Host "Cancelled." -ForegroundColor Red
    exit
}

Write-Host ""
Write-Host "[1/4] Updating configuration..." -ForegroundColor Green

# Backup current config
Copy-Item reindex_config.py reindex_config.py.backup -Force

# Read config
$config = Get-Content reindex_config.py -Raw

# Modify GITHUB_ROOT to skip GitHub
$config = $config -replace 'GITHUB_ROOT = r"D:\\GitHub"', 'GITHUB_ROOT = r"D:\GitHub_SKIP"  # SKIPPING GITHUB'

# Write back
$config | Set-Content reindex_config.py -NoNewline

Write-Host "   ✓ GitHub indexing disabled" -ForegroundColor Green
Write-Host ""

Write-Host "[2/4] Cleaning old data..." -ForegroundColor Green
Remove-Item data\vector_db_new -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item reindex_progress.json -ErrorAction SilentlyContinue
Remove-Item reindex.log -ErrorAction SilentlyContinue
Write-Host "   ✓ Database cleaned" -ForegroundColor Green
Write-Host ""

Write-Host "[3/4] Verifying configuration..." -ForegroundColor Green
python reindex_config.py
Write-Host ""

Write-Host "[4/4] Starting re-index..." -ForegroundColor Green
Write-Host ""
Write-Host "This will take 4-6 hours." -ForegroundColor Yellow
Write-Host "You can close this window - the process will continue." -ForegroundColor Yellow
Write-Host "Check progress with: python check_db.py" -ForegroundColor Cyan
Write-Host ""

Start-Sleep -Seconds 3

# Run the reindex
python reindex_with_metadata.py

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   RE-INDEX COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Run: python verify_reindex.py" -ForegroundColor White
Write-Host "  2. Test searches" -ForegroundColor White
Write-Host "  3. Copy to main machine" -ForegroundColor White
