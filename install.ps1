# Sets up mcp-web on Windows and prints the LM Studio config to paste.
$ErrorActionPreference = "Stop"

Set-Location -LiteralPath $PSScriptRoot
Write-Host "Installing mcp-web in $PSScriptRoot"

$VenvPy = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

# uv handles everything including fetching a Python if none is new enough.
if (Get-Command uv -ErrorAction SilentlyContinue) {
    uv venv --python 3.12
    uv pip install --python $VenvPy -e .
} else {
    $Py = $null
    foreach ($candidate in @("python3.13", "python3.12", "python3.11", "python", "py")) {
        $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
        if (-not $cmd) { continue }
        & $candidate -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)' 2>$null
        if ($LASTEXITCODE -eq 0) { $Py = $candidate; break }
    }
    if (-not $Py) {
        Write-Host ""
        Write-Host "No Python 3.11 or newer found. Install uv, which will fetch one for you:"
        Write-Host "  powershell -c ""irm https://astral.sh/uv/install.ps1 | iex"""
        Write-Host "then run this script again."
        exit 1
    }
    & $Py -m venv .venv
    & $VenvPy -m pip install --quiet --upgrade pip
    & $VenvPy -m pip install --quiet -e .
}

$Bin = Join-Path $PSScriptRoot ".venv\Scripts\mcp-web.exe"
& $VenvPy -c 'import mcp_web.server' | Out-Null

# JSON needs each backslash doubled.
$BinJson = $Bin -replace '\\', '\\'

@"

Done. Now open LM Studio, go to the Program tab in the right sidebar,
choose Install > Edit mcp.json, and add this entry:

{
  "mcpServers": {
    "mcp-web": {
      "command": "$BinJson"
    }
  }
}

If mcp.json already has other servers, add "mcp-web" alongside them
inside the existing "mcpServers" object.

Then load a model that supports tools and enable mcp-web in the chat.
"@
