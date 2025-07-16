# Ergosafe

This project provides tools for streaming RTSP cameras and performing ergonomic assessment using YOLO pose detection.

## Structure

- `ergosafe/api/` – FastAPI service exposing the HTTP API
- `ergosafe/db/` – database models and CRUD helpers
- `ergosafe/streaming/` – camera drivers and pose inference logic
- `ergosafe/scoring/` – utilities to compute REBA and RULA scores
- `ergosafe/influx/` – InfluxDB client configuration and helpers
- `scripts/` – example helper scripts (`stream_server.py`, `camera_driver.py`)
- `config/` – camera configuration files
- `openapi.yaml` – API specification

## Running the API

Install dependencies and run FastAPI with uvicorn:

```bash
pip install -r requirements.txt
uvicorn ergosafe.api.main:app --reload
```

