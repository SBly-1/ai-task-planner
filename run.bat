@echo off
:: Navigate to the directory where the batch file is located
cd /d "%~dp0"

:: Use 'call' to run poetry without terminating the batch file early
call poetry run chainlit run app.py -w

:: Keep the window open so you can see output/errors
pause
