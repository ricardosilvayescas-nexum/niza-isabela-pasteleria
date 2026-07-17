"""
security.py
Todo lo relacionado a login: hashing de contraseñas, JWT, y las
dependencias que protegen rutas (get_current_user, get_current_admin).
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from . import models
from .database import get_db

# En producción, SECRET_KEY debe venir de una variable de entorno real y
# ser larga/aleatoria (ej. generada con `openssl rand -hex 32`).
SECRET_KEY = os.getenv("SECRET_KEY", "cambia-esto-en-produccion-por-una-clave-larga-y-aleatoria")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 días

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.Usuario:
    """Decodifica el JWT y devuelve el usuario autenticado. 401 si el token es inválido."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar la sesión",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        usuario_id: Optional[str] = payload.get("sub")
        if usuario_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if usuario is None:
        raise credentials_exception
    return usuario


def get_current_admin(usuario: models.Usuario = Depends(get_current_user)) -> models.Usuario:
    """Igual que get_current_user, pero además exige rol admin. 403 si no lo tiene."""
    if usuario.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos de administrador",
        )
    return usuario


def get_current_user_opcional(
    token: Optional[str] = Depends(OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)),
    db: Session = Depends(get_db),
) -> Optional[models.Usuario]:
    """Igual que get_current_user, pero no truena si no hay token —
    devuelve None en vez de 401. Para endpoints públicos que opcionalmente
    capturan quién hizo la solicitud, como /api/cotizaciones/."""
    if token is None:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        usuario_id: Optional[str] = payload.get("sub")
        if usuario_id is None:
            return None
    except JWTError:
        return None

    return db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()