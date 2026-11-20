from __future__ import annotations

import json
import urllib.error
import urllib.request

from configuracion import ajustes
from negocio.servicio_ia import TIPOS, IntencionConsulta

LARGO_MAXIMO = 120  # recorte de los campos que devuelve el modelo


class ErrorInterprete(RuntimeError):
    """El modelo no pudo interpretar la pregunta: red, cuota o formato."""
    def __init__(self, mensaje: str, codigo: int | None = None) -> None:
        super().__init__(mensaje)
        self.codigo = codigo

MOTIVOS = {
    400: "El modelo rechazo la peticion. Revisa IA_MODELO en el .env.",
    401: "La clave no es valida. Revisa IA_API_KEY en el .env.",
    403: "La clave no tiene permiso. Si es de Google, restringela a "
         "'Gemini API only' en AI Studio.",
    404: "La ruta no existe. Revisa IA_BASE_URL en el .env.",
    429: "Se agoto la cuota. En el plan gratuito de Gemini el cupo diario "
         "se reinicia a medianoche hora del Pacifico.",
}


INSTRUCCIONES = """\
Eres el interprete de un sistema de bibliotecas. Tu unica tarea es traducir
la pregunta del usuario a un objeto JSON. No respondas la pregunta y no
inventes titulos, autores ni disponibilidad: no tienes acceso al catalogo.

Devuelve EXCLUSIVAMENTE un objeto JSON con estas claves:

  "tipo"      uno de: DISPONIBILIDAD, SEDE, PRESTAMOS_USUARIO,
              PRESTAMOS_VENCIDOS, DESCONOCIDA
  "titulo"    titulo del libro mencionado, o null
  "autor"     nombre del autor mencionado, o null
  "isbn"      ISBN mencionado, solo digitos, o null
  "lector"    nombre o documento del lector mencionado, o null
  "confianza" numero entre 0 y 1

Como elegir el tipo:
  DISPONIBILIDAD      pregunta si hay un libro o cuantos ejemplares hay.
  SEDE                pregunta en que biblioteca o sede esta un libro.
  PRESTAMOS_USUARIO   pregunta que tiene prestado una persona.
  PRESTAMOS_VENCIDOS  pregunta por prestamos vencidos o atrasados.
  DESCONOCIDA         la pregunta no es sobre la biblioteca, o no se entiende.

Copia los nombres tal como los escribio el usuario: no los corrijas, no los
completes y no los traduzcas. Si un dato no aparece en la pregunta, pon null.
No agregues explicaciones ni texto fuera del JSON.

Ejemplos:
P: Tienen Cien anos de soledad?
R: {"tipo":"DISPONIBILIDAD","titulo":"Cien anos de soledad","autor":null,"isbn":null,"lector":null,"confianza":0.95}
P: En que biblioteca esta Clean Code?
R: {"tipo":"SEDE","titulo":"Clean Code","autor":null,"isbn":null,"lector":null,"confianza":0.93}
P: Hay algo de Borges?
R: {"tipo":"DISPONIBILIDAD","titulo":null,"autor":"Borges","isbn":null,"lector":null,"confianza":0.88}
P: Que tiene prestado Juan Perez?
R: {"tipo":"PRESTAMOS_USUARIO","titulo":null,"autor":null,"isbn":null,"lector":"Juan Perez","confianza":0.9}
P: Cuales prestamos estan vencidos?
R: {"tipo":"PRESTAMOS_VENCIDOS","titulo":null,"autor":null,"isbn":null,"lector":null,"confianza":0.92}
P: Cuanto es 2 mas 2?
R: {"tipo":"DESCONOCIDA","titulo":null,"autor":null,"isbn":null,"lector":null,"confianza":0.99}
"""


