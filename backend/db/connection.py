"""Acceso a SQL Server mediante pyodbc.

Expone dos context managers:

* ``conexion()``  -> conexion cruda en autocommit (lecturas).
* ``transaccion()`` -> unidad de trabajo atomica: commit al salir bien,
  rollback ante cualquier excepcion. Con esto se cumplen las propiedades
  ACID exigidas para prestamos y devoluciones.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Iterator, Sequence

try:
    import pyodbc
except ImportError:  # pragma: no cover
    pyodbc = None  # type: ignore[assignment]

from config.settings import DatabaseConfig

logger = logging.getLogger(__name__)

# Nivel de aislamiento por defecto para las transacciones de negocio.
# READ COMMITTED evita lecturas sucias sin bloquear de mas.
ISOLATION_LEVEL = "READ COMMITTED"


class DatabaseError(RuntimeError):
    """Error de base de datos propio del backend."""


class Database:
    """Fabrica de conexiones para un nodo concreto."""

    def __init__(self, config: DatabaseConfig) -> None:
        if pyodbc is None:
            raise DatabaseError(
                "pyodbc no esta instalado. Ejecuta: pip install -r requirements.txt"
            )
        self.config = config

    # ------------------------------------------------------------------
    # Conexiones
    # ------------------------------------------------------------------
    def _connect(self, autocommit: bool):
        try:
            return pyodbc.connect(
                self.config.connection_string(),
                timeout=self.config.timeout,
                autocommit=autocommit,
            )
        except Exception as exc:  # pragma: no cover - depende del entorno
            raise DatabaseError(
                f"No se pudo conectar a la base de datos '{self.config.database}': {exc}"
            ) from exc

    @contextmanager
    def conexion(self) -> Iterator[Any]:
        """Conexion en autocommit, pensada para consultas de solo lectura."""
        cnx = self._connect(autocommit=True)
        try:
            yield cnx
        finally:
            cnx.close()

    @contextmanager
    def transaccion(self) -> Iterator[Any]:
        """Unidad de trabajo atomica (ACID).

        Uso::

            with db.transaccion() as cursor:
                cursor.execute(...)
                cursor.execute(...)
        """
        cnx = self._connect(autocommit=False)
        cursor = cnx.cursor()
        try:
            cursor.execute(f"SET TRANSACTION ISOLATION LEVEL {ISOLATION_LEVEL};")
            yield cursor
            cnx.commit()
        except Exception:
            cnx.rollback()
            logger.exception("Transaccion revertida (rollback)")
            raise
        finally:
            cursor.close()
            cnx.close()

    # ------------------------------------------------------------------
    # Helpers de consulta
    # ------------------------------------------------------------------
    def consultar(self, sql: str, params: Sequence[Any] = ()) -> list[dict[str, Any]]:
        """Ejecuta un SELECT y devuelve una lista de diccionarios."""
        with self.conexion() as cnx:
            cursor = cnx.cursor()
            cursor.execute(sql, params)
            columnas = [col[0] for col in cursor.description]
            filas = [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
            cursor.close()
            return filas

    def consultar_uno(
        self, sql: str, params: Sequence[Any] = ()
    ) -> dict[str, Any] | None:
        filas = self.consultar(sql, params)
        return filas[0] if filas else None

    def ejecutar(self, sql: str, params: Sequence[Any] = ()) -> int:
        """Ejecuta un INSERT/UPDATE/DELETE aislado y devuelve filas afectadas."""
        with self.transaccion() as cursor:
            cursor.execute(sql, params)
            return cursor.rowcount

    def probar_conexion(self) -> bool:
        """Verifica que el nodo puede hablar con su base de datos."""
        return self.diagnosticar()[0]

    def diagnosticar(self) -> tuple[bool, str | None]:
        """Como probar_conexion, pero devuelve tambien el motivo del fallo."""
        try:
            self.consultar("SELECT 1 AS ok;")
            return True, None
        except DatabaseError as exc:
            return False, str(exc)


def filas_a_dicts(cursor) -> list[dict[str, Any]]:
    """Convierte el resultado actual de un cursor en lista de diccionarios."""
    columnas = [col[0] for col in cursor.description]
    return [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
