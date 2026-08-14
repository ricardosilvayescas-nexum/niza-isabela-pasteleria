"""
routers/auth.py
Registro, login y "quién soy" (usado por el front-end para saber
si mostrar el link de Panel admin, o la sección Mis cursos/pedidos).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from datetime import datetime, timedelta

import os
from .. import models, schemas, security
from ..database import get_db
from ..utils.correo import enviar_correo, correo_reset_password

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5500")


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


@router.post("/olvide-password", response_model=schemas.MensajeSimple)
def solicitar_reset_password(datos: schemas.SolicitarResetPassword, db: Session = Depends(get_db)):
    """
    Siempre regresa el mismo mensaje genérico, exista o no el correo —
    así nadie puede usar este endpoint para averiguar qué correos están registrados.
    """
    usuario = db.query(models.Usuario).filter(models.Usuario.email == datos.email).first()

    if usuario:
        token = security.generar_reset_token()
        usuario.reset_token = token
        usuario.reset_token_expira = datetime.utcnow() + timedelta(hours=1)
        db.commit()

        link_reset = f"{FRONTEND_URL}/restablecer-password.html?token={token}"
        enviar_correo(
            destinatario=usuario.email,
            asunto="Restablece tu contraseña — Niza Isabela",
            contenido_html=correo_reset_password(nombre=usuario.nombre, link_reset=link_reset),
        )

    return {"mensaje": "Si el correo existe en nuestro sistema, recibirás un enlace para restablecer tu contraseña."}


@router.post("/restablecer-password", response_model=schemas.MensajeSimple)
def restablecer_password(datos: schemas.ConfirmarResetPassword, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.reset_token == datos.token).first()

    if not usuario or not usuario.reset_token_expira or usuario.reset_token_expira < datetime.utcnow():
        raise HTTPException(status_code=400, detail="El enlace es inválido o ya expiró. Solicita uno nuevo.")

    if len(datos.password_nueva) < 6:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 6 caracteres.")

    usuario.password_hash = security.hash_password(datos.password_nueva)
    usuario.reset_token = None
    usuario.reset_token_expira = None
    db.commit()

    return {"mensaje": "Tu contraseña se actualizó correctamente. Ya puedes iniciar sesión."}