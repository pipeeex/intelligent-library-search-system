"""Reglas de negocio del catalogo: libros, ejemplares y usuarios."""

from __future__ import annotations

from config.settings import NodoConfig
from db.connection import Database
from models.entidades import (
    DisponibilidadLibro,
    Ejemplar,
    ESTADOS_EJEMPLAR,
    Libro,
    Usuario,
)
from repositories.biblioteca_repository import BibliotecaRepository
from repositories.ejemplar_repository import EjemplarRepository
from repositories.libro_repository import LibroRepository
from repositories.usuario_repository import UsuarioRepository
from services.excepciones import DatosInvalidos, NoEncontrado, ReglaViolada


class CatalogoService:
    def __init__(self, db: Database, nodo: NodoConfig) -> None:
        self.db = db
        self.nodo = nodo
        self.libros = LibroRepository(db)
        self.ejemplares = EjemplarRepository(db)
        self.usuarios = UsuarioRepository(db)
        self.bibliotecas = BibliotecaRepository(db)

    # ------------------------------------------------------------------
    # Libros
    # ------------------------------------------------------------------
    def crear_libro(self, libro: Libro) -> Libro:
        if not libro.isbn.strip():
            raise DatosInvalidos("El ISBN es obligatorio.")
        if not libro.titulo.strip():
            raise DatosInvalidos("El titulo es obligatorio.")
        if not libro.autor.strip():
            raise DatosInvalidos("El autor es obligatorio.")
        if self.libros.obtener_por_isbn(libro.isbn):
            raise ReglaViolada(f"Ya existe un libro con el ISBN {libro.isbn}.")

        libro.id_libro = self.libros.crear(libro)
        return libro

    def obtener_libro(self, id_libro: int) -> Libro:
        libro = self.libros.obtener(id_libro)
        if libro is None:
            raise NoEncontrado(f"No existe el libro {id_libro}.")
        return libro

    def listar_libros(self, limite: int = 200) -> list[Libro]:
        return self.libros.listar(limite)

    def buscar_libros(
        self,
        titulo: str | None = None,
        autor: str | None = None,
        isbn: str | None = None,
        limite: int = 100,
    ) -> list[Libro]:
        return self.libros.buscar(titulo, autor, isbn, limite)

    def actualizar_libro(self, libro: Libro) -> Libro:
        self.obtener_libro(int(libro.id_libro or 0))
        self.libros.actualizar(libro)
        return libro

    def eliminar_libro(self, id_libro: int) -> bool:
        self.obtener_libro(id_libro)
        if self.ejemplares.listar_por_libro(id_libro):
            raise ReglaViolada(
                "No se puede eliminar el libro: tiene ejemplares registrados. "
                "Da de baja los ejemplares primero."
            )
        return self.libros.eliminar(id_libro)

    # ------------------------------------------------------------------
    # Disponibilidad (base para el modulo de IA)
    # ------------------------------------------------------------------
    def disponibilidad(
        self,
        titulo: str | None = None,
        autor: str | None = None,
        isbn: str | None = None,
        limite: int = 50,
    ) -> list[DisponibilidadLibro]:
        resultados = self.libros.disponibilidad(titulo, autor, isbn, limite)
        for item in resultados:
            item.nodo = self.nodo.numero
            item.biblioteca = self.nodo.nombre
        return resultados

    # ------------------------------------------------------------------
    # Ejemplares
    # ------------------------------------------------------------------
    def crear_ejemplar(self, ejemplar: Ejemplar) -> Ejemplar:
        self.obtener_libro(ejemplar.id_libro)
        if ejemplar.estado not in ESTADOS_EJEMPLAR:
            raise DatosInvalidos(
                f"Estado invalido '{ejemplar.estado}'. Permitidos: {ESTADOS_EJEMPLAR}"
            )
        if not ejemplar.codigo_inventario.strip():
            raise DatosInvalidos("El codigo de inventario es obligatorio.")
        if self.bibliotecas.obtener(ejemplar.id_biblioteca) is None:
            raise NoEncontrado(
                f"No existe la biblioteca {ejemplar.id_biblioteca} en este nodo."
            )
        ejemplar.id_ejemplar = self.ejemplares.crear(ejemplar)
        return ejemplar

    def listar_ejemplares(
        self, id_libro: int, solo_disponibles: bool = False
    ) -> list[Ejemplar]:
        self.obtener_libro(id_libro)
        return self.ejemplares.listar_por_libro(id_libro, solo_disponibles)

    def cambiar_estado_ejemplar(self, id_ejemplar: int, estado: str) -> Ejemplar:
        if estado not in ESTADOS_EJEMPLAR:
            raise DatosInvalidos(
                f"Estado invalido '{estado}'. Permitidos: {ESTADOS_EJEMPLAR}"
            )
        ejemplar = self.ejemplares.obtener(id_ejemplar)
        if ejemplar is None:
            raise NoEncontrado(f"No existe el ejemplar {id_ejemplar}.")
        if ejemplar.estado == "PRESTADO" and estado != "PRESTADO":
            raise ReglaViolada(
                "El ejemplar esta prestado: registra primero la devolucion."
            )
        self.ejemplares.cambiar_estado(id_ejemplar, estado)
        ejemplar.estado = estado
        return ejemplar

    # ------------------------------------------------------------------
    # Usuarios
    # ------------------------------------------------------------------
    def crear_usuario(self, usuario: Usuario) -> Usuario:
        if not usuario.nombre.strip():
            raise DatosInvalidos("El nombre es obligatorio.")
        if not usuario.documento.strip():
            raise DatosInvalidos("El documento es obligatorio.")
        if self.usuarios.obtener_por_documento(usuario.documento):
            raise ReglaViolada(
                f"Ya existe un usuario con el documento {usuario.documento}."
            )
        usuario.id_usuario = self.usuarios.crear(usuario)
        return usuario

    def obtener_usuario(self, id_usuario: int) -> Usuario:
        usuario = self.usuarios.obtener(id_usuario)
        if usuario is None:
            raise NoEncontrado(f"No existe el usuario {id_usuario}.")
        return usuario

    def listar_usuarios(self, limite: int = 200) -> list[Usuario]:
        return self.usuarios.listar(limite)

    def actualizar_usuario(self, usuario: Usuario) -> Usuario:
        self.obtener_usuario(int(usuario.id_usuario or 0))
        self.usuarios.actualizar(usuario)
        return usuario

    def eliminar_usuario(self, id_usuario: int) -> bool:
        self.obtener_usuario(id_usuario)
        if self.usuarios.tiene_prestamos_activos(id_usuario):
            raise ReglaViolada("El usuario tiene prestamos activos o vencidos.")
        return self.usuarios.eliminar(id_usuario)
