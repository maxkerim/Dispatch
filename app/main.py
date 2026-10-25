from fastapi import Depends, FastAPI, HTTPException, status
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import check_database, get_db
from app.models import Dispatch
from app.schemas import DispatchCreate, DispatchResponse, DispatchStatus, DispatchStatusUpdate

app = FastAPI(title="Dispatch API")
ALLOWED_STATUS_TRANSITIONS = {
    DispatchStatus.PENDING: {DispatchStatus.ASSIGNED, DispatchStatus.CANCELLED},
    DispatchStatus.ASSIGNED: {DispatchStatus.IN_TRANSIT, DispatchStatus.CANCELLED},
    DispatchStatus.IN_TRANSIT: {DispatchStatus.DELIVERED},
    DispatchStatus.DELIVERED: set(),
    DispatchStatus.CANCELLED: set(),
}


@app.get("/")
def root():
    return {"message": "Dispatch API is running"}


@app.post(
    "/dispatches",
    response_model=DispatchResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_dispatch(payload: DispatchCreate, db: Session = Depends(get_db)):
    dispatch = Dispatch(origin=payload.origin, destination=payload.destination)
    db.add(dispatch)
    db.commit()
    db.refresh(dispatch)
    return dispatch


@app.get("/dispatches/{dispatch_id}", response_model=DispatchResponse)
def get_dispatch(dispatch_id: int, db: Session = Depends(get_db)):
    dispatch = db.get(Dispatch, dispatch_id)
    if dispatch is None:
        raise HTTPException(status_code=404, detail="Dispatch not found")
    return dispatch


@app.patch("/dispatches/{dispatch_id}/status", response_model=DispatchResponse)
def update_dispatch_status(
    dispatch_id: int,
    payload: DispatchStatusUpdate,
    db: Session = Depends(get_db),
):
    dispatch = db.get(Dispatch, dispatch_id)
    if dispatch is None:
        raise HTTPException(status_code=404, detail="Dispatch not found")
    if payload.status not in ALLOWED_STATUS_TRANSITIONS[DispatchStatus(dispatch.status)]:
        raise HTTPException(status_code=409, detail="Invalid status transition")
    dispatch.status = payload.status.value
    db.commit()
    db.refresh(dispatch)
    return dispatch


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


Instrumentator().instrument(app).expose(app, include_in_schema=False)
