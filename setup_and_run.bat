@echo off
REM Add Node.js to PATH
set PATH=C:\Program Files\nodejs;%PATH%

REM Verify installation
echo Verification:
node --version
npm --version

echo.
echo Installing npm dependencies...
npm install

echo.
echo Done! Now you can run:
echo   npm start
echo.
pause
