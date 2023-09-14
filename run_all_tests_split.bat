@echo off
setlocal EnableDelayedExpansion

REM glob is case insensitive on windows but on linux would need [a-hA-H]* etc
REM have had issues with instrona and ngpsu, so split here

for %%i in ( "a-h" "i" "j-m" "n" "o-z" ) do (
    call %~dp0run_all_tests.bat -tf "[%%~i]*"
    if !errorlevel! NEQ 0 (
        @echo ERROR code !errorlevel! returned from run_all_tests.bat
        exit /b !errorlevel!
    )
)
exit /b 0
