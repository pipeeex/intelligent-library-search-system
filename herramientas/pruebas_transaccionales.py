"""Suite de pruebas transaccionales del sistema distribuido.

Ejecuta casos verificables contra los nodos que esten levantados y deja un
reporte fechado en docs/evidencias/. Cada caso compara el estado de la base
antes y despues de la operacion, de modo que el resultado no depende de lo que
diga la aplicacion sino de lo que realmente quedo guardado.

Uso:
    python herramientas/pruebas_transaccionales.py
    python herramientas/pruebas_transaccionales.py --nodo 2
    python herramientas/pruebas_transaccionales.py --sin-reporte

Requisitos: los nodos levantados y los datos de ejemplo cargados
(python herramientas/cargar_datos.py --todos).
"""

from __future__ import annotations

import argparse
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import grpc  # noqa: E402

from configuracion.ajustes import (  # noqa: E402
    NODOS_VALIDOS,
    NodoConfig,
    get_nodo_config,
    get_todos_los_nodos,
)
from presentacion.servicios.cliente_grpc import (  # noqa: E402
    ClienteDistribuido,
    ClienteNodo,
)
from presentacion.servicios.generados import biblioteca_pb2 as pb  # noqa: E402

PUERTO_INEXISTENTE = 59999


# ---------------------------------------------------------------------------
# Registro de resultados
# ---------------------------------------------------------------------------
@dataclass
class Comprobacion:
    descripcion: str
    esperado: str
    obtenido: str
    ok: bool


@dataclass
class Caso:
    codigo: str
    nombre: str
    objetivo: str
    comprobaciones: list[Comprobacion] = field(default_factory=list)
    estado: str = "PENDIENTE"
    detalle: str = ""
    segundos: float = 0.0

    def verificar(self, descripcion: str, esperado, obtenido) -> bool:
        ok = esperado == obtenido
        self.comprobaciones.append(
            Comprobacion(descripcion, str(esperado), str(obtenido), ok))
        return ok

    @property
    def paso(self) -> bool:
        return self.estado == "PASA"


class Suite:
    def __init__(self) -> None:
        self.casos: list[Caso] = []
        self.inicio = datetime.now()

    def ejecutar(self, codigo, nombre, objetivo, funcion) -> Caso:
        caso = Caso(codigo, nombre, objetivo)
        self.casos.append(caso)
        print(f"\n[{codigo}] {nombre}")
        arranque = time.time()
        try:
            funcion(caso)
            if caso.estado == "PENDIENTE":
                caso.estado = "PASA" if all(c.ok for c in caso.comprobaciones) else "FALLA"
        except _Omitir as exc:
            caso.estado = "OMITIDO"
            caso.detalle = str(exc)
        except grpc.RpcError as exc:
            caso.estado = "FALLA"
            caso.detalle = f"gRPC {exc.code().name}: {exc.details()}"
        except Exception as exc:  # pragma: no cover
            caso.estado = "FALLA"
            caso.detalle = f"{type(exc).__name__}: {exc}"
        caso.segundos = round(time.time() - arranque, 2)

        for c in caso.comprobaciones:
            marca = "  OK  " if c.ok else " FALLA"
            print(f"   {marca}  {c.descripcion}")
            if not c.ok:
                print(f"           esperado: {c.esperado}")
                print(f"           obtenido: {c.obtenido}")
        if caso.detalle:
            print(f"          {caso.detalle}")
        print(f"   -> {caso.estado} ({caso.segundos} s)")
        return caso


class _Omitir(Exception):
    """El caso no se puede ejecutar con los datos disponibles."""


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def disponibles_de(cliente: ClienteNodo, id_libro: int) -> int:
    respuesta = cliente.stub.ListarEjemplares(
        pb.ListarEjemplaresRequest(id_libro=id_libro, solo_disponibles=True))
    return len(respuesta.ejemplares)


def usuarios_de(cliente: ClienteNodo, limite: int = 50) -> list:
    return list(cliente.stub.ListarUsuarios(pb.ListarRequest(limite=limite)).usuarios)


def catalogo_de(cliente: ClienteNodo) -> list:
    return list(cliente.disponibilidad(limite=200).resultados)


