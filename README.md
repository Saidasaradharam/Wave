# Wave

A real-time team coordination platform built with FastAPI, React, and Google Cloud Services.

## Features
- Real-time team dashboard (kanban)
- Task assignment and tracking
- Team communication via comments
- Google Cloud Storage file attachments
- User authentication
- Google Cloud metrics, logging, and security

## Tech Stack
- **Backend:** FastAPI, PostgreSQL, SQLAlchemy
- **Frontend:** React, Vite, Tailwind CSS
- **Google Services:** Cloud Run, Cloud Storage, Secret Manager, Cloud Logging, Cloud Monitoring, Cloud SQL, Firebase Auth, Google Analytics.

## Setup Instructions

### Backend Setup
1. `cd backend`
2. `python -m venv venv`
3. `source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
4. `pip install -r requirements.txt`
5. Configure `.env` file from `.env.example`
6. `uvicorn main:app --reload`

### Frontend Setup
1. `cd frontend`
2. `npm install`
3. `npm run dev`

### Testing
- Backend: `cd backend && pytest`
- Frontend: `cd frontend && npm test`
