# AI情报站前端启动脚本
$frontendPath = "d:\Vibe coding\AI情报站\frontend"
$logFile = "d:\Vibe coding\AI情报站\logs\frontend_startup.log"

# 创建日志目录（如果不存在）
$logDir = Split-Path $logFile -Parent
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

# 记录启动日志
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
"$timestamp - 前端服务启动" | Out-File -FilePath $logFile -Append -Encoding UTF8

# 切换到前端目录并启动服务
Set-Location $frontendPath
Start-Process powershell -ArgumentList "-NoExit", "-Command", "npm run dev" -WindowStyle Normal
