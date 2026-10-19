"""Consulta y visualizacion de los usuarios registrados."""

from __future__ import annotations

from tkinter import ttk

from app.componentes import Aviso, Tabla, Tarjeta, encabezado


class VistaUsuarios(ttk.Frame):
    def __init__(self, maestro, proveedor):
        super().__init__(maestro, style="Fondo.TFrame", padding=(26, 22))
        self.proveedor = proveedor
        self.usuarios: list[dict] = []

        encabezado(self, "Usuarios registrados",
                   "Cada biblioteca administra su propia lista de lectores. "
                   "El codigo solo identifica al usuario dentro de su sede.")

        self.aviso = Aviso(self)

        buscador = Tarjeta(self)
        buscador.colocar(fill="x", pady=(0, 16))
        fila = ttk.Frame(buscador, style="Tarjeta.TFrame")
        fila.pack(fill="x")
        ttk.Label(fila, text="Nombre o documento", style="Campo.TLabel"
                  ).pack(side="left", padx=(0, 12))
        self.entrada = ttk.Entry(fila, width=36)
        self.entrada.pack(side="left")
        self.entrada.bind("<Return>", lambda _e: self.buscar())
        ttk.Button(fila, text="Buscar", style="Primario.TButton",
                   command=self.buscar).pack(side="left", padx=(12, 0))
        ttk.Button(fila, text="Ver todos", style="Secundario.TButton",
                   command=self.recargar).pack(side="left", padx=(8, 0))

        tarjeta = Tarjeta(self, "Listado")
        tarjeta.colocar(fill="both", expand=True)
        self.tabla = Tabla(tarjeta, [
            ("biblioteca", "Biblioteca", 125),
            ("id_usuario", "Codigo", 70),
            ("nombre", "Nombre", 210),
            ("documento", "Documento", 125),
            ("correo", "Correo", 215),
            ("telefono", "Telefono", 110),
        ], alto=16)
        self.tabla.pack(fill="both", expand=True)

        self.pie = ttk.Label(tarjeta, text="", style="Ayuda.TLabel")
        self.pie.pack(anchor="w", pady=(12, 0))

        self.recargar()

    def buscar(self) -> None:
        self._consultar(self.entrada.get().strip())

    def recargar(self) -> None:
        self.entrada.delete(0, "end")
        self._consultar("")

    def _consultar(self, texto: str) -> None:
        self.aviso.ocultar()
        try:
            self.usuarios = self.proveedor.buscar_usuarios(texto)
        except Exception as exc:  # pragma: no cover
            self.usuarios = []
            self.aviso.mostrar(f"No se pudo consultar: {exc}", "error")
        self.tabla.cargar(self.usuarios)
        sedes = {u.get("biblioteca", "") for u in self.usuarios}
        self.pie.configure(
            text=f"{len(self.usuarios)} usuario(s) en {len(sedes)} biblioteca(s).")
        if texto and not self.usuarios:
            self.aviso.mostrar(f"Ningun usuario coincide con '{texto}'.", "aviso")
