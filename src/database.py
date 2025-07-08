from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/mydb"

engine = create_engine(DATABASE_URL, echo=True)


def get_session():
    return Session(engine)


def init_db():
    SQLModel.metadata.create_all(engine)

