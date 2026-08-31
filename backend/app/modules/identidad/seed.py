from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.usuario import Usuario


def seed_if_empty(db: Session) -> None:
    if db.query(Usuario).filter(Usuario.es_plataforma.is_(True)).first():
        return
    ops = Usuario(
        email="ops@classified.app",
        password_hash=hash_password("clave123"),
        es_plataforma=True,
    )
    db.add(ops)
    db.commit()
