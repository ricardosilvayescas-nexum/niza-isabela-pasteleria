"""
main.py
Punto de entrada de la API. Arranca con:
    uvicorn app.main:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from .routers import productos, cursos, cotizaciones, pedidos, configuracion, auth, contacto, sucursales, reportes, pagos, uploads

app = FastAPI(
    title="Niza Isabela — API",
    description="Backend de pastelería, pedidos, cotizaciones y cursos digitales.",
    version="1.0.0",
)

# En producción, reemplazar "*" por el dominio real del sitio (ej. https://nizaisabela.com)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(productos.router)
app.include_router(cursos.router)
app.include_router(cotizaciones.router)
app.include_router(pedidos.router)
app.include_router(configuracion.router)
app.include_router(contacto.router)
app.include_router(sucursales.router)
app.include_router(reportes.router)
app.include_router(pagos.router)
app.include_router(uploads.router)

@app.get("/")
def raiz():
    return {"status": "ok", "servicio": "Niza Isabela API"}


@app.get("/health")
def health_check():
    """Endpoint simple para que Azure App Service confirme que el servicio sigue vivo."""
    return {"status": "healthy"}
