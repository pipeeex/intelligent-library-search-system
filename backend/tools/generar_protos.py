"""Genera los stubs de gRPC a partir de proto/biblioteca.proto.

Uso (desde la carpeta backend/):

    python tools/generar_protos.py

Deja biblioteca_pb2.py y biblioteca_pb2_grpc.py dentro de grpc_service/generated/
y corrige el import absoluto que genera protoc.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PROTO_DIR = BASE_DIR / "proto"
OUT_DIR = BASE_DIR / "grpc_service" / "generated"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "__init__.py").touch()

    comando = [
        sys.executable,
        "-m",
        "grpc_tools.protoc",
        f"-I{PROTO_DIR}",
        f"--python_out={OUT_DIR}",
        f"--pyi_out={OUT_DIR}",
        f"--grpc_python_out={OUT_DIR}",
        str(PROTO_DIR / "biblioteca.proto"),
    ]
    print("Ejecutando:", " ".join(comando))
    resultado = subprocess.run(comando)
    if resultado.returncode != 0:
        print("Error generando los stubs. Instala grpcio-tools:")
        print("    pip install grpcio-tools")
        return resultado.returncode

    # protoc genera 'import biblioteca_pb2 as ...', que falla al importar el
    # paquete. Lo convertimos en import relativo.
    grpc_file = OUT_DIR / "biblioteca_pb2_grpc.py"
    contenido = grpc_file.read_text(encoding="utf-8")
    contenido = re.sub(
        r"^import biblioteca_pb2 as",
        "from . import biblioteca_pb2 as",
        contenido,
        flags=re.MULTILINE,
    )
    grpc_file.write_text(contenido, encoding="utf-8")

    print(f"Stubs generados en {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
