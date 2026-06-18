# AI Kubernetes Agent

AI-powered on-demand Kubernetes troubleshooting system.

## Quick Start

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Health check: http://localhost:8000/health

## Project Structure

```
ai-kubernetes-agent/
├── backend/          FastAPI backend
├── frontend/         Next.js frontend
├── docs/             Documentation
├── prompts/          Prompt files
├── docker-compose.yml
└── README.md
```

## Development (without Docker)

**Backend**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

**Frontend**
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```
