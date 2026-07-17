"""
routers/cotizaciones.py
Endpoint del formulario de cotización — pasteles personalizados.
No procesa pago; solo registra la solicitud y valida días mínimos de anticipación.
"""
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, security
from ..database import get_db
from ..utils.correo import (
    enviar_correo,
    correo_confirmacion_cotizacion,
    correo_notificacion_nueva_cotizacion,
    obtener_correo_notificaciones,
)
router = APIRouter(prefix="/api/cotizaciones", tags=["Cotizaciones"])


def dias_minimos_anticipacion(db: Session) -> int:
    config = db.query(models.Configuracion).filter(
        models.Configuracion.clave == "dias_minimos_anticipacion"
    ).first()
    return int(config.valor) if config else 3


@router.post("/", response_model=schemas.CotizacionOut)
def crear_cotizacion(
    datos: schemas.CotizacionCreate,
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario | None = Depends(security.get_current_user_opcional),
):
    minimo = dias_minimos_anticipacion(db)
    if datos.fecha_deseada < date.today() + timedelta(days=minimo):
        # No se bloquea la solicitud (Niza decide si puede cumplirla),
        # pero el front-end ya avisó al cliente con la misma regla.
        pass

    nueva = models.Cotizacion(
        usuario_id=usuario_actual.id if usuario_actual else None,
        nombre_cliente=datos.nombre_cliente,
        producto_id=datos.producto_id,
        sucursal_id=datos.sucursal_id,
        tamano=datos.tamano,
        sabor=datos.sabor,
        relleno=datos.relleno,
        decoracion_texto=datos.decoracion_texto,
        foto_referencia_url=datos.foto_referencia_url,
        mensaje_pastel=datos.mensaje_pastel,
        fecha_deseada=datos.fecha_deseada,
        telefono_cliente=datos.telefono_cliente,
        email_cliente=datos.email_cliente,
        estado="nueva",
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)

    if nueva.email_cliente:
        enviar_correo(
            destinatario=nueva.email_cliente,
            asunto="Recibimos tu solicitud de cotización — Niza Isabela",
            contenido_html=correo_confirmacion_cotizacion(
                nombre=nueva.nombre_cliente,
                tamano=nueva.tamano,
                sabor=nueva.sabor,
                fecha_deseada=nueva.fecha_deseada.strftime("%d/%m/%Y"),
            ),
        )

    correo_isabela = obtener_correo_notificaciones(db)
    if correo_isabela:
        enviar_correo(
            destinatario=correo_isabela,
            asunto="Nueva cotización recibida — Niza Isabela",
            contenido_html=correo_notificacion_nueva_cotizacion(
                nombre=nueva.nombre_cliente,
                telefono=nueva.telefono_cliente,
                tamano=nueva.tamano,
                sabor=nueva.sabor,
                fecha_deseada=nueva.fecha_deseada.strftime("%d/%m/%Y"),
            ),
        )

    return nueva


@router.get("/", response_model=List[schemas.CotizacionOut])
def listar_cotizaciones(
    estado: str | None = None,
    db: Session = Depends(get_db),
    _admin: models.Usuario = Depends(security.get_current_admin),
):
    """Solo admin — bandeja de solicitudes en el panel."""
    query = db.query(models.Cotizacion)
    if estado:
        query = query.filter(models.Cotizacion.estado == estado)
    return query.order_by(models.Cotizacion.created_at.desc()).all()


@router.patch("/{cotizacion_id}/estado")
def actualizar_estado(
    cotizacion_id: str,
    nuevo_estado: str,
    db: Session = Depends(get_db),
    _admin: models.Usuario = Depends(security.get_current_admin),
):
    cotizacion = db.query(models.Cotizacion).filter(models.Cotizacion.id == cotizacion_id).first()
    if not cotizacion:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
    if nuevo_estado not in ("nueva", "contactada", "cerrada"):
        raise HTTPException(status_code=400, detail="Estado inválido")
    cotizacion.estado = nuevo_estado
    db.commit()
    return {"ok": True, "estado": nuevo_estado}
