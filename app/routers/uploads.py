import uuid
import re
from datetime import datetime, timedelta
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from azure.storage.blob import BlobServiceClient, ContentSettings, generate_blob_sas, BlobSasPermissions
import os
from dotenv import load_dotenv
from .. import models, security

load_dotenv()

router = APIRouter(prefix="/api/uploads", tags=["uploads"])

CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = os.getenv("AZURE_STORAGE_CONTAINER")


def _extraer_credenciales(connection_string: str):
    """Extrae account_name y account_key de la connection string, necesarios para firmar SAS tokens."""
    partes = dict(p.split("=", 1) for p in connection_string.split(";") if "=" in p)
    return partes.get("AccountName"), partes.get("AccountKey")

EXTENSIONES_PERMITIDAS = {
    "imagen": {".jpg", ".jpeg", ".png", ".webp"},
    "pdf": {".pdf"},
}

@router.post("/{tipo}")
async def subir_archivo(tipo: str, archivo: UploadFile = File(...)):
    if tipo not in EXTENSIONES_PERMITIDAS:
        raise HTTPException(status_code=400, detail="Tipo de archivo no soportado. Usa 'imagen' o 'pdf'.")

    extension = os.path.splitext(archivo.filename)[1].lower()
    if extension not in EXTENSIONES_PERMITIDAS[tipo]:
        raise HTTPException(status_code=400, detail=f"Extensión no permitida para tipo '{tipo}': {extension}")

    nombre_unico = f"{tipo}/{uuid.uuid4()}{extension}"

    try:
        blob_service = BlobServiceClient.from_connection_string(CONNECTION_STRING)
        blob_client = blob_service.get_blob_client(container=CONTAINER_NAME, blob=nombre_unico)

        contenido = await archivo.read()
        content_type = "application/pdf" if tipo == "pdf" else archivo.content_type

        blob_client.upload_blob(
            contenido,
            overwrite=True,
            content_settings=ContentSettings(content_type=content_type),
        )

        return {"url": blob_client.url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir archivo: {str(e)}")


EXTENSIONES_VIDEO = {".mp4", ".mov", ".webm"}


@router.get("/sas-video")
def obtener_sas_video(
    filename: str,
    _admin: models.Usuario = Depends(security.get_current_admin),
):
    """
    Genera una URL firmada temporal (SAS) para que el navegador suba
    un video DIRECTO a Blob Storage, sin pasar por este servidor.
    Necesario porque los videos son demasiado grandes para procesarlos
    en memoria dentro del plan B1 de App Service.
    """
    extension = os.path.splitext(filename)[1].lower()
    if extension not in EXTENSIONES_VIDEO:
        raise HTTPException(status_code=400, detail="Formato de video no soportado (usa .mp4, .mov o .webm)")

    account_name, account_key = _extraer_credenciales(CONNECTION_STRING)
    if not account_name or not account_key:
        raise HTTPException(status_code=500, detail="Configuración de almacenamiento incompleta")

    nombre_blob = f"video/{uuid.uuid4()}{extension}"

    sas_token = generate_blob_sas(
        account_name=account_name,
        account_key=account_key,
        container_name=CONTAINER_NAME,
        blob_name=nombre_blob,
        permission=BlobSasPermissions(write=True, create=True),
        expiry=datetime.utcnow() + timedelta(minutes=30),
    )

    upload_url = f"https://{account_name}.blob.core.windows.net/{CONTAINER_NAME}/{nombre_blob}?{sas_token}"
    public_url = f"https://{account_name}.blob.core.windows.net/{CONTAINER_NAME}/{nombre_blob}"

    return {"upload_url": upload_url, "public_url": public_url}