# Quick Start Guide

## Backend is Running! ✅

The Flask backend server should be running on `http://localhost:5000`

## To Use the Application:

### Option 1: HTML Frontend (Easiest - No Flutter needed!)
1. Open `frontend/index.html` in your web browser
2. The app will connect to the backend automatically
3. Start creating charts!

### Option 2: Flutter Frontend (If Flutter is installed)
1. Open a new terminal
2. Navigate to frontend folder:
   ```bash
   cd "c:\Users\DP\OneDrive\Desktop\charts generator\frontend"
   ```
3. Install dependencies:
   ```bash
   flutter pub get
   ```
4. Run the app:
   ```bash
   flutter run -d chrome
   ```

## Testing the Backend

You can test if the backend is running by opening:
- http://localhost:5000/api/chart-types

This should return JSON with available chart types.

## If Backend is Not Running

Start it manually:
```bash
cd "c:\Users\DP\OneDrive\Desktop\charts generator\backend"
python app.py
```

## Usage Flow

1. **Select Chart Type**: Choose "Pie Chart"
2. **Select Dataset**: Choose the sample dataset or upload your own CSV/Excel file
3. **Select Column**: Pick which column to visualize
4. **Customize**: Set title, fonts, colors
5. **Generate**: Create your chart
6. **Export**: Download as PNG, PDF, HTML, or get R code

Enjoy creating charts! 🎨📊
