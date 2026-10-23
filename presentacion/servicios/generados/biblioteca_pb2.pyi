from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class IdRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: int
    def __init__(self, id: _Optional[int] = ...) -> None: ...

class ListarRequest(_message.Message):
    __slots__ = ("limite",)
    LIMITE_FIELD_NUMBER: _ClassVar[int]
    limite: int
    def __init__(self, limite: _Optional[int] = ...) -> None: ...

class OperacionResponse(_message.Message):
    __slots__ = ("exito", "mensaje")
    EXITO_FIELD_NUMBER: _ClassVar[int]
    MENSAJE_FIELD_NUMBER: _ClassVar[int]
    exito: bool
    mensaje: str
    def __init__(self, exito: _Optional[bool] = ..., mensaje: _Optional[str] = ...) -> None: ...

class PingRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class PingResponse(_message.Message):
    __slots__ = ("nodo", "nombre", "base_datos_ok", "version")
    NODO_FIELD_NUMBER: _ClassVar[int]
    NOMBRE_FIELD_NUMBER: _ClassVar[int]
    BASE_DATOS_OK_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    nodo: int
    nombre: str
    base_datos_ok: bool
    version: str
    def __init__(self, nodo: _Optional[int] = ..., nombre: _Optional[str] = ..., base_datos_ok: _Optional[bool] = ..., version: _Optional[str] = ...) -> None: ...

class Libro(_message.Message):
    __slots__ = ("id_libro", "isbn", "titulo", "autor", "editorial", "anio_publicacion")
    ID_LIBRO_FIELD_NUMBER: _ClassVar[int]
    ISBN_FIELD_NUMBER: _ClassVar[int]
    TITULO_FIELD_NUMBER: _ClassVar[int]
    AUTOR_FIELD_NUMBER: _ClassVar[int]
    EDITORIAL_FIELD_NUMBER: _ClassVar[int]
    ANIO_PUBLICACION_FIELD_NUMBER: _ClassVar[int]
    id_libro: int
    isbn: str
    titulo: str
    autor: str
    editorial: str
    anio_publicacion: int
    def __init__(self, id_libro: _Optional[int] = ..., isbn: _Optional[str] = ..., titulo: _Optional[str] = ..., autor: _Optional[str] = ..., editorial: _Optional[str] = ..., anio_publicacion: _Optional[int] = ...) -> None: ...

class CrearLibroRequest(_message.Message):
    __slots__ = ("isbn", "titulo", "autor", "editorial", "anio_publicacion")
    ISBN_FIELD_NUMBER: _ClassVar[int]
    TITULO_FIELD_NUMBER: _ClassVar[int]
    AUTOR_FIELD_NUMBER: _ClassVar[int]
    EDITORIAL_FIELD_NUMBER: _ClassVar[int]
    ANIO_PUBLICACION_FIELD_NUMBER: _ClassVar[int]
    isbn: str
    titulo: str
    autor: str
    editorial: str
    anio_publicacion: int
    def __init__(self, isbn: _Optional[str] = ..., titulo: _Optional[str] = ..., autor: _Optional[str] = ..., editorial: _Optional[str] = ..., anio_publicacion: _Optional[int] = ...) -> None: ...

class ActualizarLibroRequest(_message.Message):
    __slots__ = ("libro",)
    LIBRO_FIELD_NUMBER: _ClassVar[int]
    libro: Libro
    def __init__(self, libro: _Optional[_Union[Libro, _Mapping]] = ...) -> None: ...

class LibroResponse(_message.Message):
    __slots__ = ("libro",)
    LIBRO_FIELD_NUMBER: _ClassVar[int]
    libro: Libro
    def __init__(self, libro: _Optional[_Union[Libro, _Mapping]] = ...) -> None: ...

class ListaLibrosResponse(_message.Message):
    __slots__ = ("libros", "nodo")
    LIBROS_FIELD_NUMBER: _ClassVar[int]
    NODO_FIELD_NUMBER: _ClassVar[int]
    libros: _containers.RepeatedCompositeFieldContainer[Libro]
    nodo: int
    def __init__(self, libros: _Optional[_Iterable[_Union[Libro, _Mapping]]] = ..., nodo: _Optional[int] = ...) -> None: ...

