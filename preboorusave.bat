@echo off
For /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%a-%%b)
For /f "tokens=1-2 delims=/: " %%a in ('time /t') do (set mytime=%%a%%b)
mkdir .\db\%mydate%_%mytime%
xcopy .\db\* .\db\%mydate%_%mytime%
@echo on