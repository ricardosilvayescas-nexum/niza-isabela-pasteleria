import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from azure.storage.blob import BlobServiceClient, ContentSettings
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/api/uploads", tags=["uploads"])

CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = os.getenv("AZURE_STORAGE_CONTAINER")

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