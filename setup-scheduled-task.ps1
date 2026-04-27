# AI情报站 - 定时启动脚本
# 使用方法：以管理员身份运行 PowerShell，执行本脚本

Write-Host "========================================"
Write-Host "AI情报站 定时启动任务设置"
Write-Host "========================================"
Write-Host ""

# 1. 创建后端启动任务
Write-Host "[1/2] 创建后端定时任务..."
Unregister-ScheduledTask -TaskName "AI情报站-后端启动" -Confirm:`$false -ErrorAction SilentlyContinue
$backendTrigger = New-ScheduledTaskTrigger -Daily -At "09:25"
$backendArg = "-ExecutionPolicy Bypass -File `"d:\Vibe coding\AI情报站\backend\start_server.ps1`""
$backendAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $backendArg
$backendSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$backendPrincipal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
Register-ScheduledTask -TaskName "AI情报站-后端启动" -Trigger $backendTrigger -Action $backendAction -Settings $backendSettings -Principal $backendPrincipal -Description "每天自动启动 AI情报站 后端服务"
Write-Host "  [OK] 后端任务已创建"

# 2. 创建前端启动任务
Write-Host "[2/2] 创建前端定时任务..."
Unregister-ScheduledTask -TaskName "AI情报站-前端启动" -Confirm:`$false -ErrorAction SilentlyContinue
$frontendTrigger = New-ScheduledTaskTrigger -Daily -At "09:26"
$frontendArg = "-ExecutionPolicy Bypass -File `"d:\Vibe coding\AI情报站\frontend\start_frontend.ps1`""
$frontendAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $frontendArg
$frontendSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$frontendPrincipal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
Register-ScheduledTask -TaskName "AI情报站-前端启动" -Trigger $frontendTrigger -Action $frontendAction -Settings $frontendSettings -Principal $frontendPrincipal -Description "每天自动启动 AI情报站 前端服务"
Write-Host "  [OK] 前端任务已创建"

Write-Host ""
Write-Host "========================================"
Write-Host "设置完成！"
Write-Host "========================================"
Write-Host ""
Write-Host "定时任务已创建："
Write-Host "  - AI情报站-后端启动 每天 09:25 启动"
Write-Host "  - AI情报站-前端启动 每天 09:26 启动"
Write-Host ""
Write-Host "查看任务命令："
Write-Host '  Get-ScheduledTask | Where-Object {$_.TaskName -like "*AI情报站*"}'
Write-Host ""
Write-Host "删除任务命令："
Write-Host '  Unregister-ScheduledTask -TaskName "AI情报站-后端启动" -Confirm:`$false'
Write-Host '  Unregister-ScheduledTask -TaskName "AI情报站-前端启动" -Confirm:`$false'
