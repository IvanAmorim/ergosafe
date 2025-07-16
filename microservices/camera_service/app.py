from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from common.stream_manager import start_acquisition, get_stream, stop_camera_stream, get_dual_stream
from common.database import init_db
from common.crud import get_camera_by_id

app = FastAPI(title="Camera Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

@app.post("/start/{camera_id}")
def api_start_stream(camera_id: int):
    start_acquisition(camera_id)
    return {"message": "Stream started"}

@app.get("/stream/{camera_id}")
def api_get_stream(camera_id: int):
    return get_stream(camera_id)

@app.get("/dual_stream/{front_id}/{side_id}")
def api_get_dual_stream(front_id: int, side_id: int):
    return get_dual_stream(front_id, side_id)

@app.get("/stop/{camera_id}")
def api_stop_stream(camera_id: int):
    stop_camera_stream(camera_id)
    return {"message": "Camera Stopped"}
