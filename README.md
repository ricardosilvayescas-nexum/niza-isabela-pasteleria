# Niza Isabela Pastelería — Plataforma de E-commerce + Cursos Digitales

Plataforma completa de comercio electrónico para una pastelería en Amecameca, México — catálogo de productos, pasteles personalizados por cotización, cursos digitales (PDF/video), pagos en línea, panel de administración, y reseñas de clientes. Desplegada en producción sobre infraestructura de **Microsoft Azure**.

🔗 Sitio en producción: [nizaisabelapasteleria.com](https://www.nizaisabelapasteleria.com)

---

## Stack técnico

| Capa | Tecnología |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy |
| Base de datos | Azure SQL Database (SQL Server) |
| Frontend | HTML / CSS / JavaScript vanilla |
| Almacenamiento de archivos | Azure Blob Storage (Gen2) |
| Autenticación | JWT (python-jose) + bcrypt |
| Pagos | Mercado Pago (Checkout Pro) |
| Correo transaccional | SendGrid (con autenticación de dominio SPF/DKIM) |
| CI/CD | GitHub Actions |

## Infraestructura en Azure

| Servicio | Uso |
|---|---|
| **Azure App Service** (Linux, plan B1) | Hosting del backend (API REST en FastAPI) |
| **Azure Static Web Apps** | Hosting del frontend, con SSL y CDN automáticos |
| **Azure SQL Database** (tier Basic/DTU) | Base de datos relacional — 13 tablas |
| **Azure Blob Storage** (cuenta de propósito general v2) | Imágenes de producto/curso, PDFs, video, con subida directa desde el navegador vía SAS tokens |
| **Azure DNS / dominio personalizado** | `nizaisabelapasteleria.com` conectado a Static Web Apps con certificado SSL gratuito |

Cada push a `main` dispara automáticamente el build y despliegue tanto del backend (App Service) como del frontend (Static Web Apps) vía GitHub Actions — sin pasos manuales.

---

## Estructura del proyecto

```
niza-isabela-pasteleria/
├── app/
│   ├── main.py                # arranca la API y registra los routers
│   ├── database.py            # conexión a Azure SQL (SQLAlchemy + pyodbc)
│   ├── security.py            # JWT, hashing, dependencias de autenticación
│   ├── models.py              # modelos ORM (13 tablas)
│   ├── schemas.py             # validación de entradas/salidas (Pydantic)
│   ├── utils/
│   │   └── correo.py          # plantillas y envío de correo vía SendGrid
│   └── routers/
│       ├── auth.py            # registro, login, recuperación de contraseña
│       ├── productos.py       # catálogo, incluye estado "agotado"
│       ├── cursos.py          # cursos digitales (PDF y/o video)
│       ├── cotizaciones.py    # pasteles personalizados
│       ├── pedidos.py         # carrito → pedido, incluye pedidos manuales
│       ├── pagos.py           # Mercado Pago (preferencias + webhook)
│       ├── uploads.py         # subida de archivos + SAS tokens para video
│       ├── resenas.py         # reseñas de productos/cursos con moderación
│       ├── reportes.py        # KPIs para el dashboard admin
│       ├── contacto.py        # formulario de dudas
│       ├── sucursales.py
│       └── configuracion.py   # ajustes editables (WhatsApp, imágenes del sitio, etc.)
├── *.html                     # páginas públicas y panel admin (frontend)
├── css/styles.css
├── js/main.js
├── requirements.txt
└── .github/workflows/         # pipelines de CI/CD (generados por Azure)
```

## Funcionalidades principales

- **Catálogo de productos** con recorte de imágenes integrado, toggle de "agotado temporalmente"
- **Pasteles personalizados** vía formulario de cotización (con foto de referencia)
- **Cursos digitales**: entrega por PDF y/o video (subida directa a Blob Storage o embed de YouTube no listado)
- **Carrito mixto**: productos físicos y cursos digitales en un mismo checkout
- **Pagos en línea** con Mercado Pago, confirmación asíncrona vía webhook
- **Cuenta de cliente**: mis pedidos, mis cotizaciones, mis cursos
- **Recuperación de contraseña** por correo con token de un solo uso
- **Reseñas de clientes** (productos y cursos) con moderación desde el panel admin
- **Panel de administración completo**: pedidos (incluye registro manual), cotizaciones, catálogo, cursos, sucursales, dudas de contacto, reseñas, reportes de ventas, ajustes generales (incluye edición de imágenes del sitio sin tocar código)
- **Correos transaccionales**: confirmación al cliente + notificación al negocio, en los 3 flujos principales (pedido, cotización, contacto)

---

## Cómo correrlo en local

1. Instala el driver ODBC de SQL Server (una sola vez).
2. Crea un entorno virtual e instala dependencias:
   ```bash
   python -m venv venv
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # Mac/Linux
   pip install -r requirements.txt
   ```
3. Copia `.env.example` a `.env` y completa las variables (ver sección siguiente).
4. Levanta el servidor:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0
   ```
5. Abre `http://localhost:8000/docs` para la documentación interactiva de la API (Swagger).
6. Para el frontend, usa Live Server (VS Code) sobre los archivos `.html` de la raíz.

## Variables de entorno requeridas

```
DATABASE_URL=mssql+pyodbc://usuario:password@servidor.database.windows.net:1433/niza_isabela?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=no&Encrypt=yes
AZURE_STORAGE_CONNECTION_STRING=...
AZURE_STORAGE_CONTAINER=archivos-publicos
MERCADOPAGO_ACCESS_TOKEN=...
MERCADOPAGO_PUBLIC_KEY=...
MERCADOPAGO_WEBHOOK_URL=https://tu-backend/api/pagos/webhook
SENDGRID_API_KEY=...
SENDGRID_FROM_EMAIL=...
FRONTEND_URL=https://tu-frontend
SECRET_KEY=una-clave-larga-y-aleatoria-para-firmar-jwt
```

---

## Autenticación

- `POST /api/auth/registro` — crea una cuenta nueva (siempre rol `cliente`).
- `POST /api/auth/login` — devuelve un JWT válido por 7 días.
- `GET /api/auth/me` — devuelve el usuario autenticado.
- `POST /api/auth/olvide-password` / `POST /api/auth/restablecer-password` — recuperación de contraseña por correo.

**Nadie puede volverse `admin` desde el registro público.** Para dar permisos de administrador:
```sql
UPDATE usuarios SET rol = 'admin' WHERE email = 'correo@ejemplo.com';
```

---

## Roadmap / pendientes conocidos

- Endurecimiento de seguridad: sanitización de contenido generado por usuarios (reseñas) contra XSS, límite de tasa en endpoints públicos (uploads, reseñas), revisión de política CORS
- Notificaciones automáticas por WhatsApp (requiere integración con Meta Business API o Twilio)
- Reorganización de `main.js` en módulos separados por página/función
- Migración de DNS a Cloudflare (mejoraría el manejo de HTTPS en el dominio raíz sin `www`)
