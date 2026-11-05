"""Widgets reutilizables de la interfaz.

Todos se adaptan al tamano de la ventana y al escalado de la pantalla: las
tablas reparten el ancho por proporcion en lugar de pixeles fijos, y los textos
largos recalculan donde cortar el renglon cada vez que la ventana cambia de
tamano. Esa es la razon por la que antes el texto se veia bien en un monitor y
recortado en otro.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk
from typing import Callable

from presentacion.escritorio import estilos as E


# ---------------------------------------------------------------------------
# Texto que se ajusta al ancho disponible
# ---------------------------------------------------------------------------
def ajustar_al_ancho(etiqueta: tk.Misc, margen: int = 24) -> None:
    """Hace que una etiqueta corte el renglon segun el ancho que tenga.

    Sin esto hay que fijar `wraplength` a un numero de pixeles, que acierta en
    una pantalla y falla en las demas.
    """
    def _recalcular(evento):
        ancho = max(evento.width - E.px(margen), E.px(120))
        try:
            etiqueta.configure(wraplength=ancho)
        except tk.TclError:  # pragma: no cover - widget destruido
            pass

    etiqueta.bind("<Configure>", _recalcular)


class MarcoDesplazable(ttk.Frame):
    """Contenedor que agrega barra vertical solo cuando el contenido no cabe.

    Es la red de seguridad del problema "en esta pantalla no se ve el boton":
    por alta que quede una vista, siempre se puede llegar al final. Si sobra
    espacio la barra desaparece y el contenido se estira, asi que en un monitor
    grande no se nota que exista.
    """

    def __init__(self, maestro, **kw):
        super().__init__(maestro, style="Fondo.TFrame", **kw)
        self.lienzo = tk.Canvas(self, background=E.FONDO, highlightthickness=0,
                                borderwidth=0, takefocus=0)
        self.barra = ttk.Scrollbar(self, orient="vertical",
                                   command=self.lienzo.yview)
        self.lienzo.configure(yscrollcommand=self._mover_barra)
        self.lienzo.pack(side="left", fill="both", expand=True)

        self.contenido = ttk.Frame(self.lienzo, style="Fondo.TFrame")
        self._ventana = self.lienzo.create_window((0, 0), window=self.contenido,
                                                  anchor="nw")
        self._barra_visible = False

        self._medida = None
        self.contenido.bind("<Configure>", self._contenido_cambio)
        self.lienzo.bind("<Configure>", self._lienzo_cambio)
        # Tk avisa cuando un widget cambia de tamano real, pero no cuando
        # cambia el que *pide*. Una revision periodica muy barata (dos
        # consultas de tamano) cubre los casos en que una vista crece al
        # cargar datos: una tabla con mas filas, un aviso que aparece.
        self._vigilar()
        # La rueda se activa al entrar y se suelta al salir: solo hay una vista
        # visible a la vez, de modo que nunca compiten dos contenedores.
        self.bind("<Enter>", self._tomar_rueda)
        self.bind("<Leave>", self._soltar_rueda)

    # -- geometria -----------------------------------------------------
    def _contenido_cambio(self, _evento=None) -> None:
        self._sincronizar()

    def _lienzo_cambio(self, _evento=None) -> None:
        self._sincronizar()

    def _sincronizar(self) -> None:
        """Iguala el ancho al del lienzo y el alto a lo que pide el contenido.

        El alto es el maximo entre lo visible y lo que el contenido necesita:
        si sobra espacio, los widgets con expand=True se estiran igual que
        antes; si falta, el area crece y entonces aparece la barra.
        """
        ancho = self.lienzo.winfo_width()
        alto_visible = self.lienzo.winfo_height()
        if ancho <= 1 or alto_visible <= 1:
            return
        pedido = self.contenido.winfo_reqheight()
        alto = max(alto_visible, pedido)
        if (ancho, alto) == self._medida:
            return                      # evita el bucle configure -> configure
        self._medida = (ancho, alto)
        self.lienzo.itemconfigure(self._ventana, width=ancho, height=alto)
        self.lienzo.configure(scrollregion=(0, 0, ancho, alto))

    def _vigilar(self) -> None:
        try:
            self._sincronizar()
            self.after(400, self._vigilar)
        except tk.TclError:  # pragma: no cover - ventana cerrada
            pass

    def _mover_barra(self, primero: str, ultimo: str) -> None:
        self.barra.set(primero, ultimo)
        necesaria = not (float(primero) <= 0.0 and float(ultimo) >= 1.0)
        if necesaria and not self._barra_visible:
            self.barra.pack(side="right", fill="y")
            self._barra_visible = True
        elif not necesaria and self._barra_visible:
            self.barra.pack_forget()
            self._barra_visible = False

    # -- rueda del raton -----------------------------------------------
    def _tomar_rueda(self, _evento=None) -> None:
        self.bind_all("<MouseWheel>", self._rodar)       # Windows y macOS
        self.bind_all("<Button-4>", self._rodar)         # Linux: arriba
        self.bind_all("<Button-5>", self._rodar)         # Linux: abajo

    def _soltar_rueda(self, _evento=None) -> None:
        for evento in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.unbind_all(evento)

    def _rodar(self, evento) -> None:
        if not self._barra_visible:
            return
        if getattr(evento, "num", 0) == 4:
            pasos = -1
        elif getattr(evento, "num", 0) == 5:
            pasos = 1
        else:
            pasos = -1 if evento.delta > 0 else 1
        self.lienzo.yview_scroll(pasos, "units")


class FilaFluida(ttk.Frame):
    """Fila de elementos que pasa al renglon siguiente cuando no caben.

    Se usa para listas cortas de enlaces o etiquetas. Con `pack(side="left")`
    los ultimos elementos se recortaban en cuanto la fuente crecia por el
    escalado de la pantalla; aqui se reacomodan solos.
    """

    def __init__(self, maestro, separacion: int = 10, estilo: str = "Tarjeta.TFrame",
                 **kw):
        super().__init__(maestro, style=estilo, **kw)
        self.separacion = E.px(separacion)
        self.elementos: list[tk.Misc] = []
        self._ancho = 0
        self.bind("<Configure>", lambda _e: self._reacomodar())

    def agregar(self, widget: tk.Misc) -> tk.Misc:
        self.elementos.append(widget)
        self._ancho = 0            # obliga a recalcular en el proximo ciclo
        self.after_idle(self._reacomodar)
        return widget

    def _reacomodar(self) -> None:
        ancho = self.winfo_width()
        if ancho <= 1:
            return
        x = y = alto_fila = 0
        for widget in self.elementos:
            pedido_x = widget.winfo_reqwidth()
            pedido_y = widget.winfo_reqheight()
            if x and x + pedido_x > ancho:
                x = 0
                y += alto_fila + E.px(4)
                alto_fila = 0
            widget.place(x=x, y=y)
            x += pedido_x + self.separacion
            alto_fila = max(alto_fila, pedido_y)
        try:
            self.configure(height=y + alto_fila)
        except tk.TclError:  # pragma: no cover
            pass


def _ancla_flotante(widget: tk.Misc) -> tk.Misc:
    """Devuelve el marco desplazable que contiene a `widget`, si existe.

    Sirve para que un mensaje flotante quede anclado a lo que se ve y no al
    contenido, que puede ser mas alto que la ventana: de otro modo el aviso
    aparecia fuera de la vista y parecia que no se hubiera mostrado.
    """
    actual = widget
    while actual is not None:
        if isinstance(actual, MarcoDesplazable):
            return actual
        actual = getattr(actual, "master", None)
    return widget


class Tarjeta(ttk.Frame):
    """Panel blanco con borde, titulo opcional y cuerpo para otros widgets."""

    def __init__(self, maestro, titulo: str = "", ayuda: str = "", **kw):
        contenedor = tk.Frame(maestro, background=E.BORDE)
        relleno = kw.pop("padding", E.px(18))
        kw.pop("wraplength", None)  # ahora se calcula solo
        super().__init__(contenedor, style="Tarjeta.TFrame", padding=relleno)
        super().pack(fill="both", expand=True, padx=1, pady=1)
        self.exterior = contenedor

        if titulo:
            ttk.Label(self, text=titulo, style="Seccion.TLabel").pack(anchor="w")
        if ayuda:
            etiqueta = ttk.Label(self, text=ayuda, style="Ayuda.TLabel",
                                 justify="left")
            etiqueta.pack(anchor="w", fill="x", pady=(E.px(3), 0))
            ajustar_al_ancho(etiqueta, margen=E.px(8))
        if titulo or ayuda:
            ttk.Separator(self, orient="horizontal").pack(
                fill="x", pady=(E.px(12), E.px(14)))

    def colocar(self, **kw):
        self.exterior.pack(**kw)
        return self

    def ubicar(self, **kw):
        self.exterior.grid(**kw)
        return self


class Indicador(tk.Frame):
    """Pastilla de color con un texto corto: el estado de un nodo, por ejemplo."""

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
                                 font=E.fuente(E.TAM_AYUDA, negrita=True),
                                 padx=E.px(10), pady=E.px(4))
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

        encabezado = ttk.Frame(self, style="Tarjeta.TFrame")
        encabezado.pack(fill="x")
        ttk.Label(encabezado, text=etiqueta, style="Campo.TLabel").pack(side="left")
        if obligatorio:
            tk.Label(encabezado, text="*", background=E.BLANCO, foreground=E.VINO,
                     font=E.fuente(E.TAM_CAMPO, negrita=True)).pack(side="left",
                                                                    padx=(E.px(3), 0))
        if ayuda:
            texto_ayuda = ttk.Label(self, text=ayuda, style="Ayuda.TLabel",
                                    justify="left")
            texto_ayuda.pack(anchor="w", fill="x", pady=(E.px(1), 0))
            ajustar_al_ancho(texto_ayuda, margen=E.px(8))

        self.variable = tk.StringVar()
        if control == "combo":
            self.control = ttk.Combobox(self, textvariable=self.variable, width=ancho,
                                        state="readonly", values=valores or [],
                                        font=E.fuente())
        elif control == "spin":
            self.control = ttk.Spinbox(self, textvariable=self.variable, width=8,
                                       from_=1, to=30, font=E.fuente())
        else:
            self.control = ttk.Entry(self, textvariable=self.variable, width=ancho,
                                     font=E.fuente())
        self.control.pack(anchor="w", pady=(E.px(5), 0),
                          fill="x" if control != "spin" else None)

        # El renglon de error no se reserva de antemano: aparece solo cuando
        # hay algo que decir. Cuatro renglones vacios sumaban casi 80 px, que
        # era justo lo que faltaba para que el formulario cupiera en una
        # pantalla de 768 px de alto.
        self.error = ttk.Label(self, text="", style="Error.TLabel", justify="left")
        ajustar_al_ancho(self.error, margen=E.px(8))

    def valor(self) -> str:
        return self.variable.get().strip()

    def asignar(self, texto: str) -> None:
        self.variable.set(texto)

    def opciones(self, valores: list[str]) -> None:
        if self.tipo == "combo":
            self.control.configure(values=valores)

    def marcar_error(self, mensaje: str) -> None:
        self.error.configure(text=mensaje)
        if not self.error.winfo_ismapped():
            self.error.pack(anchor="w", fill="x", pady=(E.px(3), 0))
        if self.tipo == "combo":
            self.control.configure(style="Malo.TCombobox")
        elif self.tipo == "entry":
            self.control.configure(style="Malo.TEntry")

    def limpiar_error(self) -> None:
        self.error.configure(text="")
        self.error.pack_forget()
        if self.tipo == "combo":
            self.control.configure(style="TCombobox")
        elif self.tipo == "entry":
            self.control.configure(style="TEntry")


class Tabla(ttk.Frame):
    """Tabla que reparte el ancho disponible entre sus columnas.

    El tercer valor de cada columna ya no es un ancho en pixeles sino un
    **peso**: cuanto espacio le toca frente a las demas. Al cambiar el tamano
    de la ventana, o al abrir la aplicacion en una pantalla con otro escalado,
    las columnas se recalculan solas. Asi ninguna queda tan angosta que corte
    el texto ni tan ancha que deje un hueco.
    """

    def __init__(self, maestro, columnas: list[tuple[str, str, int]],
                 alto: int = 10, al_seleccionar: Callable | None = None, **kw):
        super().__init__(maestro, style="Tarjeta.TFrame", **kw)
        self.claves = [c[0] for c in columnas]
        self.pesos = {c[0]: max(int(c[2]), 1) for c in columnas}
        self._ultimo_ancho = 0

        # `alto` es el numero de filas deseado, no un minimo rigido. En una
        # pantalla baja se pide menos para que la tarjeta entera quepa; como
        # las vistas empaquetan la tabla con expand=True, en un monitor grande
        # crece igual hasta llenar el espacio libre.
        filas = alto
        try:
            # Alto util en medidas de diseno: una pantalla de 768 px con el
            # texto al 125 % equivale a 614, y ahi caben menos filas.
            util = maestro.winfo_screenheight() / max(E.FACTOR, 1.0)
            if util < 800:
                filas = min(alto, 7)
            elif util < 1000:
                filas = min(alto, 11)
        except tk.TclError:  # pragma: no cover
            pass

        self.arbol = ttk.Treeview(self, columns=self.claves, show="headings",
                                  height=filas, selectmode="browse")

        # Medimos el encabezado con la fuente real: asi el minimo de cada
        # columna depende del texto y del escalado, no de un calculo a ojo.
        try:
            medidor = tkfont.Font(root=maestro,
                                  font=E.fuente(E.TAM_CUERPO, negrita=True))
        except tk.TclError:  # pragma: no cover
            medidor = None
        for clave, titulo, peso in columnas:
            self.arbol.heading(clave, text=titulo, anchor="w")
            # El minimo garantiza que el encabezado nunca se recorte.
            if medidor is not None:
                minimo = medidor.measure(titulo) + E.px(24)
            else:  # pragma: no cover
                minimo = len(titulo) * E.px(8) + E.px(24)
            self.arbol.column(clave, width=minimo, minwidth=minimo,
                              anchor="center" if peso <= 80 else "w", stretch=True)

        barra = ttk.Scrollbar(self, orient="vertical", command=self.arbol.yview)
        self.arbol.configure(yscrollcommand=barra.set)
        self.arbol.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")

        self.arbol.tag_configure("par", background=E.MARFIL)
        self.arbol.tag_configure("impar", background=E.BLANCO)
        self.arbol.tag_configure("alerta", foreground=E.ROJO)

        self.arbol.bind("<Configure>", self._repartir_ancho)
        if al_seleccionar:
            self.arbol.bind("<<TreeviewSelect>>", lambda _e: al_seleccionar())

    # ------------------------------------------------------------------
    def _repartir_ancho(self, evento=None) -> None:
        ancho = self.arbol.winfo_width()
        if ancho <= 1 or abs(ancho - self._ultimo_ancho) < 4:
            return
        self._ultimo_ancho = ancho

        minimos = {c: self.arbol.column(c, "minwidth") for c in self.claves}
        reservado = sum(minimos.values())
        sobrante = max(ancho - reservado - E.px(4), 0)
        total_pesos = sum(self.pesos.values()) or 1

        for clave in self.claves:
            extra = int(sobrante * self.pesos[clave] / total_pesos)
            self.arbol.column(clave, width=minimos[clave] + extra)

    # ------------------------------------------------------------------
    def cargar(self, filas: list[dict], etiquetas: Callable | None = None) -> None:
        self.arbol.delete(*self.arbol.get_children())
        for indice, fila in enumerate(filas):
            valores = [fila.get(c, "") for c in self.claves]
            tags = ["par" if indice % 2 == 0 else "impar"]
            if etiquetas:
                extra = etiquetas(fila)
                if extra:
                    tags.append(extra)
            self.arbol.insert("", "end", iid=str(indice), values=valores,
                              tags=tuple(tags))
        self._ultimo_ancho = 0
        self.after_idle(self._repartir_ancho)

    def indice_seleccionado(self) -> int | None:
        seleccion = self.arbol.selection()
        return int(seleccion[0]) if seleccion else None

    def vaciar(self) -> None:
        self.arbol.delete(*self.arbol.get_children())


class Aviso(tk.Frame):
    """Mensaje flotante que se superpone a la vista y se va solo.

    Va con `place`, no con `pack`, para que al aparecer no empuje el contenido
    ni desplace los botones fuera de la pantalla.
    """

    DURACION = {"ok": 5000, "info": 7000, "aviso": 8000, "error": 9000}

    def __init__(self, maestro, **kw):
        # Se cuelga del marco desplazable, no de la vista: asi permanece en la
        # esquina visible aunque el contenido sea mas alto que la ventana.
        self.ancla = _ancla_flotante(maestro)
        super().__init__(self.ancla, background=E.BORDE, **kw)
        interior = tk.Frame(self, background=E.BLANCO)
        interior.pack(fill="both", expand=True, padx=1, pady=1)
        self.interior = interior

        self.barra = tk.Frame(interior, width=E.px(4), background=E.BORDE)
        self.barra.pack(side="left", fill="y")
        # La "x" se empaqueta ANTES que el texto: asi reserva su ancho y el
        # texto se queda con lo que sobra. Al reves, el texto se lo llevaba
        # todo y el aspa quedaba cortada.
        self.cerrar = tk.Label(interior, text="×", background=E.BLANCO,
                               foreground=E.TEXTO_SUAVE,
                               font=E.fuente(E.TAM_SECCION, negrita=True),
                               padx=E.px(10), anchor="center", cursor="hand2")
        self.cerrar.pack(side="right", fill="y")
        self.texto = tk.Label(interior, text="", background=E.BLANCO,
                              foreground=E.TEXTO, font=E.fuente(), justify="left",
                              anchor="w", padx=E.px(12), pady=E.px(10),
                              wraplength=E.px(400))
        self.texto.pack(side="left", fill="both", expand=True)

        for widget in (self, interior, self.texto, self.cerrar):
            widget.bind("<Button-1>", lambda _e: self.ocultar())

        self._visible = False
        self._temporizador = None

    def mostrar(self, mensaje: str, tipo: str = "info",
                milisegundos: int | None = None) -> None:
        fondo, color = Indicador.COLORES.get(tipo, Indicador.COLORES["info"])
        self.configure(background=color)
        self.barra.configure(background=color)
        self.interior.configure(background=fondo)
        self.texto.configure(text=mensaje, background=fondo, foreground=color)
        self.cerrar.configure(background=fondo, foreground=color)

        if not self._visible:
            # El ancho se adapta a la ventana: en pantallas pequenas no se sale.
            disponible = self.ancla.winfo_width() or E.px(900)
            ancho = max(min(int(disponible * 0.46), E.px(470)), E.px(260))
            self.texto.configure(wraplength=ancho - E.px(60))
            # El desplazamiento deja libre la franja de la barra lateral.
            self.place(relx=1.0, rely=1.0, x=-E.px(16), y=-E.px(6), anchor="se",
                       width=ancho)
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
    marco.pack(fill="x", pady=(0, E.px(16)))
    ttk.Label(marco, text=titulo, style="Titulo.TLabel").pack(anchor="w")
    if subtitulo:
        etiqueta = ttk.Label(marco, text=subtitulo, style="Subtitulo.TLabel",
                             justify="left")
        etiqueta.pack(anchor="w", fill="x", pady=(E.px(3), 0))
        ajustar_al_ancho(etiqueta, margen=E.px(8))
    return marco
