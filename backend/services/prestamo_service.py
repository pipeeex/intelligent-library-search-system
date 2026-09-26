"""Prestamos y devoluciones con garantias ACID.

Cada operacion abre UNA transaccion que toca varias tablas:

* Prestar  -> bloquear ejemplar DISPONIBLE, marcarlo PRESTADO, insertar Prestamo.
* Devolver -> insertar Devolucion, marcar Prestamo DEVUELTO, liberar el ejemplar.

Si cualquiera de los pasos falla se hace rollback completo (atomicidad), y los
hints UPDLOCK/ROWLOCK evitan que dos operaciones concurrentes tomen el mismo
ejemplar (aislamiento).
"""

from __future__ import annotations

from datetime import datetime, timedelta

from config.settings import DIAS_PRESTAMO, NodoConfig
from db.connection import Database
from models.entidades import Devolucion, Prestamo
from repositories.ejemplar_repository import EjemplarRepository
from repositories.libro_repository import LibroRepository
from repositories.prestamo_repository import (
    DevolucionRepository,
    PrestamoRepository,
)
from repositories.usuario_repository import UsuarioRepository
from services.excepciones import (
    DatosInvalidos,
    NoEncontrado,
    ReglaViolada,
    SinDisponibilidad,
)

MAX_PRESTAMOS_ACTIVOS = 3


class PrestamoService:
    def __init__(self, db: Database, nodo: NodoConfig) -> None:
        self.db = db
        self.nodo = nodo
        self.libros = LibroRepository(db)
        self.ejemplares = EjemplarRepository(db)
        self.usuarios = UsuarioRepository(db)
        self.prestamos = PrestamoRepository(db)
        self.devoluciones = DevolucionRepository(db)

    # ------------------------------------------------------------------
    def prestar(
        self,
        id_usuario: int,
        id_libro: int,
        dias: int | None = None,
    ) -> Prestamo:
        """Presta el primer ejemplar disponible del libro indicado."""
        dias = dias or DIAS_PRESTAMO
        if dias <= 0:
            raise DatosInvalidos("Los dias de prestamo deben ser mayores que cero.")

        ahora = datetime.now()
        vencimiento = ahora + timedelta(days=dias)

        with self.db.transaccion() as cursor:
            usuario = self.usuarios.obtener(id_usuario, cursor)
            if usuario is None:
                raise NoEncontrado(f"No existe el usuario {id_usuario}.")

            libro = self.libros.obtener(id_libro, cursor)
            if libro is None:
                raise NoEncontrado(f"No existe el libro {id_libro}.")

            activos = self.prestamos.listar_por_usuario(
                id_usuario, solo_activos=True, cursor=cursor
            )
            if len(activos) >= MAX_PRESTAMOS_ACTIVOS:
                raise ReglaViolada(
                    f"El usuario ya tiene {len(activos)} prestamos activos "
                    f"(maximo {MAX_PRESTAMOS_ACTIVOS})."
                )
            if any(p.estado == "VENCIDO" for p in activos):
                raise ReglaViolada(
                    "El usuario tiene prestamos vencidos; debe devolverlos primero."
                )

            ejemplar = self.ejemplares.bloquear_disponible(id_libro, cursor)
            if ejemplar is None:
                raise SinDisponibilidad(
                    f"No hay ejemplares disponibles de '{libro.titulo}' en "
                    f"{self.nodo.nombre}."
                )

            self.ejemplares.cambiar_estado(
                int(ejemplar.id_ejemplar), "PRESTADO", cursor
            )

            prestamo = Prestamo(
                id_usuario=id_usuario,
                id_ejemplar=int(ejemplar.id_ejemplar),
                fecha_prestamo=ahora,
                fecha_vencimiento=vencimiento,
                estado="ACTIVO",
            )
            prestamo.id_prestamo = self.prestamos.crear(prestamo, cursor)
            return prestamo

    # ------------------------------------------------------------------
    def devolver(self, id_prestamo: int, observacion: str | None = None) -> Devolucion:
        """Registra la devolucion y libera el ejemplar."""
        ahora = datetime.now()

        with self.db.transaccion() as cursor:
            prestamo = self.prestamos.obtener_para_actualizar(id_prestamo, cursor)
            if prestamo is None:
                raise NoEncontrado(f"No existe el prestamo {id_prestamo}.")
            if prestamo.estado == "DEVUELTO":
                raise ReglaViolada("El prestamo ya fue devuelto.")

            devolucion = Devolucion(
                id_prestamo=id_prestamo,
                fecha_devolucion=ahora,
                observacion=observacion,
            )
            devolucion.id_devolucion = self.devoluciones.crear(devolucion, cursor)

            self.prestamos.cambiar_estado(id_prestamo, "DEVUELTO", cursor)
            self.ejemplares.cambiar_estado(prestamo.id_ejemplar, "DISPONIBLE", cursor)
            return devolucion

    # ------------------------------------------------------------------
    def listar_por_usuario(
        self, id_usuario: int, solo_activos: bool = False
    ) -> list[Prestamo]:
        if self.usuarios.obtener(id_usuario) is None:
            raise NoEncontrado(f"No existe el usuario {id_usuario}.")
        return self.prestamos.listar_por_usuario(id_usuario, solo_activos)

    def listar_vencidos(self) -> list[Prestamo]:
        return self.prestamos.listar_vencidos()

    def actualizar_vencidos(self) -> int:
        """Marca como VENCIDOS los prestamos activos cuya fecha ya paso."""
        return self.prestamos.marcar_vencidos()
