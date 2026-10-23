import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://dispatch:dispatch@localhost:5432/dispatch",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    with SessionLocal() as session:
        yield session


def check_database():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))