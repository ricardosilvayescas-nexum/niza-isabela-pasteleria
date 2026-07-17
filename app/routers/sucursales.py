from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, security
from ..database import get_db

router = APIRouter(prefix="/api/sucursales", tags=["Sucursales"])


@router.get("/", response_model=List[schemas.SucursalOut])
def listar_sucursales(db: Session = Depends(get_db)):
    return db.query(models.Sucursal).all()


@router.patch("/admin/{sucursal_id}", response_model=schemas.SucursalOut)
def actualizar_sucursal(
    sucursal_id: str,
    datos: schemas.SucursalUpdate,
    db: Session = Depends(get_db),
    admin=Depends(security.get_current_admin),
):
    sucursal = db.query(models.Sucursal).filter(models.Sucursal.id == sucursal_id).first()
    if not sucursal:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada")
    sucursal.nombre = datos.nombre
    sucursal.direccion = datos.direccion
    sucursal.horario = datos.horario
    sucursal.telefono = datos.telefono
    db.commit()
    db.refresh(sucursal)
    return sucursal