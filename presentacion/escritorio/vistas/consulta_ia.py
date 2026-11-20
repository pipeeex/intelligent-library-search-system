"""Pantalla de consulta en lenguaje natural.

La pregunta la interpreta el modulo de IA (ServicioIA): el modelo de
lenguaje cuando esta configurado en el .env, y las reglas locales como
respaldo. La respuesta se redacta UNICAMENTE con los datos que devuelven
los nodos; el interprete no ve el catalogo.

La llamada al modelo tarda segundos, asi que corre en un hilo aparte.
Tkinter no es seguro desde otros hilos, y eso incluye programar tareas: si
el hilo de trabajo llama a after(), Tcl falla con "main thread is not in
main loop". Por eso el hilo deja el resultado en una cola y es el hilo de
la interfaz el que la revisa cada 100 ms. El hilo de trabajo no toca
ningun widget ni la cola de Tk.
"""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import ttk

from negocio.servicio_ia import ErrorConsulta
from presentacion.escritorio import estilos as E
from presentacion.escritorio.componentes import Aviso, FilaFluida, Tarjeta, encabezado

# Los titulos van con sus tildes y su ene: la busqueda compara el texto
# contra el del catalogo, y "anos" no coincide con "años".
EJEMPLOS = [
    "¿Tienen Cien años de soledad?",
    "¿Dónde puedo encontrar algo de Borges?",
    "Necesito Clean Code, ¿hay disponible?",
]


