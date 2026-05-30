# Ticket Management API

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-6.0-092E20?style=for-the-badge&logo=django&logoColor=white)
![DRF](https://img.shields.io/badge/Django_REST_Framework-3.17-red?style=for-the-badge)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-Auth-black?style=for-the-badge&logo=jsonwebtokens)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-11%20passing-brightgreen?style=for-the-badge)

API REST para gestión de tickets de soporte técnico. Permite crear, asignar y resolver tickets con control de roles, historial de comentarios, filtros avanzados y documentación interactiva.

![Swagger UI](docs/images/3.jpg)

---

## Descripción técnica

El proyecto sigue una arquitectura en capas **Cliente → View → Serializer → Model → PostgreSQL**, separando responsabilidades entre validación de negocio, transformación de datos y persistencia.

### Decisiones de arquitectura

**Modelo de usuario personalizado (`AbstractUser`)**
Se extendió `AbstractUser` en lugar de crear un perfil separado. Esto evita un JOIN extra en cada request de autenticación y permite cambiar el campo de login a `email` de forma nativa. El campo `role` con choices `ADMIN`/`USER` vive directamente en el modelo sin tablas auxiliares.

**JWT stateless con SimpleJWT**
Se eligió JWT sobre sesiones porque la API está diseñada para ser consumida por clientes externos (SPA, mobile, herramientas como Postman). No requiere estado en el servidor, escala horizontalmente y el token incluye el rol del usuario evitando consultas adicionales.

**`ModelViewSet` + `DefaultRouter` para tickets**
Un solo `ViewSet` provee los 5 verbos HTTP sin repetir código. El `DefaultRouter` genera las URLs automáticamente. Toda la lógica de negocio que depende del usuario (filtrado por rol, asignación restringida) vive en `get_queryset` y el serializer, no en los métodos de la vista.

**Máquina de estados en el serializer**
Las transiciones válidas (`OPEN → IN_PROGRESS → RESOLVED → CLOSED`) se definen como un diccionario `VALID_TRANSITIONS` y se validan en `validate_status`. Esto garantiza que ningún cliente pueda saltar estados arbitrariamente, independientemente de cómo llame al endpoint.

**`closed_at` auto-asignado en `Model.save()`**
Cuando el status cambia a `CLOSED`, el campo `closed_at` se setea automáticamente dentro del método `save()` del modelo consultando el estado previo. La lógica de negocio que siempre debe ejecutarse vive en el modelo, no en la vista.

**Permisos como clase separada (`TicketPermission`)**
Las reglas de acceso (solo ADMIN puede eliminar, solo el dueño o ADMIN puede editar) están en `tickets/permissions.py` aisladas de la vista. Esto las hace testeables de forma independiente y evita condicionales dispersos en los métodos del ViewSet.

**`select_related` en `get_queryset`**
Los campos `created_by` y `assigned_to` se resuelven con un JOIN en la misma query inicial, eliminando el problema N+1 que ocurriría al serializar la lista de tickets con datos de usuario anidados.

---

## Funcionalidades

- Registro y login con JWT (access 1h / refresh 7 días)
- CRUD completo de tickets con control de roles
- Máquina de estados con transiciones validadas
- Asignación de tickets restringida a ADMIN
- Comentarios anidados por ticket
- Filtros por `status`, `priority`, `assigned_to`
- Búsqueda por título (`?search=`)
- Ordenamiento configurable (`?ordering=`)
- Paginación automática (10 por página)
- Documentación interactiva con Swagger UI y ReDoc
- 11 tests automatizados

---

## Stack tecnológico

| Tecnología | Versión | Uso |
|---|---|---|
| Python | 3.12 | Lenguaje base |
| Django | 6.0 | Framework web |
| Django REST Framework | 3.17 | API REST |
| SimpleJWT | 5.5 | Autenticación JWT |
| drf-spectacular | 0.29 | Swagger / OpenAPI 3.0 |
| PostgreSQL | 16 | Base de datos |
| psycopg2 | 2.9 | Driver PostgreSQL |
| python-decouple | 3.8 | Variables de entorno |
| Docker Compose | — | Contenedores |

---

## Estructura del proyecto

```
ticket-api/
├── core/               # Configuración Django (settings, urls)
├── users/              # Modelo User, registro, login, JWT
│   ├── models.py       # AbstractUser con rol ADMIN/USER
│   ├── serializers.py  # Register, Login, UserSerializer
│   ├── views.py        # RegisterView, LoginView, RefreshView
│   └── urls.py
├── tickets/            # CRUD Tickets, permisos, máquina de estados
│   ├── models.py       # Ticket con status, priority, category
│   ├── serializers.py  # Validación de transiciones de estado
│   ├── permissions.py  # TicketPermission (rol + propiedad)
│   ├── views.py        # TicketViewSet con filtros
│   └── urls.py
├── comments/           # Comentarios anidados bajo tickets
│   ├── models.py
│   ├── serializers.py
│   └── views.py
├── docs/images/        # Capturas de pantalla
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Endpoints

![Endpoints en Swagger](docs/images/1.jpg)

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/auth/register` | Registrar usuario | No |
| `POST` | `/api/auth/login` | Login, devuelve tokens JWT | No |
| `POST` | `/api/auth/refresh` | Renovar access token | No |
| `GET` | `/api/tickets/` | Listar tickets | Sí |
| `POST` | `/api/tickets/` | Crear ticket | Sí |
| `GET` | `/api/tickets/{id}/` | Detalle de ticket | Sí |
| `PUT` | `/api/tickets/{id}/` | Actualizar ticket completo | Sí |
| `PATCH` | `/api/tickets/{id}/` | Actualizar ticket parcial | Sí |
| `DELETE` | `/api/tickets/{id}/` | Eliminar ticket | Solo ADMIN |
| `GET` | `/api/tickets/{id}/comments` | Listar comentarios | Sí |
| `POST` | `/api/tickets/{id}/comments` | Agregar comentario | Sí |
| `GET` | `/api/docs/` | Swagger UI | No |
| `GET` | `/api/redoc/` | ReDoc | No |

### Filtros disponibles

```
GET /api/tickets/?status=OPEN
GET /api/tickets/?priority=HIGH
GET /api/tickets/?assigned_to=3
GET /api/tickets/?search=bug
GET /api/tickets/?ordering=-created_at
GET /api/tickets/?status=OPEN&priority=HIGH&ordering=created_at
```

---

## Control de roles

| Acción | USER | ADMIN |
|--------|------|-------|
| Crear ticket | ✅ | ✅ |
| Ver sus tickets | ✅ | ✅ |
| Ver todos los tickets | ❌ | ✅ |
| Editar ticket propio (solo si está OPEN) | ✅ | ✅ |
| Asignar ticket a otro usuario | ❌ | ✅ |
| Eliminar ticket | ❌ | ✅ |
| Comentar en ticket | ✅ | ✅ |

### Máquina de estados

```
OPEN → IN_PROGRESS → RESOLVED → CLOSED
```

Saltar estados (ej. `OPEN → CLOSED`) retorna `400 Bad Request`.

---

## Instalación local

### Requisitos previos

- Python 3.12+
- PostgreSQL corriendo localmente

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/TuskDev09/ticket-api.git
cd ticket-api

# 2. Crear y activar entorno virtual
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales de PostgreSQL

# 5. Crear la base de datos en PostgreSQL
psql -U postgres -c "CREATE DATABASE ticket_db;"

# 6. Aplicar migraciones
python manage.py migrate

# 7. (Opcional) Crear superusuario admin
python manage.py createsuperuser

# 8. Correr el servidor
python manage.py runserver
```

La API estará disponible en `http://127.0.0.1:8000`

---

## Instalación con Docker

![Docker Desktop corriendo](docs/images/docker.png)

### Requisitos previos

- Docker Desktop instalado y corriendo

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/TuskDev09/ticket-api.git
cd ticket-api

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env (el host de la DB debe ser "db", no localhost)

# 3. Levantar los servicios
docker-compose up --build

# 4. En otra terminal, aplicar migraciones
docker-compose exec api python manage.py migrate

# 5. (Opcional) Crear superusuario
docker-compose exec api python manage.py createsuperuser
```

Los servicios que levanta Docker Compose:
- `api` — Django en `http://localhost:8000`
- `db` — PostgreSQL 16 con volumen persistente

Para detener:
```bash
docker-compose down
```

Para detener y borrar la base de datos:
```bash
docker-compose down -v
```

---

## Variables de entorno

Crear un archivo `.env` en la raíz del proyecto:

```env
SECRET_KEY=django-insecure-cambiar-en-produccion
DEBUG=True

DB_NAME=ticket_db
DB_USER=postgres
DB_PASSWORD=tu_contraseña
DB_HOST=localhost
DB_PORT=5432
```

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `SECRET_KEY` | Clave secreta de Django | `django-insecure-...` |
| `DEBUG` | Modo debug | `True` / `False` |
| `DB_NAME` | Nombre de la base de datos | `ticket_db` |
| `DB_USER` | Usuario PostgreSQL | `postgres` |
| `DB_PASSWORD` | Contraseña PostgreSQL | `mipassword` |
| `DB_HOST` | Host de la DB | `localhost` / `db` (Docker) |
| `DB_PORT` | Puerto PostgreSQL | `5432` |

> Con Docker, `DB_HOST` debe ser `db` (nombre del servicio en docker-compose.yml).

---

## Autenticación JWT

### 1. Registrar usuario

```bash
POST /api/auth/register
Content-Type: application/json

{
  "username": "jose",
  "email": "jose@ejemplo.com",
  "password": "MiPassword123!"
}
```

### 2. Login

```bash
POST /api/auth/login
Content-Type: application/json

{
  "email": "jose@ejemplo.com",
  "password": "MiPassword123!"
}
```

![Login response con tokens JWT](docs/images/2.jpg)

La respuesta incluye `access`, `refresh` y los datos del usuario.

### 3. Usar el token

Agregar el header en cada request protegido:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6...
```

En Swagger UI, hacer clic en **Authorize** e ingresar el token:

![Ingresando JWT token en Swagger](docs/images/5.jpg)
![Token JWT autorizado](docs/images/4.jpg)

### 4. Renovar token

```bash
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6..."
}
```

---

## Ejemplos de requests

### Crear ticket

```bash
POST /api/tickets/
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Error en módulo de pagos",
  "description": "El botón de pago no responde en Safari",
  "priority": "HIGH",
  "category": "BUG"
}
```

### Avanzar estado del ticket

```bash
PATCH /api/tickets/1/
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "IN_PROGRESS"
}
```

### Asignar ticket (solo ADMIN)

```bash
PATCH /api/tickets/1/
Authorization: Bearer <token>
Content-Type: application/json

