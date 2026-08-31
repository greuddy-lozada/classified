# Classified

SIS para colegios privados en Venezuela.

## Stack

- Quasar (Vue 3)
- FastAPI
- PostgreSQL 16

## Desarrollo

```bash
docker compose up --build
```

API: http://localhost:8000  
Cliente: http://localhost:9000

Usuario de plataforma (si `SEED_DEV=1`): `ops@classified.app` / `clave123`

Migraciones (dentro de `backend/` o el contenedor):

```bash
alembic upgrade head
```

Tests:

```bash
cd backend && pytest -v
```
