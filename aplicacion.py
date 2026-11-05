"""Aplicacion de escritorio del Sistema Distribuido de Consulta Inteligente
de Bibliotecas.

Uso:
    python aplicacion.py            intenta conectarse a los nodos gRPC
    python aplicacion.py --demo     fuerza los datos de prueba en memoria

Sobre el tamano de la ventana: no se fija en pixeles. Primero se declara la
aplicacion consciente del DPI (``E.activar_dpi()``, antes de crear la ventana),
despues ``E.aplicar_estilos()`` calcula el factor de escala de esa pantalla y
recien entonces se decide la geometria a partir del tamano real del monitor.
De esa forma la misma aplicacion se ve igual en un portatil de 1366x768 con
Windows al 125 % y en un monitor de 1920x1080 al 100 %.
"""

from __future__ import annotations

import argparse
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk

sys.path.insert(0, str(Path(__file__).resolve().parent))

from presentacion.escritorio import estilos as E  # noqa: E402
from presentacion.escritorio.componentes import Indicador, MarcoDesplazable  # noqa: E402
from presentacion.escritorio.servicio_cliente import crear_proveedor  # noqa: E402
from presentacion.escritorio.vistas.catalogo import VistaCatalogo  # noqa: E402
from presentacion.escritorio.vistas.consulta_ia import VistaConsultaIA  # noqa: E402
from presentacion.escritorio.vistas.inicio import VistaInicio  # noqa: E402
from presentacion.escritorio.vistas.prestamos import VistaPrestamos  # noqa: E402
from presentacion.escritorio.vistas.usuarios import VistaUsuarios  # noqa: E402

TITULO = "Sistema Distribuido de Consulta Inteligente de Bibliotecas"
TITULO_CORTO = "Bibliotecas UMB - Sistema distribuido"
INTERVALO_MONITOR = 6000  # milisegundos entre revisiones del estado de los nodos

