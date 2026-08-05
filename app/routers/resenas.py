"""
routers/resenas.py
Reseñas de clientes sobre productos del catálogo — cualquiera puede dejar una,
pero requieren aprobación del admin antes de mostrarse públicamente.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, security
from ..database import get_db

router = APIRouter(prefix="/api/resenas", tags=["Reseñas"])


@router.post("/", response_model=schemas.ResenaOut)
def crear_resena(datos: schemas.ResenaCreate, db: Session = Depends(get_db)):
    if not (1 <= datos.calificacion <= 5):
        raise HTTPException(status_code=400, detail="La calificación debe ser entre 1 y 5")

    if bool(datos.producto_id) == bool(datos.curso_id):
        raise HTTPException(status_code=400, detail="Debes especificar exactamente un producto o un curso")

    if datos.producto_id:
        item = db.query(models.Producto).filter(models.Producto.id == datos.producto_id).first()
    else:
        item = db.query(models.Curso).filter(models.Curso.id == datos.curso_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="No encontrado")

    resena = models.Resena(
        producto_id=datos.producto_id,
        curso_id=datos.curso_id,
        nombre_cliente=datos.nombre_cliente,
        calificacion=datos.calificacion,
        comentario=datos.comentario,
        estado="pendiente",
    )
    db.add(resena)
    db.commit()
    db.refresh(resena)
    return resena


@router.get("/producto/{producto_id}", response_model=List[schemas.ResenaOut])
def resenas_aprobadas_de_producto(producto_id: str, db: Session = Depends(get_db)):
    """Público — solo reseñas ya aprobadas, para mostrar en el modal de vista rápida."""
    return (
        db.query(models.Resena)
        .filter(models.Resena.producto_id == producto_id, models.Resena.estado == "aprobada")
        .order_by(models.Resena.created_at.desc())
        .all()
    )


@router.get("/curso/{curso_id}", response_model=List[schemas.ResenaOut])
def resenas_aprobadas_de_curso(curso_id: str, db: Session = Depends(get_db)):
    """Público — solo reseñas ya aprobadas, para mostrar en el modal de vista rápida del curso."""
    return (
        db.query(models.Resena)
        .filter(models.Resena.curso_id == curso_id, models.Resena.estado == "aprobada")
        .order_by(models.Resena.created_at.desc())
        .all()
    )


@router.get("/admin/todas", response_model=List[schemas.ResenaOut])
def listar_resenas_admin(
    db: Session = Depends(get_db),
    _admin: models.Usuario = Depends(security.get_current_admin),
):
    """Solo admin — bandeja de moderación, pendientes primero."""
    return (
        db.query(models.Resena)
        .order_by(
            (models.Resena.estado == "pendiente").desc(),
            models.Resena.created_at.desc(),
        )
        .all()
    )


@router.patch("/admin/{resena_id}", response_model=schemas.ResenaOut)
def moderar_resena(
    resena_id: str,
    datos: schemas.ResenaAdminUpdate,
    db: Session = Depends(get_db),
    _admin: models.Usuario = Depends(security.get_current_admin),
):
    resena = db.query(models.Resena).filter(models.Resena.id == resena_id).first()
    if not resena:
        raise HTTPException(status_code=404, detail="Reseña no encontrada")
    if datos.estado not in ("aprobada", "rechazada"):
        raise HTTPException(status_code=400, detail="Estado inválido")
    resena.estado = datos.estado
    db.commit()
    db.refresh(resena)
    return resena