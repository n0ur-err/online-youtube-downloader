@echo off
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Starting server on http://localhost:5000
python server.py
