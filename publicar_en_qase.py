"""Publica en Qase el resultado de la suite de pruebas transaccionales.

Lee el informe que deja `herramientas/pruebas_transaccionales.py` en
`docs/evidencias/`, crea una ejecucion en Qase y sube los ocho casos con sus
comprobaciones como pasos. Asi la evidencia queda en los dos sitios: el archivo
fechado en el repositorio y la ejecucion en la herramienta.

No necesita librerias externas: usa solo la biblioteca estandar de Python, para
que funcione en cualquiera de los tres equipos sin instalar nada.

Configuracion (variables de entorno, o en el .env del proyecto):

    QASE_TOKEN     token de la API, se saca en Qase > Apps > API Tokens
    QASE_PROJECT   codigo del proyecto, las letras que Qase pone antes del
                   numero de caso (por ejemplo SDCIB)

Uso:
    python publicar_en_qase.py                       # toma el informe mas reciente
    python publicar_en_qase.py --informe docs/evidencias/pruebas_...md
    python publicar_en_qase.py --simular             # no envia nada, solo muestra

Sobre el mapeo de casos: la primera vez no hace falta. Qase acepta resultados
identificando el caso por su titulo, y si no existe lo crea. Cuando ya tengan
el catalogo importado, conviene rellenar `mapeo_casos.json` con los
identificadores reales para que los resultados caigan sobre los casos
existentes en lugar de crear duplicados:

    {"PT-01": 12, "PT-02": 13, ...}
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

API = "https://api.qase.io/v1"
SUITE_QASE = "Prestamos y devoluciones"

# Estados que acepta la API de Qase para un resultado y para un paso.
# No son iguales: 'skipped' vale para el resultado pero no para el paso.
ESTADO_RESULTADO = {"PASA": "passed", "FALLA": "failed",
                    "OMITIDO": "skipped", "PENDIENTE": "blocked"}
ESTADO_PASO = {"OK": "passed", "FALLA": "failed"}


@dataclass
class Comprobacion:
    descripcion: str
    esperado: str
    obtenido: str
    ok: bool


@dataclass
class CasoEjecutado:
    codigo: str
    nombre: str
    estado: str                      # PASA, FALLA, OMITIDO
    segundos: float = 0.0
    objetivo: str = ""
    observacion: str = ""
    comprobaciones: list[Comprobacion] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Lectura del informe
# ---------------------------------------------------------------------------
def ultimo_informe(carpeta: Path) -> Path:
    informes = sorted(carpeta.glob("pruebas_transaccionales_*.md"))
    if not informes:
        raise SystemExit(f"No hay informes en {carpeta}. Ejecuta primero la suite.")
    return informes[-1]


def _celdas(linea: str) -> list[str]:
    return [c.strip() for c in linea.strip().strip("|").split("|")]


def leer_informe(ruta: Path) -> tuple[list[CasoEjecutado], str]:
    """Convierte el informe en Markdown en objetos. Devuelve (casos, fecha)."""
    texto = ruta.read_text(encoding="utf-8")

    fecha = ""
    m = re.search(r"\*\*Fecha de ejecucion:\*\*\s*(.+)", texto)
    if m:
        fecha = m.group(1).strip()

    # -- tabla de resumen ----------------------------------------------
    casos: dict[str, CasoEjecutado] = {}
    orden: list[str] = []
    for linea in texto.splitlines():
        m = re.match(r"^\|\s*(PT-\d+)\s*\|", linea)
        if not m:
            continue
        cols = _celdas(linea)
        if len(cols) < 4:
            continue
        codigo = cols[0]
        estado = re.sub(r"[*\s]", "", cols[2]).upper()
        segundos = 0.0
        ms = re.search(r"([\d.]+)\s*s", cols[3])
        if ms:
            segundos = float(ms.group(1))
        casos[codigo] = CasoEjecutado(codigo=codigo, nombre=cols[1],
                                      estado=estado, segundos=segundos)
        orden.append(codigo)

    if not casos:
        raise SystemExit(f"No se reconocio ningun caso PT en {ruta.name}.")

    # -- detalle por caso ----------------------------------------------
    bloques = re.split(r"^### ", texto, flags=re.M)[1:]
    for bloque in bloques:
        m = re.match(r"(PT-\d+)", bloque)
        if not m or m.group(1) not in casos:
            continue
        caso = casos[m.group(1)]

        mo = re.search(r"\*\*Objetivo\.\*\*\s*(.+)", bloque)
        if mo:
            caso.objetivo = mo.group(1).strip()
        mb = re.search(r"\*\*Observacion\.\*\*\s*(.+)", bloque)
        if mb:
            caso.observacion = mb.group(1).strip()

        for linea in bloque.splitlines():
            if not linea.startswith("|"):
                continue
            cols = _celdas(linea)
            if len(cols) != 4:
                continue
            if cols[0] in ("Comprobacion", "---") or set(cols[0]) == {"-"}:
                continue
            caso.comprobaciones.append(Comprobacion(
                descripcion=cols[0],
                esperado=cols[1].strip("`"),
                obtenido=cols[2].strip("`"),
                ok=cols[3].upper() == "OK",
            ))

    return [casos[c] for c in orden], fecha


# ---------------------------------------------------------------------------
# Construccion de la peticion
# ---------------------------------------------------------------------------
def armar_resultados(casos: list[CasoEjecutado], mapeo: dict[str, int]) -> list[dict]:
    resultados = []
    for caso in casos:
        pasos = [{
            "status": "passed" if c.ok else "failed",
            "action": c.descripcion,
            "expected_result": c.esperado,
            "comment": f"Obtenido: {c.obtenido}",
        } for c in caso.comprobaciones]

        comentario = [f"{caso.codigo} - {caso.nombre}"]
        if caso.objetivo:
            comentario.append(f"Objetivo: {caso.objetivo}")
        if caso.observacion:
            comentario.append(f"Observacion: {caso.observacion}")
        correctas = sum(1 for c in caso.comprobaciones if c.ok)
        comentario.append(f"Comprobaciones: {correctas} de {len(caso.comprobaciones)}")

        resultado = {
            "status": ESTADO_RESULTADO.get(caso.estado, "blocked"),
            "time_ms": int(caso.segundos * 1000),
            "comment": "\n".join(comentario),
        }
        if pasos:
            resultado["steps"] = pasos

        if caso.codigo in mapeo:
            resultado["case_id"] = int(mapeo[caso.codigo])
        else:
            # Sin mapeo, Qase identifica el caso por su titulo.
            resultado["case"] = {
                "title": f"{caso.codigo} - {caso.nombre}",
                "suite_title": SUITE_QASE,
                "description": caso.objetivo,
            }
        resultados.append(resultado)
    return resultados


# ---------------------------------------------------------------------------
# Cliente de la API
# ---------------------------------------------------------------------------
class Qase:
    def __init__(self, token: str, proyecto: str) -> None:
        self.token = token
        self.proyecto = proyecto

    def _pedir(self, metodo: str, ruta: str, cuerpo: dict | None = None) -> dict:
        datos = json.dumps(cuerpo).encode("utf-8") if cuerpo is not None else None
        peticion = urllib.request.Request(
            f"{API}{ruta}", data=datos, method=metodo,
            headers={"Token": self.token,
                     "Content-Type": "application/json",
                     "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(peticion, timeout=30) as respuesta:
                return json.loads(respuesta.read().decode("utf-8") or "{}")
        except urllib.error.HTTPError as exc:
            detalle = exc.read().decode("utf-8", "replace")[:400]
            if exc.code == 401:
                raise SystemExit("Qase rechazo el token (401). Revisa QASE_TOKEN.")
            if exc.code == 404:
                raise SystemExit(
                    f"Qase respondio 404. Revisa que el codigo de proyecto "
                    f"'{self.proyecto}' sea el correcto.")
            raise SystemExit(f"Qase respondio {exc.code}: {detalle}")
        except urllib.error.URLError as exc:
            raise SystemExit(f"No se pudo contactar a Qase: {exc.reason}")

    def crear_ejecucion(self, titulo: str, descripcion: str) -> int:
        datos = self._pedir("POST", f"/run/{self.proyecto}", {
            "title": titulo,
            "description": descripcion,
            "is_autotest": True,
        })
        try:
            return int(datos["result"]["id"])
        except (KeyError, TypeError):
            raise SystemExit(f"Respuesta inesperada al crear la ejecucion: {datos}")

    def subir_resultados(self, id_ejecucion: int, resultados: list[dict]) -> None:
        # La API admite hasta 200 resultados por llamada.
        for i in range(0, len(resultados), 200):
            self._pedir("POST",
                        f"/result/{self.proyecto}/{id_ejecucion}/bulk",
                        {"results": resultados[i:i + 200]})

    def cerrar_ejecucion(self, id_ejecucion: int) -> None:
        self._pedir("POST", f"/run/{self.proyecto}/{id_ejecucion}/complete")


# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description="Publica resultados en Qase")
    parser.add_argument("--informe", type=Path,
                        help="Informe concreto; por defecto, el mas reciente")
    parser.add_argument("--evidencias", type=Path, default=Path("docs/evidencias"),
                        help="Carpeta donde la suite deja los informes")
    parser.add_argument("--mapeo", type=Path, default=Path("mapeo_casos.json"),
                        help="Equivalencia PT-xx -> identificador de caso en Qase")
    parser.add_argument("--titulo", help="Titulo de la ejecucion en Qase")
    parser.add_argument("--simular", action="store_true",
                        help="Mostrar lo que se enviaria, sin enviarlo")
    args = parser.parse_args()

    ruta = args.informe or ultimo_informe(args.evidencias)
    casos, fecha = leer_informe(ruta)

    pasan = sum(1 for c in casos if c.estado == "PASA")
    total_comp = sum(len(c.comprobaciones) for c in casos)
    print(f"Informe: {ruta.name}")
    print(f"  {len(casos)} casos ({pasan} pasan), {total_comp} comprobaciones")

    mapeo: dict[str, int] = {}
    if args.mapeo.exists():
        mapeo = json.loads(args.mapeo.read_text(encoding="utf-8"))
        print(f"  Mapeo cargado: {len(mapeo)} casos enlazados a Qase")
    else:
        print(f"  Sin {args.mapeo.name}: los casos se identificaran por su titulo")

    resultados = armar_resultados(casos, mapeo)

    titulo = args.titulo or f"Pruebas transaccionales - {fecha or ruta.stem}"
    descripcion = (
        f"Ejecucion automatica de la suite de pruebas transaccionales.\n"
        f"Informe: {ruta.name}\n"
        f"Resultado: {pasan} de {len(casos)} casos superados, "
        f"{total_comp} comprobaciones."
    )

    if args.simular:
        print(f"\n[simulacion] Ejecucion: {titulo}")
        for r, c in zip(resultados, casos):
            enlace = f"caso {r['case_id']}" if "case_id" in r else "por titulo"
            print(f"  {c.codigo}  {r['status']:<7} {r['time_ms']:>6} ms  "
                  f"{len(r.get('steps', []))} pasos  ({enlace})")
        print("\nNo se envio nada. Quita --simular para publicar.")
        return 0

    token = os.getenv("QASE_TOKEN")
    proyecto = os.getenv("QASE_PROJECT")
    if not token or not proyecto:
        raise SystemExit(
            "Faltan QASE_TOKEN o QASE_PROJECT.\n"
            "  Windows:  set QASE_TOKEN=...   y   set QASE_PROJECT=...\n"
            "  Linux:    export QASE_TOKEN=... y export QASE_PROJECT=...")

    qase = Qase(token, proyecto)
    id_ejecucion = qase.crear_ejecucion(titulo, descripcion)
    print(f"  Ejecucion creada: #{id_ejecucion}")
    qase.subir_resultados(id_ejecucion, resultados)
    print(f"  {len(resultados)} resultados enviados")
    qase.cerrar_ejecucion(id_ejecucion)
    print(f"  Ejecucion cerrada")
    print(f"\nhttps://app.qase.io/run/{proyecto}/dashboard/{id_ejecucion}")
    return 0 if pasan == len(casos) else 1


if __name__ == "__main__":
    raise SystemExit(main())
