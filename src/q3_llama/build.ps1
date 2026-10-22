#requires -Version 5.1
<#
.SYNOPSIS
    OpenLab 纳新题 · 第 3 题「！？模型？！」
    一键准备工具链 + 从源码编译 llama.cpp，并把全过程 stdout 存成 build_log.txt

.DESCRIPTION
    默认走 CPU 后端；加 -Cuda 会额外开启 CUDA 后端（需要已装 CUDA Toolkit）。
    编译日志会完整写入 build_log.txt，不要删改、不要截断——阅卷要查。

.EXAMPLE
    .\build.ps1                 # CPU 后端
    .\build.ps1 -Cuda           # CPU + CUDA（RTX 5060 用这个）
    .\build.ps1 -WorkDir D:\dev -Jobs 18
#>

param(
    [switch] $Cuda,
    [string] $WorkDir = "$env:USERPROFILE\dev\llm",
    [int]    $Jobs = 0
)

# 注意：不能设 $ErrorActionPreference='Stop'。
# git/cmake/cl 都会往 stderr 写进度，PowerShell 会把它们当成错误直接掐断。
# 正确做法是：把每行输出转成字符串，再手动检查 $LASTEXITCODE。

# 日志编码：Tee-Object 在 PowerShell 5.1 里默认按 UTF-16LE 追加，
# 一旦和 Out-File -Encoding utf8 混用，同一个文件里就是两种编码 → 打开全是乱码。
# 这里全程只用 AppendAllText(UTF-8) 一种写法，杜绝混编。
$script:Utf8 = New-Object System.Text.UTF8Encoding($true)

# 原生程序（cl.exe / rc.exe）的中文按系统 ANSI 代码页（中文 Windows = GBK）输出，
# 让 PowerShell 用它去解码，否则中文会变成问号。
try {
    $ansi = [System.Globalization.CultureInfo]::CurrentCulture.TextInfo.ANSICodePage
    [Console]::OutputEncoding = [System.Text.Encoding]::GetEncoding($ansi)
    $OutputEncoding = [Console]::OutputEncoding
} catch { }

$script:LogPath = $null

function Write-Log {
    param([string] $Msg)
    if ($script:LogPath) {
        [System.IO.File]::AppendAllText($script:LogPath, $Msg + "`r`n", $script:Utf8)
    }
}

function Write-Step($msg) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  $msg" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Log ""
    Write-Log ("=" * 60)
    Write-Log "  $msg"
    Write-Log ("=" * 60)
}

function Test-Cmd($name) {
    return $null -ne (Get-Command $name -ErrorAction SilentlyContinue)
}

function Invoke-Logged {
    <#
      执行一个外部命令：
        - 全部输出（含 stderr）逐行转字符串，同时打屏 + 以 UTF-8 追加进 build_log.txt
        - 用退出码判断成败，而不是靠 PowerShell 的错误流
    #>
    param(
        [Parameter(Mandatory = $true)][string] $File,
        [Parameter(ValueFromRemainingArguments = $true)][string[]] $CmdArgs
    )
    $cmdLine = ">> $File $($CmdArgs -join ' ')"
    Write-Host $cmdLine -ForegroundColor DarkGray
    Write-Log $cmdLine
    & $File @CmdArgs 2>&1 | ForEach-Object {
        $line = "$_"
        Write-Host $line
        Write-Log $line
    }
    $code = $LASTEXITCODE
    if ($code -ne 0) { throw "$File 失败，退出码 $code" }
    return $code
}

# ---------------------------------------------------------------- 0. 基本信息
if ($Jobs -le 0) { $Jobs = [Environment]::ProcessorCount }

New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null
Set-Location $WorkDir

$script:LogPath = Join-Path $WorkDir 'build_log.txt'
# 每次重跑都从头写一份干净日志（旧的重命名为 .old.txt 留档，不删）
if (Test-Path $script:LogPath) {
    Move-Item -Force $script:LogPath "$script:LogPath.old.txt"
}