class BuscarLibrosRequest(_message.Message):
    __slots__ = ("titulo", "autor", "isbn", "limite")
    TITULO_FIELD_NUMBER: _ClassVar[int]
    AUTOR_FIELD_NUMBER: _ClassVar[int]
    ISBN_FIELD_NUMBER: _ClassVar[int]
    LIMITE_FIELD_NUMBER: _ClassVar[int]
    titulo: str
    autor: str
    isbn: str
    limite: int
    def __init__(self, titulo: _Optional[str] = ..., autor: _Optional[str] = ..., isbn: _Optional[str] = ..., limite: _Optional[int] = ...) -> None: ...

class DisponibilidadRequest(_message.Message):
    __slots__ = ("titulo", "autor", "isbn", "limite")
    TITULO_FIELD_NUMBER: _ClassVar[int]
    AUTOR_FIELD_NUMBER: _ClassVar[int]
    ISBN_FIELD_NUMBER: _ClassVar[int]
    LIMITE_FIELD_NUMBER: _ClassVar[int]
    titulo: str
    autor: str
    isbn: str
    limite: int
    def __init__(self, titulo: _Optional[str] = ..., autor: _Optional[str] = ..., isbn: _Optional[str] = ..., limite: _Optional[int] = ...) -> None: ...

class DisponibilidadItem(_message.Message):
    __slots__ = ("id_libro", "isbn", "titulo", "autor", "total_ejemplares", "disponibles", "prestados", "nodo", "biblioteca")
    ID_LIBRO_FIELD_NUMBER: _ClassVar[int]
    ISBN_FIELD_NUMBER: _ClassVar[int]
    TITULO_FIELD_NUMBER: _ClassVar[int]
    AUTOR_FIELD_NUMBER: _ClassVar[int]
    TOTAL_EJEMPLARES_FIELD_NUMBER: _ClassVar[int]
    DISPONIBLES_FIELD_NUMBER: _ClassVar[int]
    PRESTADOS_FIELD_NUMBER: _ClassVar[int]
    NODO_FIELD_NUMBER: _ClassVar[int]
    BIBLIOTECA_FIELD_NUMBER: _ClassVar[int]
    id_libro: int
    isbn: str
    titulo: str
    autor: str
    total_ejemplares: int
    disponibles: int
    prestados: int
    nodo: int
    biblioteca: str
    def __init__(self, id_libro: _Optional[int] = ..., isbn: _Optional[str] = ..., titulo: _Optional[str] = ..., autor: _Optional[str] = ..., total_ejemplares: _Optional[int] = ..., disponibles: _Optional[int] = ..., prestados: _Optional[int] = ..., nodo: _Optional[int] = ..., biblioteca: _Optional[str] = ...) -> None: ...

class DisponibilidadResponse(_message.Message):
    __slots__ = ("resultados", "nodo", "biblioteca")
    RESULTADOS_FIELD_NUMBER: _ClassVar[int]
    NODO_FIELD_NUMBER: _ClassVar[int]
    BIBLIOTECA_FIELD_NUMBER: _ClassVar[int]
    resultados: _containers.RepeatedCompositeFieldContainer[DisponibilidadItem]
    nodo: int
    biblioteca: str
    def __init__(self, resultados: _Optional[_Iterable[_Union[DisponibilidadItem, _Mapping]]] = ..., nodo: _Optional[int] = ..., biblioteca: _Optional[str] = ...) -> None: ...

class Ejemplar(_message.Message):
    __slots__ = ("id_ejemplar", "id_libro", "id_biblioteca", "codigo_inventario", "estado", "titulo", "autor")
    ID_EJEMPLAR_FIELD_NUMBER: _ClassVar[int]
    ID_LIBRO_FIELD_NUMBER: _ClassVar[int]
    ID_BIBLIOTECA_FIELD_NUMBER: _ClassVar[int]
    CODIGO_INVENTARIO_FIELD_NUMBER: _ClassVar[int]
    ESTADO_FIELD_NUMBER: _ClassVar[int]
    TITULO_FIELD_NUMBER: _ClassVar[int]
    AUTOR_FIELD_NUMBER: _ClassVar[int]
    id_ejemplar: int
    id_libro: int
    id_biblioteca: int
    codigo_inventario: str
    estado: str
    titulo: str
    autor: str
    def __init__(self, id_ejemplar: _Optional[int] = ..., id_libro: _Optional[int] = ..., id_biblioteca: _Optional[int] = ..., codigo_inventario: _Optional[str] = ..., estado: _Optional[str] = ..., titulo: _Optional[str] = ..., autor: _Optional[str] = ...) -> None: ...

