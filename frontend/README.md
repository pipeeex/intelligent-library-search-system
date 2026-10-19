# Interfaz de escritorio

Aplicación de escritorio del *Sistema Distribuido de Consulta Inteligente de
Bibliotecas*, desarrollada en Python con Tkinter. Corresponde a la Fase III del
proyecto: evolución de la interfaz, desarrollo de una operación principal y
gestión inicial de la información.

## Ejecución

```bash
cd frontend
python main.py            # intenta conectarse a los nodos gRPC
python main.py --demo     # fuerza los datos de prueba, sin backend
```

No requiere instalar nada: Tkinter viene con Python. Si los nodos están
levantados (`python servidor.py --nodo 1|2|3` en la carpeta `backend/`), la
aplicación trabaja contra SQL Server. Si no responden, cae sola a datos de
prueba en memoria y lo indica en la barra inferior.

## Pantallas

| Sección | Qué hace |
|---|---|
| **Inicio** | Estado de los tres nodos, conteo de títulos, ejemplares y disponibles, accesos rápidos. |
| **Catálogo** | Búsqueda por título, autor o ISBN sobre las tres bibliotecas, con el resultado unificado. |
| **Préstamos** | Operación principal: registrar préstamo y registrar devolución. |
| **Usuarios** | Consulta de lectores por nombre o documento. |
| **Consulta IA** | Pantalla preparada para el módulo de lenguaje natural, todavía sin intérprete. |

## Operación principal: registrar préstamo

Corresponde al requerimiento **RF-06** y al caso de uso **CU-06** del documento
maestro. Es la operación central del sistema transaccional, porque toca varias
tablas y tiene que dejarlas consistentes.

**Validaciones antes de enviar nada al nodo:**

- Biblioteca, usuario y libro son obligatorios; el campo que falte se marca en
  rojo con su mensaje debajo.
- Los días de préstamo deben ser un número entero entre 1 y 30.
- No se permite seleccionar un título sin ejemplares disponibles.

**Reglas que verifica el sistema al registrar:**

- El usuario no puede superar los 3 préstamos activos.
- Un usuario con préstamos vencidos no puede llevar otro libro.
- Debe quedar al menos un ejemplar disponible en esa sede.

Al confirmar, el inventario baja en uno y el préstamo aparece en la tabla de la
derecha. Los vencidos se muestran en rojo. Desde la misma pantalla se registra
la devolución, que devuelve el ejemplar al inventario.

## Comportamiento en ejecución

- **Estado de los nodos en vivo.** Cada 6 segundos la aplicación consulta a las
  tres bibliotecas en un hilo aparte, así que la ventana nunca se congela. Si
  una deja de responder, la barra inferior lo muestra y aparece un aviso, sin
  tener que cambiar de sección. Cuando vuelve, también lo informa.
- **Listas siempre al día.** Al entrar a Préstamos se releen usuarios y
  catálogo conservando lo que ya estuviera seleccionado. Un usuario creado
  directamente en SQL Server aparece sin reiniciar el programa.
- **Avisos flotantes.** Los mensajes se superponen en la esquina inferior
  derecha y desaparecen solos a los pocos segundos, de modo que no desplazan
  los botones ni el formulario. También se cierran con un clic.

## Gestión de la información

- **Registro:** alta de préstamos y de devoluciones.
- **Consulta:** catálogo, disponibilidad por sede y consolidada, usuarios,
  préstamos por usuario.
- **Actualización:** el estado del préstamo y la disponibilidad del ejemplar
  cambian con cada operación.
- **Validaciones:** campos obligatorios, rangos numéricos y reglas de negocio.
- **Datos:** conexión real por gRPC contra las tres bases SQL Server, o datos de
  prueba en memoria como respaldo.

## Estructura

```
frontend/
├── main.py                   # ventana principal y navegación
├── app/
│   ├── estilos.py            # paleta institucional y estilos ttk
│   ├── componentes.py        # tarjetas, campos, tablas, avisos
│   ├── datos.py              # ProveedorGRPC y ProveedorDemo
│   └── vistas/
│       ├── inicio.py
│       ├── catalogo.py
│       ├── prestamos.py      # operación principal
│       ├── usuarios.py
│       └── consulta_ia.py
```

Las vistas no saben si detrás hay gRPC o datos de prueba: ambos proveedores
exponen la misma API (`app/datos.py`). Cambiar de uno a otro no obliga a tocar
ninguna pantalla.

## Pendiente

- Conectar el intérprete del módulo de IA en la pantalla de Consulta IA.
- Autenticación y roles: hoy todas las secciones están disponibles.
- Formularios de alta de libros y usuarios desde la interfaz.
