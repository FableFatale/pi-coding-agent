# Start Docker Desktop
$dockerPath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
if (Test-Path $dockerPath) {
    Write-Host "Starting Docker Desktop..."
    Start-Process $dockerPath -WindowStyle Hidden
    
    # Wait for Docker to be ready
    $maxWait = 60
    $waited = 0
    while ($waited -lt $maxWait) {
        try {
            $result = docker version 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Docker is ready!"
                exit 0
            }
        } catch {}
        Start-Sleep -Seconds 2
        $waited += 2
        Write-Host "Waiting for Docker... ($waited seconds)"
    }
    Write-Host "Docker started but may not be fully ready"
    exit 0
} else {
    Write-Host "Docker Desktop not found at $dockerPath"
    exit 1
}