class CrearEjemplarRequest(_message.Message):
    __slots__ = ("id_libro", "id_biblioteca", "codigo_inventario", "estado")
    ID_LIBRO_FIELD_NUMBER: _ClassVar[int]
    ID_BIBLIOTECA_FIELD_NUMBER: _ClassVar[int]
    CODIGO_INVENTARIO_FIELD_NUMBER: _ClassVar[int]
    ESTADO_FIELD_NUMBER: _ClassVar[int]
    id_libro: int
    id_biblioteca: int
    codigo_inventario: str
    estado: str
    def __init__(self, id_libro: _Optional[int] = ..., id_biblioteca: _Optional[int] = ..., codigo_inventario: _Optional[str] = ..., estado: _Optional[str] = ...) -> None: ...

class ListarEjemplaresRequest(_message.Message):
    __slots__ = ("id_libro", "solo_disponibles")
    ID_LIBRO_FIELD_NUMBER: _ClassVar[int]
    SOLO_DISPONIBLES_FIELD_NUMBER: _ClassVar[int]
    id_libro: int
    solo_disponibles: bool
    def __init__(self, id_libro: _Optional[int] = ..., solo_disponibles: _Optional[bool] = ...) -> None: ...

class EstadoEjemplarRequest(_message.Message):
    __slots__ = ("id_ejemplar", "estado")
    ID_EJEMPLAR_FIELD_NUMBER: _ClassVar[int]
    ESTADO_FIELD_NUMBER: _ClassVar[int]
    id_ejemplar: int
    estado: str
    def __init__(self, id_ejemplar: _Optional[int] = ..., estado: _Optional[str] = ...) -> None: ...

class EjemplarResponse(_message.Message):
    __slots__ = ("ejemplar",)
    EJEMPLAR_FIELD_NUMBER: _ClassVar[int]
    ejemplar: Ejemplar
    def __init__(self, ejemplar: _Optional[_Union[Ejemplar, _Mapping]] = ...) -> None: ...

class ListaEjemplaresResponse(_message.Message):
    __slots__ = ("ejemplares",)
    EJEMPLARES_FIELD_NUMBER: _ClassVar[int]
    ejemplares: _containers.RepeatedCompositeFieldContainer[Ejemplar]
    def __init__(self, ejemplares: _Optional[_Iterable[_Union[Ejemplar, _Mapping]]] = ...) -> None: ...

class Usuario(_message.Message):
    __slots__ = ("id_usuario", "nombre", "documento", "correo", "telefono")
    ID_USUARIO_FIELD_NUMBER: _ClassVar[int]
    NOMBRE_FIELD_NUMBER: _ClassVar[int]
    DOCUMENTO_FIELD_NUMBER: _ClassVar[int]
    CORREO_FIELD_NUMBER: _ClassVar[int]
    TELEFONO_FIELD_NUMBER: _ClassVar[int]
    id_usuario: int
    nombre: str
    documento: str
    correo: str
    telefono: str
    def __init__(self, id_usuario: _Optional[int] = ..., nombre: _Optional[str] = ..., documento: _Optional[str] = ..., correo: _Optional[str] = ..., telefono: _Optional[str] = ...) -> None: ...

class CrearUsuarioRequest(_message.Message):
    __slots__ = ("nombre", "documento", "correo", "telefono")
    NOMBRE_FIELD_NUMBER: _ClassVar[int]
    DOCUMENTO_FIELD_NUMBER: _ClassVar[int]
    CORREO_FIELD_NUMBER: _ClassVar[int]
    TELEFONO_FIELD_NUMBER: _ClassVar[int]
    nombre: str
    documento: str
    correo: str
    telefono: str
    def __init__(self, nombre: _Optional[str] = ..., documento: _Optional[str] = ..., correo: _Optional[str] = ..., telefono: _Optional[str] = ...) -> None: ...

class ActualizarUsuarioRequest(_message.Message):
    __slots__ = ("usuario",)
    USUARIO_FIELD_NUMBER: _ClassVar[int]
    usuario: Usuario
    def __init__(self, usuario: _Optional[_Union[Usuario, _Mapping]] = ...) -> None: ...

class UsuarioResponse(_message.Message):
    __slots__ = ("usuario",)
    USUARIO_FIELD_NUMBER: _ClassVar[int]
    usuario: Usuario
    def __init__(self, usuario: _Optional[_Union[Usuario, _Mapping]] = ...) -> None: ...

class ListaUsuariosResponse(_message.Message):
    __slots__ = ("usuarios",)
    USUARIOS_FIELD_NUMBER: _ClassVar[int]
    usuarios: _containers.RepeatedCompositeFieldContainer[Usuario]
    def __init__(self, usuarios: _Optional[_Iterable[_Union[Usuario, _Mapping]]] = ...) -> None: ...

