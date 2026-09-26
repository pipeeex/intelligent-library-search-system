"""CRUD de usuarios."""

from __future__ import annotations

from models.entidades import Usuario
from repositories.base import BaseRepository

CAMPOS = "id_usuario, nombre, documento, correo, telefono"


class UsuarioRepository(BaseRepository):
    def crear(self, usuario: Usuario, cursor=None) -> int:
        sql = """
            INSERT INTO Usuario (nombre, documento, correo, telefono)
            OUTPUT INSERTED.id_usuario
            VALUES (?, ?, ?, ?);
        """
        return self._insert_returning_id(
            sql,
            (usuario.nombre, usuario.documento, usuario.correo, usuario.telefono),
            cursor,
        )

    def obtener(self, id_usuario: int, cursor=None) -> Usuario | None:
        row = self._select_one(
            f"SELECT {CAMPOS} FROM Usuario WHERE id_usuario = ?;", (id_usuario,), cursor
        )
        return Usuario.from_row(row) if row else None

    def obtener_por_documento(self, documento: str, cursor=None) -> Usuario | None:
        row = self._select_one(
            f"SELECT {CAMPOS} FROM Usuario WHERE documento = ?;", (documento,), cursor
        )
        return Usuario.from_row(row) if row else None

    def listar(self, limite: int = 200, cursor=None) -> list[Usuario]:
        rows = self._select(
            f"SELECT TOP (?) {CAMPOS} FROM Usuario ORDER BY nombre;", (limite,), cursor
        )
        return [Usuario.from_row(r) for r in rows]

    def buscar_por_nombre(
        self, nombre: str, limite: int = 100, cursor=None
    ) -> list[Usuario]:
        rows = self._select(
            f"SELECT TOP (?) {CAMPOS} FROM Usuario WHERE nombre LIKE ? ORDER BY nombre;",
            (limite, f"%{nombre}%"),
            cursor,
        )
        return [Usuario.from_row(r) for r in rows]

    def actualizar(self, usuario: Usuario, cursor=None) -> bool:
        sql = """
            UPDATE Usuario
               SET nombre = ?, documento = ?, correo = ?, telefono = ?
             WHERE id_usuario = ?;
        """
        filas = self._execute(
            sql,
            (
                usuario.nombre,
                usuario.documento,
                usuario.correo,
                usuario.telefono,
                usuario.id_usuario,
            ),
            cursor,
        )
        return filas > 0

    def eliminar(self, id_usuario: int, cursor=None) -> bool:
        filas = self._execute(
            "DELETE FROM Usuario WHERE id_usuario = ?;", (id_usuario,), cursor
        )
        return filas > 0

    def tiene_prestamos_activos(self, id_usuario: int, cursor=None) -> bool:
        row = self._select_one(
            """
            SELECT COUNT(*) AS n
              FROM Prestamo
             WHERE id_usuario = ? AND estado IN ('ACTIVO', 'VENCIDO');
            """,
            (id_usuario,),
            cursor,
        )
        return bool(row and row["n"] > 0)
