"""Modelos de dominio: reflejan las tablas del script SQL de cada nodo."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# ---------------------------------------------------------------------------
# Estados permitidos (deben coincidir con los CHECK CONSTRAINT del script SQL)
# ---------------------------------------------------------------------------
ESTADOS_EJEMPLAR = ("DISPONIBLE", "PRESTADO", "MANTENIMIENTO", "BAJA")
ESTADOS_PRESTAMO = ("ACTIVO", "DEVUELTO", "VENCIDO")
ESTADOS_BIBLIOTECA = ("ACTIVA", "INACTIVA")


def _dt(valor: Any) -> datetime | None:
    if valor is None or isinstance(valor, datetime):
        return valor
    return datetime.fromisoformat(str(valor))


@dataclass
class Biblioteca:
    id_biblioteca: int | None = None
    nombre: str = ""
    direccion: str = ""
    estado: str = "ACTIVA"

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "Biblioteca":
        return cls(
            id_biblioteca=row["id_biblioteca"],
            nombre=row["nombre"],
            direccion=row["direccion"],
            estado=row["estado"],
        )


@dataclass
class Libro:
    id_libro: int | None = None
    isbn: str = ""
    titulo: str = ""
    autor: str = ""
    editorial: str | None = None
    anio_publicacion: int | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "Libro":
        return cls(
            id_libro=row["id_libro"],
            isbn=row["isbn"],
            titulo=row["titulo"],
            autor=row["autor"],
            editorial=row.get("editorial"),
            anio_publicacion=row.get("anio_publicacion"),
        )


@dataclass
class Usuario:
    id_usuario: int | None = None
    nombre: str = ""
    documento: str = ""
    correo: str | None = None
    telefono: str | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "Usuario":
        return cls(
            id_usuario=row["id_usuario"],
            nombre=row["nombre"],
            documento=row["documento"],
            correo=row.get("correo"),
            telefono=row.get("telefono"),
        )


@dataclass
class Ejemplar:
    id_ejemplar: int | None = None
    id_libro: int = 0
    id_biblioteca: int = 0
    codigo_inventario: str = ""
    estado: str = "DISPONIBLE"
    # Campos derivados de JOIN (opcionales)
    titulo: str | None = None
    autor: str | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "Ejemplar":
        return cls(
            id_ejemplar=row["id_ejemplar"],
            id_libro=row["id_libro"],
            id_biblioteca=row["id_biblioteca"],
            codigo_inventario=row["codigo_inventario"],
            estado=row["estado"],
            titulo=row.get("titulo"),
            autor=row.get("autor"),
        )


@dataclass
class Prestamo:
    id_prestamo: int | None = None
    id_usuario: int = 0
    id_ejemplar: int = 0
    fecha_prestamo: datetime | None = None
    fecha_vencimiento: datetime | None = None
    estado: str = "ACTIVO"

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "Prestamo":
        return cls(
            id_prestamo=row["id_prestamo"],
            id_usuario=row["id_usuario"],
            id_ejemplar=row["id_ejemplar"],
            fecha_prestamo=_dt(row.get("fecha_prestamo")),
            fecha_vencimiento=_dt(row.get("fecha_vencimiento")),
            estado=row["estado"],
        )


@dataclass
class Devolucion:
    id_devolucion: int | None = None
    id_prestamo: int = 0
    fecha_devolucion: datetime | None = None
    observacion: str | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "Devolucion":
        return cls(
            id_devolucion=row["id_devolucion"],
            id_prestamo=row["id_prestamo"],
            fecha_devolucion=_dt(row.get("fecha_devolucion")),
            observacion=row.get("observacion"),
        )


@dataclass
class DisponibilidadLibro:
    """Resumen de disponibilidad de un titulo dentro de un nodo."""

    id_libro: int
    isbn: str
    titulo: str
    autor: str
    total_ejemplares: int = 0
    disponibles: int = 0
    prestados: int = 0
    nodo: int = 0
    biblioteca: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "DisponibilidadLibro":
        return cls(
            id_libro=row["id_libro"],
            isbn=row["isbn"],
            titulo=row["titulo"],
            autor=row["autor"],
            total_ejemplares=int(row.get("total_ejemplares") or 0),
            disponibles=int(row.get("disponibles") or 0),
            prestados=int(row.get("prestados") or 0),
        )
