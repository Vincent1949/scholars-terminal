# corey-cup-day0.ps1
# The Corey Cup — Day 0 Allocation Dispatch
# Run when US markets open (~23:30 AEST Friday 8 May 2026).
# Dispatches Day 0 allocation prompts to all three external siblings sequentially.
# Sir Claude's allocation is requested separately in the Big Brother chat.

# Ensure local temp dir exists
if (!(Test-Path C:\temp)) {
    New-Item -ItemType Directory -Path C:\temp -Force | Out-Null
}

# Common prompt template — single-quoted here-string preserves $ signs and brackets literally
$promptTemplate = @'
You are [SIBLING] in The Corey Cup. This is Day 0 -- Allocation Day.

US markets have just opened. You will now execute your allocation per your
locked manifesto at claude-work\corey-cup\Manifesto.md. The strategy
framework is locked; only specific ticker selection within that framework
remains.

YOUR TASK FOR DAY 0:

1. Re-read your manifesto. Confirm what you committed to.
2. Select specific tickers within your manifesto framework. You may consult
   current market data for ticker selection -- but you may NOT change your
   strategy, percentages, or decision rules. Those are immutable.
3. Calculate share counts at current prices. Document your starting portfolio.

Format your response as Markdown:

# Day 0 -- [SIBLING] -- Allocation

## Tickers Selected
| Sleeve | Allocation | Ticker | Price | Shares | $ Value |
|--------|-----------|--------|-------|--------|---------|

## Starting Portfolio
- Total holdings: $X
- Cash: $Y
- Portfolio total: ~$1,000.00

## Reasoning
2-3 sentences on WHY these specific tickers within your committed framework.

End with: "DAY 0 COMPLETE -- [SIBLING] -- 8 May 2026 -- $[Total]"

Append your record to: claude-work\corey-cup\decisions.md
'@

# Per-sibling dispatch table
$dispatches = @(
    @{
        Sibling  = 'Little Brother'
        File     = 'C:\temp\corey-day0-LB.txt'
        SshArgs  = @('geekom', 'claude --print --allowedTools Write,Edit,Read')
    },
    @{
        Sibling  = 'Little Sister'
        File     = 'C:\temp\corey-day0-LS.txt'
        SshArgs  = @('farthing@192.168.1.105', 'claude --print --allowedTools Write,Edit,Read')
    },
    @{
        Sibling  = 'Scholar'
        File     = 'C:\temp\corey-day0-Scholar.txt'
        SshArgs  = @('-i', 'C:\Users\Marcus\.ssh\fastpc_key',
                     '-p', '1233',
                     'scholars@192.168.1.110',
                     'claude --print --allowedTools Write,Edit,Read')
    }
)

foreach ($d in $dispatches) {
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host "  Dispatching Day 0 prompt to $($d.Sibling)" -ForegroundColor Cyan
    Write-Host "================================================================" -ForegroundColor Cyan

    # Substitute sibling name and write to file
    $customPrompt = $promptTemplate -replace '\[SIBLING\]', $d.Sibling
    $customPrompt | Out-File -FilePath $d.File -Encoding utf8
    Write-Host "  Prompt -> $($d.File)" -ForegroundColor DarkGray

    # Dispatch via SSH stdin pipe
    $sshArgs = $d.SshArgs
    try {
        Get-Content $d.File | ssh @sshArgs
    } catch {
        Write-Host "  ERROR dispatching to $($d.Sibling): $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Green
Write-Host "  Day 0 external dispatch complete." -ForegroundColor Green
Write-Host "  Sir Claude's allocation: ask in Big Brother chat." -ForegroundColor Green
Write-Host "  Update LEDGER.md with all four starting portfolios." -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green