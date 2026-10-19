"""Aplicacion de escritorio del Sistema Distribuido de Consulta Inteligente
de Bibliotecas.

Uso:
    python main.py            intenta conectarse a los nodos gRPC
    python main.py --demo     fuerza los datos de prueba en memoria
"""

from __future__ import annotations

import argparse
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import estilos as E  # noqa: E402
from app.componentes import Indicador  # noqa: E402
from app.datos import crear_proveedor  # noqa: E402
from app.vistas.catalogo import VistaCatalogo  # noqa: E402
from app.vistas.consulta_ia import VistaConsultaIA  # noqa: E402
from app.vistas.inicio import VistaInicio  # noqa: E402
from app.vistas.prestamos import VistaPrestamos  # noqa: E402
from app.vistas.usuarios import VistaUsuarios  # noqa: E402

TITULO = "Sistema Distribuido de Consulta Inteligente de Bibliotecas"
INTERVALO_MONITOR = 6000  # milisegundos entre revisiones del estado de los nodos
ANCHO_MENU = 236

SECCIONES = [
    ("inicio", "Inicio", "Estado general"),
    ("catalogo", "Catalogo", "Buscar y consultar"),
    ("prestamos", "Prestamos", "Registrar y devolver"),
    ("usuarios", "Usuarios", "Lectores registrados"),
    ("consulta_ia", "Consulta IA", "Lenguaje natural"),
]


