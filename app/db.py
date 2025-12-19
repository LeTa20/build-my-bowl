from sqlmodel import SQLModel, create_engine, Session
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://app:app@localhost:5432/app",
)

engine = create_engine(DATABASE_URL, echo=False)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session