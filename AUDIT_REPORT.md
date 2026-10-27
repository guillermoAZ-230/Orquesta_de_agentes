# AUDIT_REPORT.md

## 1. VEREDICTO EJECUTIVO
**Estado:** REJECTED FOR PRODUCTION
**Calificación:** 4.2/10

El código implementa la lógica de negocio correctamente, pero presenta una vulnerabilidad crítica de autenticación (falta de firma/verificación de identidad) que invalida los controles de acceso. No es seguro para producción.

## 2. MATRIZ DE TRAZABILIDAD DEL PRD

| Requisito | Estado | Observación Técnica |
| :--- | :---: | :--- |
| **AC-01: Creación Exitosa** | ✅ PASS | Retorna `201` y estado `PENDING`. Lógica de saldo correcta. |
| **AC-02: Rechazo por Saldo** | ✅ PASS | Retorna `400` con mensaje exacto "Insufficient vacation balance". |
| **AC-03: Autorización Manager** | ✅ PASS | Verifica `empleado.manager_id == x_user_id` y rol `MANAGER`. Retorna `403` correcto. |
| **Fórmula Antigüedad** | ✅ PASS | Implementa `min(12 + 2*(n-1), 20)` correctamente para `n>=1`. |
| **Máquina de Estados** | ✅ PASS | Bloquea transiciones desde estados finales (`APPROVED`/`REJECTED`). |

## 3. AUDITORÍA OWASP API SECURITY

*   **API1: Broken Object Level Authorization (BOLA)**
    *   **Mitigación:** El endpoint `/revisar` valida explícitamente que `empleado.manager_id` coincida con el `x_user_id` del solicitante. Esto previene que un manager acceda a solicitudes de no-subordinados.
    *   **Deficiencia:** La validación depende de un header no firmado (`X-User-Id`). Un atacante puede forjar este header para suplantar la identidad de cualquier manager, anulando el control BOLA.

*   **API5: Broken Function Level Authorization (BFLA)**
    *   **Mitigación:** El endpoint `/empleados` verifica que el rol del usuario sea `ADMIN_RRHH` antes de permitir la creación.
    *   **Deficiencia:** Al igual que en BOLA, la identidad se toma de un header plano sin verificación criptográfica. Un usuario `EMPLEADO` puede enviar `X-User-Id: <id_admin>` y crear registros, violando la restricción de rol.

## 4. RECOMENDACIONES DE MEJORA PARA PRODUCCIÓN

1.  **Implementar Autenticación Robusta (JWT/OAuth2):**
    Reemplazar el header `X-User-Id` por un token JWT firmado (HS256/RS256) o integración con OAuth2. El middleware debe verificar la firma y extraer el `sub` (subject) como identidad confiable. Nunca confiar en headers enviados por el cliente sin verificación.

2.  **Migraciones y Índices con Alembic:**
    Eliminar `Base.metadata.create_all()` en producción. Usar Alembic para gestionar el esquema. Añadir índices compuestos en `solicitudes_vacaciones(empleado_id, estado)` para optimizar la consulta de saldo y evitar degradación de rendimiento con alto volumen.

3.  **Validación de Datos y Transacciones:**
    Añadir validaciones Pydantic estrictas (ej. `dias_solicitados > 0`). Usar `db.begin()` explícito en operaciones críticas para garantizar atomicidad y evitar condiciones de carrera en el cálculo del saldo si múltiples solicitudes se procesan simultáneamente.