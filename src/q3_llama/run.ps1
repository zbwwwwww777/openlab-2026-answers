#requires -Version 5.1
<#
.SYNOPSIS
    第 3 题 · 用自己编译出来的 llama-cli 跑一次对话，并对比 CPU / GPU 速度。

.EXAMPLE
    .\run.ps1 -Model D:\models\gemma-4-e2b-q4_0.gguf
    .\run.ps1 -Model D:\models\gemma-4-e2b-q4_0.gguf -Threads 1     # 演示 -t 1 的效果
    .\run.ps1 -Model D:\models\gemma-4-e2b-q4_0.gguf -Compare       # CPU vs GPU 速度对比
#>

param(
    [Parameter(Mandatory = $true)]
    [string] $Model,

    [string] $WorkDir = "$env:USERPROFILE\dev\llm",

    [int]    $Threads = 0,      # -t：生成阶段 CPU 线程数，0 = 让 llama.cpp 自己定
    [int]    $GpuLayers = 99,   # -ngl：卸载到 GPU 的层数
    [int]    $Predict = 128,    # -n：最多生成多少个 token
    [string] $Prompt = '用一句话解释什么是版本控制系统 Git。',

    [switch] $Compare           # 额外跑一次纯 CPU，做速度对比
)

# 不设 $ErrorActionPreference='Stop'：llama-cli 会把进度写进 stderr，
# 开了 Stop 就会被当成错误掐断。这里手动检查退出码。

Set-Location (Join-Path $WorkDir 'llama.cpp')

$cli = Join-Path $WorkDir 'llama.cpp\build\bin\llama-cli.exe'
if (-not (Test-Path $cli)) {
    $cli = Join-Path $WorkDir 'llama.cpp\build\bin\Release\llama-cli.exe'
}
if (-not (Test-Path $cli)) { throw "找不到 llama-cli.exe，请先跑 .\build.ps1" }
if (-not (Test-Path $Model)) { throw "找不到模型文件：$Model" }

function Invoke-Llama([int] $ngl, [int] $threads, [string] $tag) {
    $cliArgs = @(
        '-m', $Model,
        '-p', $Prompt,
        '-n', $Predict,
        '-ngl', $ngl,
        '-st'
    )
    if ($threads -gt 0) { $cliArgs += @('-t', $threads) }

    Write-Host ""
    Write-Host "--- [$tag] llama-cli $($cliArgs -join ' ') ---" -ForegroundColor Cyan
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    # 2>&1 把 stderr 并进主输出，转成字符串防止触发 PowerShell 错误流
    & $cli @cliArgs 2>&1 | ForEach-Object { "$_" }
    $sw.Stop()
    if ($LASTEXITCODE -ne 0) { throw "llama-cli [$tag] 失败，退出码 $LASTEXITCODE" }
    Write-Host "[$tag] 总耗时 $($sw.Elapsed.TotalSeconds.ToString('F2')) 秒" -ForegroundColor DarkGray
    return $sw.Elapsed.TotalSeconds
}

Write-Host "== 正式跑一次（GPU offload $GpuLayers 层）==" -ForegroundColor Green
Invoke-Llama -ngl $GpuLayers -threads $Threads -tag 'GPU'

if ($Compare) {
    Write-Host ""
    Write-Host "== 对照：纯 CPU（-ngl 0）==" -ForegroundColor Green
    Invoke-Llama -ngl 0 -threads $Threads -tag 'CPU'

    if ($Threads -ne 1) {
        Write-Host ""
        Write-Host "== 对照：-t 1（单线程）==" -ForegroundColor Green
        Invoke-Llama -ngl 0 -threads 1 -tag 'CPU-1T'
    }
}

Write-Host ""
Write-Host @"
提示：
  · 输出里的 "eval time" / "tokens per second" 就是题目要的推理速度（tokens/s）
  · 截图时请把命令行 + 输出一起截进去
  · 想看 -ngl 的显存估算，加 -fitp on（llama-cli 参数）
"@ -ForegroundColor Yellow
