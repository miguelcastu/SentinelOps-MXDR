param([switch]$Apply, [switch]$IncludeAdditional)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $repoRoot
try {
    $arguments = @('run', '--python', '3.12', '--with', 'pynacl==1.6.2', '--no-project', 'python', '-m', 'scripts.bootstrap_oidc')
    if ($Apply) { $arguments += '--apply' }
    if ($IncludeAdditional) { $arguments += '--include-additional' }
    & uv @arguments
    if ($LASTEXITCODE -ne 0) { throw 'Restricted Azure/GitHub setup failed. See the sanitized error above.' }
}
finally { Pop-Location }
