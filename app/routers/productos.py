"""
routers/productos.py
Endpoints del catálogo: listar productos, ver detalle.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import models, schemas, security
from ..database import get_db


router = APIRouter(prefix="/api/productos", tags=["Productos"])


@router.get("/", response_model=List[schemas.ProductoOut])
def listar_productos(tipo: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Lista productos activos. Filtra por ?tipo=fijo o ?tipo=personalizable
    (usado por los botones de filtro del catálogo en el front-end).
    """
    query = db.query(models.Producto).filter(models.Producto.activo == True)  # noqa: E712
    if tipo:
        query = query.filter(models.Producto.tipo == tipo)
    return query.all()


@router.get("/{producto_id}", response_model=schemas.ProductoOut)
def obtener_producto(producto_id: str, db: Session = Depends(get_db)):
    producto = db.query(models.Producto).filter(models.Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto


@router.get("/admin/todos", response_model=List[schemas.ProductoOut])
def listar_productos_admin(
    db: Session = Depends(get_db),
    _admin: models.Usuario = Depends(security.get_current_admin),
):
    """Solo admin — incluye productos inactivos, a diferencia del listado público."""
    return db.query(models.Producto).all()


@router.post("/admin", response_model=schemas.ProductoOut)
def crear_producto(
    datos: schemas.ProductoCreate,
    db: Session = Depends(get_db),
    _admin: models.Usuario = Depends(security.get_current_admin),
):
    producto = models.Producto(**datos.model_dump())
    db.add(producto)
    db.commit()
    db.refresh(producto)
    return producto


@router.patch("/admin/{producto_id}", response_model=schemas.ProductoOut)
def actualizar_producto(
    producto_id: str,
    datos: schemas.ProductoUpdate,
    db: Session = Depends(get_db),
    _admin: models.Usuario = Depends(security.get_current_admin),
):
    producto = db.query(models.Producto).filter(models.Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    for campo, valor in datos.model_dump().items():
        setattr(producto, campo, valor)
    db.commit()
    db.refresh(producto)
    return producto


@router.post("/admin/{producto_id}/opciones", response_model=schemas.ProductoOpcionOut)
def crear_opcion(
    producto_id: str,
    datos: schemas.ProductoOpcionCreate,
    db: Session = Depends(get_db),
    _admin: models.Usuario = Depends(security.get_current_admin),
):
    opcion = models.ProductoOpcion(producto_id=producto_id, **datos.model_dump())
    db.add(opcion)
    db.commit()
    db.refresh(opcion)
    return opcion


@router.delete("/admin/opciones/{opcion_id}")
def eliminar_opcion(
    opcion_id: str,
    db: Session = Depends(get_db),
    _admin: models.Usuario = Depends(security.get_current_admin),
):
    opcion = db.query(models.ProductoOpcion).filter(models.ProductoOpcion.id == opcion_id).first()
    if not opcion:
        raise HTTPException(status_code=404, detail="Opción no encontrada")
    db.delete(opcion)
    db.commit()
    return {"ok": True}