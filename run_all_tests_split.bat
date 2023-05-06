@echo off
setlocal EnableDelayedExpansion

REM glob is case insensitive on windows but on linux would need [a-hA-H]* etc
REM have had issues with instrona and ngpsu, so split here

call %~dp0run_all_tests.bat -tf "[a-h]*"
set ERRCODE=!ERRORLEVEL!
if !ERRCODE! EQU 0 (
    call %~dp0run_all_tests.bat -tf "[i-m]*"
    set ERRCODE=!ERRORLEVEL!
)
if !ERRCODE! EQU 0 (
    call %~dp0run_all_tests.bat -tf "[n-z]*"
    set ERRCODE=!ERRORLEVEL!
)
exit /b !ERRCODE!
