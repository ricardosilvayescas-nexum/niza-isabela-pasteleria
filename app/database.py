"""
database.py
Configura la conexión a SQL Server (local o Azure SQL Database) vía SQLAlchemy + pyodbc.
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Carga las variables del archivo .env al entorno — sin esto, DATABASE_URL
# nunca se lee y siempre se usa el valor por defecto de abajo.
load_dotenv()

# La cadena de conexión viene de una variable de entorno — nunca hardcodeada.
# Ejemplo para Azure SQL:
# DATABASE_URL=mssql+pyodbc://usuario:password@servidor.database.windows.net:1433/niza_isabela?driver=ODBC+Driver+18+for+SQL+Server
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mssql+pyodbc://sa:TuPassword123@localhost:1433/niza_isabela?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependencia de FastAPI: entrega una sesión de base de datos por request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
