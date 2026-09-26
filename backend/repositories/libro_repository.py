"""CRUD de libros y consultas de disponibilidad por titulo."""

from __future__ import annotations

from models.entidades import DisponibilidadLibro, Libro
from repositories.base import BaseRepository

CAMPOS = "id_libro, isbn, titulo, autor, editorial, anio_publicacion"


class LibroRepository(BaseRepository):
    # -- Create ---------------------------------------------------------
    def crear(self, libro: Libro, cursor=None) -> int:
        sql = f"""
            INSERT INTO Libro (isbn, titulo, autor, editorial, anio_publicacion)
            OUTPUT INSERTED.id_libro
            VALUES (?, ?, ?, ?, ?);
        """
        return self._insert_returning_id(
            sql,
            (
                libro.isbn,
                libro.titulo,
                libro.autor,
                libro.editorial,
                libro.anio_publicacion,
            ),
            cursor,
        )

    # -- Read -----------------------------------------------------------
    def obtener(self, id_libro: int, cursor=None) -> Libro | None:
        row = self._select_one(
            f"SELECT {CAMPOS} FROM Libro WHERE id_libro = ?;", (id_libro,), cursor
        )
        return Libro.from_row(row) if row else None

    def obtener_por_isbn(self, isbn: str, cursor=None) -> Libro | None:
        row = self._select_one(
            f"SELECT {CAMPOS} FROM Libro WHERE isbn = ?;", (isbn,), cursor
        )
        return Libro.from_row(row) if row else None

    def listar(self, limite: int = 200, cursor=None) -> list[Libro]:
        rows = self._select(
            f"SELECT TOP (?) {CAMPOS} FROM Libro ORDER BY titulo;", (limite,), cursor
        )
        return [Libro.from_row(r) for r in rows]

    def buscar(
        self,
        titulo: str | None = None,
        autor: str | None = None,
        isbn: str | None = None,
        limite: int = 100,
        cursor=None,
    ) -> list[Libro]:
        """Busqueda flexible por titulo, autor y/o ISBN."""
        condiciones: list[str] = []
        params: list[object] = [limite]
        if titulo:
            condiciones.append("titulo LIKE ?")
            params.append(f"%{titulo}%")
        if autor:
            condiciones.append("autor LIKE ?")
            params.append(f"%{autor}%")
        if isbn:
            condiciones.append("isbn = ?")
            params.append(isbn)

        where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""
        sql = f"SELECT TOP (?) {CAMPOS} FROM Libro {where} ORDER BY titulo;"
        rows = self._select(sql, params, cursor)
        return [Libro.from_row(r) for r in rows]

    def disponibilidad(
        self,
        titulo: str | None = None,
        autor: str | None = None,
        isbn: str | None = None,
        limite: int = 50,
        cursor=None,
    ) -> list[DisponibilidadLibro]:
        """Resumen de ejemplares totales / disponibles / prestados por libro."""
        condiciones: list[str] = []
        params: list[object] = [limite]
        if titulo:
            condiciones.append("l.titulo LIKE ?")
            params.append(f"%{titulo}%")
        if autor:
            condiciones.append("l.autor LIKE ?")
            params.append(f"%{autor}%")
        if isbn:
            condiciones.append("l.isbn = ?")
            params.append(isbn)
        where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""

        sql = f"""
            SELECT TOP (?)
                l.id_libro,
                l.isbn,
                l.titulo,
                l.autor,
                COUNT(e.id_ejemplar) AS total_ejemplares,
                SUM(CASE WHEN e.estado = 'DISPONIBLE' THEN 1 ELSE 0 END) AS disponibles,
                SUM(CASE WHEN e.estado = 'PRESTADO'   THEN 1 ELSE 0 END) AS prestados
            FROM Libro l
            LEFT JOIN Ejemplar e ON e.id_libro = l.id_libro
            {where}
            GROUP BY l.id_libro, l.isbn, l.titulo, l.autor
            ORDER BY l.titulo;
        """
        rows = self._select(sql, params, cursor)
        return [DisponibilidadLibro.from_row(r) for r in rows]

    # -- Update ---------------------------------------------------------
    def actualizar(self, libro: Libro, cursor=None) -> bool:
        sql = """
            UPDATE Libro
               SET isbn = ?, titulo = ?, autor = ?, editorial = ?, anio_publicacion = ?
             WHERE id_libro = ?;
        """
        filas = self._execute(
            sql,
            (
                libro.isbn,
                libro.titulo,
                libro.autor,
                libro.editorial,
                libro.anio_publicacion,
                libro.id_libro,
            ),
            cursor,
        )
        return filas > 0

    # -- Delete ---------------------------------------------------------
    def eliminar(self, id_libro: int, cursor=None) -> bool:
        """Elimina el libro. Falla si tiene ejemplares asociados (FK)."""
        filas = self._execute(
            "DELETE FROM Libro WHERE id_libro = ?;", (id_libro,), cursor
        )
        return filas > 0
