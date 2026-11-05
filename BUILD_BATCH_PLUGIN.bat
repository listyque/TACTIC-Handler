@echo off
setlocal
cd /d "%~dp0"
set /p "pluginVersion=Plugin version (for example 1.0.1): "
set /p "pluginOutput=Release output folder: "
py -3 tools\client_plugins.py build --version "%pluginVersion%" --output "%pluginOutput%"
set "plugin_exit=%errorlevel%"
pause
exit /b %plugin_exit%
