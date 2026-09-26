"""Bitacora de consultas (la usara el modulo de IA cuando se implemente)."""

from __future__ import annotations

from typing import Any

from repositories.base import BaseRepository


class ConsultaRepository(BaseRepository):
    def registrar_consulta(
        self, pregunta: str, tipo_consulta: str = "DISPONIBILIDAD", cursor=None
    ) -> int:
        sql = """
            INSERT INTO Consulta (pregunta, tipo_consulta)
            OUTPUT INSERTED.id_consulta
            VALUES (?, ?);
        """
        return self._insert_returning_id(sql, (pregunta[:500], tipo_consulta), cursor)

    def registrar_resultado(
        self,
        id_consulta: int,
        id_biblioteca: int,
        disponibilidad: str,
        cantidad_disponible: int,
        mensaje: str | None = None,
        cursor=None,
    ) -> int:
        sql = """
            INSERT INTO Resultado_Consulta
                (id_consulta, id_biblioteca, disponibilidad, cantidad_disponible, mensaje)
            OUTPUT INSERTED.id_resultado
            VALUES (?, ?, ?, ?, ?);
        """
        return self._insert_returning_id(
            sql,
            (
                id_consulta,
                id_biblioteca,
                disponibilidad,
                max(0, int(cantidad_disponible)),
                (mensaje or "")[:500] or None,
            ),
            cursor,
        )

    def historial(self, limite: int = 50, cursor=None) -> list[dict[str, Any]]:
        return self._select(
            """
            SELECT TOP (?) id_consulta, pregunta, fecha_hora, tipo_consulta
              FROM Consulta
             ORDER BY fecha_hora DESC;
            """,
            (limite,),
            cursor,
        )
