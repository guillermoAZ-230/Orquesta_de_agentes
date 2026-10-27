import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import Base, engine


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ac01_solicitud_valida_y_calculo_saldo(client):
    # Crear ADMIN_RRHH (id=1)
    client.post(
        "/api/v1/empleados",
        json={
            "nombre": "Admin",
            "email": "admin@test.com",
            "rol": "ADMIN_RRHH",
            "anios_antiguedad": 5,
        },
    )

    # Crear MANAGER (id=2)
    client.post(
        "/api/v1/empleados",
        json={
            "nombre": "Manager",
            "email": "manager@test.com",
            "rol": "MANAGER",
            "anios_antiguedad": 3,
        },
        headers={"X-User-Id": "1"},
    )

    # Crear EMPLEADO (id=3, anios_antiguedad=3, manager_id=2)
    client.post(
        "/api/v1/empleados",
        json={
            "nombre": "Empleado",
            "email": "empleado@test.com",
            "rol": "EMPLEADO",
            "anios_antiguedad": 3,
            "manager_id": 2,
        },
        headers={"X-User-Id": "1"},
    )

    # Verificar saldo inicial: dias_totales = min(12 + 2*(3-1), 20) = 16
    response = client.get("/api/v1/vacaciones/saldo/3")
    assert response.status_code == 200
    data = response.json()
    assert data["dias_totales"] == 16
    assert data["saldo_disponible"] == 16

    # Solicitar 5 días
    response = client.post(
        "/api/v1/vacaciones/solicitar",
        json={
            "empleado_id": 3,
            "dias_solicitados": 5,
            "motivo": "Vacaciones de verano",
        },
    )
    assert response.status_code == 201
    sol_data = response.json()
    assert sol_data["estado"] == "PENDING"
    solicitud_id = sol_data["id"]

    # Manager aprueba
    response = client.post(
        f"/api/v1/vacaciones/{solicitud_id}/revisar",
        json={"accion": "APPROVE"},
        headers={"X-User-Id": "2"},
    )
    assert response.status_code == 200
    rev_data = response.json()
    assert rev_data["estado"] == "APPROVED"

    # Verificar nuevo saldo: 16 - 5 = 11
    response = client.get("/api/v1/vacaciones/saldo/3")
    assert response.status_code == 200
    saldo_data = response.json()
    assert saldo_data["saldo_disponible"] == 11


def test_ac02_saldo_insuficiente(client):
    # Crear ADMIN_RRHH (id=1)
    client.post(
        "/api/v1/empleados",
        json={
            "nombre": "Admin",
            "email": "admin@test.com",
            "rol": "ADMIN_RRHH",
            "anios_antiguedad": 5,
        },
    )

    # Crear EMPLEADO (id=2, anios_antiguedad=1 -> 12 días)
    client.post(
        "/api/v1/empleados",
        json={
            "nombre": "Empleado",
            "email": "empleado@test.com",
            "rol": "EMPLEADO",
            "anios_antiguedad": 1,
        },
        headers={"X-User-Id": "1"},
    )

    # Intentar solicitar 15 días (excede saldo de 12)
    response = client.post(
        "/api/v1/vacaciones/solicitar",
        json={
            "empleado_id": 2,
            "dias_solicitados": 15,
            "motivo": "Demasiados días",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Insufficient vacation balance"


def test_ac03_manager_no_autorizado(client):
    # Crear ADMIN_RRHH (id=1)
    client.post(
        "/api/v1/empleados",
        json={
            "nombre": "Admin",
            "email": "admin@test.com",
            "rol": "ADMIN_RRHH",
            "anios_antiguedad": 5,
        },
    )

    # Crear MANAGER A (id=2)
    client.post(
        "/api/v1/empleados",
        json={
            "nombre": "Manager A",
            "email": "manager_a@test.com",
            "rol": "MANAGER",
            "anios_antiguedad": 3,
        },
        headers={"X-User-Id": "1"},
    )

    # Crear MANAGER B (id=3)
    client.post(
        "/api/v1/empleados",
        json={
            "nombre": "Manager B",
            "email": "manager_b@test.com",
            "rol": "MANAGER",
            "anios_antiguedad": 3,
        },
        headers={"X-User-Id": "1"},
    )

    # Crear EMPLEADO (id=4, manager_id=2)
    client.post(
        "/api/v1/empleados",
        json={
            "nombre": "Empleado",
            "email": "empleado@test.com",
            "rol": "EMPLEADO",
            "anios_antiguedad": 2,
            "manager_id": 2,
        },
        headers={"X-User-Id": "1"},
    )

    # Empleado 4 solicita 3 días
    response = client.post(
        "/api/v1/vacaciones/solicitar",
        json={
            "empleado_id": 4,
            "dias_solicitados": 3,
            "motivo": "Vacaciones",
        },
    )
    assert response.status_code == 201
    solicitud_id = response.json()["id"]

    # MANAGER B (id=3) intenta aprobar -> NO es su jefe directo
    response = client.post(
        f"/api/v1/vacaciones/{solicitud_id}/revisar",
        json={"accion": "APPROVE"},
        headers={"X-User-Id": "3"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Unauthorized: Not the direct manager"
