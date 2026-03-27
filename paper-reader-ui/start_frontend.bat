@echo off
cd /d %~dp0

echo [1/2] Installing frontend dependencies...
npm install

echo [2/2] Starting frontend server...
npm run dev

pause