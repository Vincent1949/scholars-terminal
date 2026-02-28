# OPTION 3: FULL RUN (EVERYTHING)
# Run time: 8-10 DAYS

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   SCHOLAR'S TERMINAL RE-INDEX" -ForegroundColor Cyan  
Write-Host "   OPTION 3: FULL RUN (8+ DAYS)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "WARNING: This will:" -ForegroundColor Red
Write-Host "  - Index 13,742 book files" -ForegroundColor Yellow
Write-Host "  - Index 982,143 GitHub files" -ForegroundColor Yellow
Write-Host "  - Take 8-10 DAYS" -ForegroundColor Red
Write-Host "  - Create ~3 million document chunks" -ForegroundColor Yellow
Write-Host "  - Create a 50-100GB+ database" -ForegroundColor Yellow
Write-Host ""

Write-Host "Are you SURE you want to run this?" -ForegroundColor Red
$confirm1 = Read-Host "Type 'YES I AM SURE' to continue"
if ($confirm1 -ne "YES I AM SURE") {
    Write-Host "Cancelled. Good choice!" -ForegroundColor Green
    Write-Host "Consider running START_BOOKS_ONLY.ps1 instead." -ForegroundColor Cyan
    exit
}

Write-Host ""
Write-Host "Really? 8-10 days?" -ForegroundColor Red
$confirm2 = Read-Host "Type 'FULL RUN' to really start"
if ($confirm2 -ne "FULL RUN") {
    Write-Host "Cancelled." -ForegroundColor Green
    exit
}

Write-Host ""
Write-Host "[1/4] Configuration check..." -ForegroundColor Green
python reindex_config.py
Write-Host ""

Write-Host "[2/4] Cleaning old data..." -ForegroundColor Green
Remove-Item data\vector_db_new -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item reindex_progress.json -ErrorAction SilentlyContinue  
Remove-Item reindex.log -ErrorAction SilentlyContinue
Write-Host "   ✓ Database cleaned" -ForegroundColor Green
Write-Host ""

Write-Host "[3/4] Final warning..." -ForegroundColor Yellow
Write-Host "This will run for 8-10 DAYS." -ForegroundColor Red
Write-Host "The i9 machine will be busy the entire time." -ForegroundColor Yellow
Write-Host ""
Start-Sleep -Seconds 5

Write-Host "[4/4] Starting FULL re-index..." -ForegroundColor Green
Write-Host ""
Write-Host "Check progress with: python check_db.py" -ForegroundColor Cyan
Write-Host "View logs with: Get-Content reindex.log -Tail 20" -ForegroundColor Cyan
Write-Host ""

Start-Sleep -Seconds 3

# Run the reindex
python reindex_with_metadata.py

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   RE-INDEX COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