class Aplicacion(tk.Tk):
    def __init__(self, forzar_demo: bool = False):
        super().__init__()
        self.title(TITULO)
        self.geometry("1320x780")
        self.minsize(1180, 680)
        self.configure(background=E.FONDO)

        E.aplicar_estilos(self)

        self.proveedor, self.aviso_inicial = crear_proveedor(forzar_demo)
        self.vistas: dict[str, ttk.Frame] = {}
        self.botones: dict[str, tk.Frame] = {}
        self.seccion_activa = ""
        self.estados_nodos: list | None = None
        self._monitor_activo = True

        self._construir_barra_estado()
        self._construir_menu()
        self._construir_area()

        self.mostrar("inicio")

        self.protocol("WM_DELETE_WINDOW", self._cerrar)
        self.after(1500, self._consultar_nodos)

    # ------------------------------------------------------------------
    # Estructura
    # ------------------------------------------------------------------
    def _construir_menu(self) -> None:
        menu = tk.Frame(self, background=E.CARBON, width=ANCHO_MENU)
        menu.pack(side="left", fill="y")
        menu.pack_propagate(False)

        cabecera = tk.Frame(menu, background=E.CARBON)
        cabecera.pack(fill="x", pady=(24, 22), padx=20)
        tk.Label(cabecera, text="BIBLIOTECAS UMB", background=E.CARBON,
                 foreground=E.VINO_CLARO, font=E.fuente(9, negrita=True)).pack(anchor="w")
        tk.Label(cabecera, text="Sistema distribuido", background=E.CARBON,
                 foreground=E.BLANCO, font=E.fuente(12, negrita=True)).pack(anchor="w",
                                                                           pady=(3, 0))
        tk.Frame(menu, background=E.CARBON_CLARO, height=1).pack(fill="x", padx=20)

        for clave, titulo, descripcion in SECCIONES:
            self.botones[clave] = self._boton_menu(menu, clave, titulo, descripcion)

        pie = tk.Frame(menu, background=E.CARBON)
        pie.pack(side="bottom", fill="x", padx=20, pady=18)
        tk.Label(pie, text="By Villaquiran, Mier & Badillo", background=E.CARBON,
                 foreground=E.TEXTO_TENUE, font=E.fuente(8)).pack(anchor="w")

    def _boton_menu(self, maestro, clave, titulo, descripcion) -> tk.Frame:
        marco = tk.Frame(maestro, background=E.CARBON, cursor="hand2")
        marco.pack(fill="x", pady=1)

        barra = tk.Frame(marco, background=E.CARBON, width=4)
        barra.pack(side="left", fill="y")

        interior = tk.Frame(marco, background=E.CARBON)
        interior.pack(side="left", fill="x", expand=True, padx=(16, 10), pady=11)

        etiqueta = tk.Label(interior, text=titulo, background=E.CARBON,
                            foreground=E.BLANCO, font=E.fuente(11, negrita=True),
                            anchor="w")
        etiqueta.pack(anchor="w")
        detalle = tk.Label(interior, text=descripcion, background=E.CARBON,
                           foreground=E.TEXTO_TENUE, font=E.fuente(8), anchor="w")
        detalle.pack(anchor="w")

        marco.partes = (barra, interior, etiqueta, detalle)
        for widget in (marco, interior, etiqueta, detalle):
            widget.bind("<Button-1>", lambda _e, c=clave: self.mostrar(c))
            widget.bind("<Enter>", lambda _e, m=marco: self._resaltar(m, True))
            widget.bind("<Leave>", lambda _e, m=marco: self._resaltar(m, False))
        return marco

    def _resaltar(self, marco: tk.Frame, encima: bool) -> None:
        clave = next((c for c, m in self.botones.items() if m is marco), None)
        if clave == self.seccion_activa:
            return
        color = E.CARBON_CLARO if encima else E.CARBON
        barra, interior, etiqueta, detalle = marco.partes
        for widget in (marco, interior, etiqueta, detalle):
            widget.configure(background=color)
        barra.configure(background=color)

    def _construir_area(self) -> None:
        self.area = tk.Frame(self, background=E.FONDO)
        self.area.pack(side="top", fill="both", expand=True)

    def _construir_barra_estado(self) -> None:
        barra = tk.Frame(self, background=E.CARBON, height=34)
        barra.pack(side="bottom", fill="x")
        barra.pack_propagate(False)

        interior = tk.Frame(barra, background=E.CARBON)
        interior.pack(fill="both", expand=True, padx=16, pady=5)

        tipo = "ok" if self.proveedor.modo == "CONECTADO" else "aviso"
        self.indicador_modo = Indicador(interior, self.proveedor.modo, tipo)
        self.indicador_modo.pack(side="left")

        tk.Label(interior, text=self.proveedor.descripcion, background=E.CARBON,
                 foreground=E.TEXTO_TENUE, font=E.fuente(9)).pack(side="left", padx=(12, 0))

        self.etiqueta_nodos = tk.Label(interior, text=self.aviso_inicial or "",
                                       background=E.CARBON, foreground=E.VINO_CLARO,
                                       font=E.fuente(9))
        self.etiqueta_nodos.pack(side="left", padx=(12, 0))

        tk.Label(interior, text=TITULO, background=E.CARBON,
                 foreground=E.TEXTO_TENUE, font=E.fuente(9)).pack(side="right")

    # ------------------------------------------------------------------
    # Navegacion
    # ------------------------------------------------------------------
    def mostrar(self, clave: str) -> None:
        if clave not in self.vistas:
            self.vistas[clave] = self._crear_vista(clave)

        for vista in self.vistas.values():
            vista.pack_forget()
        self.vistas[clave].pack(fill="both", expand=True)

        self.seccion_activa = clave
        self._pintar_menu()

        vista = self.vistas[clave]
        if clave == "prestamos":
            # Relee usuarios y catalogo conservando lo ya elegido: si alguien
            # creo un usuario en SQL Server, aparece sin reiniciar la aplicacion.
            nuevos = vista.refrescar_listas()
            if nuevos:
                vista.aviso.mostrar(
                    f"Se incorporaron {nuevos} usuario(s) nuevo(s) a la lista.", "info")
        elif clave == "usuarios":
            vista.recargar()
        elif hasattr(vista, "recargar"):
            vista.recargar()

    def _crear_vista(self, clave: str) -> ttk.Frame:
        if clave == "inicio":
            return VistaInicio(self.area, self.proveedor, ir_a=self.mostrar)
        if clave == "catalogo":
            return VistaCatalogo(self.area, self.proveedor)
        if clave == "prestamos":
            return VistaPrestamos(self.area, self.proveedor,
                                  al_cambiar_datos=self._datos_cambiaron)
        if clave == "usuarios":
            return VistaUsuarios(self.area, self.proveedor)
        return VistaConsultaIA(self.area, self.proveedor)

    def _pintar_menu(self) -> None:
        for clave, marco in self.botones.items():
            barra, interior, etiqueta, detalle = marco.partes
            activo = clave == self.seccion_activa
            fondo = E.CARBON_CLARO if activo else E.CARBON
            for widget in (marco, interior, etiqueta, detalle):
                widget.configure(background=fondo)
            barra.configure(background=E.VINO if activo else fondo)
            etiqueta.configure(foreground=E.BLANCO)
            detalle.configure(foreground=E.VINO_CLARO if activo else E.TEXTO_TENUE)

    def _datos_cambiaron(self) -> None:
        """Una operacion modifico datos: refresca las vistas ya creadas."""
        for clave in ("inicio", "catalogo"):
            vista = self.vistas.get(clave)
            if vista is not None and hasattr(vista, "recargar"):
                vista.recargar()

    # ------------------------------------------------------------------
    # Monitor de nodos
    # ------------------------------------------------------------------
    def _consultar_nodos(self) -> None:
        """Lanza la consulta de estado en segundo plano, sin congelar la ventana."""
        if not self._monitor_activo:
            return
        hilo = threading.Thread(target=self._consultar_en_hilo, daemon=True)
        hilo.start()

    def _consultar_en_hilo(self) -> None:
        try:
            estados = self.proveedor.estado_nodos()
        except Exception:  # pragma: no cover
            estados = []
        try:
            self.after(0, lambda: self._aplicar_estados(estados))
        except (RuntimeError, tk.TclError):  # pragma: no cover - ventana cerrada
            pass

    def _aplicar_estados(self, estados: list) -> None:
        if not self._monitor_activo:
            return

        firma = tuple((e.numero, e.en_linea, e.base_datos_ok) for e in estados)
        firma_anterior = getattr(self, "firma_nodos", None)
        self.estados_nodos = estados
        self.firma_nodos = firma

        en_linea = sum(1 for e in estados if e.en_linea)
        total = len(estados) or 3

        if en_linea == total:
            self.etiqueta_nodos.configure(
                text=f"{en_linea} de {total} nodos en linea", foreground=E.TEXTO_TENUE)
        else:
            caidos = ", ".join(str(e.numero) for e in estados if not e.en_linea)
            self.etiqueta_nodos.configure(
                text=f"{en_linea} de {total} nodos en linea - sin respuesta: {caidos}",
                foreground=E.VINO_CLARO)

        vista_inicio = self.vistas.get("inicio")
        if vista_inicio is not None and hasattr(vista_inicio, "aplicar_estados"):
            vista_inicio.aplicar_estados(estados)

        if firma_anterior is not None and firma != firma_anterior:
            self._avisar_cambio_nodos(estados, firma_anterior)

        self.after(INTERVALO_MONITOR, self._consultar_nodos)

    def _avisar_cambio_nodos(self, estados: list, firma_anterior) -> None:
        previos = {n: (linea, bd) for n, linea, bd in firma_anterior}
        cayeron, volvieron = [], []
        for e in estados:
            antes = previos.get(e.numero)
            if antes is None:
                continue
            if antes[0] and not e.en_linea:
                cayeron.append(e.numero)
            elif not antes[0] and e.en_linea:
                volvieron.append(e.numero)

        vista = self.vistas.get(self.seccion_activa)
        if vista is None or not hasattr(vista, "aviso"):
            return
        if cayeron:
            nodos = ", ".join(map(str, cayeron))
            vista.aviso.mostrar(
                f"El nodo {nodos} dejo de responder. El sistema sigue operando "
                f"con las bibliotecas restantes.", "aviso")
        elif volvieron:
            nodos = ", ".join(map(str, volvieron))
            vista.aviso.mostrar(f"El nodo {nodos} volvio a estar en linea.", "ok")

    def _cerrar(self) -> None:
        self._monitor_activo = False
        self.destroy()


def main() -> int:
    parser = argparse.ArgumentParser(description="Interfaz del sistema de bibliotecas")
    parser.add_argument("--demo", action="store_true",
                        help="Usar datos de prueba sin conectarse a los nodos")
    args = parser.parse_args()

    app = Aplicacion(forzar_demo=args.demo)
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
