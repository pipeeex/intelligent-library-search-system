"""Pantalla reservada para la consulta en lenguaje natural.

El modulo de Inteligencia Artificial esta documentado pero todavia no
implementado. La pantalla queda armada para que al conectarlo solo haya que
reemplazar el metodo responder().
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from presentacion.escritorio import estilos as E
from presentacion.escritorio.componentes import Aviso, Tarjeta, encabezado

EJEMPLOS = [
    "¿Tienen Cien anos de soledad?",
    "¿Donde puedo encontrar algo de Borges?",
    "Necesito Clean Code, ¿hay disponible?",
]


class VistaConsultaIA(ttk.Frame):
    def __init__(self, maestro, proveedor):
        super().__init__(maestro, style="Fondo.TFrame", padding=(26, 22))
        self.proveedor = proveedor

        encabezado(self, "Consulta en lenguaje natural",
                   "Pantalla preparada para el modulo de Inteligencia Artificial.")

        self.aviso = Aviso(self)
        self.aviso.mostrar(
            "El interprete de preguntas aun no esta implementado. Mientras tanto, "
            "la pantalla busca por coincidencia de texto sobre los datos reales de "
            "los nodos y senala que la respuesta no proviene del modulo de IA.",
            "info")

        tarjeta = Tarjeta(self, "Escriba su pregunta",
                          "La respuesta se construye unicamente con los datos que "
                          "devuelven las bibliotecas. El sistema nunca estima la "
                          "disponibilidad.")
        tarjeta.colocar(fill="x", pady=(0, 16))

        fila = ttk.Frame(tarjeta, style="Tarjeta.TFrame")
        fila.pack(fill="x")
        self.entrada = ttk.Entry(fila, width=60)
        self.entrada.pack(side="left", fill="x", expand=True)
        self.entrada.bind("<Return>", lambda _e: self.responder())
        ttk.Button(fila, text="Preguntar", style="Primario.TButton",
                   command=self.responder).pack(side="left", padx=(12, 0))

        ejemplos = ttk.Frame(tarjeta, style="Tarjeta.TFrame")
        ejemplos.pack(fill="x", pady=(12, 0))
        ttk.Label(ejemplos, text="Ejemplos:", style="Ayuda.TLabel").pack(side="left")
        for texto in EJEMPLOS:
            enlace = tk.Label(ejemplos, text=texto, background=E.BLANCO,
                              foreground=E.AZUL, font=E.fuente(9), cursor="hand2")
            enlace.pack(side="left", padx=(10, 0))
            enlace.bind("<Button-1>", lambda _e, t=texto: self._usar_ejemplo(t))

        salida = Tarjeta(self, "Respuesta")
        salida.colocar(fill="both", expand=True)
        self.texto = tk.Text(salida, height=12, wrap="word", relief="flat",
                             background=E.BLANCO, foreground=E.TEXTO,
                             font=E.fuente(10), padx=4, pady=4)
        self.texto.pack(fill="both", expand=True)
        self.texto.configure(state="disabled")

    def _usar_ejemplo(self, texto: str) -> None:
        self.entrada.delete(0, "end")
        self.entrada.insert(0, texto)
        self.responder()

    def responder(self) -> None:
        pregunta = self.entrada.get().strip()
        if not pregunta:
            self._escribir("Escriba una pregunta para consultar el catalogo.")
            return

        criterio = _extraer_criterio(pregunta)
        try:
            filas = self.proveedor.disponibilidad(criterio)
        except Exception as exc:  # pragma: no cover
            self._escribir(f"No se pudo consultar a los nodos: {exc}")
            return

        lineas = [f"Pregunta: {pregunta}",
                  f"Criterio de busqueda extraido: '{criterio}'", ""]
        if not filas:
            lineas.append("No encontre ese libro en ninguna de las tres bibliotecas.")
        else:
            for fila in filas:
                if fila.get("disponibles", 0) > 0:
                    lineas.append(
                        f"- {fila['titulo']} ({fila['autor']}): "
                        f"{fila['disponibles']} disponible(s) en {fila['biblioteca']}.")
                else:
                    lineas.append(
                        f"- {fila['titulo']} ({fila['autor']}): sin ejemplares "
                        f"disponibles en {fila['biblioteca']}.")
        lineas.append("")
        lineas.append("Nota: busqueda por coincidencia de texto. El interprete de "
                      "lenguaje natural se incorporara en una etapa posterior.")
        self._escribir("\n".join(lineas))

    def _escribir(self, texto: str) -> None:
        self.texto.configure(state="normal")
        self.texto.delete("1.0", "end")
        self.texto.insert("1.0", texto)
        self.texto.configure(state="disabled")


PALABRAS_VACIAS = {
    "tienen", "tiene", "hay", "donde", "puedo", "encontrar", "algo", "de", "del",
    "la", "el", "los", "las", "un", "una", "necesito", "busco", "quiero",
    "disponible", "disponibles", "libro", "ejemplar", "por", "favor", "esta",
    "que", "con",
}


def _extraer_criterio(pregunta: str) -> str:
    limpio = pregunta.lower()
    for signo in "¿?¡!.,;:":
        limpio = limpio.replace(signo, " ")
    palabras = [p for p in limpio.split() if p not in PALABRAS_VACIAS and len(p) > 2]
    return " ".join(palabras[:4])
