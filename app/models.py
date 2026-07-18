"""
models.py
Modelos SQLAlchemy — reflejan 1:1 el esquema T-SQL de 03-Base-de-Datos.md
"""
import uuid
from pydantic import BaseModel
from sqlalchemy import (
    Column, String, Boolean, DateTime, Date, Numeric, Integer, Uuid, text,
    ForeignKey, func
)
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import Mapped, relationship
from .database import Base


def gen_uuid():
    return str(uuid.uuid4())


class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(UNIQUEIDENTIFIER(as_uuid=False), primary_key=True, default=gen_uuid)
    nombre = Column(String(150), nullable=False)
    email = Column(String(150), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    telefono = Column(String(20))
    rol = Column(String(10), nullable=False, default="cliente")  # 'cliente' | 'admin'
    created_at = Column(DateTime, server_default=func.now())


class Sucursal(Base):
    __tablename__ = "sucursales"
    id = Column(UNIQUEIDENTIFIER(as_uuid=False), primary_key=True, default=gen_uuid)
    nombre = Column(String(100), nullable=False)
    direccion = Column(String(255), nullable=False)
    horario = Column(String(100))
    telefono = Column(String(20))


class Producto(Base):
    __tablename__ = "productos"
    id = Column(UNIQUEIDENTIFIER(as_uuid=False), primary_key=True, default=gen_uuid)
    nombre = Column(String(150), nullable=False)
    descripcion = Column(String)
    tipo = Column(String(15), nullable=False)  # 'fijo' | 'personalizable'
    precio_base = Column(Numeric(10, 2))
    foto_url = Column(String(500))
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    opciones = relationship("ProductoOpcion", back_populates="producto")


class ProductoOpcion(Base):
    __tablename__ = "producto_opciones"
    id = Column(UNIQUEIDENTIFIER(as_uuid=False), primary_key=True, default=gen_uuid)
    producto_id = Column(UNIQUEIDENTIFIER(as_uuid=False), ForeignKey("productos.id"))
    tipo_opcion = Column(String(15), nullable=False)  # tamaño | sabor | relleno | decoracion
    nombre = Column(String(100), nullable=False)
    precio_extra = Column(Numeric(10, 2), default=0)
    producto = relationship("Producto", back_populates="opciones")


class Direccion(Base):
    __tablename__ = "direcciones"
    id = Column(UNIQUEIDENTIFIER(as_uuid=False), primary_key=True, default=gen_uuid)
    usuario_id = Column(UNIQUEIDENTIFIER(as_uuid=False), ForeignKey("usuarios.id"))
    direccion = Column(String(255), nullable=False)
    referencias = Column(String(255))
    zona_delivery = Column(String(100))


class Pedido(Base):
    __tablename__ = "pedidos"
    id = Column(UNIQUEIDENTIFIER(as_uuid=False), primary_key=True, default=gen_uuid)
    usuario_id = Column(UNIQUEIDENTIFIER(as_uuid=False), ForeignKey("usuarios.id"))
    sucursal_id = Column(UNIQUEIDENTIFIER(as_uuid=False), ForeignKey("sucursales.id"))
    tipo_entrega = Column(String(10), nullable=False)  # recoger | delivery
    direccion_id = Column(UNIQUEIDENTIFIER(as_uuid=False), ForeignKey("direcciones.id"))
    fecha_entrega = Column(Date, nullable=False)
    estado = Column(String(15), nullable=False, default="recibido")
    total = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    items = relationship("PedidoItem", back_populates="pedido")


class PedidoItem(Base):
    __tablename__ = "pedido_items"
    id = Column(UNIQUEIDENTIFIER(as_uuid=False), primary_key=True, default=gen_uuid)
    pedido_id = Column(UNIQUEIDENTIFIER(as_uuid=False), ForeignKey("pedidos.id"))
    producto_id = Column(UNIQUEIDENTIFIER(as_uuid=False), ForeignKey("productos.id"))
    opcion_id = Column(UNIQUEIDENTIFIER(as_uuid=False), ForeignKey("producto_opciones.id"))
    cantidad = Column(Integer, nullable=False, default=1)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    pedido = relationship("Pedido", back_populates="items")


class Pago(Base):
    __tablename__ = "pagos"
    id = Column(UNIQUEIDENTIFIER(as_uuid=False), primary_key=True, default=gen_uuid)
    pedido_id = Column(UNIQUEIDENTIFIER(as_uuid=False), ForeignKey("pedidos.id"), unique=True)
    proveedor = Column(String(50), default="mercado_pago")
    monto = Column(Numeric(10, 2), nullable=False)
    estado = Column(String(12), nullable=False, default="pendiente")
    referencia_externa = Column(String(150))
    created_at = Column(DateTime, server_default=func.now())


class Cotizacion(Base):
    __tablename__ = "cotizaciones"
    id = Column(UNIQUEIDENTIFIER(as_uuid=False), primary_key=True, default=gen_uuid)
    usuario_id = Column(UNIQUEIDENTIFIER(as_uuid=False), ForeignKey("usuarios.id"))
    nombre_cliente = Column(String(150), nullable=True)
    producto_id = Column(UNIQUEIDENTIFIER(as_uuid=False), ForeignKey("productos.id"))
    sucursal_id = Column(UNIQUEIDENTIFIER(as_uuid=False), ForeignKey("sucursales.id"))
    tamano = Column("tamaño", String(50))
    sabor = Column(String(100))
    telefono_cliente = Column(String(20), nullable=True)
    email_cliente = Column(String(150), nullable=True)
    relleno = Column(String(100))
    decoracion_texto = Column(String)
    foto_referencia_url = Column(String(500))
    mensaje_pastel = Column(String(255))
    fecha_deseada = Column(Date, nullable=False)
    estado = Column(String(12), nullable=False, default="nueva")  # nueva | contactada | cerrada
    created_at = Column(DateTime, server_default=func.now())


class Configuracion(Base):
    __tablename__ = "configuracion"
    clave = Column(String(100), primary_key=True)
    valor = Column(String(255), nullable=False)


class Curso(Base):
    __tablename__ = "cursos"
    id = Column(UNIQUEIDENTIFIER(as_uuid=False), primary_key=True, default=gen_uuid)
    nombre = Column(String(150), nullable=False)
    descripcion = Column(String)
    precio = Column(Numeric(10, 2), nullable=False)
    portada_url = Column(String(500))
    archivo_pdf_url = Column(String(500), nullable=False)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    descuento_activo = Column("DescuentoActivo", Boolean, default=False)
    porcentaje_descuento = Column("PorcentajeDescuento", Numeric(5, 2), default=35.00)
    fecha_inicio_descuento = Column("FechaInicioDescuento", Date, nullable=True)
    fecha_fin_descuento = Column("FechaFinDescuento", Date, nullable=True)


class CompraCurso(Base):
    __tablename__ = "compras_cursos"
    id = Column(UNIQUEIDENTIFIER(as_uuid=False), primary_key=True, default=gen_uuid)
    usuario_id = Column(UNIQUEIDENTIFIER(as_uuid=False), ForeignKey("usuarios.id"), nullable=False)
    curso_id = Column(UNIQUEIDENTIFIER(as_uuid=False), ForeignKey("cursos.id"), nullable=False)
    pedido_id = Column(UNIQUEIDENTIFIER(as_uuid=False), ForeignKey("pedidos.id"), nullable=True)
    monto = Column(Numeric(10, 2), nullable=False)
    estado_pago = Column(String(12), nullable=False, default="pendiente")
    referencia_externa = Column(String(150))
    created_at = Column(DateTime, server_default=func.now())


class ContactoMensaje(Base):
    __tablename__ = "ContactoMensajes"
    contacto_mensaje_id = Column("ContactoMensajeID", UNIQUEIDENTIFIER(as_uuid=False), primary_key=True, default=gen_uuid)
    nombre = Column("Nombre", String(150), nullable=False)
    correo = Column("Correo", String(150), nullable=False)
    telefono = Column("Telefono", String(20), nullable=True)
    mensaje = Column("Mensaje", String, nullable=False)
    fecha_envio = Column("FechaEnvio", DateTime, server_default=func.now())
    leido = Column("Leido", Boolean, default=False)

