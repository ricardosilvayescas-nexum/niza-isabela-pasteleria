"""
routers/auth.py
Registro, login y "quién soy" (usado por el front-end para saber
si mostrar el link de Panel admin, o la sección Mis cursos/pedidos).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas, security
from ..database import get_db

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])


@router.post("/registro", response_model=schemas.Token, status_code=status.HTTP_201_CREATED)
def registro(datos: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    existente = db.query(models.Usuario).filter(models.Usuario.email == datos.email).first()
    if existente:
        raise HTTPException(status_code=400, detail="Ya existe una cuenta con ese correo")

    nuevo = models.Usuario(
        nombre=datos.nombre,
        email=datos.email,
        password_hash=security.hash_password(datos.password),
        telefono=datos.telefono,
        rol="cliente",  # el rol admin se asigna manualmente en la base de datos, nunca desde el registro público
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    token = security.create_access_token({"sub": nuevo.id})
    return {"access_token": token, "usuario": nuevo}


@router.post("/login", response_model=schemas.Token)
def login(datos: schemas.UsuarioLogin, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.email == datos.email).first()
    if not usuario or not security.verify_password(datos.password, usuario.password_hash):
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")

    token = security.create_access_token({"sub": usuario.id})
    return {"access_token": token, "usuario": usuario}


@router.get("/me", response_model=schemas.UsuarioOut)
def quien_soy(usuario_actual: models.Usuario = Depends(security.get_current_user)):
    """El front-end llama esto para saber quién está logueado y qué rol tiene."""
    return usuario_actual
