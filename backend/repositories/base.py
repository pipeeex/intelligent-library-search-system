"""Clase base para los repositorios."""

from __future__ import annotations

from typing import Any, Sequence

from db.connection import Database


class BaseRepository:
    """Repositorio con acceso a la base de datos del nodo.

    Todos los metodos aceptan un ``cursor`` opcional: cuando se pasa, la
    operacion se ejecuta dentro de la transaccion abierta por el servicio
    (permitiendo atomicidad entre varias tablas). Cuando no se pasa, la
    operacion se ejecuta en su propia conexion.
    """

    def __init__(self, db: Database) -> None:
        self.db = db

    # -- helpers --------------------------------------------------------
    @staticmethod
    def _rows(cursor) -> list[dict[str, Any]]:
        columnas = [col[0] for col in cursor.description]
        return [dict(zip(columnas, fila)) for fila in cursor.fetchall()]

    def _select(
        self, sql: str, params: Sequence[Any] = (), cursor=None
    ) -> list[dict[str, Any]]:
        if cursor is None:
            return self.db.consultar(sql, params)
        cursor.execute(sql, params)
        return self._rows(cursor)

    def _select_one(
        self, sql: str, params: Sequence[Any] = (), cursor=None
    ) -> dict[str, Any] | None:
        filas = self._select(sql, params, cursor)
        return filas[0] if filas else None

    def _execute(self, sql: str, params: Sequence[Any] = (), cursor=None) -> int:
        if cursor is None:
            return self.db.ejecutar(sql, params)
        cursor.execute(sql, params)
        return cursor.rowcount

    def _insert_returning_id(
        self, sql: str, params: Sequence[Any] = (), cursor=None
    ) -> int:
        """Ejecuta un INSERT con clausula OUTPUT INSERTED.<id> y lo devuelve."""
        if cursor is None:
            with self.db.transaccion() as cur:
                cur.execute(sql, params)
                return int(cur.fetchone()[0])
        cursor.execute(sql, params)
        return int(cursor.fetchone()[0])