class Prestamo(_message.Message):
    __slots__ = ("id_prestamo", "id_usuario", "id_ejemplar", "fecha_prestamo", "fecha_vencimiento", "estado")
    ID_PRESTAMO_FIELD_NUMBER: _ClassVar[int]
    ID_USUARIO_FIELD_NUMBER: _ClassVar[int]
    ID_EJEMPLAR_FIELD_NUMBER: _ClassVar[int]
    FECHA_PRESTAMO_FIELD_NUMBER: _ClassVar[int]
    FECHA_VENCIMIENTO_FIELD_NUMBER: _ClassVar[int]
    ESTADO_FIELD_NUMBER: _ClassVar[int]
    id_prestamo: int
    id_usuario: int
    id_ejemplar: int
    fecha_prestamo: str
    fecha_vencimiento: str
    estado: str
    def __init__(self, id_prestamo: _Optional[int] = ..., id_usuario: _Optional[int] = ..., id_ejemplar: _Optional[int] = ..., fecha_prestamo: _Optional[str] = ..., fecha_vencimiento: _Optional[str] = ..., estado: _Optional[str] = ...) -> None: ...

class PrestamoRequest(_message.Message):
    __slots__ = ("id_usuario", "id_libro", "dias")
    ID_USUARIO_FIELD_NUMBER: _ClassVar[int]
    ID_LIBRO_FIELD_NUMBER: _ClassVar[int]
    DIAS_FIELD_NUMBER: _ClassVar[int]
    id_usuario: int
    id_libro: int
    dias: int
    def __init__(self, id_usuario: _Optional[int] = ..., id_libro: _Optional[int] = ..., dias: _Optional[int] = ...) -> None: ...

class PrestamoResponse(_message.Message):
    __slots__ = ("prestamo",)
    PRESTAMO_FIELD_NUMBER: _ClassVar[int]
    prestamo: Prestamo
    def __init__(self, prestamo: _Optional[_Union[Prestamo, _Mapping]] = ...) -> None: ...

class DevolucionRequest(_message.Message):
    __slots__ = ("id_prestamo", "observacion")
    ID_PRESTAMO_FIELD_NUMBER: _ClassVar[int]
    OBSERVACION_FIELD_NUMBER: _ClassVar[int]
    id_prestamo: int
    observacion: str
    def __init__(self, id_prestamo: _Optional[int] = ..., observacion: _Optional[str] = ...) -> None: ...

class Devolucion(_message.Message):
    __slots__ = ("id_devolucion", "id_prestamo", "fecha_devolucion", "observacion")
    ID_DEVOLUCION_FIELD_NUMBER: _ClassVar[int]
    ID_PRESTAMO_FIELD_NUMBER: _ClassVar[int]
    FECHA_DEVOLUCION_FIELD_NUMBER: _ClassVar[int]
    OBSERVACION_FIELD_NUMBER: _ClassVar[int]
    id_devolucion: int
    id_prestamo: int
    fecha_devolucion: str
    observacion: str
    def __init__(self, id_devolucion: _Optional[int] = ..., id_prestamo: _Optional[int] = ..., fecha_devolucion: _Optional[str] = ..., observacion: _Optional[str] = ...) -> None: ...

class DevolucionResponse(_message.Message):
    __slots__ = ("devolucion",)
    DEVOLUCION_FIELD_NUMBER: _ClassVar[int]
    devolucion: Devolucion
    def __init__(self, devolucion: _Optional[_Union[Devolucion, _Mapping]] = ...) -> None: ...

class ListarPrestamosRequest(_message.Message):
    __slots__ = ("id_usuario", "solo_activos")
    ID_USUARIO_FIELD_NUMBER: _ClassVar[int]
    SOLO_ACTIVOS_FIELD_NUMBER: _ClassVar[int]
    id_usuario: int
    solo_activos: bool
    def __init__(self, id_usuario: _Optional[int] = ..., solo_activos: _Optional[bool] = ...) -> None: ...

class ListaPrestamosResponse(_message.Message):
    __slots__ = ("prestamos",)
    PRESTAMOS_FIELD_NUMBER: _ClassVar[int]
    prestamos: _containers.RepeatedCompositeFieldContainer[Prestamo]
    def __init__(self, prestamos: _Optional[_Iterable[_Union[Prestamo, _Mapping]]] = ...) -> None: ...