def prestamos_de(cliente: ClienteNodo, id_usuario: int, solo_activos=False) -> list:
    return list(cliente.stub.ListarPrestamos(
        pb.ListarPrestamosRequest(id_usuario=id_usuario,
                                  solo_activos=solo_activos)).prestamos)


def elegir_libro_disponible(catalogo: list):
    candidatos = [c for c in catalogo if c.disponibles > 0]
    if not candidatos:
        raise _Omitir("Ningun titulo tiene ejemplares disponibles en este nodo.")
    return min(candidatos, key=lambda c: c.disponibles)


# ---------------------------------------------------------------------------
# PT-01  Consulta de disponibilidad distribuida
# ---------------------------------------------------------------------------
def pt01_disponibilidad(caso: Caso, distribuido: ClienteDistribuido) -> None:
    caso.objetivo = ("La consulta llega a las tres bibliotecas y el resultado "
                     "se presenta unificado por sede.")
    respuestas = distribuido.estado_nodos()
    vivos = [r for r in respuestas if r.ok]
    caso.verificar("Al menos un nodo responde al Ping", True, len(vivos) >= 1)

    filas = distribuido.resumen_disponibilidad()
    caso.verificar("La consulta distribuida devuelve registros", True, len(filas) > 0)

    sedes = sorted({f["nodo"] for f in filas})
    caso.verificar("Los registros vienen identificados por sede",
                   True, len(sedes) >= 1)

    completos = all(
        {"titulo", "disponibles", "total_ejemplares", "biblioteca"} <= set(f)
        for f in filas)
    caso.verificar("Cada fila trae titulo, sede y conteo de ejemplares",
                   True, completos)

    coherentes = all(0 <= f["disponibles"] <= f["total_ejemplares"] for f in filas)
    caso.verificar("Disponibles nunca supera el total de ejemplares",
                   True, coherentes)

    caso.detalle = (f"{len(filas)} registros desde las sedes {sedes}; "
                    f"{len(vivos)} de {len(respuestas)} nodos en linea.")


# ---------------------------------------------------------------------------
# PT-02  Sincronizacion entre bibliotecas
# ---------------------------------------------------------------------------
def pt02_sincronizacion(caso: Caso, distribuido: ClienteDistribuido,
                        cliente: ClienteNodo, nodo: int) -> None:
    caso.objetivo = ("Una operacion ejecutada en una sede se refleja de "
                     "inmediato en la consulta agregada de las tres, sin "
                     "reiniciar ni sincronizar a mano.")
    catalogo = catalogo_de(cliente)
    libro = elegir_libro_disponible(catalogo)
    usuarios = usuarios_de(cliente)
    if not usuarios:
        raise _Omitir("El nodo no tiene usuarios registrados.")

    def disponibles_vista_global() -> int:
        filas = distribuido.resumen_disponibilidad(titulo=libro.titulo)
        propias = [f for f in filas
                   if f["nodo"] == nodo and f["id_libro"] == libro.id_libro]
        return propias[0]["disponibles"] if propias else -1

    antes = disponibles_vista_global()
    caso.verificar("La vista global ve el titulo antes del prestamo",
                   True, antes >= 1)

    prestamo = cliente.prestar(usuarios[0].id_usuario, libro.id_libro, 7).prestamo
    despues = disponibles_vista_global()
    caso.verificar("La vista global refleja el prestamo al instante",
                   antes - 1, despues)

    cliente.devolver(prestamo.id_prestamo, "PT-02")
    final = disponibles_vista_global()
    caso.verificar("La vista global refleja la devolucion al instante",
                   antes, final)

    caso.detalle = (f"Titulo '{libro.titulo}' en la sede {nodo}: "
                    f"{antes} -> {despues} -> {final} disponibles.")


