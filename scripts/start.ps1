$ErrorActionPreference = "Stop"

$ImageName = "pm-app"
$ContainerName = "pm-app"
$Port = 8000
$ProjectDir = Split-Path -Parent $PSScriptRoot
$DataDir = Join-Path $ProjectDir "data"

if (-not (Test-Path $DataDir)) { New-Item -ItemType Directory -Path $DataDir | Out-Null }

Write-Host "Building $ImageName..."
docker build -t $ImageName $ProjectDir

Write-Host "Starting container on port $Port..."
docker run -d `
  --name $ContainerName `
  --env-file "$ProjectDir\.env" `
  -e DB_PATH=/app/data/kanban.db `
  -p "${Port}:8000" `
  -v "${DataDir}:/app/data" `
  $ImageName

Write-Host "Running at http://localhost:$Port"
