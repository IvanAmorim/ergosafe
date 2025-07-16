from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from common.models import User, Camera, CameraSide
from common.database import init_db
from common.crud import (
    create_user, get_users, create_camera, get_cameras,
    get_user_cameras, delete_user, delete_camera
)

app = FastAPI(title="User Service")

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

@app.delete("/users/{user_id}")
def api_delete_user(user_id: int):
    if not delete_user(user_id):
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")
    return {"message": "Utilizador eliminado com sucesso"}

@app.post("/cameras/", response_model=Camera)
def api_create_camera(camera: Camera):
    return create_camera(camera)

@app.get("/cameras/", response_model=list[Camera])
def api_get_cameras(side: CameraSide | None = None):
    return get_cameras(side)

@app.get("/users/{user_id}/cameras", response_model=list[Camera])
def api_get_user_cameras(user_id: int, side: CameraSide | None = None):
    return get_user_cameras(user_id, side)

@app.delete("/cameras/{camera_id}")
def api_delete_camera(camera_id: int):
    if not delete_camera(camera_id):
        raise HTTPException(status_code=404, detail="Câmara não encontrada")
    return {"message": "Câmara eliminada com sucesso"}
