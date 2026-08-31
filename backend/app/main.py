from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.session import SessionLocal
from app.modules.evaluacion.router import router as evaluacion_router
from app.modules.identidad.router import router as identidad_router
from app.modules.identidad.seed import seed_if_empty
from app.modules.inscripcion.router import router as inscripcion_router
from app.modules.periodo.router import router as periodo_router
from app.modules.personas.router import router as personas_router
from app.modules.plataforma.router import router as plataforma_router

app = FastAPI(title="Classified")

app.include_router(identidad_router)
app.include_router(plataforma_router)
app.include_router(personas_router)
app.include_router(periodo_router)
app.include_router(inscripcion_router)
app.include_router(evaluacion_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _seed() -> None:
    if not settings.seed_dev:
        return
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
