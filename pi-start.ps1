# Pi 启动脚本 - 自动读取 config.json 设置 API keys

$ErrorActionPreference = "SilentlyContinue"

# ============================================
# 自动启动 Redis（如果未运行）
# ============================================
function Start-RedisIfNeeded {
    $redisRunning = Get-Process redis-server -ErrorAction SilentlyContinue
    
    if (-not $redisRunning) {
        Write-Host "🔴 Redis 未运行，正在启动..." -ForegroundColor Yellow
        
        # 尝试启动 Redis（Windows 服务或直接启动）
        try {
            # 方式1: 尝试作为服务启动
            Start-Service Redis 2>$null
            
            # 方式2: 直接启动 redis-server
            if (-not (Get-Process redis-server -ErrorAction SilentlyContinue)) {
                $redisPath = Get-Command redis-server -ErrorAction SilentlyContinue
                if ($redisPath) {
                    Start-Process -FilePath $redisPath.Source -ArgumentList "--daemonize yes" -WindowStyle Hidden
                } else {
                    # 尝试常见路径
                    $commonPaths = @(
                        "C:\Redis\redis-server.exe",
                        "$env:ProgramFiles\Redis\redis-server.exe",
                        "$env:LOCALAPPDATA\Programs\Redis\redis-server.exe"
                    )
                    foreach ($path in $commonPaths) {
                        if (Test-Path $path) {
                            Start-Process -FilePath $path -ArgumentList "--daemonize yes" -WindowStyle Hidden
                            break
                        }
                    }
                }
            }
            
            # 等待 Redis 启动
            Start-Sleep -Seconds 2
            
            # 验证 Redis 是否启动成功
            if (Get-Process redis-server -ErrorAction SilentlyContinue) {
                Write-Host "🟢 Redis 已启动" -ForegroundColor Green
            } else {
                Write-Host "⚠️ Redis 启动失败，请手动启动 Redis" -ForegroundColor Red
            }
        } catch {
            Write-Host "⚠️ Redis 启动失败: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "🟢 Redis 已在运行" -ForegroundColor Green
    }
}

# 启动 Redis
Start-RedisIfNeeded

# ============================================
# 读取 config.json
# ============================================
$configPath = Join-Path $PSScriptRoot "config.json"
if (Test-Path $configPath) {
    $config = Get-Content $configPath | ConvertFrom-Json
    
    # 设置各 Provider 的 API Key
    if ($config.apiKeys.minimax) {
        $env:MINIMAX_API_KEY = $config.apiKeys.minimax
    }
    if ($config.apiKeys.google) {
        $env:GOOGLE_API_KEY = $config.apiKeys.google
    }
    if ($config.apiKeys.anthropic) {
        $env:ANTHROPIC_API_KEY = $config.apiKeys.anthropic
    }
    if ($config.apiKeys.openai) {
        $env:OPENAI_API_KEY = $config.apiKeys.openai
    }
}

# 设置 PATH
$env:PATH = "C:\Program Files\nodejs;" + $env:PATH

# ============================================
# 启动 pi
# ============================================
Write-Host ""
Write-Host "🚀 正在启动 Pi..." -ForegroundColor Cyan
& "$PSScriptRoot\node_modules\@mariozechner\pi-coding-agent\dist\cli.js" $args
