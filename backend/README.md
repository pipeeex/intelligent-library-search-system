# Backend — Nodo bibliotecario

Backend de un nodo del *Sistema Distribuido de Consulta Inteligente de Libros*.
Los tres nodos ejecutan **el mismo código**; lo único que cambia es el número de
nodo (`--nodo 1|2|3`), que determina su base de datos y su puerto gRPC.

## Estructura

```
backend/
├── servidor.py                 # Punto de entrada: python servidor.py --nodo 1
├── requirements.txt
├── .env.example                # Copiar a .env y ajustar
├── config/
│   └── settings.py             # Config de los 3 nodos (BD + host/puerto)
├── db/
│   └── connection.py           # pyodbc: conexiones y transacciones ACID
├── models/
│   └── entidades.py            # Dataclasses espejo de las tablas SQL
├── repositories/               # SQL puro, un repositorio por tabla
│   ├── base.py
│   ├── biblioteca_repository.py
│   ├── libro_repository.py
│   ├── usuario_repository.py
│   ├── ejemplar_repository.py
│   ├── prestamo_repository.py
│   └── consulta_repository.py
├── services/                   # Reglas de negocio
│   ├── excepciones.py
│   ├── catalogo_service.py     # Libros, ejemplares, usuarios
│   ├── prestamo_service.py     # Préstamos/devoluciones transaccionales
│   └── ia_service.py           # Interfaz reservada (sin implementar aún)
├── proto/
│   └── biblioteca.proto        # Contrato gRPC del nodo
├── grpc_service/
│   ├── server.py               # Arranque del servidor
│   ├── servicer.py             # Implementación de los RPC
│   ├── cliente.py              # Cliente que consulta los 3 nodos en paralelo
│   └── generated/              # Stubs generados (no se versionan)
└── tools/
    ├── generar_protos.py       # Genera los stubs desde el .proto
    └── probar_nodos.py         # Prueba de humo contra los 3 nodos
```

**Capas:** `gRPC → services → repositories → db`. La capa gRPC no escribe SQL y
los repositorios no conocen gRPC, así que la GUI (Tkinter/PyQt) o el módulo de
IA pueden usar los servicios directamente o por la red, sin duplicar lógica.

## Puesta en marcha

### 1. Bases de datos

En SQL Server, ejecutar el script `SQLQuery_BibliotecasDB.sql` **tres veces**,
cambiando el nombre de la base en las líneas de `CREATE DATABASE` / `USE`:
`Biblioteca1DB`, `Biblioteca2DB` y `Biblioteca3DB`.

### 2. Entorno

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

copy .env.example .env         # y ajustar DB_SERVER, driver, etc.
```

Si no está instalado, hace falta el **ODBC Driver 17 (o 18) for SQL Server**.
Con el 18 hay que poner `DB_DRIVER=ODBC Driver 18 for SQL Server` y
`DB_ENCRYPT=no` (o `DB_TRUST_SERVER_CERTIFICATE=yes`).

### 3. Generar los stubs de gRPC

```bash
python tools/generar_protos.py
```

Hay que repetirlo cada vez que se modifique `proto/biblioteca.proto`.

### 4. Levantar los nodos (una terminal por nodo)

```bash
python servidor.py --nodo 1     # 127.0.0.1:50051 -> Biblioteca1DB
python servidor.py --nodo 2     # 127.0.0.1:50052 -> Biblioteca2DB
python servidor.py --nodo 3     # 127.0.0.1:50053 -> Biblioteca3DB
```

### 5. Cargar datos de ejemplo

```bash
python tools/cargar_datos.py --todos            # los tres nodos
python tools/cargar_datos.py --nodo 1 --limpiar # recargar uno desde cero
```

Cada nodo recibe un catálogo distinto con algunos títulos repetidos entre
bibliotecas, para que la consulta distribuida tenga algo que agregar. No
necesita los servidores levantados: escribe directo contra la base.

### 6. Comprobar

```bash
python tools/diagnostico.py              # conexión a SQL Server
python tools/probar_nodos.py             # ping a los 3 nodos
python tools/probar_nodos.py --titulo "cien"
python tools/probar_flujo.py --nodo 1    # prueba end-to-end del préstamo
```

`probar_flujo.py` recorre el ciclo completo por gRPC (prestar → verificar que
baja el inventario → devolver → verificar que vuelve) y comprueba que las
reglas de negocio devuelvan el código gRPC correcto.

## Operaciones expuestas por gRPC

| Grupo | RPC |
|---|---|
| Salud | `Ping` |
| Libros | `CrearLibro`, `ObtenerLibro`, `ListarLibros`, `BuscarLibros`, `ActualizarLibro`, `EliminarLibro` |
| Disponibilidad | `ConsultarDisponibilidad` |
| Ejemplares | `CrearEjemplar`, `ListarEjemplares`, `CambiarEstadoEjemplar` |
| Usuarios | `CrearUsuario`, `ObtenerUsuario`, `ListarUsuarios`, `ActualizarUsuario`, `EliminarUsuario` |
| Préstamos | `RegistrarPrestamo`, `RegistrarDevolucion`, `ListarPrestamos` |

## ACID en préstamos y devoluciones

`PrestamoService` abre **una sola transacción** por operación:

- **Prestar:** valida usuario y libro → bloquea un ejemplar `DISPONIBLE` con
  `UPDLOCK, ROWLOCK, READPAST` → lo marca `PRESTADO` → inserta el `Prestamo`.
- **Devolver:** bloquea el préstamo → inserta la `Devolucion` → marca el
  préstamo `DEVUELTO` → libera el ejemplar.

Si cualquier paso falla se hace `rollback` completo (**atomicidad**); los
`CHECK`/`FOREIGN KEY` del script SQL sostienen la **consistencia**; los hints de
bloqueo dan **aislamiento** ante dos préstamos simultáneos del mismo título; y
el `commit` de SQL Server garantiza la **durabilidad**.

## Reglas de negocio actuales

- Máximo **3** préstamos activos por usuario (`MAX_PRESTAMOS_ACTIVOS`).
- Un usuario con préstamos vencidos no puede pedir otro libro.
- Préstamo por defecto de **15 días** (`DIAS_PRESTAMO` en `.env`).
- No se puede borrar un libro con ejemplares, ni un usuario con préstamos activos.
- Los ejemplares se dan de **baja lógica** (`estado = 'BAJA'`) para conservar el historial.

## Errores y códigos gRPC

| Excepción | Código gRPC |
|---|---|
| `NoEncontrado` | `NOT_FOUND` |
| `DatosInvalidos` | `INVALID_ARGUMENT` |
| `SinDisponibilidad` | `RESOURCE_EXHAUSTED` |
| `ReglaViolada` | `FAILED_PRECONDITION` |
| `DatabaseError` | `UNAVAILABLE` |

## Pendiente

- Módulo de IA: `services/ia_service.py` deja la interfaz lista
  (`InterpretePregunta` → `IntencionConsulta` → disponibilidad real de los nodos).
  Falta el intérprete (reglas locales o LLM).
- Autenticación/roles (administrador, bibliotecario, usuario).
- Reportes e interfaz gráfica.
- Pruebas automatizadas de los servicios.
