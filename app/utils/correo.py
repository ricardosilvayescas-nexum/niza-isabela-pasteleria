"""
utils/correo.py
Módulo de envío de correos transaccionales vía SendGrid.
Usado por: cotizaciones, pedidos, contacto (confirmación al cliente).
"""
import os
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

load_dotenv()

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL")


def enviar_correo(destinatario: str, asunto: str, contenido_html: str) -> bool:
    """
    Envía un correo vía SendGrid. Regresa True/False según el resultado,
    y NUNCA lanza una excepción hacia arriba — un fallo de correo no debe
    tumbar el flujo principal (crear cotización, pedido, etc.).
    """
    if not destinatario:
        return False

    mensaje = Mail(
        from_email=SENDGRID_FROM_EMAIL,
        to_emails=destinatario,
        subject=asunto,
        html_content=contenido_html,
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(mensaje)
        return response.status_code in (200, 201, 202)
    except Exception as e:
        print(f"[correo] Error al enviar a {destinatario}: {e}")
        return False


def _plantilla_base(titulo: str, cuerpo_html: str) -> str:
    """Envoltura visual compartida — paleta café/dorado de Niza Isabela."""
    return f"""
    <div style="font-family:Arial,sans-serif; max-width:520px; margin:0 auto; background:#FFFDEE; padding:32px; border-radius:8px;">
      <div style="text-align:center; margin-bottom:24px;">
        <span style="font-size:22px; font-weight:600; color:#2E2013;">Niza <span style="color:#8D582E;">Isabela</span></span>
      </div>
      <h2 style="color:#2E2013; font-size:20px; margin-bottom:16px;">{titulo}</h2>
      <div style="color:#4A3722; font-size:14px; line-height:1.7;">
        {cuerpo_html}
      </div>
      <p style="margin-top:28px; font-size:12px; color:#8A7860; text-align:center;">
        Niza Isabela Pastelería — Amecameca, México
      </p>
    </div>
    """


def correo_confirmacion_cotizacion(nombre: str, tamano: str, sabor: str, fecha_deseada: str) -> str:
    cuerpo = f"""
      <p>Hola {nombre},</p>
      <p>Recibimos tu solicitud de cotización para un pastel personalizado:</p>
      <ul>
        <li><b>Tamaño:</b> {tamano or '—'}</li>
        <li><b>Sabor:</b> {sabor or '—'}</li>
        <li><b>Fecha deseada:</b> {fecha_deseada}</li>
      </ul>
      <p>Nos pondremos en contacto contigo por WhatsApp para afinar los detalles y coordinar el pago.</p>
    """
    return _plantilla_base("¡Recibimos tu solicitud! 🎂", cuerpo)


def correo_confirmacion_pedido(nombre: str, pedido_id: str, total: float, tipo_entrega: str) -> str:
    entrega_texto = "Recoger en sucursal" if tipo_entrega == "recoger" else "Entrega a domicilio"
    cuerpo = f"""
      <p>Hola {nombre},</p>
      <p>Tu pedido <b>#{pedido_id[:8]}</b> fue registrado correctamente.</p>
      <ul>
        <li><b>Total:</b> ${total:.0f} MXN</li>
        <li><b>Entrega:</b> {entrega_texto}</li>
      </ul>
      <p>Te avisaremos conforme tu pedido avance de estado. ¡Gracias por tu compra!</p>
    """
    return _plantilla_base("¡Gracias por tu pedido! 🧁", cuerpo)


def correo_confirmacion_contacto(nombre: str) -> str:
    cuerpo = f"""
      <p>Hola {nombre},</p>
      <p>Recibimos tu mensaje y te responderemos lo antes posible.</p>
      <p>Gracias por escribirnos.</p>
    """
    return _plantilla_base("Recibimos tu mensaje ✉️", cuerpo)


def correo_notificacion_nueva_cotizacion(nombre: str, telefono: str, tamano: str, sabor: str, fecha_deseada: str) -> str:
    cuerpo = f"""
      <p>Se recibió una nueva solicitud de cotización:</p>
      <ul>
        <li><b>Cliente:</b> {nombre}</li>
        <li><b>Teléfono:</b> {telefono or '—'}</li>
        <li><b>Tamaño:</b> {tamano or '—'}</li>
        <li><b>Sabor:</b> {sabor or '—'}</li>
        <li><b>Fecha deseada:</b> {fecha_deseada}</li>
      </ul>
      <p>Revisa el panel admin para ver todos los detalles y contactar al cliente.</p>
    """
    return _plantilla_base("Nueva cotización recibida 📋", cuerpo)


def correo_notificacion_nuevo_pedido(nombre: str, pedido_id: str, total: float, tipo_entrega: str) -> str:
    entrega_texto = "Recoger en sucursal" if tipo_entrega == "recoger" else "Entrega a domicilio"
    cuerpo = f"""
      <p>Se recibió un nuevo pedido:</p>
      <ul>
        <li><b>Cliente:</b> {nombre}</li>
        <li><b>Pedido:</b> #{pedido_id[:8]}</li>
        <li><b>Total:</b> ${total:.0f} MXN</li>
        <li><b>Entrega:</b> {entrega_texto}</li>
      </ul>
      <p>Revisa el panel admin para ver el detalle completo.</p>
    """
    return _plantilla_base("Nuevo pedido recibido 🧁", cuerpo)


def correo_notificacion_nueva_duda(nombre: str, correo: str, mensaje: str) -> str:
    cuerpo = f"""
      <p>Se recibió un nuevo mensaje de contacto:</p>
      <ul>
        <li><b>Nombre:</b> {nombre}</li>
        <li><b>Correo:</b> {correo}</li>
        <li><b>Mensaje:</b> "{mensaje}"</li>
      </ul>
      <p>Revisa el panel admin para marcarlo como leído.</p>
    """
    return _plantilla_base("Nuevo mensaje de contacto ✉️", cuerpo)


def obtener_correo_notificaciones(db) -> str | None:
    """Lee la clave 'correo_notificaciones' de la tabla configuracion."""
    from .. import models
    config = db.query(models.Configuracion).filter(
        models.Configuracion.clave == "correo_notificaciones"
    ).first()
    return config.valor if config and config.valor else None