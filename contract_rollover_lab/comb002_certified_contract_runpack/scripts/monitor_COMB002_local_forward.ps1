param(
    [string]$Assets = "ES,FDAX,NQ",
    [string]$Timeframes = "15m",
    [int]$Workers = 3
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$LogDir = Join-Path $Root "logs"
$OutDir = Join-Path $Root "outputs\contract_phase2a_forward_dual"
$AnnualOut = Join-Path $Root "outputs\annual_pf\COMB002_forward_best_candidates_annual_pf.csv"
$Runner = Join-Path $Root "scripts\run_COMB002_contract_phase2a_forward_dual.py"
$AnnualRunner = Join-Path $Root "scripts\annual_pf_from_forward_results.py"
$FinalizeRunner = Join-Path $Root "scripts\finalize_COMB002_15m_independent_phase5_7.py"
$RunLog = Join-Path $LogDir "contract_phase3_4_local_all_independent_from_phase1.log"
$RunErr = Join-Path $LogDir "contract_phase3_4_local_all_independent_from_phase1.err.log"
$FinalizeLog = Join-Path $LogDir "finalize_COMB002_15m_independent_phase5_7.log"
$FinalizeErr = Join-Path $LogDir "finalize_COMB002_15m_independent_phase5_7.err.log"
$AnnualLog = Join-Path $LogDir "annual_pf_local.log"
$AnnualErr = Join-Path $LogDir "annual_pf_local.err.log"
$PidFile = Join-Path $LogDir "contract_phase3_4_local_all_independent_from_phase1.pid"
$FinalizeOut = Join-Path $Root "outputs\independent_phase5_7\COMB002_15m_independent_from_phase1_phase5_7_summary.json"

New-Item -ItemType Directory -Force -Path $LogDir, $OutDir | Out-Null

function Get-Comb002RunnerProcess {
    Get-CimInstance Win32_Process |
        Where-Object {
            $_.Name -match "^(py|python)\.exe$" -and
            $_.CommandLine -like "*run_COMB002_contract_phase2a_forward_dual.py*"
        }
}

function Get-AnnualPfProcess {
    Get-CimInstance Win32_Process |
        Where-Object {
            $_.Name -match "^(py|python)\.exe$" -and
            $_.CommandLine -like "*annual_pf_from_forward_results.py*"
        }
}

function Get-FinalizeProcess {
    Get-CimInstance Win32_Process |
        Where-Object {
            $_.Name -match "^(py|python)\.exe$" -and
            $_.CommandLine -like "*finalize_COMB002_15m_independent_phase5_7.py*"
        }
}

function Test-IndependentPhase4Complete {
    foreach ($tf in $Timeframes.Split(",") | Where-Object { $_ }) {
        foreach ($asset in $Assets.Split(",") | Where-Object { $_ }) {
            $stem = "COMB002_contract_${asset}_${tf}_friday_to_expiry_week_monday_label_left"
            $expected = Join-Path $OutDir "$asset\$tf\independent_from_phase2a\${stem}_phase4_from_phase1_stops_top_params.json"
            if (-not (Test-Path $expected)) {
                return $false
            }
        }
    }
    return $true
}

function Test-AnnualReportStale {
    if (-not (Test-Path $AnnualOut)) {
        return $true
    }
    $reportTime = (Get-Item $AnnualOut).LastWriteTimeUtc
    $latestResult = Get-ChildItem -Path $OutDir -Recurse -Filter "*from_phase1*results.csv" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTimeUtc -Descending |
        Select-Object -First 1
    return ($latestResult -and $latestResult.LastWriteTimeUtc -gt $reportTime)
}

$runner = Get-Comb002RunnerProcess
if ($runner) {
    "$(Get-Date -Format s) runner active: $($runner.ProcessId -join ',')" | Add-Content -Path $RunLog
    exit 0
}

if (-not (Test-IndependentPhase4Complete)) {
    $args = @(
        "-3",
        "`"$Runner`"",
        "--assets", $Assets,
        "--timeframes", $Timeframes,
        "--lanes", "independent",
        "--independent-timeframes", $Timeframes,
        "--end-phase", "phase4",
        "--workers", "$Workers",
        "--out-dir", "`"$OutDir`""
    )
    $proc = Start-Process -FilePath "py" -ArgumentList $args -WorkingDirectory $Root -RedirectStandardOutput $RunLog -RedirectStandardError $RunErr -WindowStyle Hidden -PassThru
    $proc.Id | Set-Content -Path $PidFile
    "$(Get-Date -Format s) started runner pid=$($proc.Id)" | Add-Content -Path $RunLog
    exit 0
}

if ((-not (Test-Path $FinalizeOut)) -and -not (Get-FinalizeProcess)) {
    $args = @("-3", "`"$FinalizeRunner`"", "--timeframe", "15m", "--assets", $Assets)
    $proc = Start-Process -FilePath "py" -ArgumentList $args -WorkingDirectory $Root -RedirectStandardOutput $FinalizeLog -RedirectStandardError $FinalizeErr -WindowStyle Hidden -PassThru
    "$(Get-Date -Format s) started finalize phase5/6/7 pid=$($proc.Id)" | Add-Content -Path $FinalizeLog
    exit 0
}

if ((Test-AnnualReportStale) -and -not (Get-AnnualPfProcess)) {
    $args = @("-3", "`"$AnnualRunner`"")
    $proc = Start-Process -FilePath "py" -ArgumentList $args -WorkingDirectory $Root -RedirectStandardOutput $AnnualLog -RedirectStandardError $AnnualErr -WindowStyle Hidden -PassThru
    "$(Get-Date -Format s) started annual PF pid=$($proc.Id)" | Add-Content -Path $AnnualLog
    exit 0
}

"$(Get-Date -Format s) complete; no action" | Add-Content -Path $RunLog
