"""Widgets reutilizables de la interfaz."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from presentacion.escritorio import estilos as E


class Tarjeta(ttk.Frame):
    """Panel blanco con borde, titulo opcional y cuerpo para otros widgets."""

    def __init__(self, maestro, titulo: str = "", ayuda: str = "", **kw):
        contenedor = tk.Frame(maestro, background=E.BORDE)
        super().__init__(contenedor, style="Tarjeta.TFrame", padding=kw.pop("padding", 18))
        super().pack(fill="both", expand=True, padx=1, pady=1)
        self.exterior = contenedor

        if titulo:
            ttk.Label(self, text=titulo, style="Seccion.TLabel").pack(anchor="w")
        if ayuda:
            ttk.Label(self, text=ayuda, style="Ayuda.TLabel",
                      wraplength=kw.pop("wraplength", 640),
                      justify="left").pack(anchor="w", pady=(2, 0))
        if titulo or ayuda:
            ttk.Separator(self, orient="horizontal").pack(fill="x", pady=(12, 14))

    def colocar(self, **kw):
        """Empaqueta la tarjeta completa (el borde exterior)."""
        self.exterior.pack(**kw)
        return self

    def ubicar(self, **kw):
        self.exterior.grid(**kw)
        return self


class Indicador(tk.Frame):
    """Pastilla de color con un texto corto: estado de un nodo, por ejemplo."""

    COLORES = {
        "ok": (E.VERDE_FONDO, E.VERDE),
        "aviso": (E.AMBAR_FONDO, E.AMBAR),
        "error": (E.ROJO_FONDO, E.ROJO),
        "info": (E.AZUL_FONDO, E.AZUL),
        "neutro": ("#ECE9E3", E.TEXTO_SUAVE),
    }

    def __init__(self, maestro, texto: str, tipo: str = "neutro", **kw):
        fondo, color = self.COLORES.get(tipo, self.COLORES["neutro"])
        super().__init__(maestro, background=fondo, **kw)
        self.etiqueta = tk.Label(self, text=texto, background=fondo, foreground=color,
                                 font=E.fuente(9, negrita=True), padx=10, pady=4)
        self.etiqueta.pack()

    def actualizar(self, texto: str, tipo: str = "neutro") -> None:
        fondo, color = self.COLORES.get(tipo, self.COLORES["neutro"])
        self.configure(background=fondo)
        self.etiqueta.configure(text=texto, background=fondo, foreground=color)


class CampoFormulario(ttk.Frame):
    """Etiqueta + control + renglon de error, con marca de obligatorio."""

    def __init__(self, maestro, etiqueta: str, control: str = "entry",
                 obligatorio: bool = False, valores: list[str] | None = None,
                 ancho: int = 36, ayuda: str = "", **kw):
        super().__init__(maestro, style="Tarjeta.TFrame", **kw)
        self.obligatorio = obligatorio
        self.tipo = control

        texto = etiqueta + (" *" if obligatorio else "")
        ttk.Label(self, text=texto, style="Campo.TLabel").pack(anchor="w")
        if ayuda:
            ttk.Label(self, text=ayuda, style="Ayuda.TLabel").pack(anchor="w", pady=(1, 0))

        self.variable = tk.StringVar()
        if control == "combo":
            self.control = ttk.Combobox(self, textvariable=self.variable, width=ancho,
                                        state="readonly", values=valores or [])
        elif control == "spin":
            self.control = ttk.Spinbox(self, textvariable=self.variable, width=8,
                                       from_=1, to=30)
        else:
            self.control = ttk.Entry(self, textvariable=self.variable, width=ancho)
        self.control.pack(anchor="w", pady=(5, 0), fill="x" if control != "spin" else None)

        self.error = ttk.Label(self, text="", style="Error.TLabel")
        self.error.pack(anchor="w", pady=(3, 0))

    # -- utilidades ------------------------------------------------------
    def valor(self) -> str:
        return self.variable.get().strip()

    def asignar(self, texto: str) -> None:
        self.variable.set(texto)

    def opciones(self, valores: list[str]) -> None:
        if self.tipo == "combo":
            self.control.configure(values=valores)

    def marcar_error(self, mensaje: str) -> None:
        self.error.configure(text=mensaje)
        estilo = "Malo.TCombobox" if self.tipo == "combo" else "Malo.TEntry"
        if self.tipo != "spin":
            self.control.configure(style=estilo)

    def limpiar_error(self) -> None:
        self.error.configure(text="")
        if self.tipo == "combo":
            self.control.configure(style="TCombobox")
        elif self.tipo == "entry":
            self.control.configure(style="TEntry")


class Tabla(ttk.Frame):
    """Treeview con barra de desplazamiento y filas alternadas."""

    def __init__(self, maestro, columnas: list[tuple[str, str, int]],
                 alto: int = 10, al_seleccionar: Callable | None = None, **kw):
        super().__init__(maestro, style="Tarjeta.TFrame", **kw)
        self.claves = [c[0] for c in columnas]

        self.arbol = ttk.Treeview(self, columns=self.claves, show="headings", height=alto)
        for clave, titulo, ancho in columnas:
            self.arbol.heading(clave, text=titulo)
            anclaje = "center" if ancho <= 80 else "w"
            self.arbol.column(clave, width=ancho, anchor=anclaje,
                              stretch=(ancho > 120))

        barra = ttk.Scrollbar(self, orient="vertical", command=self.arbol.yview)
        self.arbol.configure(yscrollcommand=barra.set)
        self.arbol.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")

        self.arbol.tag_configure("par", background="#FAF8F5")
        self.arbol.tag_configure("impar", background=E.BLANCO)
        self.arbol.tag_configure("alerta", foreground=E.ROJO)

        if al_seleccionar:
            self.arbol.bind("<<TreeviewSelect>>", lambda _e: al_seleccionar())

    def cargar(self, filas: list[dict], etiquetas: Callable | None = None) -> None:
        self.arbol.delete(*self.arbol.get_children())
        for indice, fila in enumerate(filas):
            valores = [fila.get(c, "") for c in self.claves]
            tags = ["par" if indice % 2 == 0 else "impar"]
            if etiquetas:
                extra = etiquetas(fila)
                if extra:
                    tags.append(extra)
            self.arbol.insert("", "end", iid=str(indice), values=valores, tags=tuple(tags))

    def indice_seleccionado(self) -> int | None:
        seleccion = self.arbol.selection()
        return int(seleccion[0]) if seleccion else None

    def vaciar(self) -> None:
        self.arbol.delete(*self.arbol.get_children())


class Aviso(tk.Frame):
    """Mensaje flotante que se superpone a la vista y se va solo.

    Va con `place`, no con `pack`, para que al aparecer no empuje el contenido
    ni desplace los botones fuera de la pantalla. Se oculta solo pasados unos
    segundos, o al hacer clic sobre el.
    """

    DURACION = {"ok": 5000, "info": 7000, "aviso": 8000, "error": 9000}

    def __init__(self, maestro, **kw):
        super().__init__(maestro, background=E.BORDE, **kw)
        interior = tk.Frame(self, background=E.BLANCO)
        interior.pack(fill="both", expand=True, padx=1, pady=1)

        self.barra = tk.Frame(interior, width=4, background=E.BORDE)
        self.barra.pack(side="left", fill="y")
        self.texto = tk.Label(interior, text="", background=E.BLANCO, foreground=E.TEXTO,
                              font=E.fuente(10), justify="left", anchor="w",
                              padx=12, pady=10, wraplength=420)
        self.texto.pack(side="left", fill="both", expand=True)
        self.cerrar = tk.Label(interior, text="X", background=E.BLANCO,
                               foreground=E.TEXTO_SUAVE, font=E.fuente(9, negrita=True),
                               padx=10, cursor="hand2")
        self.cerrar.pack(side="right", fill="y")

        for widget in (self, interior, self.texto, self.cerrar):
            widget.bind("<Button-1>", lambda _e: self.ocultar())

        self._visible = False
        self._temporizador = None

    def mostrar(self, mensaje: str, tipo: str = "info", milisegundos: int | None = None) -> None:
        fondo, color = Indicador.COLORES.get(tipo, Indicador.COLORES["info"])
        self.configure(background=color)
        self.barra.configure(background=color)
        self.texto.configure(text=mensaje, background=fondo, foreground=color)
        self.cerrar.configure(background=fondo, foreground=color)
        self.texto.master.configure(background=fondo)

        if not self._visible:
            # Esquina inferior derecha: flota sobre el contenido sin taparlo.
            self.place(relx=1.0, rely=1.0, x=-2, y=-2, anchor="se", width=470)
            self._visible = True
        self.lift()

        if self._temporizador is not None:
            try:
                self.after_cancel(self._temporizador)
            except Exception:
                pass
        espera = milisegundos or self.DURACION.get(tipo, 7000)
        self._temporizador = self.after(espera, self.ocultar)

    def ocultar(self) -> None:
        if self._temporizador is not None:
            try:
                self.after_cancel(self._temporizador)
            except Exception:
                pass
            self._temporizador = None
        if self._visible:
            self.place_forget()
            self._visible = False


def encabezado(maestro, titulo: str, subtitulo: str = "") -> ttk.Frame:
    """Titulo y bajada de una vista."""
    marco = ttk.Frame(maestro, style="Fondo.TFrame")
    marco.pack(fill="x", pady=(0, 18))
    ttk.Label(marco, text=titulo, style="Titulo.TLabel").pack(anchor="w")
    if subtitulo:
        ttk.Label(marco, text=subtitulo, style="Subtitulo.TLabel").pack(anchor="w", pady=(3, 0))
    return marco
