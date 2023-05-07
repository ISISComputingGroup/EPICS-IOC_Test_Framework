@echo off
setlocal EnableDelayedExpansion

REM glob is case insensitive on windows but on linux would need [a-hA-H]* etc
REM have had issues with instrona and ngpsu, so split here

for %%i in ( "a-h" "i" "j-m" "n" "o-z" ) do (
    call %~dp0run_all_tests.bat -tf "[%%~i]*"
    if !ERRCODE! NEQ 0 (
        @echo ERROR code !ERRCODE! returned from run_all_tests.bat
        exit /b !ERRCODE!
    )
)
exit /b 0