Write-Host "工作目录 : $WorkDir"
Write-Host "并行任务 : $Jobs"
Write-Host "CUDA     : $($Cuda.IsPresent)"
Write-Log "工作目录 : $WorkDir"
Write-Log "并行任务 : $Jobs"
Write-Log "CUDA     : $($Cuda.IsPresent)"

# ---------------------------------------------------------------- 1. 工具链
Write-Step "1/5 检查工具链"

foreach ($tool in 'git', 'cmake', 'ninja') {
    if (Test-Cmd $tool) {
        Write-Host "$tool  : $((Get-Command $tool).Source)" -ForegroundColor Green
        Write-Log ("$tool  : $((Get-Command $tool).Source)")
    } else {
        throw "找不到 $tool。请先装：winget install Git.Git / Kitware.CMake / Ninja-build.Ninja"
    }
}

# MSVC：找带 C++ 工具链的最新 Visual Studio
$vsWhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
$vsPath = $null
if (Test-Path $vsWhere) {
    $vsPath = & $vsWhere -latest -products * `
        -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 `
        -property installationPath
}
if (-not $vsPath) {
    Write-Host "没有带 C++ 工具链的 Visual Studio，正在用 winget 装 Build Tools..." -ForegroundColor Yellow
    winget install --id Microsoft.VisualStudio.2022.BuildTools -e `
        --accept-source-agreements --accept-package-agreements `
        --override "--wait --passive --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
    throw "Build Tools 装完了，请重开一个 PowerShell 再跑本脚本。"
}
Write-Host "Visual Studio: $vsPath" -ForegroundColor Green
Write-Log ("Visual Studio: $vsPath")

# ---------------------------------------------------------------- 2. 拉源码
Write-Step "2/5 获取 llama.cpp 源码（不用预编译包）"

$repo = Join-Path $WorkDir 'llama.cpp'
if (-not (Test-Path (Join-Path $repo '.git'))) {
    if (Test-Path $repo) { Remove-Item -Recurse -Force $repo }   # 清掉上次没克隆完的残骸
    Invoke-Logged git clone --depth 1 https://github.com/ggml-org/llama.cpp.git $repo
} else {
    # 不能直接写 git -C <path>：-C 会被 PowerShell 当成函数自身的参数名前缀去匹配，
    # 报 "找不到接受实际参数 pull 的位置形式参数"。用数组展开传参。
    $gitArgs = @('-C', $repo, 'pull', '--ff-only')
    Invoke-Logged git @gitArgs
}
Set-Location $repo

Write-Log ("--- 编译开始 $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ---")
Write-Log ("commit: $(git rev-parse HEAD)")
Write-Log ("cmake : $(cmake --version | Select-Object -First 1)")
Write-Log ("cuda  : $(if ($Cuda) {'ON'} else {'OFF'})")
# ---------------------------------------------------------------- 3. 进 VS 开发环境
Write-Step "3/5 初始化 MSVC 环境（vcvars64）"

$vcvars = Join-Path $vsPath 'VC\Auxiliary\Build\vcvars64.bat'
if (-not (Test-Path $vcvars)) { throw "找不到 vcvars64.bat：$vcvars" }

