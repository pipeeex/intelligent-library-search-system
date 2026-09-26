"""Arranque del servidor gRPC de un nodo."""

from __future__ import annotations

import logging
from concurrent import futures

import grpc

from config.settings import NodoConfig
from db.connection import Database

from grpc_service.generated import biblioteca_pb2_grpc as pb_grpc
from grpc_service.servicer import BibliotecaNodoServicer

logger = logging.getLogger(__name__)

MAX_WORKERS = 10


def crear_servidor(nodo: NodoConfig) -> grpc.Server:
    db = Database(nodo.database)

    servidor = grpc.server(futures.ThreadPoolExecutor(max_workers=MAX_WORKERS))
    pb_grpc.add_BibliotecaNodoServicer_to_server(
        BibliotecaNodoServicer(db, nodo), servidor
    )
    servidor.add_insecure_port(nodo.address)

    ok, motivo = db.diagnosticar()
    if ok:
        logger.info("Conexion a '%s' verificada.", nodo.database.database)
    else:
        logger.warning(
            "No se pudo conectar a '%s'. El nodo arranca igual, pero las "
            "operaciones fallaran hasta que la base de datos este disponible.",
            nodo.database.database,
        )
        logger.warning("Motivo: %s", motivo)
        logger.warning(
            "Cadena usada: %s", nodo.database.connection_string().replace(
                nodo.database.password or "\x00", "***"
            )
        )
        logger.warning("Ejecuta 'python tools/diagnostico.py' para revisar la conexion.")

    return servidor


def iniciar(nodo: NodoConfig) -> None:
    servidor = crear_servidor(nodo)
    servidor.start()
    logger.info("Nodo %s escuchando en %s", nodo.numero, nodo.address)
    print(f"[Nodo {nodo.numero}] {nodo.nombre} escuchando en {nodo.address}")
    print("Ctrl+C para detener.")
    try:
        servidor.wait_for_termination()
    except KeyboardInterrupt:
        print("\nDeteniendo nodo...")
        servidor.stop(grace=3).wait()
        print("Nodo detenido.")
