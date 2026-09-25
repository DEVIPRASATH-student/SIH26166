@echo off
echo ===================================================
echo Starting LunarSynapse Backend (FastAPI + Uvicorn)
echo ===================================================
cd ..\..
python -m uvicorn outgraph.backend.app.main:app --host 127.0.0.1 --port 8000 --reload
pause
