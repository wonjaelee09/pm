$ContainerName = "pm-app"

docker stop $ContainerName 2>$null
docker rm $ContainerName 2>$null

Write-Host "Done."
