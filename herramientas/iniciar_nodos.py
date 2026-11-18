"""Levanta los tres nodos en un solo comando, en lugar de una terminal por nodo.

Cada nodo corre en su propio proceso (python servidor.py --nodo N) y su
salida se muestra en esta misma terminal con el prefijo [Nodo N]. Ctrl+C
detiene los tres a la vez.

Uso:
    python herramientas/iniciar_nodos.py
    python herramientas/iniciar_nodos.py --nodos 1 2
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import threading
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
NODOS_VALIDOS = (1, 2, 3)


def _leer_salida(proceso: subprocess.Popen, nodo: int) -> None:
    assert proceso.stdout is not None
    for linea in proceso.stdout:
        print(f"[Nodo {nodo}] {linea.rstrip()}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Levanta varios nodos a la vez")
    parser.add_argument(
        "--nodos",
        type=int,
        nargs="+",
        choices=NODOS_VALIDOS,
        default=list(NODOS_VALIDOS),
        help="Nodos a levantar (por defecto: 1 2 3)",
    )
    args = parser.parse_args()

    procesos: list[tuple[int, subprocess.Popen]] = []
    for nodo in args.nodos:
        proceso = subprocess.Popen(
            [sys.executable, "servidor.py", "--nodo", str(nodo)],
            cwd=RAIZ,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        procesos.append((nodo, proceso))
        hilo = threading.Thread(target=_leer_salida, args=(proceso, nodo), daemon=True)
        hilo.start()

    print(f"Levantando nodos {args.nodos}... Ctrl+C para detener todos.\n")

    try:
        while True:
            for nodo, proceso in procesos:
                codigo = proceso.poll()
                if codigo is not None:
                    print(f"[Nodo {nodo}] terminó (codigo {codigo}).")
                    procesos.remove((nodo, proceso))
            if not procesos:
                print("No quedan nodos corriendo.")
                return 1
            for _, proceso in procesos:
                try:
                    proceso.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    pass
    except KeyboardInterrupt:
        print("\nDeteniendo todos los nodos...")
        for nodo, proceso in procesos:
            proceso.terminate()
        for nodo, proceso in procesos:
            try:
                proceso.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proceso.kill()
        print("Nodos detenidos.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
