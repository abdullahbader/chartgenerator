# Setup Instructions

## Backend Setup (Python)

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Copy the sample dataset to the backend sample_datasets folder:
```bash
# The sample_data.csv should already be in backend/sample_datasets/
```

6. Run the Flask server:
```bash
python app.py
```

The backend will run on `http://localhost:5000`

## Frontend Setup (Flutter)

1. Make sure Flutter is installed on your system:
```bash
flutter --version
```

2. Navigate to the frontend directory:
```bash
cd frontend
```

3. Get Flutter dependencies:
```bash
flutter pub get
```

4. Run the Flutter web app:
```bash
flutter run -d chrome
```

Or for web:
```bash
flutter run -d web-server --web-port 8080
```

## Usage

1. Start the backend server first (Python Flask)
2. Start the Flutter frontend
3. Open the app in your browser
4. Select "Pie Chart" from the chart types
5. Choose a dataset (or upload your own CSV/Excel file)
6. Select a column
7. Customize your chart (colors, fonts, title)
8. Generate and export your chart in PNG, PDF, HTML, or get the R code

## Notes

- The backend API runs on port 5000 by default
- Make sure CORS is enabled (already configured in the backend)
- Sample dataset is included: `backend/sample_datasets/sample_data.csv`
- Uploaded datasets are stored in memory (for production, use a database)
