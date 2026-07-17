# Niza Isabela — Backend (FastAPI + SQL Server)

## Estructura
```
backend-niza-isabela/
├── app/
│   ├── main.py           # arranca la API y registra los routers
│   ├── database.py        # conexión a SQL Server (SQLAlchemy + pyodbc)
│   ├── models.py           # tablas, igual al esquema T-SQL ya diseñado
│   ├── schemas.py          # validación de entradas/salidas (Pydantic)
│   └── routers/
│       ├── productos.py
│       ├── cursos.py
│       ├── cotizaciones.py
│       ├── pedidos.py
│       └── configuracion.py
├── requirements.txt
└── .env.example
```

## Cómo correrlo en tu computadora

1. Instala el driver ODBC de SQL Server (una sola vez):
   - Windows: normalmente ya viene con SQL Server Management Studio.
   - Mac: `brew install unixodbc` y luego el driver de Microsoft.

2. Crea un entorno virtual e instala dependencias:
   ```
   python -m venv venv
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # Mac/Linux
   pip install -r requirements.txt
   ```

3. Copia `.env.example` a `.env` y ajusta `DATABASE_URL` con los datos de tu SQL Server local.

4. Corre las tablas del script T-SQL (el de 03-Base-de-Datos.md) contra tu base `niza_isabela`.

5. Levanta el servidor:
   ```
   uvicorn app.main:app --reload
   ```

6. Abre `http://localhost:8000/docs` — FastAPI genera automáticamente una interfaz
   interactiva donde puedes probar cada endpoint sin necesidad de Postman.

## Conectar el front-end

En `sitio-niza-isabela/js/main.js`, las llamadas a estos endpoints reemplazan
los datos estáticos que hoy están escritos directo en el HTML. Por ejemplo,
el catálogo pasaría de tener las tarjetas fijas en `catalogo.html` a pedirlas
con `fetch('http://localhost:8000/api/productos/')`.

## Desplegar en Azure (cuando esté listo)

1. Crear un **Azure SQL Database** (tier Basic) y correr ahí el script T-SQL.
2. Crear un **Azure App Service** (Linux, Python 3.12, tier B1 Basic).
3. Configurar `DATABASE_URL` como variable de entorno en el App Service
   (Configuration → Application settings) — nunca subir el `.env` real.
4. Para FastAPI, Azure necesita un comando de arranque personalizado:
   ```
   gunicorn -w 2 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 app.main:app
   ```
   (Se configura en Configuration → General settings → Startup Command)

## Autenticación

- `POST /api/auth/registro` — crea una cuenta nueva. Siempre con rol `cliente`.
- `POST /api/auth/login` — devuelve un JWT (`access_token`) válido por 7 días.
- `GET /api/auth/me` — con el token en el header `Authorization: Bearer <token>`, devuelve quién está logueado.

**Por seguridad, nadie puede volverse `admin` a través del registro público.** Para convertir la cuenta de Isabela en admin:

1. Que ella se registre normalmente desde el sitio (quedará como `cliente`).
2. Tú, directo en SSMS, corres:
   ```sql
   UPDATE usuarios SET rol = 'admin' WHERE email = 'correo-de-isabela@ejemplo.com';
   ```
3. Isabela vuelve a iniciar sesión — ahora sí verá el link "Panel admin" en la navegación.

## Lo que falta para producción (siguiente iteración)

- Integración con Mercado Pago (crear preferencia de pago, recibir webhook de confirmación).
- Subida de archivos (fotos de referencia, PDFs de cursos) a Azure Blob Storage.
- Envío de correos (confirmación de pedido, enlace de descarga de curso).
- Migraciones de base de datos con Alembic, en vez de correr el script T-SQL a mano.
- Recuperación de contraseña ("olvidé mi contraseña").
