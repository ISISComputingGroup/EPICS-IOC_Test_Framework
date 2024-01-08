@echo off
setlocal EnableDelayedExpansion

REM glob is case insensitive on windows but on linux would need [a-hA-H]* etc
REM have had issues with instrona and ngpsu, hence split here at i and n

set final_errcode=0

for %%i in ( "a-h" "i" "j-m" "n" "o-z" ) do (
    call %~dp0run_all_tests.bat -tf "[%%~i]*"
    if !errorlevel! NEQ 0 (
        @echo ERROR: code !errorlevel! returned from [%%i] tests in run_all_tests_split.bat
        @echo ERROR: will continue running tests, but will return overall failure code at end
        set final_errcode=!errorlevel!
    )
)

exit /b !final_errcode!