# 把 vcvars 设好的环境变量搬进当前 PowerShell 会话
$tempBat = Join-Path $env:TEMP 'vcvars_probe.bat'
"@echo off`ncall `"$vcvars`"`nset" | Out-File -FilePath $tempBat -Encoding ascii
& cmd /c $tempBat | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        Set-Item -Path "env:$($Matches[1])" -Value $Matches[2]
    }
}
Remove-Item $tempBat -Force
Write-Host "cl.exe: $((Get-Command cl).Source)" -ForegroundColor Green
Write-Log ("cl    : $(cl 2>&1 | Select-Object -First 1)")
# vcvars64 偶尔探测不到 Windows SDK（rc.exe 不在 PATH、INCLUDE 缺 SDK 目录），
# 导致 cmake TryCompile 链接阶段报 "rc ... no such file or directory"。
# 这里手动兜底：若 rc 找不到，就扫描最新版 SDK 并把 bin/Include/Lib 补进环境。
if (-not (Get-Command rc -ErrorAction SilentlyContinue)) {
    Write-Host "rc.exe 不在 PATH，手动补 Windows SDK 路径..." -ForegroundColor Yellow
    $kitRoot = 'C:\Program Files (x86)\Windows Kits\10'
    $sdkVer = Get-ChildItem "$kitRoot\bin" -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match '^10\.\d+\.' } |
        Sort-Object { [version]$_.Name } -Descending |
        Select-Object -First 1 -ExpandProperty Name
    if (-not $sdkVer) { throw "vcvars64 没找到 SDK，$kitRoot\bin 下也没有任何 10.x 目录，请在 VS Installer 里安装 Windows 11 SDK" }
    $sdkBin = "$kitRoot\bin\$sdkVer\x64"
    $env:Path = "$sdkBin;$env:Path"
    $env:INCLUDE = "$env:INCLUDE;$kitRoot\Include\$sdkVer\ucrt;$kitRoot\Include\$sdkVer\um;$kitRoot\Include\$sdkVer\shared;$kitRoot\Include\$sdkVer\winrt"
    $env:LIB = "$env:LIB;$kitRoot\Lib\$sdkVer\ucrt\x64;$kitRoot\Lib\$sdkVer\um\x64"
    if (-not (Get-Command rc -ErrorAction SilentlyContinue)) { throw "补了 $sdkBin 之后 rc.exe 仍不可用" }
    Write-Host "已接入 Windows SDK $sdkVer" -ForegroundColor Green
    Write-Log ("SDK   : 手动接入 $sdkVer（vcvars64 未自动探测到）")
}

# ---------------------------------------------------------------- 4. configure
Write-Step "4/5 cmake configure"

$cmakeArgs = @('-B', 'build', '-G', 'Ninja')
# WinGet 的 Links\ninja.exe 是"执行别名存根"，cmake 的 ExecuteProcess 调不动它
# （会报 inappropriate file type or format）。这里改用 Packages 目录下的真身。
$ninjaReal = (Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Recurse -Filter ninja.exe -ErrorAction SilentlyContinue |
    Select-Object -First 1).FullName
if ($ninjaReal) {
    $cmakeArgs += "-DCMAKE_MAKE_PROGRAM=$ninjaReal"
    Write-Host "ninja 真身: $ninjaReal" -ForegroundColor Green
    Write-Log ("ninja 真身: $ninjaReal")
}
if ($Cuda) {
    if (-not (Test-Cmd 'nvcc')) {
        throw @"
没有检测到 nvcc。RTX 5060（Blackwell, sm_120）需要 CUDA Toolkit 12.8 或更高。
安装：https://developer.nvidia.com/cuda-downloads
装完后重开 PowerShell 再跑本脚本。
"@
    }
    $cmakeArgs += '-DGGML_CUDA=ON'
    $cmakeArgs += '-DCMAKE_CUDA_ARCHITECTURES=120'
    Write-Host "nvcc: $((Get-Command nvcc).Source)" -ForegroundColor Green
} else {
    Write-Host "使用 CPU 后端（不加 -Cuda 时）" -ForegroundColor Yellow
}
$cmakeArgs += '-DCMAKE_BUILD_TYPE=Release'

Invoke-Logged cmake @cmakeArgs

# ---------------------------------------------------------------- 5. build
Write-Step "5/5 cmake build（这一步最久，先去泡杯茶）"

Invoke-Logged cmake --build build --config Release --parallel $Jobs

Write-Log ("--- 编译结束 $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ---")
Write-Step "完成"
Get-ChildItem -Path 'build\bin' -Filter '*.exe' -ErrorAction SilentlyContinue |
    Select-Object -First 20 -ExpandProperty Name |
    ForEach-Object { Write-Log $_ }
Write-Host ""
Write-Host "编译日志: $script:LogPath" -ForegroundColor Green
Write-Host "下一步  : .\run.ps1 -Model <gemma gguf 路径>" -ForegroundColor Green
