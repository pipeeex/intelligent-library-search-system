"""Prueba rapida de humo: hace Ping a los tres nodos y muestra su estado.

Uso (desde backend/, con los nodos levantados):

    python tools/probar_nodos.py
    python tools/probar_nodos.py --titulo "cien anos"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from grpc_service.cliente import ClienteDistribuido  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Prueba de humo de los nodos")
    parser.add_argument("--titulo", help="Consultar disponibilidad por titulo")
    parser.add_argument("--autor", help="Consultar disponibilidad por autor")
    args = parser.parse_args()

    with ClienteDistribuido() as cliente:
        print("=== Estado de los nodos ===")
        for respuesta in cliente.estado_nodos():
            if respuesta.ok:
                bd = "OK" if respuesta.datos.base_datos_ok else "SIN BD"
                print(f"  Nodo {respuesta.nodo}: activo  (BD: {bd})")
            else:
                print(f"  Nodo {respuesta.nodo}: caido   ({respuesta.error})")

        if args.titulo or args.autor:
            print("\n=== Disponibilidad ===")
            filas = cliente.resumen_disponibilidad(
                titulo=args.titulo, autor=args.autor
            )
            if not filas:
                print("  Sin resultados.")
            for fila in filas:
                print(
                    f"  [Nodo {fila['nodo']}] {fila['titulo']} - {fila['autor']}: "
                    f"{fila['disponibles']}/{fila['total_ejemplares']} disponibles"
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
