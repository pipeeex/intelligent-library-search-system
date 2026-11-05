# Capturas de la interfaz

Evidencia del criterio 4.2 de la entrega: interfaz mejorada y opciones de
navegación.

> **Nota sobre estas capturas.** Se tomaron con la aplicación en modo
> demostración (`python aplicacion.py --demo`), que usa datos en memoria. Sirven
> para evidenciar el diseño y la navegación. Las capturas con datos reales de
> SQL Server, que corresponden a los criterios 4.3 y 4.4, están en
> [`../evidencias/`](../evidencias/).

| Archivo | Qué muestra |
|---|---|
| `01_inicio_navegacion.png` | Panel de inicio con el menú lateral de cinco secciones, los indicadores del sistema, el estado de los tres nodos y los accesos directos a las operaciones frecuentes. |
| `02_catalogo_consulta_distribuida.png` | Consulta de catálogo con el resultado unificado de las tres bibliotecas. Cada fila indica la sede, los ejemplares disponibles y el total. Las filas en rojo son títulos sin ejemplares libres en esa sede. |
| `03_registrar_prestamo.png` | Operación principal. Formulario con los campos obligatorios marcados y el panel de préstamos del lector seleccionado. |
| `04_usuarios_por_sede.png` | Listado de lectores con la columna de biblioteca, que deja ver que cada sede administra sus propios usuarios. |
| `05_consulta_lenguaje_natural.png` | Pantalla de consulta en lenguaje natural, con el aviso de que el intérprete aún no está implementado. |
| `06_adaptacion_pantalla_pequena.png` | La misma pantalla de préstamos en una resolución de 1024×768: el formulario y la tabla se apilan en lugar de recortarse. |
| `07_adaptacion_escalado_150.png` | El panel de inicio con el escalado de Windows al 150 %: la interfaz crece con el sistema y no se corta el texto. |

## Cómo reproducirlas

```bash
python aplicacion.py --demo
```

Para las capturas con datos reales hay que levantar los tres nodos primero:

```bash
python servidor.py --nodo 1
python servidor.py --nodo 2
python servidor.py --nodo 3
python aplicacion.py
```
