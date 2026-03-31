<#
.SYNOPSIS
    Waits for CPU usage to drop below a threshold, then hibernates the system.

.PARAMETER ThresholdPercent
    Hibernate when average CPU drops below this value (default: 10).

.PARAMETER SampleInterval
    Seconds between each CPU measurement (default: 5).

.PARAMETER ConsecutiveCount
    How many consecutive samples below threshold before acting (default: 3).

.PARAMETER CountdownSeconds
    Warning countdown before hibernating. 0 = no countdown (default: 30).
#>
param(
    [int]$ThresholdPercent   = 10,
    [int]$SampleInterval     = 5,
    [int]$ConsecutiveCount   = 3,
    [int]$CountdownSeconds   = 30
)

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
          ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {

    Write-Host "Not elevated — relaunching as Administrator..."

    $args = @(
    "-NoExit",
        "-ExecutionPolicy", "Bypass",
        "-File", "`"$PSCommandPath`""
    ) + $PSBoundParameters.GetEnumerator().ForEach({ "-$($_.Key)", "$($_.Value)" })

    Start-Process pwsh.exe -ArgumentList $args -Verb RunAs
    exit
}

Write-Host "Waiting for CPU < $ThresholdPercent% ($ConsecutiveCount consecutive samples of ${SampleInterval}s each)..."

$below = 0

while ($true) {
    # Get average CPU load across all cores
    $cpu = (Get-CimInstance -ClassName Win32_Processor |
            Measure-Object -Property LoadPercentage -Average).Average

    $ts = Get-Date -Format "HH:mm:ss"
    Write-Host "[$ts] CPU: $cpu%"

    if ($cpu -lt $ThresholdPercent) {
        $below++
        Write-Host "  -> Below threshold ($below/$ConsecutiveCount)"

        if ($below -ge $ConsecutiveCount) {
            break
        }
    } else {
        if ($below -gt 0) {
            Write-Host "  -> Reset (CPU spiked back up)"
        }
        $below = 0
    }

    Start-Sleep -Seconds $SampleInterval
}

Write-Host "`nCPU has been quiet. Preparing to hibernate..."

if ($CountdownSeconds -gt 0) {
    for ($i = $CountdownSeconds; $i -gt 0; $i--) {
        Write-Host "  Hibernating in $i seconds... (Ctrl+C to cancel)"
        Start-Sleep -Seconds 1
    }
}

Write-Host "Hibernating now."
shutdown.exe /h