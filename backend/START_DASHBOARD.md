# How to Start the Dashboard

## Quick Start (Windows)

**Option 1: Double-click the batch file**
- Double-click `start_dashboard.bat` in the `backend` folder

**Option 2: Manual command**
Open PowerShell or Command Prompt and run:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
streamlit run pricing_dashboard.py
```

## What Happens

1. Streamlit will start the server
2. Your browser should automatically open to `http://localhost:8501`
3. If not, manually go to: `http://localhost:8501`

## To Stop

Press `Ctrl+C` in the terminal window where Streamlit is running

## Troubleshooting

**If port 8501 is already in use:**
- Streamlit will automatically try port 8502, 8503, etc.
- Check the terminal output for the actual URL

**If you get "streamlit not found":**
- Make sure you activated the virtual environment first:
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```

**If dashboard shows errors:**
- Make sure `pricing_recommendations.csv` exists (run `python pricing_engine.py` first)


