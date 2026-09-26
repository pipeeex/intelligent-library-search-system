"""Datos de la(s) biblioteca(s) registradas en el nodo."""

from __future__ import annotations

from models.entidades import Biblioteca
from repositories.base import BaseRepository

CAMPOS = "id_biblioteca, nombre, direccion, estado"


class BibliotecaRepository(BaseRepository):
    def listar(self, cursor=None) -> list[Biblioteca]:
        rows = self._select(
            f"SELECT {CAMPOS} FROM Biblioteca ORDER BY id_biblioteca;", (), cursor
        )
        return [Biblioteca.from_row(r) for r in rows]

    def obtener(self, id_biblioteca: int, cursor=None) -> Biblioteca | None:
        row = self._select_one(
            f"SELECT {CAMPOS} FROM Biblioteca WHERE id_biblioteca = ?;",
            (id_biblioteca,),
            cursor,
        )
        return Biblioteca.from_row(row) if row else None

    def crear(self, biblioteca: Biblioteca, cursor=None) -> int:
        sql = """
            INSERT INTO Biblioteca (nombre, direccion, estado)
            OUTPUT INSERTED.id_biblioteca
            VALUES (?, ?, ?);
        """
        return self._insert_returning_id(
            sql,
            (biblioteca.nombre, biblioteca.direccion, biblioteca.estado),
            cursor,
        )

    def actualizar(self, biblioteca: Biblioteca, cursor=None) -> bool:
        filas = self._execute(
            """
            UPDATE Biblioteca
               SET nombre = ?, direccion = ?, estado = ?
             WHERE id_biblioteca = ?;
            """,
            (
                biblioteca.nombre,
                biblioteca.direccion,
                biblioteca.estado,
                biblioteca.id_biblioteca,
            ),
            cursor,
        )
        return filas > 0
