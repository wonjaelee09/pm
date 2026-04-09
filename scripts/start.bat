@echo off
setlocal

set IMAGE_NAME=pm-app
set CONTAINER_NAME=pm-app
set PORT=8000
set PROJECT_DIR=%~dp0..
set DATA_DIR=%PROJECT_DIR%\data

if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"

echo Building %IMAGE_NAME%...
docker build -t %IMAGE_NAME% "%PROJECT_DIR%"

echo Starting container on port %PORT%...
docker run -d ^
  --name %CONTAINER_NAME% ^
  --env-file "%PROJECT_DIR%\.env" ^
  -e DB_PATH=/app/data/kanban.db ^
  -p %PORT%:8000 ^
  -v "%DATA_DIR%:/app/data" ^
  %IMAGE_NAME%

echo Running at http://localhost:%PORT%
