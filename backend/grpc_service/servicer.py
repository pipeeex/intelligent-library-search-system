"""Implementacion del servicio gRPC de un nodo bibliotecario.

Traduce mensajes protobuf <-> modelos de dominio y delega toda la logica en
los servicios. Los errores de negocio se convierten en codigos gRPC.
"""

from __future__ import annotations

import logging

import grpc

from config.settings import NodoConfig
from db.connection import Database, DatabaseError
from models.entidades import Ejemplar, Libro, Usuario
from services.catalogo_service import CatalogoService
from services.excepciones import (
    DatosInvalidos,
    ErrorNegocio,
    NoEncontrado,
    ReglaViolada,
    SinDisponibilidad,
)
from services.prestamo_service import PrestamoService

from grpc_service.generated import biblioteca_pb2 as pb
from grpc_service.generated import biblioteca_pb2_grpc as pb_grpc

logger = logging.getLogger(__name__)

VERSION = "0.1.0"

CODIGOS = {
    NoEncontrado: grpc.StatusCode.NOT_FOUND,
    DatosInvalidos: grpc.StatusCode.INVALID_ARGUMENT,
    SinDisponibilidad: grpc.StatusCode.RESOURCE_EXHAUSTED,
    ReglaViolada: grpc.StatusCode.FAILED_PRECONDITION,
}


def _codigo(exc: ErrorNegocio) -> grpc.StatusCode:
    for tipo, codigo in CODIGOS.items():
        if isinstance(exc, tipo):
            return codigo
    return grpc.StatusCode.UNKNOWN


def manejar_errores(func):
    """Decorador: convierte excepciones en respuestas gRPC con estado."""

    def wrapper(self, request, context):
        try:
            return func(self, request, context)
        except ErrorNegocio as exc:
            context.abort(_codigo(exc), str(exc))
        except DatabaseError as exc:
            logger.error("Error de base de datos: %s", exc)
            context.abort(grpc.StatusCode.UNAVAILABLE, str(exc))
        except Exception as exc:  # pragma: no cover
            logger.exception("Error inesperado en %s", func.__name__)
            context.abort(grpc.StatusCode.INTERNAL, f"Error interno: {exc}")

    wrapper.__name__ = func.__name__
    return wrapper


# ---------------------------------------------------------------------------
# Conversores modelo -> protobuf
# ---------------------------------------------------------------------------
def _iso(valor) -> str:
    return valor.isoformat() if valor else ""


def libro_pb(libro: Libro) -> pb.Libro:
    return pb.Libro(
        id_libro=libro.id_libro or 0,
        isbn=libro.isbn or "",
        titulo=libro.titulo or "",
        autor=libro.autor or "",
        editorial=libro.editorial or "",
        anio_publicacion=libro.anio_publicacion or 0,
    )


def usuario_pb(usuario: Usuario) -> pb.Usuario:
    return pb.Usuario(
        id_usuario=usuario.id_usuario or 0,
        nombre=usuario.nombre or "",
        documento=usuario.documento or "",
        correo=usuario.correo or "",
        telefono=usuario.telefono or "",
    )


def ejemplar_pb(ejemplar: Ejemplar) -> pb.Ejemplar:
    return pb.Ejemplar(
        id_ejemplar=ejemplar.id_ejemplar or 0,
        id_libro=ejemplar.id_libro or 0,
        id_biblioteca=ejemplar.id_biblioteca or 0,
        codigo_inventario=ejemplar.codigo_inventario or "",
        estado=ejemplar.estado or "",
        titulo=ejemplar.titulo or "",
        autor=ejemplar.autor or "",
    )


def prestamo_pb(prestamo) -> pb.Prestamo:
    return pb.Prestamo(
        id_prestamo=prestamo.id_prestamo or 0,
        id_usuario=prestamo.id_usuario or 0,
        id_ejemplar=prestamo.id_ejemplar or 0,
        fecha_prestamo=_iso(prestamo.fecha_prestamo),
        fecha_vencimiento=_iso(prestamo.fecha_vencimiento),
        estado=prestamo.estado or "",
    )


def devolucion_pb(devolucion) -> pb.Devolucion:
    return pb.Devolucion(
        id_devolucion=devolucion.id_devolucion or 0,
        id_prestamo=devolucion.id_prestamo or 0,
        fecha_devolucion=_iso(devolucion.fecha_devolucion),
        observacion=devolucion.observacion or "",
    )


