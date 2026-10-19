"""Paleta institucional y estilos de los widgets ttk."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

# ---------------------------------------------------------------------------
# Paleta (tomada de la identidad visual de la Universidad Manuela Beltran)
# ---------------------------------------------------------------------------
VINO = "#8C1A2B"
VINO_OSCURO = "#6E1422"
VINO_CLARO = "#C9A0A8"
CARBON = "#1F2328"
CARBON_CLARO = "#2B3138"
FONDO = "#F4F2EE"
BLANCO = "#FFFFFF"
BORDE = "#D8D4CB"
TEXTO = "#1F2328"
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


def fuente(tam: int = 10, negrita: bool = False, cursiva: bool = False):
    estilo = ""
    if negrita:
        estilo += "bold "
    if cursiva:
        estilo += "italic"
    return (FUENTE, tam, estilo.strip()) if estilo.strip() else (FUENTE, tam)


def aplicar_estilos(root: tk.Misc) -> ttk.Style:
    """Configura el tema de los widgets ttk que usa la aplicacion."""
    estilo = ttk.Style(root)
    try:
        estilo.theme_use("clam")
    except tk.TclError:  # pragma: no cover
        pass

    estilo.configure(".", font=fuente(10), background=FONDO, foreground=TEXTO)

    estilo.configure("Fondo.TFrame", background=FONDO)
    estilo.configure("Tarjeta.TFrame", background=BLANCO, relief="flat")
    estilo.configure("Barra.TFrame", background=CARBON)

    estilo.configure("Titulo.TLabel", background=FONDO, foreground=TEXTO,
                     font=fuente(19, negrita=True))
    estilo.configure("Subtitulo.TLabel", background=FONDO, foreground=TEXTO_SUAVE,
                     font=fuente(10))
    estilo.configure("Seccion.TLabel", background=BLANCO, foreground=TEXTO,
                     font=fuente(12, negrita=True))
    estilo.configure("Campo.TLabel", background=BLANCO, foreground=TEXTO,
                     font=fuente(10, negrita=True))
    estilo.configure("Ayuda.TLabel", background=BLANCO, foreground=TEXTO_SUAVE,
                     font=fuente(9))
    estilo.configure("Error.TLabel", background=BLANCO, foreground=ROJO,
                     font=fuente(9))
    estilo.configure("Tarjeta.TLabel", background=BLANCO, foreground=TEXTO,
                     font=fuente(10))
    estilo.configure("Dato.TLabel", background=BLANCO, foreground=VINO,
                     font=fuente(24, negrita=True))
    estilo.configure("DatoPie.TLabel", background=BLANCO, foreground=TEXTO_SUAVE,
                     font=fuente(9))

    # -- Entradas -------------------------------------------------------
    estilo.configure("TEntry", fieldbackground=BLANCO, bordercolor=BORDE,
                     lightcolor=BORDE, darkcolor=BORDE, padding=6)
    estilo.map("TEntry", bordercolor=[("focus", VINO)])
    estilo.configure("Malo.TEntry", fieldbackground=ROJO_FONDO, bordercolor=ROJO,
                     lightcolor=ROJO, darkcolor=ROJO, padding=6)

    estilo.configure("TCombobox", fieldbackground=BLANCO, background=BLANCO,
                     bordercolor=BORDE, arrowcolor=CARBON, padding=5)
    estilo.map("TCombobox", fieldbackground=[("readonly", BLANCO)],
               bordercolor=[("focus", VINO)])
    estilo.configure("Malo.TCombobox", fieldbackground=ROJO_FONDO, bordercolor=ROJO)

    estilo.configure("TSpinbox", fieldbackground=BLANCO, bordercolor=BORDE,
                     arrowcolor=CARBON, padding=5)

    # -- Botones --------------------------------------------------------
    estilo.configure("Primario.TButton", background=VINO, foreground=BLANCO,
                     font=fuente(10, negrita=True), borderwidth=0, padding=(18, 9))
    estilo.map("Primario.TButton",
               background=[("active", VINO_OSCURO), ("disabled", "#C8C4BC")])

    estilo.configure("Secundario.TButton", background=BLANCO, foreground=TEXTO,
                     font=fuente(10), borderwidth=1, bordercolor=BORDE,
                     padding=(14, 8))
    estilo.map("Secundario.TButton", background=[("active", "#ECE9E3")])

    estilo.configure("Peligro.TButton", background=BLANCO, foreground=ROJO,
                     font=fuente(10), borderwidth=1, bordercolor=ROJO,
                     padding=(14, 8))
    estilo.map("Peligro.TButton", background=[("active", ROJO_FONDO)])

    # -- Tablas ---------------------------------------------------------
    estilo.configure("Treeview", background=BLANCO, fieldbackground=BLANCO,
                     foreground=TEXTO, rowheight=27, borderwidth=0,
                     font=fuente(10))
    estilo.configure("Treeview.Heading", background="#ECE9E3", foreground=TEXTO,
                     font=fuente(10, negrita=True), relief="flat", padding=6)
    estilo.map("Treeview.Heading", background=[("active", "#E2DED6")])
    estilo.map("Treeview", background=[("selected", VINO_CLARO)],
               foreground=[("selected", CARBON)])

    estilo.configure("TNotebook", background=FONDO, borderwidth=0)
    estilo.configure("TNotebook.Tab", background="#E7E3DC", foreground=TEXTO,
                     padding=(16, 8), font=fuente(10))
    estilo.map("TNotebook.Tab", background=[("selected", BLANCO)])

    estilo.configure("TSeparator", background=BORDE)
    estilo.configure("Vertical.TScrollbar", background="#D8D4CB",
                     troughcolor=FONDO, borderwidth=0, arrowcolor=CARBON)

    return estilo
