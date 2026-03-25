# Troubleshooting Guide

## "Failed to fetch" Error

If you see "Failed to fetch" or "Error uploading dataset", check:

1. **Backend is Running**: 
   - Open a terminal/command prompt
   - Navigate to: `cd "c:\Users\DP\OneDrive\Desktop\charts generator\backend"`
   - Run: `python app.py`
   - You should see: `Running on http://127.0.0.1:5000`

2. **Check Backend Status**:
   - Open browser and go to: http://localhost:5000/api/chart-types
   - You should see JSON data with chart types

3. **Port Already in Use**:
   - If port 5000 is busy, stop other Python processes
   - Or change the port in `backend/app.py` (last line)

4. **CORS Issues**:
   - Make sure you're opening the HTML file directly (file://) or through a web server
   - The backend CORS is configured to allow all origins

## Chart Selector Not Working

1. **Check Browser Console**:
   - Press F12 to open developer tools
   - Go to Console tab
   - Look for any red error messages

2. **Verify API Connection**:
   - Check Network tab in developer tools
   - Look for requests to `http://localhost:5000/api/chart-types`
   - If they fail, the backend isn't running

3. **Refresh the Page**:
   - Hard refresh: Ctrl+F5 (Windows) or Cmd+Shift+R (Mac)

## File Upload Issues

1. **File Format**:
   - Only CSV (.csv) and Excel (.xlsx, .xls) files are supported
   - Make sure your file has headers in the first row

2. **File Size**:
   - Very large files may take time to process
   - Check browser console for specific error messages

3. **File Path Issues**:
   - Avoid special characters in filenames
   - The uploads folder is created automatically in `backend/uploads/`

## Quick Fixes

### Restart Backend:
```bash
cd "c:\Users\DP\OneDrive\Desktop\charts generator\backend"
python app.py
```

### Check if Backend is Running:
```bash
netstat -ano | findstr :5000
```

### Test Backend API:
Open in browser: http://localhost:5000/api/chart-types

### Clear Browser Cache:
- Press Ctrl+Shift+Delete
- Clear cached images and files
- Refresh the page

## Still Having Issues?

1. Check the terminal where the backend is running for error messages
2. Check browser console (F12) for JavaScript errors
3. Make sure Python and all dependencies are installed:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
