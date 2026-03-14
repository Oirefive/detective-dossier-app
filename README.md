# Detective Dossier

Investigation dossier application with a React frontend and a Python backend.

## Stack

- React + Vite + TypeScript for the UI
- FastAPI for the backend API
- SQLite for local storage
- ReportLab for PDF generation

## Quick Start

```bash
npm install
python -m pip install -r requirements.txt
python -m backend.app
npm run dev
```

Frontend: `http://127.0.0.1:1420`

Backend: `http://127.0.0.1:8000`

## Structure

- `src/` React UI
- `backend/` Python API, database access, PDF generation
- `app_data/` generated SQLite database and exported PDFs

## Notes

- PDF files are generated into `app_data/exports/`
- The old `src-tauri/` code is kept as legacy and is no longer used by the frontend
