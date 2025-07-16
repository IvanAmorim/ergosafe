# gateway.py

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI(title="API Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Define domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# URLs dos serviços internos
USER_SERVICE_URL = "http://user-service:8001"
CAMERA_SERVICE_URL = "http://camera-service:8002"
ANALYTICS_SERVICE_URL = "http://analytics-service:8003"

# Helper para encaminhar requests
async def proxy_request(client: httpx.AsyncClient, method: str, url: str, request: Request):
    try:
        req_data = await request.body()
        headers = dict(request.headers)
        response = await client.request(
            method,
            url,
            content=req_data,
            headers=headers,
            params=request.query_params
        )
        return response
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.api_route("/users/{full_path:path}", methods=["GET", "POST", "DELETE"])
async def users_proxy(request: Request, full_path: str):
    async with httpx.AsyncClient() as client:
        url = f"{USER_SERVICE_URL}/users/{full_path}"
        response = await proxy_request(client, request.method, url, request)
    return response.json(), response.status_code


@app.api_route("/cameras/{full_path:path}", methods=["GET", "POST", "DELETE"])
async def cameras_proxy(request: Request, full_path: str):
    async with httpx.AsyncClient() as client:
        url = f"{USER_SERVICE_URL}/cameras/{full_path}"
        response = await proxy_request(client, request.method, url, request)
    return response.json(), response.status_code


@app.api_route("/stream/{full_path:path}", methods=["GET", "POST"])
async def stream_proxy(request: Request, full_path: str):
    async with httpx.AsyncClient() as client:
        url = f"{CAMERA_SERVICE_URL}/stream/{full_path}"
        response = await proxy_request(client, request.method, url, request)
    return response.content, response.status_code  # pode ser imagem ou stream


@app.api_route("/start/{camera_id}", methods=["POST"])
async def start_camera_proxy(camera_id: int, request: Request):
    async with httpx.AsyncClient() as client:
        url = f"{CAMERA_SERVICE_URL}/start/{camera_id}"
        response = await proxy_request(client, request.method, url, request)
    return response.json(), response.status_code


@app.api_route("/analytics/{path:path}", methods=["GET"])
async def analytics_proxy(request: Request, path: str):
    async with httpx.AsyncClient() as client:
        url = f"{ANALYTICS_SERVICE_URL}/{path}"
        response = await proxy_request(client, request.method, url, request)
    return response.json(), response.status_code