# ---------------------------------------------------------------------------
# Servicer
# ---------------------------------------------------------------------------
class BibliotecaNodoServicer(pb_grpc.BibliotecaNodoServicer):
    def __init__(self, db: Database, nodo: NodoConfig) -> None:
        self.db = db
        self.nodo = nodo
        self.catalogo = CatalogoService(db, nodo)
        self.prestamos = PrestamoService(db, nodo)

    # -- Salud ----------------------------------------------------------
    def Ping(self, request, context):
        return pb.PingResponse(
            nodo=self.nodo.numero,
            nombre=self.nodo.nombre,
            base_datos_ok=self.db.probar_conexion(),
            version=VERSION,
        )

    # -- Libros ---------------------------------------------------------
    @manejar_errores
    def CrearLibro(self, request, context):
        libro = self.catalogo.crear_libro(
            Libro(
                isbn=request.isbn,
                titulo=request.titulo,
                autor=request.autor,
                editorial=request.editorial or None,
                anio_publicacion=request.anio_publicacion or None,
            )
        )
        return pb.LibroResponse(libro=libro_pb(libro))

    @manejar_errores
    def ObtenerLibro(self, request, context):
        return pb.LibroResponse(libro=libro_pb(self.catalogo.obtener_libro(request.id)))

    @manejar_errores
    def ListarLibros(self, request, context):
        libros = self.catalogo.listar_libros(request.limite or 200)
        return pb.ListaLibrosResponse(
            libros=[libro_pb(l) for l in libros], nodo=self.nodo.numero
        )

    @manejar_errores
    def BuscarLibros(self, request, context):
        libros = self.catalogo.buscar_libros(
            titulo=request.titulo or None,
            autor=request.autor or None,
            isbn=request.isbn or None,
            limite=request.limite or 100,
        )
        return pb.ListaLibrosResponse(
            libros=[libro_pb(l) for l in libros], nodo=self.nodo.numero
        )

    @manejar_errores
    def ActualizarLibro(self, request, context):
        origen = request.libro
        libro = self.catalogo.actualizar_libro(
            Libro(
                id_libro=origen.id_libro,
                isbn=origen.isbn,
                titulo=origen.titulo,
                autor=origen.autor,
                editorial=origen.editorial or None,
                anio_publicacion=origen.anio_publicacion or None,
            )
        )
        return pb.LibroResponse(libro=libro_pb(libro))

    @manejar_errores
    def EliminarLibro(self, request, context):
        self.catalogo.eliminar_libro(request.id)
        return pb.OperacionResponse(exito=True, mensaje="Libro eliminado.")

    # -- Disponibilidad -------------------------------------------------
    @manejar_errores
    def ConsultarDisponibilidad(self, request, context):
        resultados = self.catalogo.disponibilidad(
            titulo=request.titulo or None,
            autor=request.autor or None,
            isbn=request.isbn or None,
            limite=request.limite or 50,
        )
        return pb.DisponibilidadResponse(
            resultados=[
                pb.DisponibilidadItem(
                    id_libro=r.id_libro,
                    isbn=r.isbn,
                    titulo=r.titulo,
                    autor=r.autor,
                    total_ejemplares=r.total_ejemplares,
                    disponibles=r.disponibles,
                    prestados=r.prestados,
                    nodo=r.nodo,
                    biblioteca=r.biblioteca,
                )
                for r in resultados
            ],
            nodo=self.nodo.numero,
            biblioteca=self.nodo.nombre,
        )

    # -- Ejemplares -----------------------------------------------------
    @manejar_errores
    def CrearEjemplar(self, request, context):
        ejemplar = self.catalogo.crear_ejemplar(
            Ejemplar(
                id_libro=request.id_libro,
                id_biblioteca=request.id_biblioteca,
                codigo_inventario=request.codigo_inventario,
                estado=request.estado or "DISPONIBLE",
            )
        )
        return pb.EjemplarResponse(ejemplar=ejemplar_pb(ejemplar))

    @manejar_errores
    def ListarEjemplares(self, request, context):
        ejemplares = self.catalogo.listar_ejemplares(
            request.id_libro, request.solo_disponibles
        )
        return pb.ListaEjemplaresResponse(
            ejemplares=[ejemplar_pb(e) for e in ejemplares]
        )

    @manejar_errores
    def CambiarEstadoEjemplar(self, request, context):
        ejemplar = self.catalogo.cambiar_estado_ejemplar(
            request.id_ejemplar, request.estado
        )
        return pb.EjemplarResponse(ejemplar=ejemplar_pb(ejemplar))

    # -- Usuarios -------------------------------------------------------
    @manejar_errores
    def CrearUsuario(self, request, context):
        usuario = self.catalogo.crear_usuario(
            Usuario(
                nombre=request.nombre,
                documento=request.documento,
                correo=request.correo or None,
                telefono=request.telefono or None,
            )
        )
        return pb.UsuarioResponse(usuario=usuario_pb(usuario))

    @manejar_errores
    def ObtenerUsuario(self, request, context):
        return pb.UsuarioResponse(
            usuario=usuario_pb(self.catalogo.obtener_usuario(request.id))
        )

    @manejar_errores
    def ListarUsuarios(self, request, context):
        usuarios = self.catalogo.listar_usuarios(request.limite or 200)
        return pb.ListaUsuariosResponse(usuarios=[usuario_pb(u) for u in usuarios])

    @manejar_errores
    def ActualizarUsuario(self, request, context):
        origen = request.usuario
        usuario = self.catalogo.actualizar_usuario(
            Usuario(
                id_usuario=origen.id_usuario,
                nombre=origen.nombre,
                documento=origen.documento,
                correo=origen.correo or None,
                telefono=origen.telefono or None,
            )
        )
        return pb.UsuarioResponse(usuario=usuario_pb(usuario))

    @manejar_errores
    def EliminarUsuario(self, request, context):
        self.catalogo.eliminar_usuario(request.id)
        return pb.OperacionResponse(exito=True, mensaje="Usuario eliminado.")

    # -- Prestamos ------------------------------------------------------
    @manejar_errores
    def RegistrarPrestamo(self, request, context):
        prestamo = self.prestamos.prestar(
            request.id_usuario, request.id_libro, request.dias or None
        )
        return pb.PrestamoResponse(prestamo=prestamo_pb(prestamo))

    @manejar_errores
    def RegistrarDevolucion(self, request, context):
        devolucion = self.prestamos.devolver(
            request.id_prestamo, request.observacion or None
        )
        return pb.DevolucionResponse(devolucion=devolucion_pb(devolucion))

    @manejar_errores
    def ListarPrestamos(self, request, context):
        prestamos = self.prestamos.listar_por_usuario(
            request.id_usuario, request.solo_activos
        )
        return pb.ListaPrestamosResponse(prestamos=[prestamo_pb(p) for p in prestamos])
