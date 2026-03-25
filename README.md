# Charts Generator

A web application for generating customizable charts with support for multiple export formats including PDF, HTML, PNG, and R code.

## Project Structure

- `backend/` - Python backend API (Flask/FastAPI)
- `frontend/` - Flutter web application
- `sample_datasets/` - Preloaded sample datasets

## Features

- Chart type selection (starting with Pie Chart)
- Dataset upload and selection
- Chart customization (colors, fonts, font sizes)
- Multiple export formats: PDF, HTML, PNG, R Code

## Getting Started

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
python app.py
```

### Frontend Setup
```bash
cd frontend
flutter pub get
flutter run -d chrome
```
