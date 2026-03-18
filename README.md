# Project Manager System

מערכת ניהול תקציב לבנייה (BMS - Building Management System)

## Stack
- **Backend**: FastAPI, SQLAlchemy, PostgreSQL, Pydantic v2, JWT, Redis, ReportLab
- **Frontend**: React 18, TypeScript, Redux Toolkit, Tailwind CSS, Recharts, Radix UI

## Development

### Backend
```bash
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Branch Strategy
- `feature/*` — פיצ'רים חדשים
- `bugfix/*` — תיקוני באגים
- כל commit בפורמט Conventional Commits: `feat:`, `fix:`, `chore:`, `refactor:`, `test:`
