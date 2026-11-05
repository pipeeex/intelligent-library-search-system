"""Paleta institucional, escalado por DPI y estilos de los widgets ttk.

El problema que resuelve el escalado: Windows permite ampliar la letra al
125 % o al 150 %, y los portatiles pequenos tienen pantallas de 1366x768. Si la
interfaz se mide en pixeles fijos, en unas pantallas el texto se corta y en
otras queda diminuto. Aqui todo se mide a partir del DPI real del monitor:

* ``activar_dpi()``        avisa a Windows que la app sabe escalar (va ANTES de crear la ventana).
* ``configurar_escalado()`` calcula el factor y se lo pasa a Tk.
* ``px(n)``                convierte una medida de diseno a pixeles de esa pantalla.

Las fuentes se declaran en puntos: Tk las convierte a pixeles usando el factor,
asi que crecen solas. Solo los tamanos en pixeles (anchos, margenes) pasan por
``px()``.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

# ---------------------------------------------------------------------------
# Paleta (identidad visual de la Universidad Manuela Beltran)
# ---------------------------------------------------------------------------
VINO = "#8C1A2B"
VINO_OSCURO = "#6E1422"
VINO_SUAVE = "#A83244"
VINO_CLARO = "#C9A0A8"
VINO_TENUE = "#F6EAEC"

CARBON = "#1C2127"
CARBON_CLARO = "#2A3139"
CARBON_HOVER = "#333B45"

FONDO = "#F4F2EE"
BLANCO = "#FFFFFF"
MARFIL = "#FAF8F5"
BORDE = "#DCD8D0"
BORDE_SUAVE = "#E8E4DC"

TEXTO = "#1C2127"
TEXTO_SUAVE = "#5A6069"
TEXTO_TENUE = "#8A9199"

VERDE = "#1E7A4C"
VERDE_FONDO = "#E6F3EC"
AMBAR = "#9A6B00"
AMBAR_FONDO = "#FBF1DA"
ROJO = "#B3261E"
ROJO_FONDO = "#FBE9E7"
AZUL = "#2F6F8F"
AZUL_FONDO = "#E8F1F5"

FUENTE = "Segoe UI"

# Escala tipografica: un solo juego de tamanos para toda la aplicacion.
TAM_TITULO = 19
TAM_SECCION = 12
TAM_CUERPO = 10
TAM_CAMPO = 10
TAM_AYUDA = 9
TAM_MICRO = 8

# Factor de escala respecto al diseno base de 96 ppp. Lo fija
# configurar_escalado(); mientras tanto, 1.0.
FACTOR = 1.0


# ---------------------------------------------------------------------------
# Escalado
# ---------------------------------------------------------------------------
def activar_dpi() -> None:
    """Declara la aplicacion consciente del DPI. Llamar ANTES de crear la ventana.

    Sin esto, Windows amplia la ventana como si fuera una imagen cuando el
    escalado del sistema no es 100 %: se ve borrosa y los textos se recortan.
    """
    try:
        import ctypes
        try:
            # PROCESS_PER_MONITOR_DPI_AWARE: se adapta a cada monitor.
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        # Linux, macOS o versiones antiguas de Windows: no hace falta.
        pass


def configurar_escalado(root: tk.Misc) -> float:
    """Ajusta Tk al DPI real de la pantalla y devuelve el factor de escala."""
    global FACTOR
    try:
        ppp = float(root.winfo_fpixels("1i"))
    except Exception:
        ppp = 96.0
    if ppp <= 0:
        ppp = 96.0

    # Tk convierte puntos a pixeles con este factor: asi las fuentes declaradas
    # en puntos ocupan el tamano fisico correcto en cualquier pantalla.
    try:
        root.tk.call("tk", "scaling", ppp / 72.0)
    except Exception:
        pass

    FACTOR = max(1.0, min(ppp / 96.0, 2.5))
    return FACTOR


def px(n: float) -> int:
    """Convierte una medida del diseno (pensada a 96 ppp) a pixeles reales."""
    return int(round(n * FACTOR))


def fuente(tam: int = TAM_CUERPO, negrita: bool = False, cursiva: bool = False):
    estilo = []
    if negrita:
        estilo.append("bold")
    if cursiva:
        estilo.append("italic")
    return (FUENTE, int(tam), " ".join(estilo)) if estilo else (FUENTE, int(tam))


# ---------------------------------------------------------------------------
# Estilos ttk
# ---------------------------------------------------------------------------
def aplicar_estilos(root: tk.Misc) -> ttk.Style:
    configurar_escalado(root)

    estilo = ttk.Style(root)
    try:
        estilo.theme_use("clam")
    except tk.TclError:  # pragma: no cover
        pass

    estilo.configure(".", font=fuente(), background=FONDO, foreground=TEXTO)

    # -- Contenedores ---------------------------------------------------
    estilo.configure("Fondo.TFrame", background=FONDO)
    estilo.configure("Tarjeta.TFrame", background=BLANCO, relief="flat")
    estilo.configure("Barra.TFrame", background=CARBON)

    # -- Textos ---------------------------------------------------------
    estilo.configure("Titulo.TLabel", background=FONDO, foreground=TEXTO,
                     font=fuente(TAM_TITULO, negrita=True))
    estilo.configure("Subtitulo.TLabel", background=FONDO, foreground=TEXTO_SUAVE,
                     font=fuente(TAM_CUERPO))
    estilo.configure("Seccion.TLabel", background=BLANCO, foreground=TEXTO,
                     font=fuente(TAM_SECCION, negrita=True))
    estilo.configure("Campo.TLabel", background=BLANCO, foreground=TEXTO,
                     font=fuente(TAM_CAMPO, negrita=True))
    estilo.configure("Ayuda.TLabel", background=BLANCO, foreground=TEXTO_SUAVE,
                     font=fuente(TAM_AYUDA))
    estilo.configure("Error.TLabel", background=BLANCO, foreground=ROJO,
                     font=fuente(TAM_AYUDA))
    estilo.configure("Tarjeta.TLabel", background=BLANCO, foreground=TEXTO,
                     font=fuente(TAM_CUERPO))
    estilo.configure("Dato.TLabel", background=BLANCO, foreground=VINO,
                     font=fuente(24, negrita=True))
    estilo.configure("DatoPie.TLabel", background=BLANCO, foreground=TEXTO_SUAVE,
                     font=fuente(TAM_AYUDA))

    # -- Entradas -------------------------------------------------------
    relleno = (px(8), px(6))
    estilo.configure("TEntry", fieldbackground=BLANCO, bordercolor=BORDE,
                     lightcolor=BORDE, darkcolor=BORDE, padding=relleno,
                     insertcolor=TEXTO)
    estilo.map("TEntry",
               bordercolor=[("focus", VINO)],
               lightcolor=[("focus", VINO)],
               darkcolor=[("focus", VINO)])
    estilo.configure("Malo.TEntry", fieldbackground=ROJO_FONDO, bordercolor=ROJO,
                     lightcolor=ROJO, darkcolor=ROJO, padding=relleno)

    estilo.configure("TCombobox", fieldbackground=BLANCO, background=BLANCO,
                     bordercolor=BORDE, arrowcolor=CARBON, padding=(px(8), px(5)))
    estilo.map("TCombobox",
               fieldbackground=[("readonly", BLANCO)],
               bordercolor=[("focus", VINO)],
               arrowcolor=[("active", VINO)])
    estilo.configure("Malo.TCombobox", fieldbackground=ROJO_FONDO, bordercolor=ROJO)

    estilo.configure("TSpinbox", fieldbackground=BLANCO, bordercolor=BORDE,
                     arrowcolor=CARBON, padding=(px(8), px(5)))
    estilo.map("TSpinbox", bordercolor=[("focus", VINO)])

    # -- Botones --------------------------------------------------------
    estilo.configure("Primario.TButton", background=VINO, foreground=BLANCO,
                     font=fuente(TAM_CUERPO, negrita=True), borderwidth=0,
                     focuscolor=VINO_CLARO, padding=(px(20), px(10)))
    estilo.map("Primario.TButton",
               background=[("pressed", VINO_OSCURO), ("active", VINO_SUAVE),
                           ("disabled", "#C8C4BC")],
               foreground=[("disabled", "#8A8781")])

    estilo.configure("Secundario.TButton", background=BLANCO, foreground=TEXTO,
                     font=fuente(TAM_CUERPO), borderwidth=1, bordercolor=BORDE,
                     focuscolor=VINO_CLARO, padding=(px(16), px(9)))
    estilo.map("Secundario.TButton",
               background=[("pressed", "#E4E0D9"), ("active", MARFIL)],
               bordercolor=[("active", VINO_CLARO)],
               foreground=[("disabled", TEXTO_TENUE)])

    estilo.configure("Peligro.TButton", background=BLANCO, foreground=ROJO,
                     font=fuente(TAM_CUERPO), borderwidth=1, bordercolor=ROJO,
                     padding=(px(16), px(9)))
    estilo.map("Peligro.TButton", background=[("active", ROJO_FONDO)])

    # -- Tablas ---------------------------------------------------------
    alto_fila = px(28)
    estilo.configure("Treeview", background=BLANCO, fieldbackground=BLANCO,
                     foreground=TEXTO, rowheight=alto_fila, borderwidth=0,
                     font=fuente(TAM_CUERPO))
    estilo.configure("Treeview.Heading", background="#EDE9E2", foreground=TEXTO,
                     font=fuente(TAM_CUERPO, negrita=True), relief="flat",
                     padding=(px(8), px(7)))
    estilo.map("Treeview.Heading", background=[("active", "#E2DED6")])
    estilo.map("Treeview",
               background=[("selected", VINO_TENUE)],
               foreground=[("selected", TEXTO)])

    estilo.configure("TNotebook", background=FONDO, borderwidth=0)
    estilo.configure("TNotebook.Tab", background="#E7E3DC", foreground=TEXTO,
                     padding=(px(16), px(8)), font=fuente(TAM_CUERPO))
    estilo.map("TNotebook.Tab", background=[("selected", BLANCO)])

    estilo.configure("TSeparator", background=BORDE_SUAVE)
    estilo.configure("Vertical.TScrollbar", background=BORDE,
                     troughcolor=FONDO, borderwidth=0, arrowcolor=TEXTO_SUAVE,
                     width=px(12))
    estilo.map("Vertical.TScrollbar", background=[("active", VINO_CLARO)])
    estilo.configure("Horizontal.TScrollbar", background=BORDE,
                     troughcolor=FONDO, borderwidth=0, arrowcolor=TEXTO_SUAVE)

    return estilo
