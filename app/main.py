from fastapi import FastAPI, HTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.database import check_database

app = FastAPI(title="Dispatch API")


@app.get("/")
def root():
    return {"message": "Dispatch API is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/ready")
def ready():
    try:
        check_database()
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return {"status": "ready"}