# Medidas del diseno, pensadas a 96 ppp. px() las traduce a la pantalla real.
ANCHO_MENU = 236
ANCHO_MENU_ESTRECHO = 198   # pantallas pequenas: el menu cede espacio al contenido
ANCHO_DISENO = 1320
ALTO_DISENO = 780
ANCHO_MINIMO = 1024
ALTO_MINIMO = 620

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
        self.configure(background=E.FONDO)

        # Fija el factor de escala y los estilos ttk. Va antes de medir la
        # ventana porque px() depende de ese factor.
        E.aplicar_estilos(self)
        self.ancho_menu = self._dimensionar_ventana()

        self.proveedor, self.aviso_inicial = crear_proveedor(forzar_demo)
        self.vistas: dict[str, ttk.Frame] = {}
        self.contenedores: dict[str, MarcoDesplazable] = {}
        self.botones: dict[str, tk.Frame] = {}
        self.seccion_activa = ""
        self.estados_nodos: list | None = None
        self._monitor_activo = True

        self._construir_barra_estado()
        self._construir_menu()
        self._construir_area()
        self._registrar_atajos()

        self.mostrar("inicio")

        self.protocol("WM_DELETE_WINDOW", self._cerrar)
        self.after(1500, self._consultar_nodos)

    # ------------------------------------------------------------------
    # Geometria
    # ------------------------------------------------------------------
    def _dimensionar_ventana(self) -> int:
        """Elige tamano, minimos y posicion segun el monitor. Devuelve el ancho del menu.

        Reglas:
        * la ventana ocupa como maximo el 92 % del escritorio, para que nunca
          nazca mas grande que la pantalla (el caso que recortaba los textos);
        * en pantallas con menos de 1200 px utiles arranca maximizada y el menu
          se vuelve estrecho;
        * el minimo tambien se limita al escritorio: un minsize mayor que la
          pantalla impide reducir la ventana y vuelve a cortar el contenido.
        """
        pantalla_ancho = self.winfo_screenwidth()
        pantalla_alto = self.winfo_screenheight()

        deseado_ancho = E.px(ANCHO_DISENO)
        deseado_alto = E.px(ALTO_DISENO)
        util_ancho = int(pantalla_ancho * 0.92)
        util_alto = int(pantalla_alto * 0.90)

        ancho = min(deseado_ancho, util_ancho)
        alto = min(deseado_alto, util_alto)

        self.minsize(min(E.px(ANCHO_MINIMO), util_ancho),
                     min(E.px(ALTO_MINIMO), util_alto))

        x = max((pantalla_ancho - ancho) // 2, 0)
        y = max((pantalla_alto - alto) // 2 - E.px(12), 0)
        self.geometry(f"{ancho}x{alto}+{x}+{y}")

        estrecha = ancho < E.px(1200)
        if estrecha:
            try:
                self.state("zoomed")       # Windows
            except tk.TclError:
                self.attributes("-zoomed", True)  # Linux; si falla, queda centrada
        return E.px(ANCHO_MENU_ESTRECHO if estrecha else ANCHO_MENU)

    # ------------------------------------------------------------------
    # Estructura
    # ------------------------------------------------------------------
    def _construir_menu(self) -> None:
        menu = tk.Frame(self, background=E.CARBON, width=self.ancho_menu)
        menu.pack(side="left", fill="y")
        menu.pack_propagate(False)

        margen = E.px(20)
        cabecera = tk.Frame(menu, background=E.CARBON)
        cabecera.pack(fill="x", pady=(E.px(24), E.px(22)), padx=margen)
        tk.Label(cabecera, text="BIBLIOTECAS UMB", background=E.CARBON,
                 foreground=E.VINO_CLARO, font=E.fuente(E.TAM_AYUDA, negrita=True),
                 anchor="w").pack(fill="x")
        tk.Label(cabecera, text="Sistema distribuido", background=E.CARBON,
                 foreground=E.BLANCO, font=E.fuente(E.TAM_SECCION, negrita=True),
                 anchor="w").pack(fill="x", pady=(E.px(3), 0))
        tk.Frame(menu, background=E.CARBON_CLARO, height=1).pack(fill="x", padx=margen)

        for clave, titulo, descripcion in SECCIONES:
            self.botones[clave] = self._boton_menu(menu, clave, titulo, descripcion)

        pie = tk.Frame(menu, background=E.CARBON)
        pie.pack(side="bottom", fill="x", padx=margen, pady=E.px(18))
        tk.Label(pie, text="Villaquiran, Mier & Badillo", background=E.CARBON,
                 foreground=E.TEXTO_TENUE, font=E.fuente(E.TAM_MICRO),
                 anchor="w").pack(fill="x")
        tk.Label(pie, text="Ctrl+1 a Ctrl+5 para navegar", background=E.CARBON,
                 foreground=E.CARBON_HOVER, font=E.fuente(E.TAM_MICRO),
                 anchor="w").pack(fill="x", pady=(E.px(3), 0))

    def _boton_menu(self, maestro, clave, titulo, descripcion) -> tk.Frame:
        marco = tk.Frame(maestro, background=E.CARBON, cursor="hand2")
        marco.pack(fill="x", pady=1)

        barra = tk.Frame(marco, background=E.CARBON, width=E.px(4))
        barra.pack(side="left", fill="y")

        interior = tk.Frame(marco, background=E.CARBON)
        interior.pack(side="left", fill="x", expand=True,
                      padx=(E.px(14), E.px(8)), pady=E.px(11))

        # anchor="w" + fill="x" en lugar de un ancho fijo: si el menu se
        # estrecha, el texto se alinea solo en vez de desbordarse.
        etiqueta = tk.Label(interior, text=titulo, background=E.CARBON,
                            foreground=E.BLANCO,
                            font=E.fuente(E.TAM_CUERPO, negrita=True), anchor="w")
        etiqueta.pack(fill="x")
        detalle = tk.Label(interior, text=descripcion, background=E.CARBON,
                           foreground=E.TEXTO_TENUE, font=E.fuente(E.TAM_MICRO),
                           anchor="w")
        detalle.pack(fill="x", pady=(E.px(1), 0))

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
        color = E.CARBON_HOVER if encima else E.CARBON
        barra, interior, etiqueta, detalle = marco.partes
        for widget in (marco, interior, etiqueta, detalle):
            widget.configure(background=color)
        barra.configure(background=E.VINO_SUAVE if encima else color)

    def _construir_area(self) -> None:
        self.area = tk.Frame(self, background=E.FONDO)
        self.area.pack(side="top", fill="both", expand=True)

    def _construir_barra_estado(self) -> None:
        """Se empaqueta primero y al fondo: asi nunca la tapa el contenido."""
        barra = tk.Frame(self, background=E.CARBON, height=E.px(34))
        barra.pack(side="bottom", fill="x")
        barra.pack_propagate(False)

        interior = tk.Frame(barra, background=E.CARBON)
        interior.pack(fill="both", expand=True, padx=E.px(16), pady=E.px(5))

        tipo = "ok" if self.proveedor.modo == "CONECTADO" else "aviso"
        self.indicador_modo = Indicador(interior, self.proveedor.modo, tipo)
        self.indicador_modo.pack(side="left")

        tk.Label(interior, text=self.proveedor.descripcion, background=E.CARBON,
                 foreground=E.TEXTO_TENUE, font=E.fuente(E.TAM_AYUDA)
                 ).pack(side="left", padx=(E.px(12), 0))

        self.etiqueta_nodos = tk.Label(interior, text=self.aviso_inicial or "",
                                       background=E.CARBON, foreground=E.VINO_CLARO,
                                       font=E.fuente(E.TAM_AYUDA))
        self.etiqueta_nodos.pack(side="left", padx=(E.px(12), 0))

        # El titulo largo es lo primero que se recorta en pantallas angostas,
        # asi que se oculta cuando no cabe en lugar de empujar al resto.
        self.etiqueta_titulo = tk.Label(interior, text=TITULO_CORTO,
                                        background=E.CARBON, foreground=E.TEXTO_TENUE,
                                        font=E.fuente(E.TAM_AYUDA))
        self.etiqueta_titulo.pack(side="right")
        barra.bind("<Configure>", self._ajustar_barra_estado)

    def _ajustar_barra_estado(self, evento) -> None:
        if evento.width < E.px(900):
            self.etiqueta_titulo.pack_forget()
        elif not self.etiqueta_titulo.winfo_ismapped():
            self.etiqueta_titulo.pack(side="right")

    def _registrar_atajos(self) -> None:
        for indice, (clave, _t, _d) in enumerate(SECCIONES, start=1):
            self.bind_all(f"<Control-Key-{indice}>",
                          lambda _e, c=clave: self.mostrar(c))
        self.bind_all("<F5>", lambda _e: self._recargar_actual())

    def _recargar_actual(self) -> None:
        vista = self.vistas.get(self.seccion_activa)
        if vista is not None and hasattr(vista, "recargar"):
            vista.recargar()

    # ------------------------------------------------------------------
    # Navegacion
    # ------------------------------------------------------------------
    def mostrar(self, clave: str) -> None:
        if clave not in self.vistas:
            self._crear_contenedor(clave)

        for contenedor in self.contenedores.values():
            contenedor.pack_forget()
        self.contenedores[clave].pack(fill="both", expand=True)

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
        elif hasattr(vista, "recargar"):
            vista.recargar()

    def _crear_contenedor(self, clave: str) -> None:
        """Cada vista nace dentro de un marco desplazable.

        Asi, si la pantalla es baja o el usuario encoge la ventana, el
        contenido no se corta: aparece una barra y se puede bajar hasta el
        ultimo boton. En pantallas holgadas la barra ni se muestra.
        """
        contenedor = MarcoDesplazable(self.area)
        vista = self._crear_vista(clave, contenedor.contenido)
        vista.pack(fill="both", expand=True)
        self.contenedores[clave] = contenedor
        self.vistas[clave] = vista

    def _crear_vista(self, clave: str, maestro) -> ttk.Frame:
        if clave == "inicio":
            return VistaInicio(maestro, self.proveedor, ir_a=self.mostrar)
        if clave == "catalogo":
            return VistaCatalogo(maestro, self.proveedor)
        if clave == "prestamos":
            return VistaPrestamos(maestro, self.proveedor,
                                  al_cambiar_datos=self._datos_cambiaron)
        if clave == "usuarios":
            return VistaUsuarios(maestro, self.proveedor)
        return VistaConsultaIA(maestro, self.proveedor)

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

    # Antes de crear la ventana: si no, Windows amplia la interfaz como una
    # imagen y los textos se ven borrosos o recortados.
    E.activar_dpi()

    app = Aplicacion(forzar_demo=args.demo)
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
