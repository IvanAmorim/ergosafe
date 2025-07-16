# Ergosafe

This project provides tools for streaming RTSP cameras and performing ergonomic assessment using YOLO pose detection.

## Structure

- `ergosafe/` – Python package with application code
- `scripts/` – Example scripts (`stream_server.py`, `camera_driver.py`)
- `config/` – Camera configuration files
- `openapi.yaml` – API specification

## Running the API

Install dependencies and run FastAPI with uvicorn:

```bash
pip install -r requirements.txt
uvicorn ergosafe.main:app --reload
```