# ---------------------------------------------------------------------------
# PT-03 / PT-04  Prestamo y devolucion
# ---------------------------------------------------------------------------
def pt03_prestamo(caso: Caso, cliente: ClienteNodo, contexto: dict) -> None:
    caso.objetivo = ("El prestamo descuenta un ejemplar y queda registrado "
                     "como ACTIVO en una sola transaccion.")
    catalogo = catalogo_de(cliente)
    libro = elegir_libro_disponible(catalogo)
    usuarios = usuarios_de(cliente)
    if not usuarios:
        raise _Omitir("El nodo no tiene usuarios registrados.")
    usuario = usuarios[0]

    antes = disponibles_de(cliente, libro.id_libro)
    activos_antes = len(prestamos_de(cliente, usuario.id_usuario, solo_activos=True))

    prestamo = cliente.prestar(usuario.id_usuario, libro.id_libro, 7).prestamo
    contexto["prestamo"] = prestamo
    contexto["libro"] = libro
    contexto["usuario"] = usuario
    contexto["disponibles_antes"] = antes

    caso.verificar("El prestamo queda en estado ACTIVO", "ACTIVO", prestamo.estado)
    caso.verificar("El inventario baja exactamente en un ejemplar",
                   antes - 1, disponibles_de(cliente, libro.id_libro))
    caso.verificar("El prestamo aparece entre los activos del usuario",
                   activos_antes + 1,
                   len(prestamos_de(cliente, usuario.id_usuario, solo_activos=True)))
    caso.verificar("Se asigno un ejemplar concreto", True, prestamo.id_ejemplar > 0)
    caso.verificar("La fecha de vencimiento es posterior a la de prestamo",
                   True, prestamo.fecha_vencimiento > prestamo.fecha_prestamo)

    caso.detalle = (f"Prestamo #{prestamo.id_prestamo} del ejemplar "
                    f"{prestamo.id_ejemplar} ('{libro.titulo}') al usuario "
                    f"{usuario.nombre}. Vence el {prestamo.fecha_vencimiento[:10]}.")


def pt04_devolucion(caso: Caso, cliente: ClienteNodo, contexto: dict) -> None:
    caso.objetivo = ("La devolucion cierra el prestamo y devuelve el ejemplar "
                     "al inventario disponible.")
    prestamo = contexto.get("prestamo")
    libro = contexto.get("libro")
    if prestamo is None or libro is None:
        raise _Omitir("PT-03 no dejo un prestamo que devolver.")

    cliente.devolver(prestamo.id_prestamo, "PT-04")

    caso.verificar("El inventario vuelve a su valor original",
                   contexto["disponibles_antes"],
                   disponibles_de(cliente, libro.id_libro))

    todos = prestamos_de(cliente, contexto["usuario"].id_usuario)
    cerrado = next((p for p in todos if p.id_prestamo == prestamo.id_prestamo), None)
    caso.verificar("El prestamo queda marcado como DEVUELTO",
                   "DEVUELTO", cerrado.estado if cerrado else "no encontrado")

    activos = prestamos_de(cliente, contexto["usuario"].id_usuario, solo_activos=True)
    caso.verificar("El prestamo ya no figura entre los activos",
                   False, any(p.id_prestamo == prestamo.id_prestamo for p in activos))

    caso.detalle = f"Prestamo #{prestamo.id_prestamo} cerrado correctamente."


# ---------------------------------------------------------------------------
# PT-05  Reglas de negocio y codigos de error
# ---------------------------------------------------------------------------
def pt05_reglas(caso: Caso, cliente: ClienteNodo, contexto: dict) -> None:
    caso.objetivo = ("Las operaciones invalidas se rechazan con el codigo gRPC "
                     "correcto, sin que el servidor se caiga.")
    usuarios = usuarios_de(cliente)
    if not usuarios:
        raise _Omitir("El nodo no tiene usuarios registrados.")

    prestamo = contexto.get("prestamo")
    if prestamo is not None:
        codigo = _codigo_de_error(lambda: cliente.devolver(prestamo.id_prestamo))
        caso.verificar("Devolver dos veces el mismo prestamo",
                       "FAILED_PRECONDITION", codigo)

    codigo = _codigo_de_error(
        lambda: cliente.prestar(usuarios[0].id_usuario, 999999, 7))
    caso.verificar("Prestar un libro inexistente", "NOT_FOUND", codigo)

    codigo = _codigo_de_error(lambda: cliente.prestar(999999, 1, 7))
    caso.verificar("Prestar a un usuario inexistente", "NOT_FOUND", codigo)

    agotados = [c for c in catalogo_de(cliente)
                if c.total_ejemplares > 0 and c.disponibles == 0]
    if agotados:
        codigo = _codigo_de_error(
            lambda: cliente.prestar(usuarios[0].id_usuario, agotados[0].id_libro, 7))
        caso.verificar("Prestar un titulo sin ejemplares libres",
                       "RESOURCE_EXHAUSTED", codigo)
    else:
        caso.detalle = ("No habia titulos agotados para probar "
                        "RESOURCE_EXHAUSTED en este nodo.")

    vivo = cliente.ping()
    caso.verificar("El nodo sigue en pie despues de los rechazos",
                   True, bool(vivo.nombre))


