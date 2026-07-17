from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import get_current_admin
from ..models import ContactoMensaje
from ..schemas import ContactoMensajeCreate, ContactoMensajeOut
from ..utils.correo import (
    enviar_correo,
    correo_confirmacion_contacto,
    correo_notificacion_nueva_duda,
    obtener_correo_notificaciones,
)

router = APIRouter(prefix="/contacto", tags=["contacto"])


@router.post("/", response_model=ContactoMensajeOut)
def crear_mensaje(datos: ContactoMensajeCreate, db: Session = Depends(get_db)):
    mensaje = ContactoMensaje(**datos.model_dump())
    db.add(mensaje)
    db.commit()
    db.refresh(mensaje)

    enviar_correo(
        destinatario=mensaje.correo,
        asunto="Recibimos tu mensaje — Niza Isabela",
        contenido_html=correo_confirmacion_contacto(nombre=mensaje.nombre),
    )

    correo_isabela = obtener_correo_notificaciones(db)
    if correo_isabela:
        enviar_correo(
            destinatario=correo_isabela,
            asunto="Nuevo mensaje de contacto — Niza Isabela",
            contenido_html=correo_notificacion_nueva_duda(
                nombre=mensaje.nombre,
                correo=mensaje.correo,
                mensaje=mensaje.mensaje,
            ),
        )

    return mensaje


@router.get("/admin", response_model=list[ContactoMensajeOut])
def listar_mensajes(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    return (
        db.query(ContactoMensaje)
        .order_by(ContactoMensaje.leido.asc(), ContactoMensaje.fecha_envio.desc())
        .all()
    )


@router.patch("/admin/{mensaje_id}", response_model=ContactoMensajeOut)
def marcar_leido(mensaje_id: str, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    mensaje = db.query(ContactoMensaje).filter(
        ContactoMensaje.contacto_mensaje_id == mensaje_id
    ).first()
    mensaje.leido = True
    db.commit()
    db.refresh(mensaje)
    return mensaje