class VistaConsultaIA(ttk.Frame):
    def __init__(self, maestro, proveedor, servicio=None, aviso_ia: str = ""):
        super().__init__(maestro, style="Fondo.TFrame", padding=(26, 22))
        self.proveedor = proveedor
        self.servicio = servicio
        # Evita que dos clics seguidos lancen dos consultas a la vez.
        self._ocupado = False
        # Por aqui el hilo de trabajo entrega su resultado.
        self._cola: queue.Queue = queue.Queue()

        encabezado(self, "Consulta en lenguaje natural",
                   "Pregunte por un titulo, por un autor o por un ISBN.")

        self.aviso = Aviso(self)
        if servicio is None:
            self.aviso.mostrar(
                "El modulo de IA no se pudo iniciar. La pantalla queda "
                "disponible pero no puede interpretar preguntas.", "aviso")
        elif aviso_ia:
            self.aviso.mostrar(aviso_ia, "info")

        tarjeta = Tarjeta(self, "Escriba su pregunta",
                          "La respuesta se construye unicamente con los datos que "
                          "devuelven las bibliotecas. El sistema nunca estima la "
                          "disponibilidad.")
        tarjeta.colocar(fill="x", pady=(0, 16))

        fila = ttk.Frame(tarjeta, style="Tarjeta.TFrame")
        fila.pack(fill="x")
        self.boton = ttk.Button(fila, text="Preguntar", style="Primario.TButton",
                                command=self.responder)
        self.boton.pack(side="right", padx=(12, 0))
        self.entrada = ttk.Entry(fila)
        self.entrada.pack(side="left", fill="x", expand=True)
        self.entrada.bind("<Return>", lambda _e: self.responder())

        # Los ejemplos van en una fila fluida: si la ventana es angosta o la
        # pantalla agranda la letra, bajan al renglon siguiente en vez de
        # quedar cortados contra el borde de la tarjeta.
        ejemplos = FilaFluida(tarjeta)
        ejemplos.pack(fill="x", pady=(E.px(12), 0))
        ejemplos.agregar(ttk.Label(ejemplos, text="Ejemplos:", style="Ayuda.TLabel"))
        for texto in EJEMPLOS:
            enlace = tk.Label(ejemplos, text=texto, background=E.BLANCO,
                              foreground=E.AZUL, font=E.fuente(E.TAM_AYUDA),
                              cursor="hand2")
            enlace.bind("<Button-1>", lambda _e, t=texto: self._usar_ejemplo(t))
            ejemplos.agregar(enlace)

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

    # --- Hilo de la interfaz ---------------------------------------------

    def responder(self) -> None:
        if self._ocupado:
            return

        pregunta = self.entrada.get().strip()
        if not pregunta:
            self._escribir("Escriba una pregunta para consultar el catalogo.")
            return

        if self.servicio is None:
            self._escribir("El modulo de IA no esta disponible en esta "
                           "instalacion. Revise la configuracion del .env.")
            return

        self._ocupado = True
        self.boton.configure(state="disabled", text="Consultando...")
        self._escribir(f"Pregunta: {pregunta}\n\nConsultando...")

        # daemon=True para que un hilo colgado no impida cerrar la ventana.
        threading.Thread(target=self._trabajar, args=(pregunta,),
                         daemon=True).start()
        self._vigilar()

    def _vigilar(self) -> None:
        """Revisa la cola desde el hilo de la interfaz, cada 100 ms.

        Es el hilo de la interfaz el que pregunta; el de trabajo nunca
        llama a after(), porque Tcl no lo admite desde otro hilo.
        """
        try:
            if not self.winfo_exists():
                return
            try:
                pendiente = self._cola.get_nowait()
            except queue.Empty:
                self.after(100, self._vigilar)
                return
        except tk.TclError:
            # La vista se destruyo (el usuario cambio de pantalla).
            return
        self._terminar(*pendiente)

    def _terminar(self, pregunta: str, estado: str, dato) -> None:
        """Ya en el hilo de la interfaz: pinta el resultado."""
        self._ocupado = False
        self.boton.configure(state="normal", text="Preguntar")
        if estado == "error":
            self._escribir(f"Pregunta: {pregunta}\n\n{dato}")
        else:
            self._escribir(_formatear(pregunta, dato))

    def _escribir(self, texto: str) -> None:
        self.texto.configure(state="normal")
        self.texto.delete("1.0", "end")
        self.texto.insert("1.0", texto)
        self.texto.configure(state="disabled")

    # --- Hilo de trabajo --------------------------------------------------

    def _trabajar(self, pregunta: str) -> None:
        """Corre FUERA del hilo de la interfaz.

        No toca ningun widget y no llama a after(): deja el resultado en la
        cola y termina. Si la vista ya no existe, nadie lo recoge y no pasa
        nada.
        """
        try:
            estado, dato = "ok", self.servicio.responder(pregunta)
        except ErrorConsulta as exc:
            estado, dato = "error", str(exc)
        except Exception as exc:  # pragma: no cover
            # Cualquier otra falla se muestra en la pantalla en vez de
            # morir en silencio dentro del hilo, donde nadie la veria.
            estado, dato = "error", f"{exc.__class__.__name__}: {exc}"

        self._cola.put((pregunta, estado, dato))


def _formatear(pregunta: str, respuesta) -> str:
    """Arma el texto de la pantalla: primero como entendio, luego los datos."""
    intencion = respuesta.intencion
    fuente = ("el modelo de lenguaje" if intencion.origen == "llm"
              else "las reglas locales")

    lineas = [
        f"Pregunta: {pregunta}",
        f"Interpretada por {fuente} como {intencion.tipo} "
        f"(confianza {intencion.confianza:.2f}).",
    ]

    campos = [f"{nombre}: {valor}" for nombre, valor in (
        ("titulo", intencion.titulo), ("autor", intencion.autor),
        ("ISBN", intencion.isbn), ("lector", intencion.lector)) if valor]
    if campos:
        lineas.append("Datos extraidos de la pregunta -> " + "; ".join(campos))

    if respuesta.aviso:
        lineas += ["", respuesta.aviso]

    lineas += ["", respuesta.texto]

    if respuesta.resultados:
        lineas += ["", f"Las bibliotecas devolvieron "
                       f"{len(respuesta.resultados)} registro(s). La respuesta "
                       "se construyo unicamente con esos datos."]
    return "\n".join(lineas)
