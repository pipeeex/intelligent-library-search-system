"""Diagnostico de la conexion a SQL Server.

Uso (desde backend/, con el venv activo):

    python tools/diagnostico.py

Hace tres cosas:
  1. Lista los drivers ODBC instalados en Windows.
  2. Muestra la cadena de conexion que arma el .env para cada nodo y la prueba.
  3. Si falla, prueba automaticamente variantes comunes de servidor/driver
     hasta encontrar una que funcione, y te dice que poner en el .env.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    import pyodbc
except ImportError:
    print("pyodbc no esta instalado. Ejecuta: pip install -r requirements.txt")
    raise SystemExit(1)

from config.settings import (  # noqa: E402
    ENV_CARGADO,
    ENV_FILE,
    ENV_ORIGEN,
    NODOS_VALIDOS,
    get_nodo_config,
)


def separador(titulo: str) -> None:
    print("\n" + "=" * 62)
    print(titulo)
    print("=" * 62)


def probar(cadena: str, timeout: int = 5) -> tuple[bool, str]:
    try:
        cnx = pyodbc.connect(cadena, timeout=timeout)
        cnx.close()
        return True, "OK"
    except Exception as exc:
        return False, str(exc).replace("\n", " ")


def main() -> int:
    # ------------------------------------------------------------------
    separador("1. Drivers ODBC instalados")
    drivers = pyodbc.drivers()
    if not drivers:
        print("  (ninguno)  -> instala el ODBC Driver 18 for SQL Server")
        return 1
    for d in drivers:
        marca = "  <-- para SQL Server" if "SQL Server" in d else ""
        print(f"  - {d}{marca}")

    drivers_sql = [d for d in drivers if "SQL Server" in d]
    if not drivers_sql:
        print("\n  No hay ningun driver de SQL Server. Instala el ODBC Driver 18.")
        return 1

    # ------------------------------------------------------------------
    separador("2. Configuracion actual (.env)")
    print(f"  Archivo .env: {ENV_FILE}")
    print(f"  Existe: {'si' if ENV_FILE.exists() else 'NO'}")
    print(f"  Cargado: {'si' if ENV_CARGADO else 'NO'}  (via {ENV_ORIGEN})")
    if not ENV_FILE.exists():
        print("  -> Copia .env.example a .env antes de continuar.")
    elif not ENV_CARGADO:
        print("  -> El .env existe pero no se pudo leer. Revisa su contenido.")

    fallo_alguno = False
    for numero in NODOS_VALIDOS:
        nodo = get_nodo_config(numero)
        cadena = nodo.database.connection_string()
        ok, detalle = probar(cadena, nodo.database.timeout)
        print(f"\n  Nodo {numero} -> {nodo.database.database}")
        print(f"    {cadena}")
        print(f"    {'CONECTA' if ok else 'FALLA'}: {detalle[:300]}")
        if not ok:
            fallo_alguno = True

    if not fallo_alguno:
        print("\nTodo conecta. Puedes levantar los nodos.")
        return 0

    # ------------------------------------------------------------------
    separador("3. Buscando una combinacion que funcione")
    base = get_nodo_config(1).database
    servidores = [
        base.server,
        "localhost",
        "127.0.0.1",
        ".",
        "(local)",
        "localhost\\SQLEXPRESS",
        ".\\SQLEXPRESS",
        os.environ.get("COMPUTERNAME", "") or "localhost",
        f"{os.environ.get('COMPUTERNAME', '')}\\SQLEXPRESS",
    ]
    # sin duplicados, conservando el orden
    servidores = list(dict.fromkeys(s for s in servidores if s))

    encontrada = None
    for driver in drivers_sql:
        for servidor in servidores:
            cadena = (
                f"DRIVER={{{driver}}};SERVER={servidor};DATABASE=Biblioteca1DB;"
                "Trusted_Connection=yes;Encrypt=no;TrustServerCertificate=yes;"
            )
            ok, detalle = probar(cadena, 3)
            estado = "OK " if ok else "-- "
            print(f"  {estado} {driver}  |  SERVER={servidor}")
            if ok:
                encontrada = (driver, servidor)
                break
        if encontrada:
            break

    separador("Resultado")
    if encontrada:
        driver, servidor = encontrada
        print("  Funciona con:\n")
        print(f"    DB_DRIVER={driver}")
        print(f"    DB_SERVER={servidor}")
        print("    DB_TRUSTED_CONNECTION=yes")
        print("    DB_ENCRYPT=no")
        print("    DB_TRUST_SERVER_CERTIFICATE=yes")
        print("\n  Pon esos valores en backend/.env y vuelve a levantar el nodo.")
        return 0

    print("  Ninguna combinacion conecto. Revisa:")
    print("   - El nombre del servidor que aparece arriba del Object Explorer")
    print("     en SSMS (boton derecho > Properties > Name).")
    print("   - Que el servicio 'SQL Server (MSSQLSERVER o SQLEXPRESS)' este")
    print("     iniciado en services.msc.")
    print("   - Que existan las bases Biblioteca1DB, Biblioteca2DB y Biblioteca3DB.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
