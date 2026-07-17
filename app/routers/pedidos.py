"""
routers/pedidos.py
Endpoints de pedidos de catálogo fijo (pasteles ya definidos).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import models, schemas, security
from ..database import get_db
from .cursos import calcular_precio_curso
from ..utils.correo import (
    enviar_correo,
    correo_confirmacion_pedido,
    correo_notificacion_nuevo_pedido,
    obtener_correo_notificaciones,
)

router = APIRouter(prefix="/api/pedidos", tags=["Pedidos"])


@router.post("/", response_model=schemas.PedidoOut)
def crear_pedido(
    datos: schemas.PedidoCreate,
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(security.get_current_user),
):
    """Requiere login — el pedido siempre se crea a nombre de quien tiene la sesión activa,
    nunca del usuario_id que venga en el body (evita que alguien haga pedidos a nombre de otro)."""
    total = sum(item.precio_unitario * item.cantidad for item in datos.items)

    cursos_info = []
    for curso_id in datos.cursos:
        curso = db.query(models.Curso).filter(models.Curso.id == curso_id).first()
        if not curso:
            raise HTTPException(status_code=404, detail=f"Curso {curso_id} no encontrado")
        precio_curso = calcular_precio_curso(curso).precio_final
        total += precio_curso
        cursos_info.append((curso, precio_curso))

    pedido = models.Pedido(
        usuario_id=usuario_actual.id,
        sucursal_id=datos.sucursal_id,
        tipo_entrega=datos.tipo_entrega,
        direccion_id=datos.direccion_id,
        fecha_entrega=datos.fecha_entrega,
        estado="recibido",
        total=total,
    )
    db.add(pedido)
    db.flush()  # obtiene pedido.id antes del commit

    for item in datos.items:
        db.add(models.PedidoItem(
            pedido_id=pedido.id,
            producto_id=item.producto_id,
            opcion_id=item.opcion_id,
            cantidad=item.cantidad,
            precio_unitario=item.precio_unitario,
        ))

    for curso, precio_curso in cursos_info:
        db.add(models.CompraCurso(
            pedido_id=pedido.id,
            usuario_id=usuario_actual.id,
            curso_id=curso.id,
            monto=precio_curso,
            estado_pago="pendiente",
        ))

    db.commit()
    db.refresh(pedido)

    if usuario_actual.email:
        enviar_correo(
            destinatario=usuario_actual.email,
            asunto="¡Gracias por tu pedido! — Niza Isabela",
            contenido_html=correo_confirmacion_pedido(
                nombre=usuario_actual.nombre,
                pedido_id=pedido.id,
                total=float(pedido.total),
                tipo_entrega=pedido.tipo_entrega,
            ),
        )

    correo_isabela = obtener_correo_notificaciones(db)
    if correo_isabela:
        enviar_correo(
            destinatario=correo_isabela,
            asunto="Nuevo pedido recibido — Niza Isabela",
            contenido_html=correo_notificacion_nuevo_pedido(
                nombre=usuario_actual.nombre,
                pedido_id=pedido.id,
                total=float(pedido.total),
                tipo_entrega=pedido.tipo_entrega,
            ),
        )

    # TODO (siguiente iteración): crear el registro en `pagos` y devolver
    # la URL de checkout de Mercado Pago (Preference API).
    return pedido


@router.get("/", response_model=List[schemas.PedidoOut])
def listar_pedidos(
    sucursal_id: Optional[str] = None,
    estado: Optional[str] = None,
    db: Session = Depends(get_db),
    _admin: models.Usuario = Depends(security.get_current_admin),
):
    """Solo admin — tabla de pedidos del panel, con filtros."""
    query = db.query(models.Pedido)
    if sucursal_id:
        query = query.filter(models.Pedido.sucursal_id == sucursal_id)
    if estado:
        query = query.filter(models.Pedido.estado == estado)
    return query.order_by(models.Pedido.created_at.desc()).all()


@router.get("/mis-pedidos", response_model=List[schemas.PedidoOut])
def mis_pedidos(
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(security.get_current_user),
):
    """Historial de pedidos del cliente logueado — para la sección 'Mi cuenta'."""
    return (
        db.query(models.Pedido)
        .filter(models.Pedido.usuario_id == usuario_actual.id)
        .order_by(models.Pedido.created_at.desc())
        .all()
    )


@router.patch("/{pedido_id}/estado")
def actualizar_estado_pedido(
    pedido_id: str,
    nuevo_estado: str,
    db: Session = Depends(get_db),
    _admin: models.Usuario = Depends(security.get_current_admin),
):
    """Solo admin — cambiar el estado de producción de un pedido."""
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    if nuevo_estado not in ("recibido", "en_produccion", "listo", "entregado"):
        raise HTTPException(status_code=400, detail="Estado inválido")
    pedido.estado = nuevo_estado
    db.commit()
    return {"ok": True, "estado": nuevo_estado}

@router.get("/admin/completo", response_model=List[schemas.PedidoAdminOut])
def listar_pedidos_admin(
    sucursal_id: Optional[str] = None,
    estado: Optional[str] = None,
    db: Session = Depends(get_db),
    _admin: models.Usuario = Depends(security.get_current_admin),
):
    """Versión enriquecida para el panel admin: incluye nombre del cliente y productos."""
    query = db.query(models.Pedido)
    if sucursal_id:
        query = query.filter(models.Pedido.sucursal_id == sucursal_id)
    if estado:
        query = query.filter(models.Pedido.estado == estado)
    pedidos = query.order_by(models.Pedido.created_at.desc()).all()

    resultado = []
    for p in pedidos:
        usuario = db.query(models.Usuario).filter(models.Usuario.id == p.usuario_id).first()
        items = db.query(models.PedidoItem).filter(models.PedidoItem.pedido_id == p.id).all()
        nombres_productos = []
        for item in items:
            producto = db.query(models.Producto).filter(models.Producto.id == item.producto_id).first()
            if producto:
                nombres_productos.append(f"{producto.nombre} x{item.cantidad}")

        compras_curso = db.query(models.CompraCurso).filter(models.CompraCurso.pedido_id == p.id).all()
        for compra in compras_curso:
            curso = db.query(models.Curso).filter(models.Curso.id == compra.curso_id).first()
            if curso:
                nombres_productos.append(f"{curso.nombre} (curso)")

        resultado.append(schemas.PedidoAdminOut(
            id=p.id,
            cliente_nombre=usuario.nombre if usuario else "Cliente desconocido",
            productos=", ".join(nombres_productos) if nombres_productos else "—",
            sucursal_id=p.sucursal_id,
            tipo_entrega=p.tipo_entrega,
            fecha_entrega=p.fecha_entrega,
            total=float(p.total),
            estado=p.estado,
            created_at=p.created_at,
        ))
    return resultado