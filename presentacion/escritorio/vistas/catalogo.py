"""Consulta del catalogo y de la disponibilidad en las tres bibliotecas."""

from __future__ import annotations

from tkinter import ttk

from presentacion.escritorio.componentes import Aviso, Tabla, Tarjeta, encabezado


class VistaCatalogo(ttk.Frame):
    def __init__(self, maestro, proveedor):
        super().__init__(maestro, style="Fondo.TFrame", padding=(26, 22))
        self.proveedor = proveedor
        self.filas: list[dict] = []

        encabezado(self, "Catalogo y disponibilidad",
                   "La busqueda se envia a las tres bibliotecas y el resultado se "
                   "presenta unificado, indicando en que sede hay ejemplares libres.")

        self.aviso = Aviso(self)

        buscador = Tarjeta(self)
        buscador.colocar(fill="x", pady=(0, 16))
        fila = ttk.Frame(buscador, style="Tarjeta.TFrame")
        fila.pack(fill="x")

        ttk.Label(fila, text="Buscar por titulo, autor o ISBN",
                  style="Campo.TLabel").pack(side="left", padx=(0, 12))
        self.entrada = ttk.Entry(fila, width=42)
        self.entrada.pack(side="left")
        self.entrada.bind("<Return>", lambda _e: self.buscar())
        ttk.Button(fila, text="Buscar", style="Primario.TButton",
                   command=self.buscar).pack(side="left", padx=(12, 0))
        ttk.Button(fila, text="Ver todo", style="Secundario.TButton",
                   command=self.ver_todo).pack(side="left", padx=(8, 0))

        tarjeta = Tarjeta(self, "Resultados")
        tarjeta.colocar(fill="both", expand=True)

        self.tabla = Tabla(tarjeta, [
            ("titulo", "Titulo", 240),
            ("autor", "Autor", 175),
            ("isbn", "ISBN", 135),
            ("biblioteca", "Biblioteca", 125),
            ("disponibles", "Disponibles", 100),
            ("total_ejemplares", "Total", 70),
        ], alto=16)
        self.tabla.pack(fill="both", expand=True)

        self.pie = ttk.Label(tarjeta, text="", style="Ayuda.TLabel")
        self.pie.pack(anchor="w", pady=(12, 0))

        self.ver_todo()

    def buscar(self) -> None:
        self._consultar(self.entrada.get().strip())

    def ver_todo(self) -> None:
        self.entrada.delete(0, "end")
        self._consultar("")

    def _consultar(self, texto: str) -> None:
        self.aviso.ocultar()
        try:
            self.filas = self.proveedor.disponibilidad(texto)
        except Exception as exc:  # pragma: no cover
            self.filas = []
            self.aviso.mostrar(f"No se pudo consultar: {exc}", "error")

        self.tabla.cargar(self.filas,
                          etiquetas=lambda f: "alerta" if f.get("disponibles", 0) == 0 else "")

        if not self.filas:
            self.pie.configure(text="Sin resultados para esa busqueda.")
            if texto:
                self.aviso.mostrar(
                    f"No se encontro ningun titulo que coincida con '{texto}'.", "aviso")
            return

        sedes = {f["biblioteca"] for f in self.filas}
        libres = sum(f.get("disponibles", 0) for f in self.filas)
        self.pie.configure(
            text=f"{len(self.filas)} registro(s) en {len(sedes)} biblioteca(s). "
                 f"{libres} ejemplar(es) disponible(s) en total.")

    def recargar(self) -> None:
        self._consultar(self.entrada.get().strip())
