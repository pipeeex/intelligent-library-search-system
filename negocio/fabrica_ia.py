"""Armado del modulo de IA.

Separa "como se arma" de "que hace", para que la aplicacion no tenga que
saber que interpretes existen ni como se configuran. Un solo punto de
entrada:

    servicio, aviso = crear_servicio_ia(proveedor)

La politica de armado es:

  - Si el .env tiene IA_BASE_URL, IA_MODELO e IA_API_KEY, el interprete
    primario es el modelo de lenguaje.
  - El interprete de reglas locales queda SIEMPRE como respaldo, incluso
    cuando el modelo esta configurado: si la llamada falla por red o por
    cuota, la pantalla sigue respondiendo.
  - Si el modelo no esta configurado, las reglas pasan a ser el unico
    interprete y el aviso lo dice.

El aviso que devuelve es texto para mostrarle al usuario, no un error.
"""

from __future__ import annotations

from negocio.interprete_reglas import InterpreteReglas
from negocio.servicio_ia import ServicioIA


def crear_servicio_ia(proveedor) -> tuple[ServicioIA, str]:
    """Devuelve (servicio, aviso) listo para la pantalla de consulta."""
    reglas = InterpreteReglas()
    primario = None
    aviso = ""

    try:
        from negocio.interprete_llm import ErrorInterprete, InterpreteLLM
    except ImportError as exc:  # pragma: no cover
        aviso = (f"No se pudo cargar el interprete del modelo ({exc}). "
                 "Las preguntas se interpretan con reglas locales.")
    else:
        try:
            primario = InterpreteLLM()
        except ErrorInterprete as exc:
            # Falta configuracion en el .env. No es un fallo: el sistema
            # funciona igual con reglas, solo acierta menos.
            aviso = (f"{exc} Mientras tanto, las preguntas se interpretan "
                     "con reglas locales.")

    if primario is not None:
        aviso = (f"Las preguntas las interpreta el modelo {primario.modelo}. "
                 "Si no responde, entran las reglas locales.")

    servicio = ServicioIA(proveedor, interprete=primario, respaldo=reglas)
    return servicio, aviso
