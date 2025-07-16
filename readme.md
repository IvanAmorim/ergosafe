# Ergosafe Microservices

This repository contains the Ergosafe application organised into three
FastAPI microservices located under the `microservices/` folder. Each service
can be run individually via `docker-compose`.

## Services

- **user-service** – manages users and cameras (CRUD endpoints).
- **camera-service** – handles camera streaming and pose detection.
- **analytics-service** – exposes REBA/RULA query endpoints.

Run all services together with:

```bash
docker-compose up --build
```
