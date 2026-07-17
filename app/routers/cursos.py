"""
routers/cursos.py
Endpoints del módulo de cursos (PDFs descargables).
"""
from fastapi import APIRouter, Depends, HTTPException
from datetime import date
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, security
from ..database import get_db

router = APIRouter(prefix="/api/cursos", tags=["Cursos"])


def calcular_precio_curso(curso: models.Curso) -> schemas.CursoOut:
    tiene_descuento = False
    precio_final = float(curso.precio)

    if curso.descuento_activo:
        hoy = date.today()
        dentro_de_rango = True
        if curso.fecha_inicio_descuento and hoy < curso.fecha_inicio_descuento:
            dentro_de_rango = False
        if curso.fecha_fin_descuento and hoy > curso.fecha_fin_descuento:
            dentro_de_rango = False

        if dentro_de_rango:
            tiene_descuento = True
            precio_final = float(curso.precio) * (1 - float(curso.porcentaje_descuento) / 100)

    return schemas.CursoOut(
        id=curso.id,
        nombre=curso.nombre,
        descripcion=curso.descripcion,
        precio_original=float(curso.precio),
        precio_final=round(precio_final, 2),
        tiene_descuento=tiene_descuento,
        portada_url=curso.portada_url,
        archivo_pdf_url=curso.archivo_pdf_url,
        activo=curso.activo,
    )

@router.get("/", response_model=List[schemas.CursoOut])
def listar_cursos(db: Session = Depends(get_db)):
    cursos = db.query(models.Curso).filter(models.Curso.activo == True).all()  # noqa: E712
    return [calcular_precio_curso(c) for c in cursos]


@router.get("/{curso_id}", response_model=schemas.CursoOut)
def obtener_curso(curso_id: str, db: Session = Depends(get_db)):
    curso = db.query(models.Curso).filter(models.Curso.id == curso_id).first()
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    return calcular_precio_curso(curso)


@router.get("/mis-cursos/todos")
def mis_cursos(
    db: Session = Depends(get_db),
    usuario_actual: models.Usuario = Depends(security.get_current_user),
):
    """
    Cursos comprados y aprobados por el usuario logueado — alimenta la sección
    "Mis cursos" de la cuenta del cliente en el front-end. Requiere estar logueado;
    ya no se puede consultar los cursos de otra persona pasando su ID en la URL.
    """
    compras = (
        db.query(models.CompraCurso)
        .filter(
            models.CompraCurso.usuario_id == usuario_actual.id,
            models.CompraCurso.estado_pago == "aprobado",
        )
        .all()
    )
    resultado = []
    for compra in compras:
        curso = db.query(models.Curso).filter(models.Curso.id == compra.curso_id).first()
        if curso:
            resultado.append({
                "curso_id": curso.id,
                "nombre": curso.nombre,
                "archivo_pdf_url": curso.archivo_pdf_url,
                "comprado_el": compra.created_at,
            })
    return resultado


@router.get("/admin/todos", response_model=List[schemas.CursoOut])
def listar_cursos_admin(
    db: Session = Depends(get_db),
    _admin: models.Usuario = Depends(security.get_current_admin),
):
    """Solo admin — incluye cursos inactivos."""
    cursos = db.query(models.Curso).all()
    return [calcular_precio_curso(c) for c in cursos]


@router.post("/admin", response_model=schemas.CursoOut)
def crear_curso(
    datos: schemas.CursoCreate,
    db: Session = Depends(get_db),
    _admin: models.Usuario = Depends(security.get_current_admin),
):
    curso = models.Curso(**datos.model_dump())
    db.add(curso)
    db.commit()
    db.refresh(curso)
    return calcular_precio_curso(curso)


@router.patch("/admin/{curso_id}", response_model=schemas.CursoOut)
def actualizar_curso(
    curso_id: str,
    datos: schemas.CursoUpdate,
    db: Session = Depends(get_db),
    _admin: models.Usuario = Depends(security.get_current_admin),
):
    curso = db.query(models.Curso).filter(models.Curso.id == curso_id).first()
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    for campo, valor in datos.model_dump().items():
        setattr(curso, campo, valor)
    db.commit()
    db.refresh(curso)
    return calcular_precio_curso(curso)