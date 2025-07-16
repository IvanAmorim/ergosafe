# src/crud.py
from sqlmodel import select, Session
from ergosafe.models import User, Camera
from ergosafe.database import get_session, engine
from typing import Optional


def create_user(user: User) -> User:
    with get_session() as session:
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def get_users() -> list[User]:
    with get_session() as session:
        return session.exec(select(User)).all()


def create_camera(camera: Camera) -> Camera:
    with get_session() as session:
        session.add(camera)
        session.commit()
        session.refresh(camera)
        return camera


def get_cameras() -> list[Camera]:
    with get_session() as session:
        return session.exec(select(Camera)).all()


def get_user_cameras(user_id: int) -> list[Camera]:
    with get_session() as session:
        return session.exec(select(Camera).where(Camera.user_id == user_id)).all()
    
def get_camera_by_id(camera_id: int) -> Optional[Camera]:
    with Session(engine) as session:
        statement = select(Camera).where(Camera.id == camera_id)
        result = session.execute(statement).scalar_one_or_none()
        return result

def delete_user(user_id: int) -> bool:
    with get_session() as session:
        user = session.get(User, user_id)
        if user:
            session.delete(user)
            session.commit()
            return True
        return False


def delete_camera(camera_id: int) -> bool:
    with get_session() as session:
        camera = session.get(Camera, camera_id)
        if camera:
            session.delete(camera)
            session.commit()
            return True
        return False