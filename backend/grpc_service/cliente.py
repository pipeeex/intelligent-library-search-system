"""Cliente distribuido: habla con los tres nodos y agrega los resultados.

Lo usara la aplicacion de escritorio y, mas adelante, el modulo de IA.
"""

from __future__ import annotations

import logging
from concurrent import futures
from dataclasses import dataclass
from typing import Any

import grpc

from config.settings import NodoConfig, get_todos_los_nodos

from grpc_service.generated import biblioteca_pb2 as pb
from grpc_service.generated import biblioteca_pb2_grpc as pb_grpc

logger = logging.getLogger(__name__)

TIMEOUT = 5.0


@dataclass
class RespuestaNodo:
    nodo: int
    nombre: str
    ok: bool
    datos: Any = None
    error: str | None = None


class ClienteNodo:
    """Cliente gRPC de un solo nodo."""

    def __init__(self, nodo: NodoConfig, timeout: float = TIMEOUT) -> None:
        self.nodo = nodo
        self.timeout = timeout
        self._canal = grpc.insecure_channel(nodo.address)
        self.stub = pb_grpc.BibliotecaNodoStub(self._canal)

    def cerrar(self) -> None:
        self._canal.close()

    def __enter__(self) -> "ClienteNodo":
        return self

    def __exit__(self, *_exc) -> None:
        self.cerrar()

    def ping(self):
        return self.stub.Ping(pb.PingRequest(), timeout=self.timeout)

    def disponibilidad(
        self,
        titulo: str | None = None,
        autor: str | None = None,
        isbn: str | None = None,
        limite: int = 50,
    ):
        peticion = pb.DisponibilidadRequest(
            titulo=titulo or "", autor=autor or "", isbn=isbn or "", limite=limite
        )
        return self.stub.ConsultarDisponibilidad(peticion, timeout=self.timeout)

    def buscar_libros(self, titulo: str = "", autor: str = "", isbn: str = ""):
        peticion = pb.BuscarLibrosRequest(titulo=titulo, autor=autor, isbn=isbn)
        return self.stub.BuscarLibros(peticion, timeout=self.timeout)

    def prestar(self, id_usuario: int, id_libro: int, dias: int = 0):
        peticion = pb.PrestamoRequest(
            id_usuario=id_usuario, id_libro=id_libro, dias=dias
        )
        return self.stub.RegistrarPrestamo(peticion, timeout=self.timeout)

    def devolver(self, id_prestamo: int, observacion: str = ""):
        peticion = pb.DevolucionRequest(
            id_prestamo=id_prestamo, observacion=observacion
        )
        return self.stub.RegistrarDevolucion(peticion, timeout=self.timeout)


class ClienteDistribuido:
    """Consulta los tres nodos en paralelo y tolera nodos caidos."""

    def __init__(self, nodos: list[NodoConfig] | None = None) -> None:
        self.nodos = nodos or get_todos_los_nodos()
        self.clientes = {n.numero: ClienteNodo(n) for n in self.nodos}

    def cerrar(self) -> None:
        for cliente in self.clientes.values():
            cliente.cerrar()

    def __enter__(self) -> "ClienteDistribuido":
        return self

    def __exit__(self, *_exc) -> None:
        self.cerrar()

    # ------------------------------------------------------------------
    def _en_paralelo(self, funcion) -> list[RespuestaNodo]:
        respuestas: list[RespuestaNodo] = []
        with futures.ThreadPoolExecutor(max_workers=len(self.clientes) or 1) as pool:
            tareas = {
                pool.submit(funcion, cliente): cliente
                for cliente in self.clientes.values()
            }
            for tarea in futures.as_completed(tareas):
                cliente = tareas[tarea]
                try:
                    respuestas.append(
                        RespuestaNodo(
                            nodo=cliente.nodo.numero,
                            nombre=cliente.nodo.nombre,
                            ok=True,
                            datos=tarea.result(),
                        )
                    )
                except grpc.RpcError as exc:
                    logger.warning(
                        "Nodo %s no respondio: %s", cliente.nodo.numero, exc.details()
                    )
                    respuestas.append(
                        RespuestaNodo(
                            nodo=cliente.nodo.numero,
                            nombre=cliente.nodo.nombre,
                            ok=False,
                            error=exc.details(),
                        )
                    )
        return sorted(respuestas, key=lambda r: r.nodo)

    # ------------------------------------------------------------------
    def estado_nodos(self) -> list[RespuestaNodo]:
        return self._en_paralelo(lambda c: c.ping())

    def disponibilidad_global(
        self,
        titulo: str | None = None,
        autor: str | None = None,
        isbn: str | None = None,
    ) -> list[RespuestaNodo]:
        return self._en_paralelo(lambda c: c.disponibilidad(titulo, autor, isbn))

    def resumen_disponibilidad(
        self,
        titulo: str | None = None,
        autor: str | None = None,
        isbn: str | None = None,
    ) -> list[dict[str, Any]]:
        """Aplana la disponibilidad de los tres nodos en una sola lista."""
        filas: list[dict[str, Any]] = []
        for respuesta in self.disponibilidad_global(titulo, autor, isbn):
            if not respuesta.ok:
                continue
            for item in respuesta.datos.resultados:
                filas.append(
                    {
                        "nodo": respuesta.nodo,
                        "biblioteca": respuesta.nombre,
                        "id_libro": item.id_libro,
                        "isbn": item.isbn,
                        "titulo": item.titulo,
                        "autor": item.autor,
                        "total_ejemplares": item.total_ejemplares,
                        "disponibles": item.disponibles,
                        "prestados": item.prestados,
                    }
                )
        return filas
