# Ord HQ Dashboard Runtime

This folder contains the real-time FastAPI stream used by the React dashboard.

## Start API

```bash
uvicorn dashboard.realtime_api:app --reload --host 0.0.0.0 --port 8000
```

## Frontend WS URL

Set this env var before running Vite:

```bash
VITE_ORD_WS_URL=ws://localhost:8000/ws/dashboard
```
