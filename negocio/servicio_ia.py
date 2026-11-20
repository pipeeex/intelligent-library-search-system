"""Modulo de IA: orquestador de la consulta en lenguaje natural.

El flujo es:

    pregunta en lenguaje natural
        -> InterpretePregunta -> IntencionConsulta
        -> proveedor.disponibilidad(criterio)
        -> respuesta redactada SOLO con los datos devueltos por los nodos

El interprete (el modelo de lenguaje o las reglas locales) traduce la
pregunta y nada mas: no recibe el catalogo, no lo consulta y no redacta la
respuesta. Por diseno no puede inventar disponibilidad, porque nunca la ve.

Alcance de esta version: disponibilidad y sede. Las preguntas sobre
prestamos se reconocen y se contestan diciendo donde se hacen, en vez de
confundirlas con la busqueda de un libro.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

# Tipos de pregunta que el interprete sabe reconocer.
TIPOS = (
    "DISPONIBILIDAD",      # hay ejemplares de un libro?
    "SEDE",                # en que biblioteca esta?
    "PRESTAMOS_USUARIO",   # que tiene prestado una persona?
    "PRESTAMOS_VENCIDOS",  # que prestamos estan atrasados?
    "DESCONOCIDA",         # la pregunta no es sobre la biblioteca
)

# Tipos que esta version responde consultando a los nodos.
TIPOS_ATENDIDOS = ("DISPONIBILIDAD", "SEDE")

# Por debajo de esta confianza, la respuesta avisa que pudo no entender.
UMBRAL_CONFIANZA = 0.4


@dataclass
class IntencionConsulta:
    """Lo que se extrae de la pregunta del usuario."""

    titulo: str | None = None
    autor: str | None = None
    isbn: str | None = None
    lector: str | None = None
    tipo: str = "DISPONIBILIDAD"
    confianza: float = 0.0
    # "llm" si lo interpreto el modelo, "reglas" si entro el respaldo.
    origen: str = "reglas"


@dataclass
class RespuestaIA:
    texto: str
    intencion: IntencionConsulta
    resultados: list[dict[str, Any]]
    # Mensaje sobre el proceso, no sobre el catalogo: por ejemplo, que el
    # modelo no respondio y contesto el motor de reglas.
    aviso: str | None = None


class ErrorConsulta(RuntimeError):
    """Los nodos no pudieron responder la consulta."""


class InterpretePregunta(Protocol):
    """Contrato del interprete: lo cumplen InterpreteLLM e InterpreteReglas."""

    def interpretar(self, pregunta: str) -> IntencionConsulta: ...


class ServicioIA:
    """Orquesta interprete y nodos. No depende de cual interprete sea.

    Recibe el proveedor de las vistas (ProveedorGRPC o ProveedorDemo), no
    el cliente gRPC directo: asi la pantalla de IA tambien funciona en modo
    demo, sin nodos levantados.
    """

    def __init__(self, proveedor, interprete: InterpretePregunta | None = None,
                 respaldo: InterpretePregunta | None = None) -> None:
        self.proveedor = proveedor
        self.interprete = interprete
        self.respaldo = respaldo

    def responder(self, pregunta: str) -> RespuestaIA:
        pregunta = (pregunta or "").strip()
        if not pregunta:
            return RespuestaIA(
                "Escriba una pregunta para consultar el catalogo.",
                IntencionConsulta(tipo="DESCONOCIDA"), [])

        intencion, aviso = self._interpretar(pregunta)

        if intencion.tipo in ("PRESTAMOS_USUARIO", "PRESTAMOS_VENCIDOS"):
            return RespuestaIA(
                "Entendi que pregunta por prestamos. Esta pantalla consulta "
                "el catalogo y la disponibilidad; los prestamos se consultan "
                "desde la pantalla de Prestamos.",
                intencion, [], aviso)

        if intencion.tipo not in TIPOS_ATENDIDOS:
            return RespuestaIA(
                "No entendi la pregunta. Puede preguntar por un titulo, por "
                "un autor o por un ISBN. Por ejemplo: tienen Cien anos de "
                "soledad?",
                intencion, [], aviso)

        resultados, criterio = self._buscar(intencion)
        return RespuestaIA(self._redactar(intencion, resultados, criterio),
                           intencion, resultados, aviso)

    # --- Interpretacion ---------------------------------------------------

    def _interpretar(self, pregunta: str) -> tuple[IntencionConsulta, str | None]:
        if self.interprete is not None:
            try:
                return self.interprete.interpretar(pregunta), None
            # Se captura Exception a proposito: el respaldo existe para
            # absorber cualquier falla del interprete primario, sea de red,
            # de cuota o de formato. Si no hay respaldo, el error sube.
            except Exception as exc:
                if self.respaldo is None:
                    raise
                motivo = str(exc).strip() or exc.__class__.__name__
                return self.respaldo.interpretar(pregunta), (
                    "El modelo de lenguaje no respondio, asi que interpreto "
                    f"la pregunta el motor de reglas local. ({motivo})")

        if self.respaldo is not None:
            return self.respaldo.interpretar(pregunta), (
                "No hay modelo de lenguaje configurado: la pregunta la "
                "interpreto el motor de reglas local.")

        raise NotImplementedError(
            "ServicioIA necesita un interprete o un respaldo.")

    # --- Consulta a los nodos --------------------------------------------

    def _buscar(self, intencion: IntencionConsulta) -> tuple[list[dict[str, Any]], str]:
        """Prueba los criterios por orden de precision hasta encontrar algo.

        El proveedor recibe un solo texto y lo compara contra titulo, autor
        e ISBN, asi que los criterios se prueban uno a uno: primero el ISBN,
        que es exacto, luego el titulo y por ultimo el autor.
        """
        criterios = [c for c in (intencion.isbn, intencion.titulo,
                                 intencion.autor) if c]
        if not criterios:
            return [], ""

        for criterio in criterios:
            try:
                resultados = self.proveedor.disponibilidad(criterio)
            except Exception as exc:
                raise ErrorConsulta(
                    f"No se pudo consultar a los nodos: {exc}") from exc
            if resultados:
                return resultados, criterio

        return [], criterios[0]

    # --- Redaccion --------------------------------------------------------

    def _redactar(self, intencion: IntencionConsulta,
                  resultados: list[dict[str, Any]], criterio: str) -> str:
        """Redacta la respuesta usando UNICAMENTE datos reales de los nodos."""
        if not resultados:
            lineas = [f"No encontre nada que coincida con '{criterio}' en "
                      "ninguna de las tres bibliotecas."
                      if criterio else
                      "No pude extraer un titulo, un autor ni un ISBN de la "
                      "pregunta."]
            if intencion.confianza < UMBRAL_CONFIANZA:
                lineas += ["", "Puede que no haya entendido bien la pregunta. "
                               "Pruebe escribiendo solo el titulo o el autor."]
            return "\n".join(lineas)

        if intencion.tipo == "SEDE":
            return _por_sede(resultados)
        return _por_libro(resultados)


def _por_libro(resultados: list[dict[str, Any]]) -> str:
    lineas = []
    for fila in resultados:
        if fila.get("disponibles", 0) > 0:
            lineas.append(
                f"- {fila['titulo']} ({fila['autor']}): "
                f"{fila['disponibles']} disponible(s) en {fila['biblioteca']}.")
        else:
            lineas.append(
                f"- {fila['titulo']} ({fila['autor']}): sin ejemplares "
                f"disponibles en {fila['biblioteca']}.")
    return "\n".join(lineas)


def _por_sede(resultados: list[dict[str, Any]]) -> str:
    """Agrupa por biblioteca: la pregunta era donde esta, no cuantos hay."""
    sedes: dict[str, list[dict[str, Any]]] = {}
    for fila in resultados:
        sedes.setdefault(fila["biblioteca"], []).append(fila)

    lineas = []
    for biblioteca in sorted(sedes):
        disponibles = [f for f in sedes[biblioteca]
                       if f.get("disponibles", 0) > 0]
        if disponibles:
            lineas.append(f"En {biblioteca}:")
            for fila in disponibles:
                lineas.append(f"    - {fila['titulo']} ({fila['autor']}): "
                              f"{fila['disponibles']} disponible(s).")
        else:
            titulos = ", ".join(sorted({f["titulo"] for f in sedes[biblioteca]}))
            lineas.append(f"En {biblioteca} esta {titulos}, pero sin "
                          "ejemplares disponibles en este momento.")
    return "\n".join(lineas)
