from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: str

    cameras: List["Camera"] = Relationship(back_populates="user")


class Camera(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    url: str
    
    user: Optional[User] = Relationship(back_populates="cameras")

