"""Carga datos de ejemplo en un nodo.

Uso (desde backend/, con el venv activo):

    python tools/cargar_datos.py --nodo 1
    python tools/cargar_datos.py --nodo 1 --limpiar   # borra y vuelve a cargar

Cada nodo recibe un catalogo de ~200 libros: unos pocos curados a mano
(CATALOGOS_BASE, algunos repetidos entre bibliotecas para que la consulta
distribuida tenga algo interesante que agregar) y el resto tomado de
datasets/libros_openlibrary.csv, un dataset real descargado de la API
publica de Open Library (https://openlibrary.org/dev/docs/api/search):
libros que existen de verdad, con su isbn, titulo, autor, editorial y
anio de publicacion. Lo unico que se inventa es la cantidad de ejemplares
de cada libro (es un dato de inventario de la biblioteca, no bibliografico).

No usa gRPC: escribe directo contra la base del nodo, asi que puedes correrlo
con los servidores apagados.
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from configuracion.ajustes import NODOS_VALIDOS, get_nodo_config  # noqa: E402
from datos.conexion import Database, DatabaseError  # noqa: E402
from entidades.entidades import Ejemplar, Libro, Usuario  # noqa: E402
from datos.repositorios.repositorio_biblioteca import RepositorioBiblioteca  # noqa: E402
from datos.repositorios.repositorio_ejemplar import RepositorioEjemplar  # noqa: E402
from datos.repositorios.repositorio_libro import RepositorioLibro  # noqa: E402
from datos.repositorios.repositorio_usuario import RepositorioUsuario  # noqa: E402

LIBROS_POR_NODO = 460
DATASET_CSV = Path(__file__).resolve().parent.parent / "datasets" / "libros_openlibrary.csv"

# ---------------------------------------------------------------------------
# Catalogo curado por nodo: (isbn, titulo, autor, editorial, anio, num_ejemplares)
# ---------------------------------------------------------------------------
CATALOGOS_BASE: dict[int, list[tuple]] = {
    1: [
        ("9780307474728", "Cien anos de soledad", "Gabriel Garcia Marquez", "Vintage", 1967, 3),
        ("9788437604947", "La ciudad y los perros", "Mario Vargas Llosa", "Catedra", 1963, 2),
        ("9789500720885", "Rayuela", "Julio Cortazar", "Sudamericana", 1963, 2),
        ("9780132350884", "Clean Code", "Robert C. Martin", "Prentice Hall", 2008, 4),
        ("9780201633610", "Design Patterns", "Erich Gamma", "Addison-Wesley", 1994, 2),
        ("9781449373320", "Designing Data-Intensive Applications", "Martin Kleppmann", "O'Reilly", 2017, 1),
    ],
    2: [
        ("9780307474728", "Cien anos de soledad", "Gabriel Garcia Marquez", "Vintage", 1967, 1),
        ("9788420412146", "El Aleph", "Jorge Luis Borges", "Alianza", 1949, 3),
        ("9788497592208", "Pedro Paramo", "Juan Rulfo", "Catedra", 1955, 2),
        ("9780132350884", "Clean Code", "Robert C. Martin", "Prentice Hall", 2008, 1),
        ("9780134685991", "Effective Java", "Joshua Bloch", "Addison-Wesley", 2018, 3),
        ("9781593279288", "Eloquent JavaScript", "Marijn Haverbeke", "No Starch Press", 2018, 2),
    ],
    3: [
        ("9788437604947", "La ciudad y los perros", "Mario Vargas Llosa", "Catedra", 1963, 1),
        ("9788420412146", "El Aleph", "Jorge Luis Borges", "Alianza", 1949, 1),
        ("9789505115952", "El tunel", "Ernesto Sabato", "Seix Barral", 1948, 2),
        ("9780596007126", "Head First Design Patterns", "Eric Freeman", "O'Reilly", 2004, 2),
        ("9781491950357", "Building Microservices", "Sam Newman", "O'Reilly", 2015, 3),
        ("9780262033848", "Introduction to Algorithms", "Thomas H. Cormen", "MIT Press", 2009, 2),
    ],
}


def _leer_dataset_externo() -> list[tuple]:
    """Lee datasets/libros_openlibrary.csv: libros reales (Open Library).

    La cantidad de ejemplares no viene en el dataset (es inventario de la
    biblioteca, no un dato bibliografico), asi que se deriva del isbn con una
    semilla fija: siempre da el mismo numero para el mismo libro, para que
    volver a correr el script no cambie el inventario ya cargado.
    """
    if not DATASET_CSV.exists():
        return []
    filas = []
    with DATASET_CSV.open(encoding="utf-8", newline="") as archivo:
        for registro in csv.DictReader(archivo):
            isbn = registro["isbn"].strip()
            if not isbn:
                continue
            cantidad = random.Random(isbn).randint(1, 5)
            filas.append((
                isbn,
                registro["titulo"].strip()[:200],  # VARCHAR(200) en Libro.titulo
                registro["autor"].strip()[:150],   # VARCHAR(150) en Libro.autor
                registro["editorial"].strip()[:150],  # VARCHAR(150) en Libro.editorial
                int(registro["anio"]),
                cantidad,
            ))
    return filas


def construir_catalogos(objetivo_por_nodo: int = LIBROS_POR_NODO) -> dict[int, list[tuple]]:
    """Catalogo final por nodo: lo curado en CATALOGOS_BASE + relleno real
    del dataset externo hasta llegar a ``objetivo_por_nodo`` libros, sin
    repetir isbn dentro del mismo nodo.

    Cada nodo tiene asignado un bloque FIJO del dataset externo (no depende
    de ``objetivo_por_nodo``): asi, si despues se sube el objetivo, cada nodo
    sigue tomando mas libros del principio de su propio bloque, en vez de
    que el bloque entero se recorra y queden libros viejos sin deduplicar.
    """
    externos = _leer_dataset_externo()
    cantidad_nodos = len(NODOS_VALIDOS)
    tam_bloque = len(externos) // cantidad_nodos

    catalogos: dict[int, list[tuple]] = {}
    for indice, numero in enumerate(NODOS_VALIDOS):
        base = list(CATALOGOS_BASE.get(numero, []))
        usados = {fila[0] for fila in base}
        bloque = externos[indice * tam_bloque:(indice + 1) * tam_bloque]
        faltan = max(0, objetivo_por_nodo - len(base))
        relleno = [fila for fila in bloque if fila[0] not in usados][:faltan]
        catalogos[numero] = base + relleno
    return catalogos


CATALOGOS: dict[int, list[tuple]] = construir_catalogos()

USUARIOS = [
    ("Ana Maria Torres", "1012345678", "ana.torres@example.com", "3001112233"),
    ("Carlos Ramirez", "1023456789", "carlos.ramirez@example.com", "3012223344"),
    ("Laura Gomez", "1034567890", "laura.gomez@example.com", "3023334455"),
    ("Julian Castro", "1045678901", "julian.castro@example.com", "3034445566"),
    ("Sofia Herrera", "1056789012", "sofia.herrera@example.com", "3045556677"),
]

TABLAS_EN_ORDEN_DE_BORRADO = [
    "Resultado_Consulta",
    "Consulta",
    "Devolucion",
    "Prestamo",
    "Ejemplar",
    "Libro",
    "Usuario",
]


def limpiar(db: Database) -> None:
    """Vacia las tablas de datos respetando las llaves foraneas."""
    with db.transaccion() as cursor:
        for tabla in TABLAS_EN_ORDEN_DE_BORRADO:
            cursor.execute(f"DELETE FROM {tabla};")
            cursor.execute(
                f"IF (OBJECTPROPERTY(OBJECT_ID('{tabla}'), 'TableHasIdentity') = 1) "
                f"DBCC CHECKIDENT ('{tabla}', RESEED, 0) WITH NO_INFOMSGS;"
            )
    print("  Tablas de datos vaciadas (las bibliotecas se conservan).")


def cargar(numero: int, con_limpieza: bool) -> int:
    nodo = get_nodo_config(numero)
    db = Database(nodo.database)

    ok, motivo = db.diagnosticar()
    if not ok:
        print(f"No hay conexion con {nodo.database.database}: {motivo}")
        return 1

    print(f"Nodo {numero} -> {nodo.database.database}")

    if con_limpieza:
        limpiar(db)

    libros_repo = RepositorioLibro(db)
    ejemplares_repo = RepositorioEjemplar(db)
    usuarios_repo = RepositorioUsuario(db)
    bibliotecas_repo = RepositorioBiblioteca(db)

    bibliotecas = bibliotecas_repo.listar()
    if not bibliotecas:
        print("  No hay bibliotecas registradas. Ejecuta primero el script SQL.")
        return 1

    # Cada nodo representa su propia biblioteca: usamos la fila que le toca
    # (nodo 1 -> primera, nodo 2 -> segunda, etc.) y si no existe, la primera.
    biblioteca = bibliotecas[numero - 1] if len(bibliotecas) >= numero else bibliotecas[0]
    id_biblioteca = int(biblioteca.id_biblioteca)
    print(f"  Biblioteca: [{id_biblioteca}] {biblioteca.nombre}")

    # -- Usuarios -------------------------------------------------------
    nuevos_usuarios = 0
    for nombre, documento, correo, telefono in USUARIOS:
        if usuarios_repo.obtener_por_documento(documento):
            continue
        usuarios_repo.crear(
            Usuario(nombre=nombre, documento=documento, correo=correo, telefono=telefono)
        )
        nuevos_usuarios += 1
    print(f"  Usuarios: {nuevos_usuarios} nuevos ({len(USUARIOS)} en el set)")

    # -- Libros y ejemplares --------------------------------------------
    nuevos_libros = 0
    nuevos_ejemplares = 0
    for isbn, titulo, autor, editorial, anio, cantidad in CATALOGOS[numero]:
        libro = libros_repo.obtener_por_isbn(isbn)
        if libro is None:
            id_libro = libros_repo.crear(
                Libro(
                    isbn=isbn,
                    titulo=titulo,
                    autor=autor,
                    editorial=editorial,
                    anio_publicacion=anio,
                )
            )
            nuevos_libros += 1
        else:
            id_libro = int(libro.id_libro)

        existentes = len(ejemplares_repo.listar_por_libro(id_libro))
        for indice in range(existentes, cantidad):
            codigo = f"N{numero}-L{id_libro}-{indice + 1:02d}"
            ejemplares_repo.crear(
                Ejemplar(
                    id_libro=id_libro,
                    id_biblioteca=id_biblioteca,
                    codigo_inventario=codigo,
                    estado="DISPONIBLE",
                )
            )
            nuevos_ejemplares += 1

    print(f"  Libros: {nuevos_libros} nuevos")
    print(f"  Ejemplares: {nuevos_ejemplares} nuevos")

    # -- Resumen --------------------------------------------------------
    print("\n  Inventario del nodo:")
    for item in libros_repo.disponibilidad(limite=100):
        print(
            f"    [{item.id_libro:>3}] {item.titulo[:42]:<42} "
            f"{item.disponibles}/{item.total_ejemplares} disponibles"
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Carga datos de ejemplo en un nodo")
    parser.add_argument("--nodo", type=int, choices=NODOS_VALIDOS, help="Nodo a cargar")
    parser.add_argument(
        "--todos", action="store_true", help="Cargar los tres nodos de una vez"
    )
    parser.add_argument(
        "--limpiar",
        action="store_true",
        help="Borrar los datos existentes antes de cargar",
    )
    args = parser.parse_args()

    if not args.nodo and not args.todos:
        parser.error("Indica --nodo N o --todos")

    nodos = list(NODOS_VALIDOS) if args.todos else [args.nodo]
    codigo = 0
    for numero in nodos:
        try:
            codigo |= cargar(numero, args.limpiar)
        except DatabaseError as exc:
            print(f"Nodo {numero}: {exc}")
            codigo = 1
        print()
    return codigo


if __name__ == "__main__":
    raise SystemExit(main())
