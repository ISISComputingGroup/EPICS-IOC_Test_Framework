@echo off
setlocal EnableDelayedExpansion

REM glob is case insensitive on windows but on linux would need [a-hA-H]* etc

call %~dp0run_all_tests.bat -tf "[a-h]*"
set ERRCODE=!ERRORLEVEL!
if !ERRCODE! EQU 0 (
    call %~dp0run_all_tests.bat -tf "[i-p]*"
    set ERRCODE=!ERRORLEVEL!
)
if !ERRCODE! EQU 0 (
    call %~dp0run_all_tests.bat -tf "[q-z]*"
    set ERRCODE=!ERRORLEVEL!
)
exit /b !ERRCODE!
