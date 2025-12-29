# Troubleshooting Guide

## Common Issues and Fixes

### Error Loading Recommendations

**Symptoms:**
- Table shows "Error loading recommendations"
- Console shows errors

**Fixes:**

1. **Check if server is running:**
   ```powershell
   cd backend
   .\venv\Scripts\Activate.ps1
   python web_app.py
   ```

2. **Check browser console for errors:**
   - Open Developer Tools (F12)
   - Look at Console tab for error messages

3. **Verify data is loaded:**
   - Make sure CSV files are in the parent directory
   - Check that phase1_engine loaded successfully

4. **Check API endpoint:**
   - Visit http://localhost:5000/api/venues
   - Should return a list of venues

### Forecast Not Showing

**Symptoms:**
- Chart doesn't appear
- "No predictions available" message

**Fixes:**

1. **Make sure Phase 2 model is loaded:**
   ```powershell
   cd backend
   python train_demand_model.py
   ```
   This creates `backend/models/demand_model.joblib`

2. **Select venue and product:**
   - Must select both venue and product from dropdowns
   - Product dropdown populates after selecting venue

3. **Load recommendations first:**
   - Go to Recommendations section
   - Click "Apply Filters" to load recommendations
   - This ensures product data is available

4. **Check browser console:**
   - Look for JavaScript errors
   - Check Network tab for failed API calls

### Server Won't Start

**Symptoms:**
- "Address already in use" error
- Port 5000 is busy

**Fixes:**

1. **Stop existing process:**
   ```powershell
   Get-Process -Name python | Stop-Process -Force
   ```

2. **Use different port:**
   ```python
   app.run(debug=True, port=5001)
   ```

### No Data Showing

**Symptoms:**
- Empty tables
- "No recommendations found"

**Fixes:**

1. **Verify CSV files exist:**
   - Check parent directory for "Drink Pricing - *.csv" files
   - Should have at least one venue CSV

2. **Check file format:**
   - Must have columns: Name, Type of Liquor, Price
   - File naming: "Drink Pricing - [Venue Name].csv"

3. **Reload data:**
   - Restart the server
   - Engine reloads data on startup

### Charts Not Rendering

**Symptoms:**
- Blank chart areas
- JavaScript errors

**Fixes:**

1. **Check Chart.js is loaded:**
   - Should see Chart.js in Network tab
   - CDN: https://cdn.jsdelivr.net/npm/chart.js

2. **Clear browser cache:**
   - Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)

3. **Check console for errors:**
   - Chart.js requires canvas elements
   - Make sure HTML structure is correct

### Phase 2 Not Working

**Symptoms:**
- All recommendations show "Phase 1 (Market)"
- No demand predictions

**Fixes:**

1. **Train the model:**
   ```powershell
   python train_demand_model.py
   ```

2. **Check model file exists:**
   - Should be at `backend/models/demand_model.joblib`

3. **Restart server:**
   - Server loads model on startup
   - Restart after training

### CORS Errors

**Symptoms:**
- "CORS policy" errors in console
- API calls blocked

**Fixes:**

1. **CORS is already enabled in web_app.py:**
   ```python
   CORS(app)
   ```

2. **Make sure you're accessing correct URL:**
   - http://localhost:5000
   - Not file:// protocol

### Performance Issues

**Symptoms:**
- Slow loading
- Timeouts

**Fixes:**

1. **Reduce data size:**
   - Filter by venue instead of loading all
   - Use pagination

2. **Check number of products:**
   - Too many products can slow down
   - Consider batching

## Debug Mode

Enable debug logging:

1. **In web_app.py:**
   ```python
   app.run(debug=True, port=5000)
   ```

2. **Check console output:**
   - Server shows all requests
   - Python errors are printed

3. **Browser Developer Tools:**
   - Network tab: See all API calls
   - Console tab: See JavaScript errors
   - Application tab: Check local storage

## Getting Help

If issues persist:

1. Check browser console for errors
2. Check server console for Python errors
3. Verify all files are in correct locations
4. Make sure virtual environment is activated
5. Try restarting server

