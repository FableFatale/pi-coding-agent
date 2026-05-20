Write-Host "========== System Environment Check ==========" -ForegroundColor Cyan
Write-Host ""

# OS
Write-Host "[OS]" -ForegroundColor Yellow
$os = Get-ComputerInfo -ErrorAction SilentlyContinue
if ($os) {
    Write-Host "Windows: $($os.WindowsProductName) $($os.WindowsVersion)"
    Write-Host "Architecture: $($os.OsArchitecture)"
}
Write-Host ""

# Node.js
Write-Host "[Node.js]" -ForegroundColor Yellow
$node = Get-Command node -ErrorAction SilentlyContinue
if ($node) {
    Write-Host "Path: $($node.Source)"
    Write-Host "Version: $(node --version)"
    Write-Host "npm: $(npm --version)"
} else {
    Write-Host "Not installed"
}
Write-Host ""

# Python
Write-Host "[Python]" -ForegroundColor Yellow
$python = Get-Command python -ErrorAction SilentlyContinue
if ($python) {
    Write-Host "Path: $($python.Source)"
    Write-Host "Version: $(python --version 2>&1)"
    Write-Host "pip: $(pip --version 2>&1)"
} else {
    Write-Host "Not installed"
}
Write-Host ""

# Redis
Write-Host "[Redis]" -ForegroundColor Yellow
$redis = Get-Command redis-server -ErrorAction SilentlyContinue
$redisCli = Get-Command redis-cli -ErrorAction SilentlyContinue
if ($redis) {
    Write-Host "redis-server: $($redis.Source)"
}
if ($redisCli) {
    Write-Host "redis-cli: $($redisCli.Source)"
}
$redisSvc = Get-Service -Name '*Redis*' -ErrorAction SilentlyContinue
if ($redisSvc) {
    Write-Host "Service: $($redisSvc.Name) - $($redisSvc.Status)"
}
Write-Host ""

# PostgreSQL
Write-Host "[PostgreSQL]" -ForegroundColor Yellow
$pg = Get-Command psql -ErrorAction SilentlyContinue
if ($pg) {
    Write-Host "psql: $($pg.Source)"
}
$pgSvc = Get-Service -Name '*postgres*','*postgresql*' -ErrorAction SilentlyContinue
if ($pgSvc) {
    Write-Host "Service: $($pgSvc.Name) - $($pgSvc.Status)"
}
Write-Host ""

# Git
Write-Host "[Git]" -ForegroundColor Yellow
$git = Get-Command git -ErrorAction SilentlyContinue
if ($git) {
    Write-Host "Path: $($git.Source)"
    Write-Host "Version: $(git --version)"
} else {
    Write-Host "Not installed"
}
Write-Host ""

# Docker
Write-Host "[Docker]" -ForegroundColor Yellow
$docker = Get-Command docker -ErrorAction SilentlyContinue
if ($docker) {
    Write-Host "Path: $($docker.Source)"
    Write-Host "Version: $(docker --version)"
} else {
    Write-Host "Not installed"
}
Write-Host ""

Write-Host "========== Done ==========" -ForegroundColor Cyan
