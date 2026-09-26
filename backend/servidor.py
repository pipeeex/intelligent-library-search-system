"""Punto de entrada de un nodo bibliotecario.

Uso:
    python servidor.py --nodo 1
    python servidor.py --nodo 2
    python servidor.py --nodo 3
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config.settings import (  # noqa: E402
    ENV_CARGADO,
    ENV_FILE,
    ENV_ORIGEN,
    NODOS_VALIDOS,
    get_nodo_config,
)


def configurar_logging(verboso: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verboso else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Nodo bibliotecario gRPC")
    parser.add_argument(
        "--nodo",
        type=int,
        required=True,
        choices=NODOS_VALIDOS,
        help="Numero del nodo a levantar (1, 2 o 3)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Logs detallados")
    args = parser.parse_args()

    configurar_logging(args.verbose)

    if ENV_CARGADO:
        logging.getLogger(__name__).info(
            "Configuracion leida de %s (%s).", ENV_FILE.name, ENV_ORIGEN
        )
    else:
        logging.getLogger(__name__).warning(
            "No se leyo ningun .env (%s). Se usaran los valores por defecto. "
            "Copia .env.example a .env en la carpeta backend/.",
            ENV_FILE,
        )

    try:
        from grpc_service.server import iniciar
    except ImportError as exc:
        print(f"No se pudieron importar los stubs de gRPC: {exc}")
        print("Genera los stubs primero:  python tools/generar_protos.py")
        return 1

    iniciar(get_nodo_config(args.nodo))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
