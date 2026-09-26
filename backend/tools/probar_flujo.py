"""Prueba end-to-end del flujo transaccional contra un nodo levantado.

Uso (con el nodo corriendo en otra terminal):

    python tools/probar_flujo.py --nodo 1

Recorre: ping -> buscar libro -> disponibilidad -> prestar -> verificar que
bajo el inventario -> listar prestamos -> devolver -> verificar que volvio.
Ademas comprueba dos reglas de negocio (devolver dos veces y prestar un
libro agotado) para confirmar que el servidor responde con el codigo gRPC
correcto en lugar de romperse.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import grpc  # noqa: E402

from config.settings import NODOS_VALIDOS, get_nodo_config  # noqa: E402
from grpc_service.cliente import ClienteNodo  # noqa: E402
from grpc_service.generated import biblioteca_pb2 as pb  # noqa: E402

fallos = 0


def paso(titulo: str) -> None:
    print(f"\n--- {titulo} ---")


def check(condicion: bool, mensaje: str) -> None:
    global fallos
    if condicion:
        print(f"  OK   {mensaje}")
    else:
        fallos += 1
        print(f"  FALLA {mensaje}")


def disponibles_de(cliente: ClienteNodo, id_libro: int) -> int:
    respuesta = cliente.stub.ListarEjemplares(
        pb.ListarEjemplaresRequest(id_libro=id_libro, solo_disponibles=True)
    )
    return len(respuesta.ejemplares)


def main() -> int:
    parser = argparse.ArgumentParser(description="Prueba end-to-end de un nodo")
    parser.add_argument("--nodo", type=int, default=1, choices=NODOS_VALIDOS)
    args = parser.parse_args()

    nodo = get_nodo_config(args.nodo)
    print(f"Probando nodo {nodo.numero} en {nodo.address}")

    with ClienteNodo(nodo) as cliente:
        # -- Ping -------------------------------------------------------
        paso("Ping")
        try:
            info = cliente.ping()
        except grpc.RpcError as exc:
            print(f"  El nodo no responde: {exc.details()}")
            print("  Levantalo con: python servidor.py --nodo", nodo.numero)
            return 1
        print(f"  {info.nombre} v{info.version}")
        check(info.base_datos_ok, "la base de datos responde")
        if not info.base_datos_ok:
            return 1

        # -- Datos de partida -------------------------------------------
        paso("Datos de partida")
        usuarios = cliente.stub.ListarUsuarios(pb.ListarRequest(limite=5)).usuarios
        check(bool(usuarios), "hay usuarios cargados")
        if not usuarios:
            print("  Ejecuta primero: python tools/cargar_datos.py --nodo", nodo.numero)
            return 1
        usuario = usuarios[0]
        print(f"  Usuario de prueba: [{usuario.id_usuario}] {usuario.nombre}")

        disponibilidad = cliente.disponibilidad(limite=50).resultados
        candidatos = [d for d in disponibilidad if d.disponibles > 0]
        check(bool(candidatos), "hay al menos un libro con ejemplares disponibles")
        if not candidatos:
            print("  Ejecuta primero: python tools/cargar_datos.py --nodo", nodo.numero)
            return 1
        libro = candidatos[0]
        print(f"  Libro de prueba: [{libro.id_libro}] {libro.titulo}")

        antes = disponibles_de(cliente, libro.id_libro)
        print(f"  Disponibles antes: {antes}")

        # -- Prestar ----------------------------------------------------
        paso("Registrar prestamo")
        prestamo = cliente.prestar(usuario.id_usuario, libro.id_libro, dias=7).prestamo
        print(
            f"  Prestamo #{prestamo.id_prestamo} | ejemplar {prestamo.id_ejemplar} "
            f"| vence {prestamo.fecha_vencimiento[:10]}"
        )
        check(prestamo.estado == "ACTIVO", "el prestamo queda ACTIVO")

        despues = disponibles_de(cliente, libro.id_libro)
        check(despues == antes - 1, f"el inventario bajo de {antes} a {despues}")

        # -- Listar -----------------------------------------------------
        paso("Listar prestamos del usuario")
        activos = cliente.stub.ListarPrestamos(
            pb.ListarPrestamosRequest(id_usuario=usuario.id_usuario, solo_activos=True)
        ).prestamos
        check(
            any(p.id_prestamo == prestamo.id_prestamo for p in activos),
            "el prestamo aparece entre los activos",
        )

        # -- Devolver ---------------------------------------------------
        paso("Registrar devolucion")
        devolucion = cliente.devolver(
            prestamo.id_prestamo, "Prueba automatica"
        ).devolucion
        print(f"  Devolucion #{devolucion.id_devolucion}")

        final = disponibles_de(cliente, libro.id_libro)
        check(final == antes, f"el inventario volvio a {antes}")

        # -- Reglas de negocio ------------------------------------------
        paso("Reglas de negocio")
        try:
            cliente.devolver(prestamo.id_prestamo)
            check(False, "devolver dos veces deberia fallar")
        except grpc.RpcError as exc:
            check(
                exc.code() == grpc.StatusCode.FAILED_PRECONDITION,
                f"devolver dos veces -> {exc.code().name}",
            )

        try:
            cliente.prestar(usuario.id_usuario, 999999)
            check(False, "prestar un libro inexistente deberia fallar")
        except grpc.RpcError as exc:
            check(
                exc.code() == grpc.StatusCode.NOT_FOUND,
                f"libro inexistente -> {exc.code().name}",
            )

        agotado = next((d for d in disponibilidad if d.disponibles == 0), None)
        if agotado:
            try:
                cliente.prestar(usuario.id_usuario, agotado.id_libro)
                check(False, "prestar un libro agotado deberia fallar")
            except grpc.RpcError as exc:
                check(
                    exc.code() == grpc.StatusCode.RESOURCE_EXHAUSTED,
                    f"libro agotado -> {exc.code().name}",
                )

    print("\n" + "=" * 50)
    if fallos:
        print(f"{fallos} comprobacion(es) fallaron.")
        return 1
    print("Todas las comprobaciones pasaron.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
