@echo off
cd /d "%~dp0"
where vivado >nul 2>nul
if errorlevel 1 (echo Open a Vivado command prompt or add Vivado to PATH. & pause & exit /b 1)
call vivado -mode batch -source scripts/vivado/run_synthesis.tcl
set RV32I_EXIT_CODE=%ERRORLEVEL%
pause
exit /b %RV32I_EXIT_CODE%

