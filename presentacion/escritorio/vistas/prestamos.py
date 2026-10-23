"""Operacion principal del sistema: registrar un prestamo.

Cubre el requerimiento RF-06 del documento maestro y el caso de uso CU-06.
La vista hace tres cosas: valida los campos obligatorios antes de enviar nada,
registra el prestamo contra el nodo correspondiente y muestra el resultado
junto con los prestamos vigentes del usuario.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from presentacion.escritorio import estilos as E
from presentacion.escritorio.componentes import Aviso, CampoFormulario, Tabla, Tarjeta, encabezado

DIAS_POR_DEFECTO = "15"
DIAS_MINIMO = 1
DIAS_MAXIMO = 30


class VistaPrestamos(ttk.Frame):
    def __init__(self, maestro, proveedor, al_cambiar_datos=None):
        super().__init__(maestro, style="Fondo.TFrame", padding=(26, 22))
        self.proveedor = proveedor
        self.al_cambiar_datos = al_cambiar_datos
        self.usuarios: list[dict] = []
        self.libros: list[dict] = []
        self.prestamos: list[dict] = []

        encabezado(self, "Registrar prestamo",
                   "Operacion principal del sistema transaccional. "
                   "Los campos marcados con * son obligatorios.")

        self.aviso = Aviso(self)

        cuerpo = ttk.Frame(self, style="Fondo.TFrame")
        cuerpo.pack(fill="both", expand=True)
        cuerpo.columnconfigure(0, weight=0, minsize=400)
        cuerpo.columnconfigure(1, weight=1)
        cuerpo.rowconfigure(0, weight=1)

        self._construir_formulario(cuerpo)
        self._construir_panel_derecho(cuerpo)

        self.recargar()

    # ------------------------------------------------------------------
    # Construccion
    # ------------------------------------------------------------------
    def _construir_formulario(self, maestro) -> None:
        tarjeta = Tarjeta(maestro, "Datos del prestamo",
                          "El sistema verifica la disponibilidad del ejemplar y el "
                          "cupo del usuario antes de confirmar.", wraplength=380)
        tarjeta.ubicar(row=0, column=0, sticky="nsew", padx=(0, 18))

        self.campo_biblioteca = CampoFormulario(
            tarjeta, "Biblioteca", control="combo", obligatorio=True, ancho=34)
        self.campo_biblioteca.pack(fill="x", pady=(0, 12))
        self.campo_biblioteca.control.bind(
            "<<ComboboxSelected>>", lambda _e: self._cambio_biblioteca())

        self.campo_usuario = CampoFormulario(
            tarjeta, "Usuario", control="combo", obligatorio=True, ancho=34,
            ayuda="Se identifica por nombre y numero de documento.")
        self.campo_usuario.pack(fill="x", pady=(0, 12))
        self.campo_usuario.control.bind(
            "<<ComboboxSelected>>", lambda _e: self._mostrar_prestamos_usuario())

        self.campo_libro = CampoFormulario(
            tarjeta, "Libro", control="combo", obligatorio=True, ancho=34,
            ayuda="Solo se listan los titulos con ejemplares en esa sede.")
        self.campo_libro.pack(fill="x", pady=(0, 12))
        self.campo_libro.control.bind(
            "<<ComboboxSelected>>", lambda _e: self._mostrar_disponibilidad())

        self.disponibilidad = ttk.Label(tarjeta, text="", style="Ayuda.TLabel")
        self.disponibilidad.pack(anchor="w", pady=(0, 12))

        self.campo_dias = CampoFormulario(
            tarjeta, "Dias de prestamo", control="spin", obligatorio=True,
            ayuda=f"Numero entero entre {DIAS_MINIMO} y {DIAS_MAXIMO}.")
        self.campo_dias.pack(fill="x", pady=(0, 16))
        self.campo_dias.asignar(DIAS_POR_DEFECTO)

        botones = ttk.Frame(tarjeta, style="Tarjeta.TFrame")
        botones.pack(fill="x")
        ttk.Button(botones, text="Registrar prestamo", style="Primario.TButton",
                   command=self.registrar).pack(side="left")
        ttk.Button(botones, text="Limpiar", style="Secundario.TButton",
                   command=self.limpiar).pack(side="left", padx=(10, 0))

    def _construir_panel_derecho(self, maestro) -> None:
        columna = ttk.Frame(maestro, style="Fondo.TFrame")
        columna.grid(row=0, column=1, sticky="nsew")

        tarjeta = Tarjeta(columna, "Prestamos del usuario seleccionado",
                          "Se marcan en rojo los que ya estan vencidos.")
        tarjeta.colocar(fill="both", expand=True)

        self.tabla = Tabla(tarjeta, [
            ("id_prestamo", "N.o", 45),
            ("titulo", "Ejemplar prestado", 150),
            ("biblioteca", "Biblioteca", 95),
            ("fecha_prestamo", "Desde", 85),
            ("fecha_vencimiento", "Vence", 85),
            ("estado", "Estado", 72),
        ], alto=12, al_seleccionar=self._al_seleccionar_prestamo)
        self.tabla.pack(fill="both", expand=True)

        pie = ttk.Frame(tarjeta, style="Tarjeta.TFrame")
        pie.pack(fill="x", pady=(14, 0))
        self.boton_devolver = ttk.Button(pie, text="Registrar devolucion",
                                         style="Secundario.TButton",
                                         command=self.devolver, state="disabled")
        self.boton_devolver.pack(side="left")
        self.resumen = ttk.Label(pie, text="", style="Ayuda.TLabel")
        self.resumen.pack(side="right")

    # ------------------------------------------------------------------
    # Carga de datos
    # ------------------------------------------------------------------
    def recargar(self, conservar: bool = False) -> None:
        """Relee nodos, usuarios y catalogo desde el proveedor.

        Con conservar=True mantiene lo que ya estaba elegido, de modo que entrar
        y salir de la seccion no borre un formulario a medio llenar. Se invoca
        cada vez que se abre la pantalla: asi un usuario creado directamente en
        SQL Server aparece sin reiniciar la aplicacion.
        """
        documento_previo = None
        id_libro_previo = None
        if conservar:
            usuario = self._usuario_seleccionado()
            documento_previo = usuario["documento"] if usuario else None
            libro = self._libro_seleccionado()
            id_libro_previo = libro["id_libro"] if libro else None

        nodos = self.proveedor.listar_nodos()
        self.nodos = nodos
        nodo_previo = self.campo_biblioteca.valor()
        self.campo_biblioteca.opciones([f"{n} - {nombre}" for n, nombre in nodos.items()])
        if nodos and not (conservar and nodo_previo):
            primero = min(nodos)
            self.campo_biblioteca.asignar(f"{primero} - {nodos[primero]}")

        self._cargar_usuarios(documento_previo)
        self._cargar_libros(id_libro_previo)

    def _cambio_biblioteca(self) -> None:
        """Al cambiar de sede hay que releer sus usuarios y su catalogo.

        Cada biblioteca administra su propia tabla de usuarios, de modo que un
        lector registrado en Biblioteca 3 solo puede recibir prestamos alli.
        """
        self._cargar_usuarios()
        self._cargar_libros()
        self.tabla.vaciar()
        self.resumen.configure(text="")
        self.boton_devolver.configure(state="disabled")

    def _cargar_usuarios(self, documento_previo: str | None = None) -> None:
        nodo = self._nodo_seleccionado()
        self.usuarios = []
        if nodo:
            try:
                self.usuarios = self.proveedor.listar_usuarios(nodo)
            except Exception as exc:  # pragma: no cover
                self.aviso.mostrar(f"No se pudieron cargar los usuarios: {exc}", "error")

        self.campo_usuario.opciones(
            [f"{u['nombre']} ({u['documento']})" for u in self.usuarios])

        indice = None
        if documento_previo:
            indice = next((i for i, u in enumerate(self.usuarios)
                           if u["documento"] == documento_previo), None)
        if indice is None:
            self.campo_usuario.asignar("")
        else:
            self.campo_usuario.control.current(indice)

    def refrescar_listas(self) -> int:
        """Relee los datos conservando la seleccion. Devuelve usuarios nuevos."""
        antes = {u["documento"] for u in self.usuarios}
        self.recargar(conservar=True)
        return len([u for u in self.usuarios if u["documento"] not in antes])

    def _nodo_seleccionado(self) -> int | None:
        texto = self.campo_biblioteca.valor()
        if not texto:
            return None
        try:
            return int(texto.split(" - ")[0])
        except (ValueError, IndexError):
            return None

    def _usuario_seleccionado(self) -> dict | None:
        indice = self.campo_usuario.control.current()
        if indice is None or indice < 0 or indice >= len(self.usuarios):
            return None
        return self.usuarios[indice]

    def _libro_seleccionado(self) -> dict | None:
        indice = self.campo_libro.control.current()
        if indice is None or indice < 0 or indice >= len(self.libros):
            return None
        return self.libros[indice]

    def _cargar_libros(self, id_libro_previo: int | None = None) -> None:
        nodo = self._nodo_seleccionado()
        self.libros = []
        if nodo:
            try:
                self.libros = self.proveedor.listar_libros(nodo)
            except Exception as exc:  # pragma: no cover
                self.aviso.mostrar(f"No se pudo leer el catalogo: {exc}", "error")
        etiquetas = [
            f"{l['titulo']} - {l['autor']}  ({l['disponibles']} de {l['total_ejemplares']})"
            for l in self.libros
        ]
        self.campo_libro.opciones(etiquetas)

        indice = None
        if id_libro_previo is not None:
            indice = next((i for i, l in enumerate(self.libros)
                           if l["id_libro"] == id_libro_previo), None)
        if indice is None:
            self.campo_libro.asignar("")
            self.disponibilidad.configure(text="")
        else:
            self.campo_libro.control.current(indice)
            self._mostrar_disponibilidad()

    def _mostrar_disponibilidad(self) -> None:
        libro = self._libro_seleccionado()
        if not libro:
            self.disponibilidad.configure(text="")
            return
        libres = libro["disponibles"]
        if libres > 0:
            texto = f"Hay {libres} ejemplar(es) disponible(s) de {libro['total_ejemplares']}."
        else:
            texto = "Sin ejemplares disponibles en esta sede."
        self.disponibilidad.configure(text=texto)
        self.campo_libro.limpiar_error()

    def _mostrar_prestamos_usuario(self) -> None:
        usuario = self._usuario_seleccionado()
        self.campo_usuario.limpiar_error()
        if not usuario:
            self.tabla.vaciar()
            self.resumen.configure(text="")
            return
        try:
            self.prestamos = self.proveedor.listar_prestamos(
                usuario["id_usuario"], usuario.get("nodo") or self._nodo_seleccionado())
        except Exception as exc:  # pragma: no cover
            self.prestamos = []
            self.aviso.mostrar(f"No se pudieron leer los prestamos: {exc}", "error")

        filas = []
        for p in self.prestamos:
            filas.append({
                "id_prestamo": p["id_prestamo"],
                "titulo": p.get("titulo", ""),
                "biblioteca": p.get("biblioteca", ""),
                "fecha_prestamo": _fecha_corta(p.get("fecha_prestamo")),
                "fecha_vencimiento": _fecha_corta(p.get("fecha_vencimiento")),
                "estado": p.get("estado", ""),
            })
        self.tabla.cargar(filas, etiquetas=lambda f: "alerta" if f["estado"] == "VENCIDO" else "")

        activos = [p for p in self.prestamos if p.get("estado") in ("ACTIVO", "VENCIDO")]
        vencidos = [p for p in activos if p.get("estado") == "VENCIDO"]
        texto = f"{len(activos)} prestamo(s) activo(s)"
        if vencidos:
            texto += f", {len(vencidos)} vencido(s)"
        self.resumen.configure(text=texto)
        self.boton_devolver.configure(state="disabled")

    def _al_seleccionar_prestamo(self) -> None:
        indice = self.tabla.indice_seleccionado()
        habilitado = "normal"
        if indice is None or indice >= len(self.prestamos):
            habilitado = "disabled"
        elif self.prestamos[indice].get("estado") == "DEVUELTO":
            habilitado = "disabled"
        self.boton_devolver.configure(state=habilitado)

    # ------------------------------------------------------------------
    # Validacion y registro
    # ------------------------------------------------------------------
    def _validar(self) -> tuple[bool, dict]:
        """Valida los campos obligatorios. Devuelve (valido, datos)."""
        for campo in (self.campo_biblioteca, self.campo_usuario,
                      self.campo_libro, self.campo_dias):
            campo.limpiar_error()

        errores = 0
        datos: dict = {}

        nodo = self._nodo_seleccionado()
        if nodo is None:
            self.campo_biblioteca.marcar_error("Seleccione la biblioteca.")
            errores += 1
        datos["nodo"] = nodo

        usuario = self._usuario_seleccionado()
        if usuario is None:
            self.campo_usuario.marcar_error("Seleccione el usuario que recibe el libro.")
            errores += 1
        datos["usuario"] = usuario

        libro = self._libro_seleccionado()
        if libro is None:
            self.campo_libro.marcar_error("Seleccione el libro que va a prestar.")
            errores += 1
        elif libro["disponibles"] <= 0:
            self.campo_libro.marcar_error("Ese titulo no tiene ejemplares disponibles.")
            errores += 1
        datos["libro"] = libro

        texto_dias = self.campo_dias.valor()
        if not texto_dias:
            self.campo_dias.marcar_error("Indique los dias de prestamo.")
            errores += 1
        elif not texto_dias.isdigit():
            self.campo_dias.marcar_error("Escriba solo numeros.")
            errores += 1
        elif not (DIAS_MINIMO <= int(texto_dias) <= DIAS_MAXIMO):
            self.campo_dias.marcar_error(
                f"Debe estar entre {DIAS_MINIMO} y {DIAS_MAXIMO} dias.")
            errores += 1
        else:
            datos["dias"] = int(texto_dias)

        return errores == 0, datos

    def registrar(self) -> None:
        self.aviso.ocultar()
        valido, datos = self._validar()
        if not valido:
            self.aviso.mostrar(
                "Revise los campos marcados: hay informacion obligatoria sin completar.",
                "error")
            return

        resultado = self.proveedor.registrar_prestamo(
            datos["nodo"], datos["usuario"]["id_usuario"],
            datos["libro"]["id_libro"], datos["dias"])

        if resultado.ok:
            self.aviso.mostrar(
                f"{resultado.mensaje}  Libro: {datos['libro']['titulo']}. "
                f"Usuario: {datos['usuario']['nombre']}.", "ok")
            self._cargar_libros()
            self._mostrar_prestamos_usuario()
            if self.al_cambiar_datos:
                self.al_cambiar_datos()
        else:
            self.aviso.mostrar(resultado.mensaje, "aviso")

    def devolver(self) -> None:
        indice = self.tabla.indice_seleccionado()
        if indice is None or indice >= len(self.prestamos):
            return
        prestamo = self.prestamos[indice]
        resultado = self.proveedor.registrar_devolucion(
            prestamo["nodo"], prestamo["id_prestamo"], "Devolucion desde la aplicacion")
        if resultado.ok:
            self.aviso.mostrar(resultado.mensaje, "ok")
            self._cargar_libros()
            self._mostrar_prestamos_usuario()
            if self.al_cambiar_datos:
                self.al_cambiar_datos()
        else:
            self.aviso.mostrar(resultado.mensaje, "aviso")

    def limpiar(self) -> None:
        self.aviso.ocultar()
        self.campo_usuario.asignar("")
        self.campo_libro.asignar("")
        self.campo_dias.asignar(DIAS_POR_DEFECTO)
        for campo in (self.campo_biblioteca, self.campo_usuario,
                      self.campo_libro, self.campo_dias):
            campo.limpiar_error()
        self.disponibilidad.configure(text="")
        self.tabla.vaciar()
        self.resumen.configure(text="")
        self.boton_devolver.configure(state="disabled")


def _fecha_corta(valor) -> str:
    if valor is None:
        return ""
    if hasattr(valor, "strftime"):
        return valor.strftime("%d/%m/%Y")
    return str(valor)[:10]
