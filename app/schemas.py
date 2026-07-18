"""
schemas.py
Esquemas Pydantic: validan lo que entra y dan forma a lo que sale de la API.
"""
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict


# ---------- Productos ----------
class ProductoOpcionOut(BaseModel):
    id: str
    tipo_opcion: str
    nombre: str
    precio_extra: float
    model_config = ConfigDict(from_attributes=True)


class ProductoOut(BaseModel):
    id: str
    nombre: str
    descripcion: Optional[str] = None
    tipo: str  # 'fijo' | 'personalizable'
    precio_base: Optional[float] = None
    foto_url: Optional[str] = None
    activo: bool
    opciones: List[ProductoOpcionOut] = []
    model_config = ConfigDict(from_attributes=True)


# ---------- Cursos ----------
class CursoOut(BaseModel):
    id: str
    nombre: str
    descripcion: Optional[str] = None
    precio_original: float
    precio_final: float
    tiene_descuento: bool
    portada_url: Optional[str] = None
    archivo_pdf_url: Optional[str] = None
    activo: bool


# ---------- Cotizaciones ----------
class CotizacionCreate(BaseModel):
    nombre_cliente: str
    producto_id: Optional[str] = None
    sucursal_id: str
    tamano: Optional[str] = None
    sabor: Optional[str] = None
    relleno: Optional[str] = None
    decoracion_texto: Optional[str] = None
    foto_referencia_url: Optional[str] = None
    mensaje_pastel: Optional[str] = None
    fecha_deseada: date
    email_cliente: EmailStr
    telefono_cliente: str


class CotizacionOut(BaseModel):
    id: str
    nombre_cliente: Optional[str] = None
    producto_id: Optional[str] = None
    sucursal_id: str
    tamano: Optional[str] = None
    sabor: Optional[str] = None
    relleno: Optional[str] = None
    decoracion_texto: Optional[str] = None
    foto_referencia_url: Optional[str] = None
    mensaje_pastel: Optional[str] = None
    fecha_deseada: date
    estado: str
    created_at: datetime
    telefono_cliente: Optional[str] = None
    email_cliente: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


# ---------- Pedidos ----------
class PedidoAdminOut(BaseModel):
    id: str
    cliente_nombre: str
    productos: str
    sucursal_id: Optional[str] = None
    tipo_entrega: str
    fecha_entrega: date
    total: float
    estado: str
    created_at: datetime

class PedidoItemCreate(BaseModel):
    producto_id: str
    opcion_id: Optional[str] = None
    cantidad: int = 1
    precio_unitario: float


class PedidoCreate(BaseModel):
    sucursal_id: Optional[str] = None
    tipo_entrega: str  # 'recoger' | 'delivery' | 'digital'
    direccion_id: Optional[str] = None
    fecha_entrega: date
    items: List[PedidoItemCreate] = []
    cursos: List[str] = []  # IDs de cursos incluidos en este pedido


class PedidoOut(BaseModel):
    id: str
    estado: str
    total: float
    fecha_entrega: date
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ContactoMensajeCreate(BaseModel):
    nombre: str
    correo: EmailStr
    mensaje: str


class ContactoMensajeOut(BaseModel):
    contacto_mensaje_id: str
    nombre: str
    correo: str
    mensaje: str
    fecha_envio: datetime
    leido: bool

    class Config:
        from_attributes = True


# ---------- Configuración ----------
class ConfiguracionOut(BaseModel):
    clave: str
    valor: str
    model_config = ConfigDict(from_attributes=True)


# ---------- Autenticación ----------
class UsuarioCreate(BaseModel):
    nombre: str
    email: EmailStr
    password: str
    telefono: Optional[str] = None


class UsuarioOut(BaseModel):
    id: str
    nombre: str
    email: EmailStr
    telefono: Optional[str] = None
    rol: str
    model_config = ConfigDict(from_attributes=True)


class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut


# ---------- Sucursales ----------

class SucursalOut(BaseModel):
    id: str
    nombre: str
    direccion: str
    horario: Optional[str] = None
    telefono: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class SucursalUpdate(BaseModel):
    nombre: str
    direccion: str
    horario: Optional[str] = None
    telefono: Optional[str] = None


class ProductoCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    tipo: str  # 'fijo' | 'personalizable'
    precio_base: Optional[float] = None
    foto_url: Optional[str] = None
    activo: bool = True


class ProductoUpdate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    tipo: str
    precio_base: Optional[float] = None
    foto_url: Optional[str] = None
    activo: bool


class CursoCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    precio: float
    portada_url: Optional[str] = None
    archivo_pdf_url: str
    activo: bool = True


class CursoUpdate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    precio: float
    portada_url: Optional[str] = None
    archivo_pdf_url: Optional[str] = None
    activo: bool


class ProductoOpcionCreate(BaseModel):
    tipo_opcion: str  # 'tamaño' | 'sabor' | 'relleno' | 'decoracion'
    nombre: str
    precio_extra: float = 0