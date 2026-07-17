"""
routers/configuracion.py
Ajustes generales editables desde el panel admin sin tocar código.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, security
from ..database import get_db

router = APIRouter(prefix="/api/configuracion", tags=["Configuración"])


@router.get("/{clave}", response_model=schemas.ConfiguracionOut)
def obtener_config(clave: str, db: Session = Depends(get_db)):
    config = db.query(models.Configuracion).filter(models.Configuracion.clave == clave).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    return config


@router.put("/{clave}", response_model=schemas.ConfiguracionOut)
def actualizar_config(
    clave: str,
    valor: str,
    db: Session = Depends(get_db),
    _admin: models.Usuario = Depends(security.get_current_admin),
):
    config = db.query(models.Configuracion).filter(models.Configuracion.clave == clave).first()
    if not config:
        config = models.Configuracion(clave=clave, valor=valor)
        db.add(config)
    else:
        config.valor = valor
    db.commit()
    db.refresh(config)
    return config
