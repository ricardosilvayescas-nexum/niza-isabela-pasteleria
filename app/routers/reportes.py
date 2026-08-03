"""
routers/reportes.py
Agregaciones para el dashboard de Reportes del panel admin.
"""
from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import models, security
from ..database import get_db

router = APIRouter(prefix="/api/reportes", tags=["Reportes"])

ESTADOS_PAGADOS = ("en_produccion", "listo", "entregado")


@router.get("/resumen")
def resumen_reportes(
    db: Session = Depends(get_db),
    _admin: models.Usuario = Depends(security.get_current_admin),
):
    hoy = date.today()
    primer_dia_mes = hoy.replace(day=1)

    # Solo pedidos con pago confirmado (excluye 'recibido' = intento sin pagar)
    pedidos_mes = (
        db.query(models.Pedido)
        .filter(
            models.Pedido.created_at >= primer_dia_mes,
            models.Pedido.estado.in_(ESTADOS_PAGADOS),
        )
        .all()
    )
    compras_mes = (
        db.query(models.CompraCurso)
        .filter(
            models.CompraCurso.created_at >= primer_dia_mes,
            models.CompraCurso.estado_pago == "aprobado",
        )
        .all()
    )

    # Ventas de pasteles = solo el valor de los PedidoItem (excluye el monto de cursos,
    # que ya viaja aparte en compras_cursos aunque comparta el mismo Pedido)
    ventas_pasteles = 0.0
    pedidos_con_producto = 0
    for p in pedidos_mes:
        items = db.query(models.PedidoItem).filter(models.PedidoItem.pedido_id == p.id).all()
        subtotal_items = sum(float(i.precio_unitario) * i.cantidad for i in items)
        if items:
            pedidos_con_producto += 1
        ventas_pasteles += subtotal_items

    ventas_cursos = sum(float(c.monto) for c in compras_mes)
    ventas_totales = ventas_pasteles + ventas_cursos

    total_transacciones = pedidos_con_producto + len(compras_mes)
    ticket_promedio = round(ventas_totales / total_transacciones, 2) if total_transacciones else 0

    # Ventas por semana del mes actual (4 buckets)
    semanas = [0.0, 0.0, 0.0, 0.0]
    for p in pedidos_mes:
        items = db.query(models.PedidoItem).filter(models.PedidoItem.pedido_id == p.id).all()
        subtotal_items = sum(float(i.precio_unitario) * i.cantidad for i in items)
        idx = min((p.created_at.day - 1) // 7, 3)
        semanas[idx] += subtotal_items
    for c in compras_mes:
        idx = min((c.created_at.day - 1) // 7, 3)
        semanas[idx] += float(c.monto)
    tope = max(semanas) if max(semanas) > 0 else 1
    ventas_por_semana = [
        {"label": f"Sem {i+1}", "monto": round(semanas[i], 2), "porcentaje": round(semanas[i] / tope * 100)}
        for i in range(4)
    ]

    pct_pasteles = round(ventas_pasteles / ventas_totales * 100) if ventas_totales else 0
    pct_cursos = 100 - pct_pasteles if ventas_totales else 0

    # Pedidos recientes: una fila por Pedido real (sin duplicar cursos que ya viven dentro de un pedido)
    recientes = []
    for p in (
        db.query(models.Pedido)
        .filter(models.Pedido.estado.in_(ESTADOS_PAGADOS))
        .order_by(models.Pedido.created_at.desc())
        .limit(10)
        .all()
    ):
        items = db.query(models.PedidoItem).filter(models.PedidoItem.pedido_id == p.id).all()
        cursos_del_pedido = db.query(models.CompraCurso).filter(
            models.CompraCurso.pedido_id == p.id,
            models.CompraCurso.estado_pago == "aprobado",
        ).all()

        if items and cursos_del_pedido:
            tipo = "mixto"
        elif cursos_del_pedido:
            tipo = "curso"
        else:
            tipo = "pastel"

        recientes.append({
            "id": p.id, "tipo": tipo, "sucursal_id": p.sucursal_id,
            "estado": p.estado, "total": float(p.total), "created_at": p.created_at,
        })
    recientes = recientes[:5]

    return {
        "ventas_totales": round(ventas_totales, 2),
        "pedidos_pasteles": pedidos_con_producto,
        "cursos_vendidos": len(compras_mes),
        "ticket_promedio": ticket_promedio,
        "ventas_por_semana": ventas_por_semana,
        "pct_pasteles": pct_pasteles,
        "pct_cursos": pct_cursos,
        "pedidos_recientes": recientes,
    }