# AI情报站后端启动脚本
$backendPath = "d:\Vibe coding\AI情报站\backend"
$logFile = "d:\Vibe coding\AI情报站\logs\startup.log"

# 创建日志目录（如果不存在）
$logDir = Split-Path $logFile -Parent
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

# 记录启动日志
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
"$timestamp - 后端服务启动" | Out-File -FilePath $logFile -Append -Encoding UTF8

# 切换到后端目录并启动服务
Set-Location $backendPath
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m uvicorn main:app --reload --port 8000 --host 0.0.0.0" -WindowStyle Normal