def _codigo_de_error(operacion) -> str:
    try:
        operacion()
    except grpc.RpcError as exc:
        return exc.code().name
    return "SIN ERROR"


# ---------------------------------------------------------------------------
# PT-06  Atomicidad
# ---------------------------------------------------------------------------
def pt06_atomicidad(caso: Caso, cliente: ClienteNodo) -> None:
    caso.objetivo = ("Una operacion rechazada no deja rastro: ni prestamo "
                     "registrado ni ejemplar descontado.")
    usuarios = usuarios_de(cliente)
    catalogo = catalogo_de(cliente)
    if not usuarios or not catalogo:
        raise _Omitir("Faltan usuarios o catalogo en este nodo.")

    usuario = usuarios[0]
    libro = elegir_libro_disponible(catalogo)

    inventario_antes = disponibles_de(cliente, libro.id_libro)
    prestamos_antes = len(prestamos_de(cliente, usuario.id_usuario))

    codigo = _codigo_de_error(lambda: cliente.prestar(usuario.id_usuario, 999999, 7))
    caso.verificar("La operacion invalida es rechazada", "NOT_FOUND", codigo)
    caso.verificar("El inventario queda intacto",
                   inventario_antes, disponibles_de(cliente, libro.id_libro))
    caso.verificar("No se creo ningun prestamo",
                   prestamos_antes, len(prestamos_de(cliente, usuario.id_usuario)))

    caso.detalle = (f"Inventario de '{libro.titulo}' antes y despues: "
                    f"{inventario_antes}. Prestamos del usuario: {prestamos_antes}.")


# ---------------------------------------------------------------------------
# PT-07  Tolerancia a fallos de conexion
# ---------------------------------------------------------------------------
def pt07_nodo_caido(caso: Caso, nodos_reales: list[NodoConfig]) -> None:
    caso.objetivo = ("Si una biblioteca no responde, el sistema sigue operando "
                     "con las demas e informa cual fallo.")
    vivos = []
    for nodo in nodos_reales:
        try:
            with ClienteNodo(nodo) as prueba:
                prueba.ping()
            vivos.append(nodo)
        except grpc.RpcError:
            pass
    if not vivos:
        raise _Omitir("Ningun nodo real esta levantado.")

    fantasma = NodoConfig(numero=9, nombre="Biblioteca inexistente",
                          host="127.0.0.1", port=PUERTO_INEXISTENTE,
                          database=vivos[0].database)

    distribuido = ClienteDistribuido(vivos + [fantasma])
    try:
        estados = distribuido.estado_nodos()
        caidos = [e for e in estados if not e.ok]
        enlinea = [e for e in estados if e.ok]

        caso.verificar("El nodo inalcanzable se reporta como caido",
                       True, any(e.nodo == 9 for e in caidos))
        caso.verificar("Los nodos vivos siguen respondiendo",
                       len(vivos), len(enlinea))
        caso.verificar("El cliente informa el motivo del fallo",
                       True, all(bool(e.error) for e in caidos))

        filas = distribuido.resumen_disponibilidad()
        caso.verificar("La consulta distribuida devuelve datos pese al nodo caido",
                       True, len(filas) > 0)
        caso.verificar("Ningun dato proviene del nodo caido",
                       False, any(f["nodo"] == 9 for f in filas))
    finally:
        distribuido.cerrar()

    caso.detalle = (f"Se consulto a {len(vivos)} nodo(s) real(es) mas uno "
                    f"apuntando al puerto {PUERTO_INEXISTENTE}. "
                    f"El sistema respondio sin lanzar excepciones.")


