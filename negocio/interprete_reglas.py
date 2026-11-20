"""Interprete de preguntas basado en reglas locales.

Cumple el mismo contrato que InterpreteLLM y no usa la red. Es el respaldo:
entra cuando no hay clave configurada, cuando no hay internet o cuando el
modelo falla, para que la pantalla siga respondiendo.

Acierta menos que el modelo y lo dice: devuelve una confianza mas baja a
proposito y deja origen en "reglas", para que la pantalla muestre cual de
los dos interpreto la pregunta.
"""

from __future__ import annotations

import re
import unicodedata

from negocio.servicio_ia import IntencionConsulta

LARGO_MAXIMO = 120

# Un ISBN: 10 o 13 digitos, admitiendo guiones y la X final del ISBN-10.
ISBN = re.compile(r"\b(\d[\d\-]{8,16}[\dXx])\b")

# Un titulo entre comillas se toma tal cual, sin adivinar nada.
COMILLAS = re.compile(r"[\"'«“]([^\"'»”]{2,})[\"'»”]")

MARCA_VENCIDOS = ("vencid", "atrasad", "en mora", "retrasad", "sin devolver")

MARCA_SEDE = ("en que biblioteca", "en que sede", "en que nodo",
              "en cual biblioteca", "en cual sede", "que biblioteca tiene",
              "donde esta", "donde queda", "donde encuentro",
              "donde puedo encontrar", "donde consigo")

# El nombre del lector puede ir antes o despues de la marca:
#   "¿Que tiene prestado Juan Perez?"      -> va despues
#   "¿Juan Perez tiene prestado algo?"     -> va antes
# Por eso se prueban los dos lados y gana el que deje un nombre utilizable.
MARCA_PRESTADO = ("tiene prestado", "tienen prestado", "tiene prestados",
                  "tiene en prestamo", "prestamos de", "prestamos del",
                  "presto a", "lleva prestado", "debe el")

MARCA_AUTOR = ("algo de ", "libros de ", "libro de ", "obras de ",
               "escrito por ", "escritos por ", "del autor ",
               "de la autora ", "autoria de ")

# Senales de que la pregunta trata de la biblioteca. Sin ninguna de estas,
# el interprete de reglas no tiene forma de distinguir un titulo de una
# frase cualquiera, asi que baja la confianza en vez de fingir certeza.
MARCA_BIBLIOTECA = ("tienen", "tiene", "hay", "donde", "disponib", "busco",
                    "buscar", "necesito", "quiero", "biblioteca", "sede",
                    "libro", "ejemplar", "prestad", "prestamo", "catalogo",
                    "autor", "titulo", "isbn", "existe", "consigo",
                    "encontrar", "encuentro", "vencid", "devolver")

# Palabras que no aportan al criterio de busqueda cuando van al principio
# de la pregunta. OJO: solo se quitan del inicio, nunca del interior.
PALABRAS_VACIAS = {
    "tienen", "tiene", "hay", "donde", "puedo", "encontrar", "algo",
    "de", "del", "la", "el", "los", "las", "un", "una", "necesito",
    "busco", "buscar", "quiero", "disponible", "disponibles", "libro",
    "libros", "ejemplar", "ejemplares", "por", "favor", "esta", "estan",
    "que", "con", "cual", "cuales", "cuantos", "cuantas", "me", "si",
    "en", "y", "o", "a", "para", "biblioteca", "sede", "nodo", "consigo",
    "existe", "tendran", "tendras", "sabes",
}


class InterpreteReglas:
    """Cumple el contrato InterpretePregunta sin salir a la red."""

    def interpretar(self, pregunta: str) -> IntencionConsulta:
        original = (pregunta or "").strip()
        if not original:
            return IntencionConsulta(tipo="DESCONOCIDA", origen="reglas")

        # El texto plano sirve SOLO para localizar los patrones. Conserva
        # la longitud y las posiciones del original, asi que lo que se
        # devuelve se recorta del original y mantiene tildes y mayusculas.
        plano = _plano(original)

        # 1. Un ISBN no admite ambiguedad.
        hallado = ISBN.search(plano)
        if hallado:
            digitos = "".join(c for c in hallado.group(1)
                              if c.isdigit() or c in "Xx")
            if len(digitos) in (10, 13):
                return IntencionConsulta(isbn=digitos, tipo="DISPONIBILIDAD",
                                         confianza=0.9, origen="reglas")

        # 2. Prestamos vencidos, con o sin lector.
        if _alguna(plano, MARCA_VENCIDOS):
            return IntencionConsulta(
                lector=_lector(original, plano),
                tipo="PRESTAMOS_VENCIDOS", confianza=0.7, origen="reglas")

        # 3. Que tiene prestado una persona.
        lector = _lector(original, plano)
        if lector:
            return IntencionConsulta(lector=lector, tipo="PRESTAMOS_USUARIO",
                                     confianza=0.6, origen="reglas")

        # 4. Sede o disponibilidad: mismo criterio, distinta pregunta.
        tipo = "SEDE" if _alguna(plano, MARCA_SEDE) else "DISPONIBILIDAD"

        autor = _tras_marca(original, plano, MARCA_AUTOR)
        titulo = _entre_comillas(original)
        if not titulo and not autor:
            titulo = _sin_encabezado(original, plano)

        if not (titulo or autor):
            return IntencionConsulta(tipo="DESCONOCIDA", confianza=0.3,
                                     origen="reglas")

        # Sin ninguna senal de biblioteca, esto puede no ser una pregunta
        # del catalogo. Una sola palabra ("hola") se descarta; una frase
        # mas larga se intenta, pero con la confianza por el piso para que
        # ServicioIA pueda avisar que quizas no entendio la pregunta.
        if not _alguna(plano, MARCA_BIBLIOTECA):
            if len((titulo or autor or "").split()) < 2:
                return IntencionConsulta(tipo="DESCONOCIDA", confianza=0.3,
                                         origen="reglas")
            return IntencionConsulta(titulo=titulo, autor=autor, tipo=tipo,
                                     confianza=0.25, origen="reglas")

        return IntencionConsulta(titulo=titulo, autor=autor, tipo=tipo,
                                 confianza=0.55, origen="reglas")