class InterpreteLLM:
    """Cumple el contrato InterpretePregunta usando un modelo remoto."""
    def __init__(self, base_url: str | None = None, modelo: str | None = None,
                 api_key: str | None = None, timeout: int | None = None,
                 esfuerzo: str | None = None) -> None:
        self.base_url = (base_url or ajustes.IA_BASE_URL).rstrip("/")
        self.modelo = modelo or ajustes.IA_MODELO
        self.timeout = timeout or ajustes.IA_TIMEOUT
        self.esfuerzo = ajustes.IA_ESFUERZO if esfuerzo is None else esfuerzo
        self._clave = api_key or ajustes.IA_API_KEY
        self._extras = True

        if not (self.base_url and self.modelo and self._clave):
            raise ErrorInterprete(
                "Falta IA_BASE_URL, IA_MODELO o IA_API_KEY en el .env.")

    def interpretar(self, pregunta: str) -> IntencionConsulta:
        minimo = {
            "model": self.modelo,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": INSTRUCCIONES},
                {"role": "user", "content": pregunta},
            ],
        }
        cuerpo = dict(minimo)
        if self._extras:
            cuerpo["response_format"] = {"type": "json_object"}
            if self.esfuerzo:
                cuerpo["reasoning_effort"] = self.esfuerzo

        try:
            return _a_intencion(self._post(cuerpo))
        except ErrorInterprete as exc:
            # Solo se reintenta cuando el proveedor rechazo la forma de la
            # peticion. Un 429 o un timeout no se reintentan: repetirlos
            # no arregla nada y duplica la espera.
            if not self._extras or exc.codigo != 400:
                raise
            self._extras = False
            return _a_intencion(self._post(minimo))

    def _post(self, cuerpo: dict) -> str:
        peticion = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(cuerpo).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._clave}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(peticion, timeout=self.timeout) as r:
                datos = json.loads(r.read().decode("utf-8"))
        # El "from None" corta la cadena de excepciones a proposito: evita
        # que un traceback mostrado en pantalla arrastre el objeto de la
        # peticion, que lleva la cabecera con la clave.
        except urllib.error.HTTPError as exc:
            raise ErrorInterprete(
                MOTIVOS.get(exc.code, f"El modelo respondio {exc.code}."),
                codigo=exc.code,
            ) from None
        except urllib.error.URLError as exc:
            raise ErrorInterprete(
                f"Sin conexion con el modelo: {exc.reason}") from None
        except (TimeoutError, OSError) as exc:
            raise ErrorInterprete(
                f"El modelo no respondio a tiempo: {exc}") from None
        except json.JSONDecodeError:
            raise ErrorInterprete(
                "El proveedor no devolvio JSON. Revisa IA_BASE_URL.") from None

        try:
            return datos["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise ErrorInterprete(
                "La respuesta del modelo no trae el campo esperado.") from None



# --- Traduccion de la respuesta del modelo -------------------------------
# Todo lo que devuelve el modelo se trata como dato sospechoso: se valida
# campo por campo y se recorta. Un modelo puede devolver un tipo que no
# existe, un numero donde va texto, o mil caracteres de titulo.

def _a_intencion(crudo: str) -> IntencionConsulta:
    try:
        datos = json.loads(_solo_json(crudo))
    except (json.JSONDecodeError, ValueError):
        raise ErrorInterprete(
            "El modelo no devolvio un JSON que se pueda leer.") from None
    if not isinstance(datos, dict):
        raise ErrorInterprete("El modelo no devolvio un objeto JSON.")

    tipo = str(datos.get("tipo", "")).strip().upper()
    if tipo not in TIPOS:
        tipo = "DESCONOCIDA"

    isbn = _texto(datos, "isbn")
    if isbn:
        isbn = "".join(c for c in isbn if c.isdigit() or c in "Xx") or None

    return IntencionConsulta(
        titulo=_texto(datos, "titulo"),
        autor=_texto(datos, "autor"),
        isbn=isbn,
        lector=_texto(datos, "lector"),
        tipo=tipo,
        confianza=_confianza(datos.get("confianza")),
        origen="llm",
    )


def _solo_json(crudo: str) -> str:
    """Aisla el objeto JSON. Los modelos suelen envolverlo en ```json."""
    texto = (crudo or "").strip()
    inicio, fin = texto.find("{"), texto.rfind("}")
    if inicio == -1 or fin <= inicio:
        raise ValueError("sin objeto JSON")
    return texto[inicio:fin + 1]


def _texto(datos: dict, clave: str) -> str | None:
    valor = datos.get(clave)
    if not isinstance(valor, str):
        return None
    return valor.strip()[:LARGO_MAXIMO] or None


def _confianza(valor) -> float:
    try:
        return max(0.0, min(float(valor), 1.0))
    except (TypeError, ValueError):
        return 0.0