# ---------------------------------------------------------------------------
# PT-08  Concurrencia
# ---------------------------------------------------------------------------
def pt08_concurrencia(caso: Caso, nodo_cfg: NodoConfig, cliente: ClienteNodo) -> None:
    caso.objetivo = ("Varios prestamos simultaneos del mismo titulo no pueden "
                     "entregar mas ejemplares de los que existen.")
    catalogo = catalogo_de(cliente)
    libro = elegir_libro_disponible(catalogo)
    disponibles = libro.disponibles

    usuarios = usuarios_de(cliente)
    solicitudes = disponibles + 1
    if len(usuarios) < solicitudes:
        raise _Omitir(
            f"Se necesitan {solicitudes} usuarios distintos para provocar la "
            f"carrera sobre '{libro.titulo}' ({disponibles} disponibles) y solo "
            f"hay {len(usuarios)}.")

    participantes = usuarios[:solicitudes]
    barrera = threading.Barrier(solicitudes)
    resultados: list[tuple[int, str, object]] = []
    candado = threading.Lock()

    def intentar(usuario):
        propio = ClienteNodo(nodo_cfg)
        try:
            barrera.wait(timeout=30)
            respuesta = propio.prestar(usuario.id_usuario, libro.id_libro, 7)
            with candado:
                resultados.append((usuario.id_usuario, "OK", respuesta.prestamo))
        except grpc.RpcError as exc:
            with candado:
                resultados.append((usuario.id_usuario, exc.code().name, None))
        except Exception as exc:  # pragma: no cover
            with candado:
                resultados.append((usuario.id_usuario, f"ERROR {exc}", None))
        finally:
            propio.cerrar()

    hilos = [threading.Thread(target=intentar, args=(u,)) for u in participantes]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join(timeout=60)

    exitos = [r for r in resultados if r[1] == "OK"]
    rechazos = [r for r in resultados if r[1] != "OK"]

    caso.verificar("Todas las solicitudes obtuvieron respuesta",
                   solicitudes, len(resultados))
    caso.verificar("Se entregaron exactamente los ejemplares que existian",
                   disponibles, len(exitos))
    caso.verificar("La solicitud sobrante fue rechazada", 1, len(rechazos))
    caso.verificar("El rechazo fue por falta de disponibilidad",
                   True, all(r[1] == "RESOURCE_EXHAUSTED" for r in rechazos))

    ejemplares = [r[2].id_ejemplar for r in exitos]
    caso.verificar("Ningun ejemplar se entrego dos veces",
                   len(ejemplares), len(set(ejemplares)))
    caso.verificar("El inventario quedo en cero", 0,
                   disponibles_de(cliente, libro.id_libro))

    # Limpieza: se devuelven los prestamos creados por la prueba.
    for _usuario, _estado, prestamo in exitos:
        try:
            cliente.devolver(prestamo.id_prestamo, "PT-08 limpieza")
        except grpc.RpcError:
            pass
    caso.verificar("El inventario se restablece tras la limpieza",
                   disponibles, disponibles_de(cliente, libro.id_libro))

    caso.detalle = (f"{solicitudes} solicitudes simultaneas sobre "
                    f"'{libro.titulo}' con {disponibles} ejemplar(es): "
                    f"{len(exitos)} aceptadas, {len(rechazos)} rechazada(s). "
                    f"Ejemplares entregados: {sorted(ejemplares)}.")


# ---------------------------------------------------------------------------
# Reporte
# ---------------------------------------------------------------------------
def escribir_reporte(suite: Suite, nodo: int, destino: Path) -> Path:
    destino.mkdir(parents=True, exist_ok=True)
    marca = suite.inicio.strftime("%Y%m%d-%H%M")
    archivo = destino / f"pruebas_transaccionales_{marca}.md"

    pasan = sum(1 for c in suite.casos if c.estado == "PASA")
    fallan = sum(1 for c in suite.casos if c.estado == "FALLA")
    omitidos = sum(1 for c in suite.casos if c.estado == "OMITIDO")

    lineas = [
        "# Evidencia de pruebas transaccionales",
        "",
        f"- **Fecha de ejecucion:** {suite.inicio.strftime('%d/%m/%Y %H:%M:%S')}",
        f"- **Nodo bajo prueba:** {nodo}",
        f"- **Resultado:** {pasan} pasan, {fallan} fallan, {omitidos} omitidos",
        "",
        "Reporte generado automaticamente por "
        "`herramientas/pruebas_transaccionales.py`.",
        "",
        "## Resumen",
        "",
        "| Caso | Nombre | Estado | Tiempo |",
        "| --- | --- | --- | --- |",
    ]
    for c in suite.casos:
        lineas.append(f"| {c.codigo} | {c.nombre} | **{c.estado}** | {c.segundos} s |")

    lineas += ["", "## Detalle por caso", ""]
    for c in suite.casos:
        lineas += [f"### {c.codigo} - {c.nombre}", "",
                   f"**Objetivo.** {c.objetivo}", ""]
        if c.comprobaciones:
            lineas += ["| Comprobacion | Esperado | Obtenido | Resultado |",
                       "| --- | --- | --- | --- |"]
            for v in c.comprobaciones:
                marca_v = "OK" if v.ok else "FALLA"
                lineas.append(
                    f"| {v.descripcion} | `{v.esperado}` | `{v.obtenido}` | {marca_v} |")
            lineas.append("")
        if c.detalle:
            lineas += [f"**Observacion.** {c.detalle}", ""]
        lineas += [f"**Estado:** {c.estado} ({c.segundos} s)", ""]

    archivo.write_text("\n".join(lineas), encoding="utf-8")
    return archivo


