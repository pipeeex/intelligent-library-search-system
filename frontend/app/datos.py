"""Capa de datos de la interfaz.

Expone una sola API para las vistas. Detras puede haber dos proveedores:

* ProveedorGRPC  -> habla con los tres nodos del backend.
* ProveedorDemo  -> datos de prueba en memoria, para cuando no hay servidores.

Las vistas no saben cual de los dos esta activo: ambos devuelven las mismas
estructuras. Toda operacion que modifica informacion devuelve un Resultado.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

MAX_PRESTAMOS_ACTIVOS = 3
DIAS_PRESTAMO_POR_DEFECTO = 15


# ---------------------------------------------------------------------------
# Estructuras comunes
# ---------------------------------------------------------------------------
@dataclass
class Resultado:
    """Respuesta de cualquier operacion de escritura."""

    ok: bool
    mensaje: str
    datos: Any = None

    @classmethod
    def exito(cls, mensaje: str, datos: Any = None) -> "Resultado":
        return cls(True, mensaje, datos)

    @classmethod
    def error(cls, mensaje: str) -> "Resultado":
        return cls(False, mensaje)


@dataclass
class EstadoNodo:
    numero: int
    nombre: str
    en_linea: bool
    base_datos_ok: bool
    detalle: str = ""


# ---------------------------------------------------------------------------
# Proveedor de demostracion (datos de prueba en memoria)
# ---------------------------------------------------------------------------
class ProveedorDemo:
    """Datos de prueba. Replica el catalogo que carga tools/cargar_datos.py."""

    modo = "DEMO"
    descripcion = "Datos de prueba en memoria"

    def __init__(self) -> None:
        self.nodos = {
            1: "Biblioteca 1",
            2: "Biblioteca 2",
            3: "Biblioteca 3",
        }

        # Cada biblioteca tiene su propia tabla Usuario: los codigos se repiten
        # entre sedes y no corresponden a la misma persona.
        self.usuarios_por_nodo: dict[int, list[dict]] = {
            1: [
                {"id_usuario": 1, "nombre": "Ana Maria Torres", "documento": "1012345678",
                 "correo": "ana.torres@example.com", "telefono": "3001112233"},
                {"id_usuario": 2, "nombre": "Carlos Ramirez", "documento": "1023456789",
                 "correo": "carlos.ramirez@example.com", "telefono": "3012223344"},
                {"id_usuario": 3, "nombre": "Laura Gomez", "documento": "1034567890",
                 "correo": "laura.gomez@example.com", "telefono": "3023334455"},
            ],
            2: [
                {"id_usuario": 1, "nombre": "Julian Castro", "documento": "1045678901",
                 "correo": "julian.castro@example.com", "telefono": "3034445566"},
                {"id_usuario": 2, "nombre": "Sofia Herrera", "documento": "1056789012",
                 "correo": "sofia.herrera@example.com", "telefono": "3045556677"},
            ],
            3: [
                {"id_usuario": 1, "nombre": "Daniel Ospina", "documento": "1067890123",
                 "correo": "daniel.ospina@example.com", "telefono": "3056667788"},
                {"id_usuario": 2, "nombre": "Valentina Rios", "documento": "1078901234",
                 "correo": "valentina.rios@example.com", "telefono": "3067778899"},
            ],
        }

        # id_libro, isbn, titulo, autor, editorial, anio, total, disponibles
        self.libros: dict[int, list[dict]] = {
            1: [
                self._libro(101, "9780307474728", "Cien anos de soledad", "Gabriel Garcia Marquez", "Vintage", 1967, 3, 3),
                self._libro(102, "9788437604947", "La ciudad y los perros", "Mario Vargas Llosa", "Catedra", 1963, 2, 2),
                self._libro(103, "9789500720885", "Rayuela", "Julio Cortazar", "Sudamericana", 1963, 2, 1),
                self._libro(104, "9780132350884", "Clean Code", "Robert C. Martin", "Prentice Hall", 2008, 4, 4),
                self._libro(105, "9780201633610", "Design Patterns", "Erich Gamma", "Addison-Wesley", 1994, 2, 2),
                self._libro(106, "9781449373320", "Designing Data-Intensive Applications", "Martin Kleppmann", "O'Reilly", 2017, 1, 0),
            ],
            2: [
                self._libro(201, "9780307474728", "Cien anos de soledad", "Gabriel Garcia Marquez", "Vintage", 1967, 1, 0),
                self._libro(202, "9788420412146", "El Aleph", "Jorge Luis Borges", "Alianza", 1949, 3, 3),
                self._libro(203, "9788497592208", "Pedro Paramo", "Juan Rulfo", "Catedra", 1955, 2, 2),
                self._libro(204, "9780132350884", "Clean Code", "Robert C. Martin", "Prentice Hall", 2008, 1, 1),
                self._libro(205, "9780134685991", "Effective Java", "Joshua Bloch", "Addison-Wesley", 2018, 3, 2),
                self._libro(206, "9781593279288", "Eloquent JavaScript", "Marijn Haverbeke", "No Starch Press", 2018, 2, 2),
            ],
            3: [
                self._libro(301, "9788437604947", "La ciudad y los perros", "Mario Vargas Llosa", "Catedra", 1963, 1, 1),
                self._libro(302, "9788420412146", "El Aleph", "Jorge Luis Borges", "Alianza", 1949, 1, 0),
                self._libro(303, "9789505115952", "El tunel", "Ernesto Sabato", "Seix Barral", 1948, 2, 2),
                self._libro(304, "9780596007126", "Head First Design Patterns", "Eric Freeman", "O'Reilly", 2004, 2, 2),
                self._libro(305, "9781491950357", "Building Microservices", "Sam Newman", "O'Reilly", 2015, 3, 3),
                self._libro(306, "9780262033848", "Introduction to Algorithms", "Thomas H. Cormen", "MIT Press", 2009, 2, 1),
            ],
        }

        ahora = datetime.now()
        self.prestamos: list[dict] = [
            {"id_prestamo": 1, "nodo": 1, "id_usuario": 2, "id_libro": 103,
             "titulo": "Rayuela", "fecha_prestamo": ahora - timedelta(days=4),
             "fecha_vencimiento": ahora + timedelta(days=11), "estado": "ACTIVO"},
            {"id_prestamo": 2, "nodo": 2, "id_usuario": 3, "id_libro": 205,
             "titulo": "Effective Java", "fecha_prestamo": ahora - timedelta(days=20),
             "fecha_vencimiento": ahora - timedelta(days=5), "estado": "VENCIDO"},
            {"id_prestamo": 3, "nodo": 3, "id_usuario": 1, "id_libro": 306,
             "titulo": "Introduction to Algorithms", "fecha_prestamo": ahora - timedelta(days=2),
             "fecha_vencimiento": ahora + timedelta(days=13), "estado": "ACTIVO"},
        ]
        self._siguiente_prestamo = 4

    @staticmethod
    def _libro(id_libro, isbn, titulo, autor, editorial, anio, total, disponibles) -> dict:
        return {
            "id_libro": id_libro, "isbn": isbn, "titulo": titulo, "autor": autor,
            "editorial": editorial, "anio_publicacion": anio,
            "total_ejemplares": total, "disponibles": disponibles,
            "prestados": total - disponibles,
        }

    # -- Consultas ------------------------------------------------------
    def estado_nodos(self) -> list[EstadoNodo]:
        return [
            EstadoNodo(n, nombre, True, True, "modo demostracion")
            for n, nombre in self.nodos.items()
        ]

    def listar_nodos(self) -> dict[int, str]:
        return dict(self.nodos)

    def disponibilidad(self, texto: str = "") -> list[dict]:
        texto = (texto or "").strip().lower()
        filas = []
        for nodo, libros in self.libros.items():
            for libro in libros:
                if texto and texto not in libro["titulo"].lower() \
                        and texto not in libro["autor"].lower() \
                        and texto not in libro["isbn"]:
                    continue
                fila = dict(libro)
                fila["nodo"] = nodo
                fila["biblioteca"] = self.nodos[nodo]
                filas.append(fila)
        return sorted(filas, key=lambda f: (f["titulo"], f["nodo"]))

    def listar_libros(self, nodo: int) -> list[dict]:
        return [dict(l) for l in self.libros.get(nodo, [])]

    def listar_usuarios(self, nodo: int | None = None) -> list[dict]:
        numeros = [nodo] if nodo else sorted(self.usuarios_por_nodo)
        usuarios = []
        for numero in numeros:
            for u in self.usuarios_por_nodo.get(numero, []):
                fila = dict(u)
                fila["nodo"] = numero
                fila["biblioteca"] = self.nodos[numero]
                usuarios.append(fila)
        return usuarios

    def buscar_usuarios(self, texto: str, nodo: int | None = None) -> list[dict]:
        texto = (texto or "").strip().lower()
        usuarios = self.listar_usuarios(nodo)
        if not texto:
            return usuarios
        return [u for u in usuarios
                if texto in u["nombre"].lower() or texto in u["documento"]]

    def listar_prestamos(self, id_usuario: int | None = None,
                         nodo: int | None = None,
                         solo_activos: bool = False) -> list[dict]:
        filas = []
        for p in self.prestamos:
            if id_usuario and p["id_usuario"] != id_usuario:
                continue
            if nodo and p["nodo"] != nodo:
                continue
            if solo_activos and p["estado"] == "DEVUELTO":
                continue
            fila = dict(p)
            fila["biblioteca"] = self.nodos[p["nodo"]]
            fila["usuario"] = self._nombre_usuario(p["nodo"], p["id_usuario"])
            filas.append(fila)
        return sorted(filas, key=lambda f: f["fecha_prestamo"], reverse=True)

    def _nombre_usuario(self, nodo: int, id_usuario: int) -> str:
        for u in self.usuarios_por_nodo.get(nodo, []):
            if u["id_usuario"] == id_usuario:
                return u["nombre"]
        return f"Usuario {id_usuario}"

    def _buscar_libro(self, nodo: int, id_libro: int) -> dict | None:
        for libro in self.libros.get(nodo, []):
            if libro["id_libro"] == id_libro:
                return libro
        return None

    # -- Operacion principal: registrar prestamo ------------------------
    def registrar_prestamo(self, nodo: int, id_usuario: int, id_libro: int,
                           dias: int) -> Resultado:
        libro = self._buscar_libro(nodo, id_libro)
        if libro is None:
            return Resultado.error("El libro seleccionado no existe en esa biblioteca.")

        # El cupo se cuenta dentro de la sede: cada nodo solo conoce sus propios
        # prestamos, igual que en el backend real.
        activos = [p for p in self.prestamos
                   if p["nodo"] == nodo and p["id_usuario"] == id_usuario
                   and p["estado"] in ("ACTIVO", "VENCIDO")]
        if any(p["estado"] == "VENCIDO" for p in activos):
            return Resultado.error(
                "El usuario tiene prestamos vencidos. Debe devolverlos antes de llevar otro libro.")
        if len(activos) >= MAX_PRESTAMOS_ACTIVOS:
            return Resultado.error(
                f"El usuario ya tiene {len(activos)} prestamos activos "
                f"(el maximo permitido es {MAX_PRESTAMOS_ACTIVOS}).")
        if libro["disponibles"] <= 0:
            return Resultado.error(
                f"No hay ejemplares disponibles de '{libro['titulo']}' en {self.nodos[nodo]}.")

        ahora = datetime.now()
        prestamo = {
            "id_prestamo": self._siguiente_prestamo,
            "nodo": nodo,
            "id_usuario": id_usuario,
            "id_libro": id_libro,
            "titulo": libro["titulo"],
            "fecha_prestamo": ahora,
            "fecha_vencimiento": ahora + timedelta(days=dias),
            "estado": "ACTIVO",
        }
        self._siguiente_prestamo += 1
        self.prestamos.append(prestamo)
        libro["disponibles"] -= 1
        libro["prestados"] += 1

        return Resultado.exito(
            f"Prestamo #{prestamo['id_prestamo']} registrado. "
            f"Vence el {prestamo['fecha_vencimiento'].strftime('%d/%m/%Y')}.",
            prestamo)

    def registrar_devolucion(self, nodo: int, id_prestamo: int,
                             observacion: str = "") -> Resultado:
        for p in self.prestamos:
            if p["id_prestamo"] == id_prestamo:
                if p["estado"] == "DEVUELTO":
                    return Resultado.error("Ese prestamo ya fue devuelto.")
                p["estado"] = "DEVUELTO"
                p["observacion"] = observacion
                libro = self._buscar_libro(p["nodo"], p["id_libro"])
                if libro:
                    libro["disponibles"] += 1
                    libro["prestados"] = max(0, libro["prestados"] - 1)
                return Resultado.exito(f"Devolucion del prestamo #{id_prestamo} registrada.")
        return Resultado.error("No se encontro el prestamo indicado.")


# ---------------------------------------------------------------------------
# Proveedor gRPC (backend real)
# ---------------------------------------------------------------------------
class ProveedorGRPC:
    """Habla con los tres nodos del backend mediante gRPC."""

    modo = "CONECTADO"
    descripcion = "Nodos gRPC + SQL Server"

    def __init__(self, cliente_distribuido, modulo_pb, modulo_grpc, clientes) -> None:
        self.cliente = cliente_distribuido
        self.pb = modulo_pb
        self.grpc = modulo_grpc
        self.clientes = clientes  # {numero: ClienteNodo}
        self.nodos = {n: c.nodo.nombre for n, c in clientes.items()}

    # -- Consultas ------------------------------------------------------
    def estado_nodos(self) -> list[EstadoNodo]:
        estados = []
        for respuesta in self.cliente.estado_nodos():
            if respuesta.ok:
                estados.append(EstadoNodo(
                    respuesta.nodo, respuesta.datos.nombre, True,
                    bool(respuesta.datos.base_datos_ok),
                    f"v{respuesta.datos.version}"))
            else:
                estados.append(EstadoNodo(
                    respuesta.nodo, respuesta.nombre, False, False,
                    respuesta.error or "sin respuesta"))
        return estados

    def listar_nodos(self) -> dict[int, str]:
        return dict(self.nodos)

    def disponibilidad(self, texto: str = "") -> list[dict]:
        filas = self.cliente.resumen_disponibilidad(titulo=texto or None)
        if texto and not filas:
            filas = self.cliente.resumen_disponibilidad(autor=texto)
        return sorted(filas, key=lambda f: (f["titulo"], f["nodo"]))

    def listar_libros(self, nodo: int) -> list[dict]:
        cliente = self.clientes[nodo]
        respuesta = cliente.disponibilidad(limite=200)
        return [{
            "id_libro": r.id_libro, "isbn": r.isbn, "titulo": r.titulo, "autor": r.autor,
            "total_ejemplares": r.total_ejemplares, "disponibles": r.disponibles,
            "prestados": r.prestados,
        } for r in respuesta.resultados]

    def listar_usuarios(self, nodo: int | None = None) -> list[dict]:
        """Usuarios de una sede, o de las tres si no se indica cual.

        Cada nodo tiene su propia tabla Usuario, asi que el mismo codigo puede
        corresponder a personas distintas en bibliotecas distintas. Por eso cada
        registro viaja con el nodo al que pertenece.
        """
        numeros = [nodo] if nodo else sorted(self.clientes)
        usuarios: list[dict] = []
        for numero in numeros:
            cliente = self.clientes.get(numero)
            if cliente is None:
                continue
            try:
                respuesta = cliente.stub.ListarUsuarios(self.pb.ListarRequest(limite=200))
            except self.grpc.RpcError:
                continue
            for u in respuesta.usuarios:
                usuarios.append({
                    "id_usuario": u.id_usuario, "nombre": u.nombre,
                    "documento": u.documento, "correo": u.correo,
                    "telefono": u.telefono, "nodo": numero,
                    "biblioteca": self.nodos.get(numero, f"Biblioteca {numero}"),
                })
        return usuarios

    def buscar_usuarios(self, texto: str, nodo: int | None = None) -> list[dict]:
        texto = (texto or "").strip().lower()
        usuarios = self.listar_usuarios(nodo)
        if not texto:
            return usuarios
        return [u for u in usuarios
                if texto in u["nombre"].lower() or texto in u["documento"]]

    def listar_prestamos(self, id_usuario: int | None = None,
                         nodo: int | None = None,
                         solo_activos: bool = False) -> list[dict]:
        """Prestamos de un usuario. El codigo solo es valido dentro de su sede."""
        if not id_usuario or not nodo:
            return []
        cliente = self.clientes.get(nodo)
        if cliente is None:
            return []
        try:
            respuesta = cliente.stub.ListarPrestamos(
                self.pb.ListarPrestamosRequest(
                    id_usuario=id_usuario, solo_activos=solo_activos))
        except self.grpc.RpcError:
            return []
        filas = []
        for p in respuesta.prestamos:
            filas.append({
                "id_prestamo": p.id_prestamo, "nodo": nodo,
                "biblioteca": self.nodos.get(nodo, f"Biblioteca {nodo}"),
                "id_usuario": p.id_usuario, "id_libro": 0,
                "titulo": f"Ejemplar {p.id_ejemplar}",
                "fecha_prestamo": _fecha(p.fecha_prestamo),
                "fecha_vencimiento": _fecha(p.fecha_vencimiento),
                "estado": p.estado, "usuario": "",
            })
        return sorted(filas, key=lambda f: f["fecha_prestamo"] or datetime.min,
                      reverse=True)

    # -- Operacion principal --------------------------------------------
    def registrar_prestamo(self, nodo: int, id_usuario: int, id_libro: int,
                           dias: int) -> Resultado:
        cliente = self.clientes.get(nodo)
        if cliente is None:
            return Resultado.error("La biblioteca seleccionada no esta configurada.")
        try:
            respuesta = cliente.prestar(id_usuario, id_libro, dias)
        except self.grpc.RpcError as exc:
            return Resultado.error(_detalle_grpc(exc))
        p = respuesta.prestamo
        vence = _fecha(p.fecha_vencimiento)
        return Resultado.exito(
            f"Prestamo #{p.id_prestamo} registrado. "
            f"Vence el {vence.strftime('%d/%m/%Y') if vence else p.fecha_vencimiento[:10]}.",
            {"id_prestamo": p.id_prestamo, "id_ejemplar": p.id_ejemplar})

    def registrar_devolucion(self, nodo: int, id_prestamo: int,
                             observacion: str = "") -> Resultado:
        cliente = self.clientes.get(nodo)
        if cliente is None:
            return Resultado.error("La biblioteca seleccionada no esta configurada.")
        try:
            cliente.devolver(id_prestamo, observacion)
        except self.grpc.RpcError as exc:
            return Resultado.error(_detalle_grpc(exc))
        return Resultado.exito(f"Devolucion del prestamo #{id_prestamo} registrada.")


def _fecha(valor: str):
    if not valor:
        return None
    try:
        return datetime.fromisoformat(valor)
    except ValueError:
        return None


def _detalle_grpc(exc) -> str:
    detalle = ""
    try:
        detalle = exc.details() or ""
    except Exception:  # pragma: no cover
        detalle = str(exc)
    return detalle or "El nodo no pudo completar la operacion."


# ---------------------------------------------------------------------------
# Seleccion del proveedor
# ---------------------------------------------------------------------------
def crear_proveedor(forzar_demo: bool = False) -> tuple[Any, str]:
    """Devuelve (proveedor, aviso). Intenta gRPC y cae a demo si no hay nodos."""
    if forzar_demo:
        return ProveedorDemo(), "Modo demostracion solicitado al iniciar."

    raiz = Path(__file__).resolve().parent.parent.parent
    backend = raiz / "backend"
    if not backend.exists():
        return ProveedorDemo(), "No se encontro la carpeta backend."

    if str(backend) not in sys.path:
        sys.path.insert(0, str(backend))

    try:
        import grpc  # noqa: F401
        from grpc_service.cliente import ClienteDistribuido, ClienteNodo
        from grpc_service.generated import biblioteca_pb2 as pb
        from config.settings import get_todos_los_nodos
    except ImportError as exc:
        return ProveedorDemo(), f"No se pudo cargar el cliente gRPC ({exc})."

    try:
        nodos = get_todos_los_nodos()
        distribuido = ClienteDistribuido(nodos)
        estados = distribuido.estado_nodos()
    except Exception as exc:  # pragma: no cover
        return ProveedorDemo(), f"No se pudo contactar a los nodos ({exc})."

    if not any(e.ok for e in estados):
        distribuido.cerrar()
        return ProveedorDemo(), "Ningun nodo respondio. Se usaran datos de prueba."

    clientes = {n.numero: ClienteNodo(n) for n in nodos}
    proveedor = ProveedorGRPC(distribuido, pb, __import__("grpc"), clientes)
    caidos = [e.nodo for e in estados if not e.ok]
    aviso = "" if not caidos else f"Nodos sin respuesta: {', '.join(map(str, caidos))}."
    return proveedor, aviso
