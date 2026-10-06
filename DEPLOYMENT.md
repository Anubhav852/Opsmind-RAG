# OpsMind Deployment

## Architecture

Frontend:
- Vercel
- React + Vite
- Root directory: `web`

Backend:
- Render
- FastAPI
- Root directory: repository root
- Build: `pip install -r requirements.txt`
- Start: `uvicorn opsmind.main:app --host 0.0.0.0 --port $PORT`

## Frontend environment variable

Vercel:

VITE_API_URL=https://YOUR-OPSMIND-BACKEND.onrender.com

## Backend

Health:

/health

OpenAPI:

/openapi.json

## Local development

Backend:

cd ~/Opsmind/opsmind
source .venv/bin/activate
export PYTHONPATH="$PWD/src:$PYTHONPATH"
uvicorn opsmind.main:app --host 0.0.0.0 --port 8000

Frontend:

cd ~/Opsmind/opsmind/web
npm run dev -- --host 0.0.0.0
