"""Prestamos y devoluciones."""

from __future__ import annotations

from datetime import datetime

from models.entidades import Devolucion, Prestamo
from repositories.base import BaseRepository

CAMPOS = (
    "id_prestamo, id_usuario, id_ejemplar, fecha_prestamo, fecha_vencimiento, estado"
)


class PrestamoRepository(BaseRepository):
    def crear(self, prestamo: Prestamo, cursor=None) -> int:
        sql = """
            INSERT INTO Prestamo
                (id_usuario, id_ejemplar, fecha_prestamo, fecha_vencimiento, estado)
            OUTPUT INSERTED.id_prestamo
            VALUES (?, ?, ?, ?, ?);
        """
        return self._insert_returning_id(
            sql,
            (
                prestamo.id_usuario,
                prestamo.id_ejemplar,
                prestamo.fecha_prestamo,
                prestamo.fecha_vencimiento,
                prestamo.estado,
            ),
            cursor,
        )

    def obtener(self, id_prestamo: int, cursor=None) -> Prestamo | None:
        row = self._select_one(
            f"SELECT {CAMPOS} FROM Prestamo WHERE id_prestamo = ?;",
            (id_prestamo,),
            cursor,
        )
        return Prestamo.from_row(row) if row else None

    def obtener_para_actualizar(self, id_prestamo: int, cursor) -> Prestamo | None:
        """Lee el prestamo bloqueando la fila dentro de la transaccion actual."""
        cursor.execute(
            f"""
            SELECT {CAMPOS}
              FROM Prestamo WITH (UPDLOCK, ROWLOCK)
             WHERE id_prestamo = ?;
            """,
            (id_prestamo,),
        )
        filas = self._rows(cursor)
        return Prestamo.from_row(filas[0]) if filas else None

    def listar_por_usuario(
        self, id_usuario: int, solo_activos: bool = False, cursor=None
    ) -> list[Prestamo]:
        filtro = "AND estado IN ('ACTIVO', 'VENCIDO')" if solo_activos else ""
        rows = self._select(
            f"""
            SELECT {CAMPOS} FROM Prestamo
             WHERE id_usuario = ? {filtro}
             ORDER BY fecha_prestamo DESC;
            """,
            (id_usuario,),
            cursor,
        )
        return [Prestamo.from_row(r) for r in rows]

    def listar_vencidos(self, ahora: datetime | None = None, cursor=None) -> list[Prestamo]:
        ahora = ahora or datetime.now()
        rows = self._select(
            f"""
            SELECT {CAMPOS} FROM Prestamo
             WHERE estado = 'ACTIVO' AND fecha_vencimiento < ?
             ORDER BY fecha_vencimiento;
            """,
            (ahora,),
            cursor,
        )
        return [Prestamo.from_row(r) for r in rows]

    def cambiar_estado(self, id_prestamo: int, estado: str, cursor=None) -> bool:
        filas = self._execute(
            "UPDATE Prestamo SET estado = ? WHERE id_prestamo = ?;",
            (estado, id_prestamo),
            cursor,
        )
        return filas > 0

    def marcar_vencidos(self, ahora: datetime | None = None, cursor=None) -> int:
        ahora = ahora or datetime.now()
        return self._execute(
            """
            UPDATE Prestamo
               SET estado = 'VENCIDO'
             WHERE estado = 'ACTIVO' AND fecha_vencimiento < ?;
            """,
            (ahora,),
            cursor,
        )


class DevolucionRepository(BaseRepository):
    def crear(self, devolucion: Devolucion, cursor=None) -> int:
        sql = """
            INSERT INTO Devolucion (id_prestamo, fecha_devolucion, observacion)
            OUTPUT INSERTED.id_devolucion
            VALUES (?, ?, ?);
        """
        return self._insert_returning_id(
            sql,
            (
                devolucion.id_prestamo,
                devolucion.fecha_devolucion,
                devolucion.observacion,
            ),
            cursor,
        )

    def obtener_por_prestamo(self, id_prestamo: int, cursor=None) -> Devolucion | None:
        row = self._select_one(
            """
            SELECT id_devolucion, id_prestamo, fecha_devolucion, observacion
              FROM Devolucion WHERE id_prestamo = ?;
            """,
            (id_prestamo,),
            cursor,
        )
        return Devolucion.from_row(row) if row else None
