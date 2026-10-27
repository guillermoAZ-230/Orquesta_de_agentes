# ARCHITECTURE.md

## 1. MODELO DE DATOS (SQLite / SQLAlchemy)

Definición exacta de las entidades usando `DeclarativeBase`.

```python
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship

class Base(DeclarativeBase):
    pass

class Empleado(Base):
    __tablename__ = "empleados"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    rol = Column(String, nullable=False) # 'EMPLEADO', 'MANAGER', 'ADMIN_RRHH'
    anios_antiguedad = Column(Integer, nullable=False, default=1)
    manager_id = Column(Integer, ForeignKey("empleados.id"), nullable=True)

class SolicitudVacaciones(Base):
    __tablename__ = "solicitudes_vacaciones"
    id = Column(Integer, primary_key=True, autoincrement=True)
    empleado_id = Column(Integer, ForeignKey("empleados.id"), nullable=False)
    dias_solicitados = Column(Integer, nullable=False)
    motivo = Column(String, nullable=True)
    estado = Column(String, nullable=False, default="PENDING") # 'PENDING', 'APPROVED', 'REJECTED'
    revisado_por_id = Column(Integer, ForeignKey("empleados.id"), nullable=True)
```

## 2. ESQUEMAS PYDANTIC V2

Clases de validación y serialización.

```python
from pydantic import BaseModel, ConfigDict
from typing import Optional

class EmpleadoCreate(BaseModel):
    nombre: str
    email: str
    rol: str
    anios_antiguedad: int
    manager_id: Optional[int] = None

class EmpleadoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    email: str
    rol: str
    anios_antiguedad: int
    manager_id: Optional[int] = None

class SaldoResponse(BaseModel):
    empleado_id: int
    dias_totales: int
    dias_aprobados: int
    saldo_disponible: int

class SolicitudCreate(BaseModel):
    empleado_id: int
    dias_solicitados: int
    motivo: Optional[str] = None

class RevisionRequest(BaseModel):
    accion: str # 'APPROVE' o 'REJECT'

class SolicitudResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    empleado_id: int
    dias_solicitados: int
    motivo: Optional[str]
    estado: str
    revisado_por_id: Optional[int]
```

## 3. ENDPOINTS REST Y RBAC

Lógica de negocio y control de acceso. Autenticación vía header `X-User-Id`.

1.  **`GET /health`**
    *   **Acceso:** Público.
    *   **Respuesta:** `200 OK` `{"status": "ok"}`.

2.  **`POST /api/v1/empleados`**
    *   **Input:** `EmpleadoCreate`.
    *   **RBAC:**
        *   Si `COUNT(empleados) == 0`: Permite creación sin validar rol (bootstrap).
        *   Si `COUNT(empleados) > 0`: Usuario `X-User-Id` debe tener `rol == 'ADMIN_RRHH'`. Si no, `403 Forbidden`.
    *   **Respuesta:** `201 Created` con `EmpleadoResponse`.

3.  **`GET /api/v1/vacaciones/saldo/{empleado_id}`**
    *   **Cálculo:**
        *   `dias_totales = min(12 + 2 * max(anios_antiguedad - 1, 0), 20)`
        *   `dias_aprobados = SUM(dias_solicitados) WHERE empleado_id == id AND estado == 'APPROVED'`
        *   `saldo_disponible = dias_totales - dias_aprobados`
    *   **Respuesta:** `200 OK` con `SaldoResponse`.

4.  **`POST /api/v1/vacaciones/solicitar`**
    *   **Input:** `SolicitudCreate`.
    *   **Validación:**
        *   Calcular `saldo_disponible` actual del `empleado_id`.
        *   Si `dias_solicitados > saldo_disponible`: `400 Bad Request` `{"detail": "Insufficient vacation balance"}`.
    *   **Acción:** Crear registro con `estado='PENDING'`.
    *   **Respuesta:** `201 Created` con `SolicitudResponse`.

5.  **`POST /api/v1/vacaciones/{solicitud_id}/revisar`**
    *   **Input:** `RevisionRequest`.
    *   **RBAC:**
        *   Usuario `X-User-Id` debe existir.
        *   Usuario debe tener `rol == 'MANAGER'`.
        *   El `empleado_id` de la solicitud debe tener `manager_id == X-User-Id`.
        *   Si falla cualquiera: `403 Forbidden` `{"detail": "Unauthorized: Not the direct manager"}`.
    *   **Validación de Estado:**
        *   Si `solicitud.estado != 'PENDING'`: `400 Bad Request`.
    *   **Acción:**
        *   Si `accion == 'APPROVE'`: `estado = 'APPROVED'`.
        *   Si `accion == 'REJECT'`: `estado = 'REJECTED'`.
        *   `revisado_por_id = X-User-Id`.
    *   **Respuesta:** `200 OK` con `SolicitudResponse`.