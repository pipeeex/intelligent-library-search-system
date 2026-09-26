"""Hueco reservado para el modulo de IA.

Todavia no esta implementado: aqui queda definida la interfaz para que el
resto del backend no cambie cuando se agregue (reglas locales o un LLM).

El flujo previsto es:

    pregunta en lenguaje natural
        -> IntencionConsulta (titulo / autor / isbn)
        -> ClienteDistribuido.resumen_disponibilidad(...)
        -> respuesta redactada SOLO con los datos devueltos por los nodos
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class IntencionConsulta:
    """Lo que se extrae de la pregunta del usuario."""

    titulo: str | None = None
    autor: str | None = None
    isbn: str | None = None
    tipo: str = "DISPONIBILIDAD"
    confianza: float = 0.0


@dataclass
class RespuestaIA:
    texto: str
    intencion: IntencionConsulta
    resultados: list[dict[str, Any]]


class InterpretePregunta(Protocol):
    """Contrato que debera cumplir el interprete (reglas locales o LLM)."""

    def interpretar(self, pregunta: str) -> IntencionConsulta: ...


class IAService:
    """Orquestador. Pendiente de implementar el interprete."""

    def __init__(self, cliente_distribuido, interprete: InterpretePregunta | None = None):
        self.cliente = cliente_distribuido
        self.interprete = interprete

    def responder(self, pregunta: str) -> RespuestaIA:
        if self.interprete is None:
            raise NotImplementedError(
                "El modulo de IA aun no esta implementado. "
                "Inyecta un InterpretePregunta en IAService."
            )
        intencion = self.interprete.interpretar(pregunta)
        resultados = self.cliente.resumen_disponibilidad(
            titulo=intencion.titulo, autor=intencion.autor, isbn=intencion.isbn
        )
        return RespuestaIA(
            texto=self._redactar(intencion, resultados),
            intencion=intencion,
            resultados=resultados,
        )

    @staticmethod
    def _redactar(intencion: IntencionConsulta, resultados: list[dict[str, Any]]) -> str:
        """Redacta la respuesta usando UNICAMENTE datos reales de los nodos."""
        if not resultados:
            return "No encontre ese libro en ninguna de las tres bibliotecas."
        lineas = []
        for fila in resultados:
            if fila["disponibles"] > 0:
                lineas.append(
                    f"- {fila['titulo']} ({fila['autor']}): "
                    f"{fila['disponibles']} disponible(s) en {fila['biblioteca']}."
                )
            else:
                lineas.append(
                    f"- {fila['titulo']} ({fila['autor']}): sin ejemplares "
                    f"disponibles en {fila['biblioteca']}."
                )
        return "\n".join(lineas)
