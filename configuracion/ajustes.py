"""Configuracion central del backend.

Cada biblioteca es un nodo autonomo: su propia base de datos SQL Server y su
propio puerto gRPC. Toda la configuracion se lee de variables de entorno
(archivo .env) para no dejar credenciales en el codigo.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

# Estado de la carga del .env; lo consulta tools/diagnostico.py.
ENV_CARGADO = False
ENV_ORIGEN = "ninguno"


def _cargar_env_manual(ruta: Path) -> bool:
    """Lector minimo de .env, por si python-dotenv no esta instalado.

    Soporta 'CLAVE=valor', comentarios con '#', lineas en blanco y comillas
    alrededor del valor. NO sobreescribe variables de entorno ya definidas,
    igual que python-dotenv.
    """
    if not ruta.exists():
        return False
    for linea in ruta.read_text(encoding="utf-8-sig").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, _, valor = linea.partition("=")
        clave = clave.strip()
        valor = valor.strip().strip('"').strip("'")
        if clave and clave not in os.environ:
            os.environ[clave] = valor
    return True


def _cargar_env() -> None:
    global ENV_CARGADO, ENV_ORIGEN
    try:
        from dotenv import load_dotenv
    except ImportError:
        ENV_CARGADO = _cargar_env_manual(ENV_FILE)
        ENV_ORIGEN = "lector interno" if ENV_CARGADO else "ninguno"
        return
    ENV_CARGADO = bool(load_dotenv(ENV_FILE))
    ENV_ORIGEN = "python-dotenv" if ENV_CARGADO else "ninguno"
    if not ENV_CARGADO:
        ENV_CARGADO = _cargar_env_manual(ENV_FILE)
        if ENV_CARGADO:
            ENV_ORIGEN = "lector interno"


_cargar_env()

NODOS_VALIDOS = (1, 2, 3)


def _bool_env(nombre: str, por_defecto: bool = False) -> bool:
    valor = os.getenv(nombre)
    if valor is None:
        return por_defecto
    return valor.strip().lower() in {"1", "true", "yes", "si", "s", "y"}


@dataclass(frozen=True)
class DatabaseConfig:
    """Datos necesarios para armar la cadena de conexion ODBC."""

    driver: str
    server: str
    database: str
    trusted_connection: bool
    user: str | None
    password: str | None
    encrypt: bool
    trust_server_certificate: bool
    timeout: int

    def connection_string(self) -> str:
        partes = [
            f"DRIVER={{{self.driver}}}",
            f"SERVER={self.server}",
            f"DATABASE={self.database}",
            f"Encrypt={'yes' if self.encrypt else 'no'}",
            f"TrustServerCertificate={'yes' if self.trust_server_certificate else 'no'}",
        ]
        if self.trusted_connection:
            partes.append("Trusted_Connection=yes")
        else:
            partes.append(f"UID={self.user or ''}")
            partes.append(f"PWD={self.password or ''}")
        return ";".join(partes) + ";"


@dataclass(frozen=True)
class NodoConfig:
    """Configuracion completa de un nodo bibliotecario."""

    numero: int
    nombre: str
    host: str
    port: int
    database: DatabaseConfig

    @property
    def address(self) -> str:
        return f"{self.host}:{self.port}"


def get_nodo_config(numero: int) -> NodoConfig:
    """Devuelve la configuracion del nodo indicado (1, 2 o 3)."""
    if numero not in NODOS_VALIDOS:
        raise ValueError(
            f"Nodo invalido: {numero}. Valores permitidos: {NODOS_VALIDOS}"
        )

    prefijo = f"NODO{numero}"
    db = DatabaseConfig(
        driver=os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server"),
        server=os.getenv("DB_SERVER", "localhost\\SQLEXPRESS"),
        database=os.getenv(f"{prefijo}_DB", f"Biblioteca{numero}DB"),
        trusted_connection=_bool_env("DB_TRUSTED_CONNECTION", True),
        user=os.getenv("DB_USER") or None,
        password=os.getenv("DB_PASSWORD") or None,
        encrypt=_bool_env("DB_ENCRYPT", False),
        trust_server_certificate=_bool_env("DB_TRUST_SERVER_CERTIFICATE", True),
        timeout=int(os.getenv("DB_TIMEOUT", "5")),
    )

    return NodoConfig(
        numero=numero,
        nombre=f"Biblioteca {numero}",
        host=os.getenv(f"{prefijo}_HOST", "127.0.0.1"),
        port=int(os.getenv(f"{prefijo}_PORT", str(50050 + numero))),
        database=db,
    )


def get_todos_los_nodos() -> list[NodoConfig]:
    """Configuracion de los tres nodos; util para el cliente distribuido."""
    return [get_nodo_config(n) for n in NODOS_VALIDOS]


DIAS_PRESTAMO = int(os.getenv("DIAS_PRESTAMO", "15"))
