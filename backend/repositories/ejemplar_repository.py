"""CRUD de ejemplares (copias fisicas de un libro dentro de una biblioteca)."""

from __future__ import annotations

from models.entidades import Ejemplar
from repositories.base import BaseRepository

CAMPOS = (
    "e.id_ejemplar, e.id_libro, e.id_biblioteca, e.codigo_inventario, e.estado, "
    "l.titulo, l.autor"
)


class EjemplarRepository(BaseRepository):
    def crear(self, ejemplar: Ejemplar, cursor=None) -> int:
        sql = """
            INSERT INTO Ejemplar (id_libro, id_biblioteca, codigo_inventario, estado)
            OUTPUT INSERTED.id_ejemplar
            VALUES (?, ?, ?, ?);
        """
        return self._insert_returning_id(
            sql,
            (
                ejemplar.id_libro,
                ejemplar.id_biblioteca,
                ejemplar.codigo_inventario,
                ejemplar.estado,
            ),
            cursor,
        )

    def obtener(self, id_ejemplar: int, cursor=None) -> Ejemplar | None:
        row = self._select_one(
            f"""
            SELECT {CAMPOS}
              FROM Ejemplar e
              JOIN Libro l ON l.id_libro = e.id_libro
             WHERE e.id_ejemplar = ?;
            """,
            (id_ejemplar,),
            cursor,
        )
        return Ejemplar.from_row(row) if row else None

    def listar_por_libro(
        self, id_libro: int, solo_disponibles: bool = False, cursor=None
    ) -> list[Ejemplar]:
        filtro = "AND e.estado = 'DISPONIBLE'" if solo_disponibles else ""
        rows = self._select(
            f"""
            SELECT {CAMPOS}
              FROM Ejemplar e
              JOIN Libro l ON l.id_libro = e.id_libro
             WHERE e.id_libro = ? {filtro}
             ORDER BY e.codigo_inventario;
            """,
            (id_libro,),
            cursor,
        )
        return [Ejemplar.from_row(r) for r in rows]

    def bloquear_disponible(self, id_libro: int, cursor) -> Ejemplar | None:
        """Toma el primer ejemplar DISPONIBLE y lo bloquea para la transaccion.

        Requiere un cursor dentro de una transaccion abierta. Los hints
        UPDLOCK/ROWLOCK evitan que dos prestamos simultaneos tomen el mismo
        ejemplar (aislamiento).
        """
        cursor.execute(
            f"""
            SELECT TOP (1) {CAMPOS}
              FROM Ejemplar e WITH (UPDLOCK, ROWLOCK, READPAST)
              JOIN Libro l ON l.id_libro = e.id_libro
             WHERE e.id_libro = ? AND e.estado = 'DISPONIBLE'
             ORDER BY e.id_ejemplar;
            """,
            (id_libro,),
        )
        filas = self._rows(cursor)
        return Ejemplar.from_row(filas[0]) if filas else None

    def cambiar_estado(self, id_ejemplar: int, estado: str, cursor=None) -> bool:
        filas = self._execute(
            "UPDATE Ejemplar SET estado = ? WHERE id_ejemplar = ?;",
            (estado, id_ejemplar),
            cursor,
        )
        return filas > 0

    def actualizar(self, ejemplar: Ejemplar, cursor=None) -> bool:
        sql = """
            UPDATE Ejemplar
               SET id_libro = ?, id_biblioteca = ?, codigo_inventario = ?, estado = ?
             WHERE id_ejemplar = ?;
        """
        filas = self._execute(
            sql,
            (
                ejemplar.id_libro,
                ejemplar.id_biblioteca,
                ejemplar.codigo_inventario,
                ejemplar.estado,
                ejemplar.id_ejemplar,
            ),
            cursor,
        )
        return filas > 0

    def dar_de_baja(self, id_ejemplar: int, cursor=None) -> bool:
        """Baja logica: se conserva el historial de prestamos."""
        return self.cambiar_estado(id_ejemplar, "BAJA", cursor)

    def eliminar(self, id_ejemplar: int, cursor=None) -> bool:
        filas = self._execute(
            "DELETE FROM Ejemplar WHERE id_ejemplar = ?;", (id_ejemplar,), cursor
        )
        return filas > 0
