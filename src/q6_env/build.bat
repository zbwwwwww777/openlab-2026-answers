@echo off
rem ---------------------------------------------------------------
rem  Q6 / VSCode C-C++ build helper
rem
rem  Why this file exists:
rem    cl.exe is not on PATH in a normal terminal, and on this machine
rem    vcvars64.bat fails to register the Windows SDK (so stdio.h and
rem    kernel32.lib could not be found). This script sets up both, then
rem    compiles hello.c with debug info.
rem
rem  Usage (plain terminal, no need for "x64 Native Tools" prompt):
rem      build.bat
rem      hello.exe 7
rem
rem  /utf-8 is required because hello.c contains Chinese comments and
rem  MSVC would otherwise emit: warning C4819 (code page 936).
rem ---------------------------------------------------------------
setlocal

set "VS=C:\Program Files\Microsoft Visual Studio\18\Community"
set "SDK=C:\Program Files (x86)\Windows Kits\10"
set "SDKVER=10.0.26100.0"

call "%VS%\VC\Auxiliary\Build\vcvars64.bat" >nul

rem --- manually append the Windows SDK paths that vcvars64 missed ---
set "INCLUDE=%INCLUDE%;%SDK%\Include\%SDKVER%\ucrt;%SDK%\Include\%SDKVER%\um;%SDK%\Include\%SDKVER%\shared;%SDK%\Include\%SDKVER%\winrt"
set "LIB=%LIB%;%SDK%\Lib\%SDKVER%\ucrt\x64;%SDK%\Lib\%SDKVER%\um\x64"

cd /d "%~dp0"

cl /Zi /EHsc /utf-8 /Fe:hello.exe hello.c
if errorlevel 1 (
    echo [build.bat] compile failed
    exit /b 1
)
echo [build.bat] OK. hello.exe ready.
endlocal
