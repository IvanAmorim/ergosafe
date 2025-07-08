# main.py

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from src.models import User, Camera
from src.database import init_db
from src.crud import create_user, get_users, create_camera, get_cameras, get_user_cameras, get_camera_by_id, delete_camera, delete_user
from src.stream_manager import start_acquisition, get_stream, stop_camera_stream
from src.influx_conf.query_scores import query_latest_table
from src.influx_conf.influx_config import INFLUX_BUCKET

app = FastAPI()

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

@app.post("/users/", response_model=User)
def api_create_user(user: User):
    return create_user(user)

@app.get("/users/", response_model=list[User])
def api_get_users():
    return get_users()

@app.post("/cameras/", response_model=Camera)
def api_create_camera(camera: Camera):
    return create_camera(camera)

@app.get("/cameras/", response_model=list[Camera])
def api_get_cameras():
    return get_cameras()

@app.get("/users/{user_id}/cameras", response_model=list[Camera])
def api_get_user_cameras(user_id: int):
    return get_user_cameras(user_id)

@app.post("/start/{camera_id}")
def api_start_stream(camera_id: int):
    # camera = get_camera_by_id(camera_id) 
    start_acquisition(camera_id)
    return {"message": "Stream started"}


@app.get("/stream/{camera_id}")
def api_get_stream(camera_id: int):
    stream = get_stream(camera_id)
    if not stream:
        raise HTTPException(status_code=404, detail="Stream não disponível")
    return stream
 
 
@app.get("/stop/{camera_id}")
def stop_acquisition(camera_id: int):
    stop_camera_stream(camera_id)
    return {"message": "Camera Stopped"}

@app.delete("/users/{user_id}")
def api_delete_user(user_id: int):
    if not delete_user(user_id):
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")
    return {"message": "Utilizador eliminado com sucesso"}


@app.delete("/cameras/{camera_id}")
def api_delete_camera(camera_id: int):
    if not delete_camera(camera_id):
        raise HTTPException(status_code=404, detail="Câmara não encontrada")
    return {"message": "Câmara eliminada com sucesso"}

#=== Scores ===

@app.get("/reba/{camera_id}/{operator}")
def api_get_reba_table(camera_id: int, operator: str):
    camera_tag = f"camera_{camera_id}"
    data = query_latest_table(bucket=INFLUX_BUCKET, measurement="reba_table", camera=camera_tag, operator=operator)
    if not data:
        raise HTTPException(status_code=404, detail="Dados REBA não encontrados")
    return {"camera": camera_tag, "operator": operator, "reba_table": data}


@app.get("/rula/{camera_id}/{operator}")
def api_get_rula_table(camera_id: int, operator: str):
    camera_tag = f"camera_{camera_id}"
    data = query_latest_table(bucket=INFLUX_BUCKET, measurement="rula_table", camera=camera_tag, operator=operator)
    if not data:
        raise HTTPException(status_code=404, detail="Dados RULA não encontrados")
    return {"camera": camera_tag, "operator": operator, "rula_table": data}
