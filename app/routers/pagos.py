"""
routers/pagos.py
Integración con Mercado Pago (Checkout Pro): creación de preferencias de pago
y webhook para recibir notificaciones de pago.
"""
import os
from dotenv import load_dotenv
load_dotenv()

import mercadopago
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from .. import models, security
from ..database import get_db

router = APIRouter(prefix="/api/pagos", tags=["Pagos"])

print("TOKEN CARGADO:", os.getenv("MERCADOPAGO_ACCESS_TOKEN")[:15] if os.getenv("MERCADOPAGO_ACCESS_TOKEN") else "NO ENCONTRADO")

sdk = mercadopago.SDK(os.getenv("MERCADOPAGO_ACCESS_TOKEN"))

# URL base del frontend, para las páginas de retorno tras el pago.
# En producción, cambiar por el dominio real (ej. https://nizaisabela.com)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5500")


@router.post("/crear-preferencia/{pedido_id}")
def crear_preferencia(
    pedido_id: str,
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(security.get_current_user),
):
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    if pedido.usuario_id != usuario_actual.id:
        raise HTTPException(status_code=403, detail="Este pedido no te pertenece")

    items_pedido = db.query(models.PedidoItem).filter(models.PedidoItem.pedido_id == pedido.id).all()
    items_mp = []
    for item in items_pedido:
        producto = db.query(models.Producto).filter(models.Producto.id == item.producto_id).first()
        items_mp.append({
            "title": producto.nombre if producto else "Producto",
            "quantity": item.cantidad,
            "unit_price": float(item.precio_unitario),
            "currency_id": "MXN",
        })

    compras_curso = db.query(models.CompraCurso).filter(models.CompraCurso.pedido_id == pedido.id).all()
    for compra in compras_curso:
        curso = db.query(models.Curso).filter(models.Curso.id == compra.curso_id).first()
        items_mp.append({
            "title": curso.nombre if curso else "Curso",
            "quantity": 1,
            "unit_price": float(compra.monto),
            "currency_id": "MXN",
        })

    preference_data = {
        "items": items_mp,
        "external_reference": pedido.id,
        "notification_url": os.getenv("MERCADOPAGO_WEBHOOK_URL"),
    }

    resultado = sdk.preference().create(preference_data)
    print("STATUS:", resultado.get("status"))
    print("RESPUESTA COMPLETA:", resultado.get("response"))
    preferencia = resultado["response"]

    pago_existente = db.query(models.Pago).filter(models.Pago.pedido_id == pedido.id).first()
    if not pago_existente:
        pago = models.Pago(
            pedido_id=pedido.id,
            proveedor="mercado_pago",
            monto=pedido.total,
            estado="pendiente",
            referencia_externa=preferencia["id"],
        )
        db.add(pago)
        db.commit()

    return {"init_point": preferencia["sandbox_init_point"], "preference_id": preferencia["id"]}


@router.post("/webhook")
async def webhook_mercadopago(request: Request, db: Session = Depends(get_db)):
    """
    Mercado Pago llama aquí cuando cambia el estado de un pago.
    Documentación: recibe ?type=payment&data.id={payment_id}
    """
    params = request.query_params
    if params.get("type") != "payment":
        return {"ok": True}  # ignoramos otros tipos de notificación

    payment_id = params.get("data.id")
    if not payment_id:
        return {"ok": True}

    payment_info = sdk.payment().get(payment_id)
    payment = payment_info["response"]

    pedido_id = payment.get("external_reference")
    estado_mp = payment.get("status")  # approved | pending | rejected | etc.

    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    pago = db.query(models.Pago).filter(models.Pago.pedido_id == pedido_id).first()

    MAPEO_ESTADOS = {
        "approved": "aprobado",
        "pending": "pendiente",
        "in_process": "pendiente",
        "rejected": "rechazado",
        "cancelled": "rechazado",
        "refunded": "rechazado",
    }
    estado_traducido = MAPEO_ESTADOS.get(estado_mp, "pendiente")

    if pago:
        pago.estado = estado_traducido
        pago.referencia_externa = str(payment_id)

    if pedido and estado_mp == "approved":
        pedido.estado = "en_produccion"

    if pedido:
        compras_curso = db.query(models.CompraCurso).filter(models.CompraCurso.pedido_id == pedido.id).all()
        for compra in compras_curso:
            compra.estado_pago = estado_traducido
            compra.referencia_externa = str(payment_id)

    db.commit()
    return {"ok": True}