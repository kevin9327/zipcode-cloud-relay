$repo = Resolve-Path (Join-Path $PSScriptRoot "..")
$report = Join-Path $repo "relay_outbox\offline_report.md"
New-Item -ItemType Directory -Force -Path (Split-Path $report) | Out-Null

$offlineReport = python (Join-Path $repo "zipcode_agent.py") `
  --root (Join-Path $repo "examples\airgap_demo_workspace") `
  --task "Find the bug in the water sensor parser and propose a safe fix." `
  --read README.md `
  --search TODO `
  --dry-run
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($report, ($offlineReport -join [Environment]::NewLine), $utf8NoBom)
$offlineReport

python (Join-Path $repo "cloud_relay.py") `
  --task "Find the bug in the water sensor parser and propose a safe fix." `
  --report $report `
  --approved-by "demo operator"
