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


@router.get("/resumen")
def resumen_reportes(
    db: Session = Depends(get_db),
    _admin: models.Usuario = Depends(security.get_current_admin),
):
    hoy = date.today()
    primer_dia_mes = hoy.replace(day=1)

    pedidos_mes = db.query(models.Pedido).filter(models.Pedido.created_at >= primer_dia_mes).all()
    compras_mes = (
        db.query(models.CompraCurso)
        .filter(
            models.CompraCurso.created_at >= primer_dia_mes,
            models.CompraCurso.estado_pago == "aprobado",
        )
        .all()
    )

    ventas_pasteles = sum(float(p.total) for p in pedidos_mes)
    ventas_cursos = sum(float(c.monto) for c in compras_mes)
    ventas_totales = ventas_pasteles + ventas_cursos

    total_transacciones = len(pedidos_mes) + len(compras_mes)
    ticket_promedio = round(ventas_totales / total_transacciones, 2) if total_transacciones else 0

    # Ventas por semana del mes actual (4 buckets)
    semanas = [0.0, 0.0, 0.0, 0.0]
    for p in pedidos_mes:
        idx = min((p.created_at.day - 1) // 7, 3)
        semanas[idx] += float(p.total)
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

    recientes = []
    for p in db.query(models.Pedido).order_by(models.Pedido.created_at.desc()).limit(5).all():
        recientes.append({
            "id": p.id, "tipo": "pastel", "sucursal_id": p.sucursal_id,
            "estado": p.estado, "total": float(p.total), "created_at": p.created_at,
        })
    for c in db.query(models.CompraCurso).order_by(models.CompraCurso.created_at.desc()).limit(5).all():
        recientes.append({
            "id": c.id, "tipo": "curso", "sucursal_id": None,
            "estado": c.estado_pago, "total": float(c.monto), "created_at": c.created_at,
        })
    recientes.sort(key=lambda r: r["created_at"], reverse=True)
    recientes = recientes[:5]

    return {
        "ventas_totales": round(ventas_totales, 2),
        "pedidos_pasteles": len(pedidos_mes),
        "cursos_vendidos": len(compras_mes),
        "ticket_promedio": ticket_promedio,
        "ventas_por_semana": ventas_por_semana,
        "pct_pasteles": pct_pasteles,
        "pct_cursos": pct_cursos,
        "pedidos_recientes": recientes,
    }