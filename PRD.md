# PRD: TalentCore API

## 1. ROLES DEL SISTEMA
*   **EMPLEADO**: Consulta saldo personal y crea solicitudes de vacaciones propias.
*   **MANAGER**: Aprueba o rechaza solicitudes exclusivamente de subordinados directos (`empleado.manager_id == manager.id`).
*   **ADMIN_RRHH**: Único rol autorizado para crear registros de empleados.

## 2. REGLA DE SALDO DE VACACIONES
*   **Cálculo de Días Totales**:
    *   Si `anios_antiguedad < 1`: `dias_totales = 12`.
    *   Si `anios_antiguedad >= 1`: `dias_totales = min(12 + 2 * (anios_antiguedad - 1), 20)`.
*   **Saldo Disponible**:
    *   `saldo_disponible = dias_totales - SUM(dias_solicitados WHERE estado == 'APPROVED')`.
*   **Validación**: Toda nueva solicitud debe cumplir `dias_solicitados <= saldo_disponible`.

## 3. MÁQUINA DE ESTADOS DE SOLICITUD
*   **Estados**: `PENDING` (inicial), `APPROVED` (descuenta saldo), `REJECTED` (no descuenta saldo).
*   **Transiciones**:
    *   Creación -> `PENDING`.
    *   `PENDING` -> `APPROVED` (acción MANAGER).
    *   `PENDING` -> `REJECTED` (acción MANAGER).
*   **Restricción**: Solo se permiten transiciones desde estado `PENDING`. Intentos sobre estados finales (`APPROVED`/`REJECTED`) deben fallar.

## 4. CRITERIOS DE ACEPTACIÓN (Gherkin)

**AC-01: Creación exitosa**
```gherkin
Dado que un EMPLEADO tiene saldo disponible suficiente
Cuando solicita vacaciones por N días
Entonces el sistema responde HTTP 201 Created
Y la solicitud se crea con estado PENDING
```

**AC-02: Rechazo por saldo**
```gherkin
Dado que un EMPLEADO solicita más días de su saldo disponible
Cuando intenta crear la solicitud
Entonces el sistema responde HTTP 400 Bad Request
Con detalle: "Insufficient vacation balance"
```

**AC-03: Autorización de Manager**
```gherkin
Dado que un MANAGER intenta revisar una solicitud
Cuando el empleado solicitante NO es su subordinado directo
Entonces el sistema responde HTTP 403 Forbidden
Con detalle: "Unauthorized: Not the direct manager"
```