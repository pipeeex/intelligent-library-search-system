"""Pantalla de inicio: estado de los nodos y resumen del sistema."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app import estilos as E
from app.componentes import Indicador, Tarjeta, encabezado


class VistaInicio(ttk.Frame):
    def __init__(self, maestro, proveedor, ir_a=None):
        super().__init__(maestro, style="Fondo.TFrame", padding=(26, 22))
        self.proveedor = proveedor
        self.ir_a = ir_a

        encabezado(self, "Panel de inicio",
                   "Estado de las tres bibliotecas y resumen del inventario.")

        self._construir_indicadores()
        self._construir_nodos()
        self._construir_accesos()
        self.recargar()

    def _construir_indicadores(self) -> None:
        fila = ttk.Frame(self, style="Fondo.TFrame")
        fila.pack(fill="x", pady=(0, 18))
        for i in range(4):
            fila.columnconfigure(i, weight=1, uniform="ind")

        self.indicadores = {}
        definicion = [
            ("titulos", "Titulos en catalogo"),
            ("ejemplares", "Ejemplares registrados"),
            ("disponibles", "Ejemplares disponibles"),
            ("sedes", "Bibliotecas en linea"),
        ]
        for columna, (clave, etiqueta) in enumerate(definicion):
            tarjeta = Tarjeta(fila, padding=16)
            tarjeta.ubicar(row=0, column=columna, sticky="nsew",
                           padx=(0 if columna == 0 else 9, 0))
            valor = ttk.Label(tarjeta, text="-", style="Dato.TLabel")
            valor.pack(anchor="w")
            ttk.Label(tarjeta, text=etiqueta, style="DatoPie.TLabel").pack(anchor="w")
            self.indicadores[clave] = valor

    def _construir_nodos(self) -> None:
        tarjeta = Tarjeta(self, "Estado de los nodos",
                          "Cada biblioteca funciona como un nodo autonomo con su propia "
                          "base de datos. El sistema sigue operando si alguna no responde.")
        tarjeta.colocar(fill="x", pady=(0, 18))
        self.contenedor_nodos = ttk.Frame(tarjeta, style="Tarjeta.TFrame")
        self.contenedor_nodos.pack(fill="x")

    def _construir_accesos(self) -> None:
        tarjeta = Tarjeta(self, "Operaciones frecuentes")
        tarjeta.colocar(fill="x")
        fila = ttk.Frame(tarjeta, style="Tarjeta.TFrame")
        fila.pack(fill="x")

        accesos = [
            ("Registrar prestamo", "prestamos", "Primario.TButton"),
            ("Consultar catalogo", "catalogo", "Secundario.TButton"),
            ("Ver usuarios", "usuarios", "Secundario.TButton"),
        ]
        for texto, destino, estilo in accesos:
            ttk.Button(fila, text=texto, style=estilo,
                       command=lambda d=destino: self.ir_a and self.ir_a(d)
                       ).pack(side="left", padx=(0, 10))

    # ------------------------------------------------------------------
    def recargar(self) -> None:
        try:
            estados = self.proveedor.estado_nodos()
        except Exception as exc:  # pragma: no cover
            estados = []
            tk.Label(self.contenedor_nodos, text=f"No se pudo consultar: {exc}",
                     background=E.BLANCO, foreground=E.ROJO,
                     font=E.fuente(10)).pack(anchor="w")
        self.aplicar_estados(estados)

    def aplicar_estados(self, estados: list) -> None:
        """Repinta el panel con estados ya consultados (los trae el monitor)."""
        for hijo in self.contenedor_nodos.winfo_children():
            hijo.destroy()

        en_linea = 0
        for estado in estados:
            marco = tk.Frame(self.contenedor_nodos, background=E.BLANCO)
            marco.pack(fill="x", pady=4)

            if estado.en_linea and estado.base_datos_ok:
                tipo, texto = "ok", "En linea"
                en_linea += 1
            elif estado.en_linea:
                tipo, texto = "aviso", "Sin base de datos"
                en_linea += 1
            else:
                tipo, texto = "error", "Sin respuesta"

            tk.Label(marco, text=f"Nodo {estado.numero}", background=E.BLANCO,
                     foreground=E.TEXTO, font=E.fuente(10, negrita=True),
                     width=10, anchor="w").pack(side="left")
            tk.Label(marco, text=estado.nombre, background=E.BLANCO,
                     foreground=E.TEXTO_SUAVE, font=E.fuente(10),
                     width=22, anchor="w").pack(side="left")
            Indicador(marco, texto, tipo).pack(side="left")
            if estado.detalle:
                tk.Label(marco, text=estado.detalle, background=E.BLANCO,
                         foreground=E.TEXTO_TENUE, font=E.fuente(9)
                         ).pack(side="left", padx=(12, 0))

        self._actualizar_indicadores(en_linea)

    def _actualizar_indicadores(self, sedes_en_linea: int) -> None:
        try:
            filas = self.proveedor.disponibilidad("")
        except Exception:  # pragma: no cover
            filas = []

        titulos = {(f["isbn"], f["titulo"]) for f in filas}
        ejemplares = sum(f.get("total_ejemplares", 0) for f in filas)
        disponibles = sum(f.get("disponibles", 0) for f in filas)

        self.indicadores["titulos"].configure(text=str(len(titulos)))
        self.indicadores["ejemplares"].configure(text=str(ejemplares))
        self.indicadores["disponibles"].configure(text=str(disponibles))
        self.indicadores["sedes"].configure(text=f"{sedes_en_linea} de 3")