{
  "assigned_to_id": 3
}
```

### Agregar comentario

```bash
POST /api/tickets/1/comments
Authorization: Bearer <token>
Content-Type: application/json

{
  "content": "Revisando el issue, necesito más información del navegador."
}
```

---

## Tests

El proyecto incluye 11 tests automatizados que cubren permisos, transiciones de estado y autenticación.

```bash
# Correr todos los tests
python manage.py test

# Correr solo los tests de tickets con detalle
python manage.py test tickets.tests --verbosity=2

# Con Docker
docker-compose exec api python manage.py test
```

### Cobertura de tests

| Suite | Tests | Qué valida |
|-------|-------|------------|
| `TicketPermissionTests` | 6 | USER no puede borrar/asignar/ver tickets ajenos, transiciones válidas e inválidas |
| `AdminTicketTests` | 3 | ADMIN puede borrar, asignar y ver todos los tickets |
| `AuthEndpointTests` | 2 | Sin token devuelve 401, login devuelve access token |

---

## Documentación de la API

### Swagger UI
`http://127.0.0.1:8000/api/docs/`

Permite probar todos los endpoints directamente desde el navegador con autenticación JWT integrada.

### ReDoc

`http://127.0.0.1:8000/api/redoc/`

![ReDoc documentation](docs/images/7.png)

Vista de referencia con formato limpio para compartir con otros equipos.

### OpenAPI Schema

`http://127.0.0.1:8000/api/schema/`

Descarga el schema en formato YAML para importar en Postman o generar clientes.
