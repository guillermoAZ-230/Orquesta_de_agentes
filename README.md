# Orquesta de Agentes para el Ciclo de Vida del Desarrollo de Software (SDLC)

Este repositorio contiene una orquestación completa de agentes de Inteligencia Artificial que simulan un equipo de desarrollo de software para concebir, diseñar, implementar, probar, auditar y desplegar microservicios de manera autónoma.

---

## 👥 Roles de los Agentes

1. **`00_test_conexion.py`**: Comprobación inicial de conectividad con el proveedor LLM (Groq).
2. **`01_agente_product_owner.py`**: Define requerimientos funcionales, historias de usuario y criterios de aceptación (`PRD.md`).
3. **`02_agente_arquitecto.py`**: Diseña la arquitectura del sistema, contratos de API y modelos de datos (`ARCHITECTURE.md`).
4. **`03_agente_developer.py`**: Genera el código del microservicio en FastAPI (`generated_project/app/`).
5. **`04_agente_qa.py`**: Diseña e implementa la suite de pruebas automatizadas con Pytest (`generated_project/tests/`).
6. **`05_agente_reviewer.py`**: Realiza auditoría de código, análisis de seguridad y mejores prácticas (`AUDIT_REPORT.md`).
7. **`06_agente_devops.py`**: Genera la infraestructura de contenedores (`Dockerfile`, `docker-compose.yml`) y el pipeline de CI/CD para GitHub Actions (`.github/workflows/ci.yml`).

---

## 📁 Estructura del Repositorio

```text
├── 00_test_conexion.py
├── 01_agente_product_owner.py
├── 02_agente_arquitecto.py
├── 03_agente_developer.py
├── 04_agente_qa.py
├── 05_agente_reviewer.py
├── 06_agente_devops.py
├── mini_crew.py              # Framework de orquestación de agentes
├── PRD.md                    # Documento de requerimientos generado
├── ARCHITECTURE.md           # Especificación de arquitectura generada
├── AUDIT_REPORT.md           # Informe de auditoría generado
├── .env.example              # Plantilla de variables de entorno (sin credenciales)
└── generated_project/        # Código generado por los agentes (TalentCore API)
    ├── Dockerfile
    ├── docker-compose.yml
    ├── requirements.txt
    ├── probar_api.py
    ├── app/                  # Endpoints y modelos FastAPI
    ├── tests/                # Pruebas con Pytest
    └── .github/workflows/    # Pipeline CI en GitHub Actions
```

---

## ⚙️ Configuración y Uso

### 1. Variables de entorno
Copia la plantilla y configura tu clave de API:
```bash
cp .env.example .env
```
Edita `.env` con tu clave de Groq:
```env
LLM_PROVIDER=groq
GROQ_API_KEY=tu_api_key_aqui
GROQ_MODEL_NAME=qwen/qwen3.8-27b
WORKSPACE_DIR=./generated_project
```

### 2. Ejecución secuencial de los agentes
```bash
python 00_test_conexion.py
python 01_agente_product_owner.py
python 02_agente_arquitecto.py
python 03_agente_developer.py
python 04_agente_qa.py
python 05_agente_reviewer.py
python 06_agente_devops.py
```
