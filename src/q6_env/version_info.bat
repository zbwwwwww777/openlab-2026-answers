@echo off
rem ---------------------------------------------------------------
rem  Prints everything needed for the "version info" screenshot:
rem  machine / user / path + VSCode + MSVC cl.exe + Python.
rem  Run it in the VSCode integrated terminal, then take one screenshot.
rem ---------------------------------------------------------------
echo ===== 1. machine =====
echo user: %USERNAME%    host: %COMPUTERNAME%
echo cwd : %CD%
echo time: %DATE% %TIME%
echo.
echo ===== 2. VSCode =====
code --version
echo.
echo ===== 3. cl.exe (MSVC) =====
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
cl
echo.
echo ===== 4. Python =====
python --version
where python
