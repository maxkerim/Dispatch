import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture
def client(monkeypatch):
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    monkeypatch.setattr("app.main.engine", test_engine)
    TestSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)

    def override_get_db():
        with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


def test_create_dispatch_persists_to_database(client):
    response = client.post(
        "/dispatches",
        json={"origin": "  Depot A  ", "destination": "Customer B"},
    )

    assert response.status_code == 201
    dispatch = response.json()
    assert dispatch["origin"] == "Depot A"
    assert dispatch["status"] == "pending"

    stored = client.get(f"/dispatches/{dispatch['id']}")
    assert stored.status_code == 200
    assert stored.json()["destination"] == "Customer B"


def test_create_dispatch_rejects_blank_address(client):
    response = client.post(
        "/dispatches",
        json={"origin": "   ", "destination": "Customer B"},
    )

    assert response.status_code == 422


def test_get_dispatch_returns_not_found(client):
    response = client.get("/dispatches/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Dispatch not found"


def test_metrics_endpoint_exposes_prometheus_metrics(client):
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "http_requests_total" in response.text


def test_dispatch_status_follows_valid_transitions(client):
    dispatch = client.post(
        "/dispatches",
        json={"origin": "Depot A", "destination": "Customer B"},
    ).json()

    for next_status in ("assigned", "in_transit", "delivered"):
        response = client.patch(
            f"/dispatches/{dispatch['id']}/status",
            json={"status": next_status},
        )
        assert response.status_code == 200
        assert response.json()["status"] == next_status


def test_dispatch_status_rejects_invalid_transition(client):
    dispatch = client.post(
        "/dispatches",
        json={"origin": "Depot A", "destination": "Customer B"},
    ).json()

    response = client.patch(
        f"/dispatches/{dispatch['id']}/status",
        json={"status": "delivered"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Invalid status transition"


def test_dispatch_status_rejects_unknown_value(client):
    dispatch = client.post(
        "/dispatches",
        json={"origin": "Depot A", "destination": "Customer B"},
    ).json()

    response = client.patch(
        f"/dispatches/{dispatch['id']}/status",
        json={"status": "teleported"},
    )

    assert response.status_code == 422