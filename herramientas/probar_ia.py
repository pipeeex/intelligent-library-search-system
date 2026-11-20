"""Prueba la consulta en lenguaje natural desde la linea de comandos.

Sirve para dos cosas: verificar la cadena completa sin abrir la interfaz, y
dejar evidencia de los casos de RF-09 copiando la salida.

    python herramientas/probar_ia.py "tienen algo de Borges?"
    python herramientas/probar_ia.py                 # corre la bateria
    python herramientas/probar_ia.py --reglas "..."   # fuerza el respaldo
    python herramientas/probar_ia.py --demo "..."     # sin nodos levantados

La diferencia entre el modelo y las reglas se ve en la linea "origen".
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Permite ejecutarlo como "python herramientas/probar_ia.py" desde la raiz.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# En Windows la consola suele venir en una pagina de codigos que no sabe
# escribir tildes ni los titulos en otros alfabetos. Sin esto, imprimir la
# respuesta puede fallar con UnicodeEncodeError.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

from negocio.interprete_reglas import InterpreteReglas  # noqa: E402
from negocio.servicio_ia import ErrorConsulta, ServicioIA  # noqa: E402
from presentacion.escritorio.servicio_cliente import crear_proveedor  # noqa: E402

BATERIA = [
    "¿Tienen Cien años de soledad?",
    "¿Hay algo de Borges?",
    "¿En qué biblioteca está Clean Code?",
    "¿Tienen el 9780132350884?",
    "¿Qué tiene prestado Juan Pérez?",
    "¿Cuánto es 2 más 2?",
]


def construir(forzar_reglas: bool, forzar_demo: bool):
    proveedor, aviso_proveedor = crear_proveedor(forzar_demo)

    primario = None
    if not forzar_reglas:
        try:
            from negocio.interprete_llm import ErrorInterprete, InterpreteLLM
            primario = InterpreteLLM()
        except ErrorInterprete as exc:
            print(f"[aviso] No se usara el modelo: {exc}")
        except ImportError as exc:
            print(f"[aviso] No se pudo importar el interprete del modelo: {exc}")

    servicio = ServicioIA(proveedor, interprete=primario,
                          respaldo=InterpreteReglas())
    return servicio, aviso_proveedor


def preguntar(servicio, pregunta: str) -> bool:
    print("=" * 70)
    print(f"PREGUNTA: {pregunta}")
    inicio = time.time()
    try:
        respuesta = servicio.responder(pregunta)
    except ErrorConsulta as exc:
        print(f"  ERROR DE NODOS: {exc}")
        return False
    except Exception as exc:  # el interprete fallo y no hubo respaldo
        print(f"  ERROR: {exc.__class__.__name__}: {exc}")
        return False
    tardo = time.time() - inicio

    i = respuesta.intencion
    print(f"  interpretado por: {i.origen}   en {tardo:.1f} s")
    print(f"  tipo: {i.tipo}   confianza: {i.confianza}")
    print(f"  titulo={i.titulo!r}  autor={i.autor!r}  isbn={i.isbn!r}"
          f"  lector={i.lector!r}")
    if respuesta.aviso:
        print(f"  aviso: {respuesta.aviso}")
    print(f"  filas devueltas por los nodos: {len(respuesta.resultados)}")
    print("  respuesta:")
    for linea in respuesta.texto.splitlines():
        print(f"    {linea}")
    return True


def main() -> int:
    analizador = argparse.ArgumentParser(
        description="Prueba la consulta en lenguaje natural.")
    analizador.add_argument("pregunta", nargs="*",
                            help="la pregunta; sin argumentos corre la bateria")
    analizador.add_argument("--reglas", action="store_true",
                            help="ignora el modelo y usa solo las reglas")
    analizador.add_argument("--demo", action="store_true",
                            help="usa el proveedor demo, sin nodos")
    args = analizador.parse_args()

    servicio, aviso = construir(args.reglas, args.demo)
    print(f"[proveedor] {aviso}")
    print(f"[modo] {servicio.proveedor.modo}")

    preguntas = [" ".join(args.pregunta)] if args.pregunta else BATERIA
    fallos = sum(0 if preguntar(servicio, p) else 1 for p in preguntas)

    print("=" * 70)
    if fallos:
        print(f"{fallos} de {len(preguntas)} preguntas terminaron en error.")
    else:
        print(f"Las {len(preguntas)} preguntas se respondieron sin errores.")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