# --- Auxiliares -----------------------------------------------------------

def _plano(texto: str) -> str:
    """Minusculas y sin tildes, conservando longitud y posiciones.

    Se normaliza caracter por caracter a proposito: asi "anos" y "años"
    ocupan lo mismo y un indice hallado en el texto plano sirve para
    recortar el texto original.
    """
    salida = []
    for caracter in texto.lower():
        descompuesto = unicodedata.normalize("NFD", caracter)
        salida.append(descompuesto[0] if descompuesto else caracter)
    return "".join(salida)


def _alguna(plano: str, marcas) -> bool:
    return any(marca in plano for marca in marcas)


def _tras_marca(original: str, plano: str, marcas) -> str | None:
    """Devuelve lo que sigue a la primera marca encontrada."""
    for marca in marcas:
        posicion = plano.find(marca)
        if posicion == -1:
            continue
        return _recortar(original[posicion + len(marca):])
    return None


def _lector(original: str, plano: str) -> str | None:
    """Busca el nombre del lector a los dos lados de la marca.

    Se prueba primero lo que va ANTES: en "¿Que tiene prestado Juan Perez?"
    lo anterior son puras palabras vacias y queda vacio, asi que se pasa a
    lo de despues. En "¿Juan Perez tiene prestado algo?" lo anterior es el
    nombre y gana.
    """
    for marca in MARCA_PRESTADO:
        posicion = plano.find(marca)
        if posicion == -1:
            continue
        antes = _recortar(original[:posicion])
        if antes and not _es_ruido(antes):
            return antes
        despues = _recortar(original[posicion + len(marca):])
        if despues and not _es_ruido(despues):
            return despues
        return None
    return None


def _es_ruido(candidato: str) -> bool:
    """Descarta un candidato que en realidad era parte de la pregunta."""
    llano = _plano(candidato)
    return any(marca in llano for marca in MARCA_VENCIDOS)


def _primera_clausula(texto: str) -> str:
    """Corta en la primera coma o signo de pregunta interno.

    "Necesito Clean Code, ¿hay disponible?" tiene que dar "Clean Code",
    no "Clean Code, ¿hay disponible".
    """
    for signo in (",", ";", "¿", "?", "!", "¡", " - "):
        corte = texto.find(signo)
        if corte > 0:
            texto = texto[:corte]
    return texto


def _entre_comillas(original: str) -> str | None:
    hallado = COMILLAS.search(original)
    if not hallado:
        return None
    return hallado.group(1).strip()[:LARGO_MAXIMO] or None


def _sin_encabezado(original: str, plano: str) -> str | None:
    """Quita el encabezado de la pregunta y conserva el resto tal cual.

    Las palabras vacias se quitan SOLO del inicio. Si se quitaran tambien
    del interior, "Cien años de soledad" quedaria como "Cien años soledad",
    que no es subcadena del titulo y la busqueda del proveedor no lo
    encuentra. Ese es justamente el error que tenia _extraer_criterio.
    """
    palabras = original.split()
    planas = plano.split()
    indice = 0
    while indice < len(palabras) and _letras(planas[indice]) in PALABRAS_VACIAS:
        indice += 1
    resto = _primera_clausula(" ".join(palabras[indice:]))
    return _recortar(resto)


def _recortar(texto: str) -> str | None:
    """Limpia signos y palabras vacias del borde izquierdo."""
    texto = texto.strip(" ¿?¡!.,;:\"'«»“”")
    palabras = texto.split()
    while palabras and _letras(_plano(palabras[0])) in PALABRAS_VACIAS:
        palabras.pop(0)
    while palabras and not _letras(_plano(palabras[-1])) \
            and not palabras[-1][-1:].isdigit():
        palabras.pop()
    return " ".join(palabras)[:LARGO_MAXIMO].strip() or None


def _letras(palabra: str) -> str:
    return "".join(c for c in palabra if c.isalnum())