# ---------------------------------------------------------------------------
# Principal
# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(
        description="Pruebas transaccionales del sistema distribuido")
    parser.add_argument("--nodo", type=int, default=1, choices=NODOS_VALIDOS,
                        help="Nodo sobre el que se ejecutan prestamos y devoluciones")
    parser.add_argument("--sin-reporte", action="store_true",
                        help="No escribir el archivo de evidencia")
    args = parser.parse_args()

    nodo_cfg = get_nodo_config(args.nodo)
    todos = get_todos_los_nodos()

    print("=" * 66)
    print("PRUEBAS TRANSACCIONALES - Sistema Distribuido de Bibliotecas")
    print(f"Nodo bajo prueba: {args.nodo} ({nodo_cfg.address})")
    print("=" * 66)

    cliente = ClienteNodo(nodo_cfg)
    try:
        cliente.ping()
    except grpc.RpcError as exc:
        print(f"\nEl nodo {args.nodo} no responde en {nodo_cfg.address}.")
        print(f"Detalle: {exc.details()}")
        print(f"Levantalo con:  python servidor.py --nodo {args.nodo}")
        cliente.cerrar()
        return 1

    distribuido = ClienteDistribuido(todos)
    suite = Suite()
    contexto: dict = {}

    try:
        suite.ejecutar("PT-01", "Consulta de disponibilidad distribuida", "",
                       lambda c: pt01_disponibilidad(c, distribuido))
        suite.ejecutar("PT-02", "Sincronizacion entre bibliotecas", "",
                       lambda c: pt02_sincronizacion(c, distribuido, cliente, args.nodo))
        suite.ejecutar("PT-03", "Registro de prestamo", "",
                       lambda c: pt03_prestamo(c, cliente, contexto))
        suite.ejecutar("PT-04", "Registro de devolucion", "",
                       lambda c: pt04_devolucion(c, cliente, contexto))
        suite.ejecutar("PT-05", "Reglas de negocio y codigos de error", "",
                       lambda c: pt05_reglas(c, cliente, contexto))
        suite.ejecutar("PT-06", "Atomicidad de la transaccion", "",
                       lambda c: pt06_atomicidad(c, cliente))
        suite.ejecutar("PT-07", "Tolerancia a un nodo caido", "",
                       lambda c: pt07_nodo_caido(c, todos))
        suite.ejecutar("PT-08", "Concurrencia sobre el mismo titulo", "",
                       lambda c: pt08_concurrencia(c, nodo_cfg, cliente))
    finally:
        distribuido.cerrar()
        cliente.cerrar()

    pasan = sum(1 for c in suite.casos if c.estado == "PASA")
    fallan = sum(1 for c in suite.casos if c.estado == "FALLA")
    omitidos = sum(1 for c in suite.casos if c.estado == "OMITIDO")

    print("\n" + "=" * 66)
    print(f"RESULTADO: {pasan} pasan, {fallan} fallan, {omitidos} omitidos")
    print("=" * 66)

    if not args.sin_reporte:
        archivo = escribir_reporte(suite, args.nodo, RAIZ / "docs" / "evidencias")
        print(f"\nEvidencia guardada en: {archivo.relative_to(RAIZ)}")

    return 1 if fallan else 0


if __name__ == "__main__":
    raise SystemExit(main())
