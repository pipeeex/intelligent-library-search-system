# Evidencia de pruebas transaccionales

- **Fecha de ejecucion:** 02/11/2026 22:22:29
- **Nodo bajo prueba:** 1
- **Resultado:** 8 pasan, 0 fallan, 0 omitidos

Reporte generado automaticamente por `herramientas/pruebas_transaccionales.py`.

## Resumen

| Caso | Nombre | Estado | Tiempo |
| --- | --- | --- | --- |
| PT-01 | Consulta de disponibilidad distribuida | **PASA** | 2.09 s |
| PT-02 | Sincronizacion entre bibliotecas | **PASA** | 0.09 s |
| PT-03 | Registro de prestamo | **PASA** | 0.03 s |
| PT-04 | Registro de devolucion | **PASA** | 0.01 s |
| PT-05 | Reglas de negocio y codigos de error | **PASA** | 0.02 s |
| PT-06 | Atomicidad de la transaccion | **PASA** | 0.02 s |
| PT-07 | Tolerancia a un nodo caido | **PASA** | 3.87 s |
| PT-08 | Concurrencia sobre el mismo titulo | **PASA** | 0.04 s |

## Detalle por caso

### PT-01 - Consulta de disponibilidad distribuida

**Objetivo.** La consulta llega a las tres bibliotecas y el resultado se presenta unificado por sede.

| Comprobacion | Esperado | Obtenido | Resultado |
| --- | --- | --- | --- |
| Al menos un nodo responde al Ping | `True` | `True` | OK |
| La consulta distribuida devuelve registros | `True` | `True` | OK |
| Los registros vienen identificados por sede | `True` | `True` | OK |
| Cada fila trae titulo, sede y conteo de ejemplares | `True` | `True` | OK |
| Disponibles nunca supera el total de ejemplares | `True` | `True` | OK |

**Observacion.** 6 registros desde las sedes [1]; 1 de 3 nodos en linea.

**Estado:** PASA (2.09 s)

### PT-02 - Sincronizacion entre bibliotecas

**Objetivo.** Una operacion ejecutada en una sede se refleja de inmediato en la consulta agregada de las tres, sin reiniciar ni sincronizar a mano.

| Comprobacion | Esperado | Obtenido | Resultado |
| --- | --- | --- | --- |
| La vista global ve el titulo antes del prestamo | `True` | `True` | OK |
| La vista global refleja el prestamo al instante | `0` | `0` | OK |
| La vista global refleja la devolucion al instante | `1` | `1` | OK |

**Observacion.** Titulo 'Designing Data-Intensive Applications' en la sede 1: 1 -> 0 -> 1 disponibles.

**Estado:** PASA (0.09 s)

### PT-03 - Registro de prestamo

**Objetivo.** El prestamo descuenta un ejemplar y queda registrado como ACTIVO en una sola transaccion.

| Comprobacion | Esperado | Obtenido | Resultado |
| --- | --- | --- | --- |
| El prestamo queda en estado ACTIVO | `ACTIVO` | `ACTIVO` | OK |
| El inventario baja exactamente en un ejemplar | `0` | `0` | OK |
| El prestamo aparece entre los activos del usuario | `1` | `1` | OK |
| Se asigno un ejemplar concreto | `True` | `True` | OK |
| La fecha de vencimiento es posterior a la de prestamo | `True` | `True` | OK |

**Observacion.** Prestamo #11 del ejemplar 14 ('Designing Data-Intensive Applications') al usuario Ana Maria Torres. Vence el 2026-11-09.

**Estado:** PASA (0.03 s)

### PT-04 - Registro de devolucion

**Objetivo.** La devolucion cierra el prestamo y devuelve el ejemplar al inventario disponible.

| Comprobacion | Esperado | Obtenido | Resultado |
| --- | --- | --- | --- |
| El inventario vuelve a su valor original | `1` | `1` | OK |
| El prestamo queda marcado como DEVUELTO | `DEVUELTO` | `DEVUELTO` | OK |
| El prestamo ya no figura entre los activos | `False` | `False` | OK |

**Observacion.** Prestamo #11 cerrado correctamente.

**Estado:** PASA (0.01 s)

### PT-05 - Reglas de negocio y codigos de error

**Objetivo.** Las operaciones invalidas se rechazan con el codigo gRPC correcto, sin que el servidor se caiga.

| Comprobacion | Esperado | Obtenido | Resultado |
| --- | --- | --- | --- |
| Devolver dos veces el mismo prestamo | `FAILED_PRECONDITION` | `FAILED_PRECONDITION` | OK |
| Prestar un libro inexistente | `NOT_FOUND` | `NOT_FOUND` | OK |
| Prestar a un usuario inexistente | `NOT_FOUND` | `NOT_FOUND` | OK |
| El nodo sigue en pie despues de los rechazos | `True` | `True` | OK |

**Observacion.** No habia titulos agotados para probar RESOURCE_EXHAUSTED en este nodo.

**Estado:** PASA (0.02 s)

### PT-06 - Atomicidad de la transaccion

**Objetivo.** Una operacion rechazada no deja rastro: ni prestamo registrado ni ejemplar descontado.

| Comprobacion | Esperado | Obtenido | Resultado |
| --- | --- | --- | --- |
| La operacion invalida es rechazada | `NOT_FOUND` | `NOT_FOUND` | OK |
| El inventario queda intacto | `1` | `1` | OK |
| No se creo ningun prestamo | `5` | `5` | OK |

**Observacion.** Inventario de 'Designing Data-Intensive Applications' antes y despues: 1. Prestamos del usuario: 5.

**Estado:** PASA (0.02 s)

### PT-07 - Tolerancia a un nodo caido

**Objetivo.** Si una biblioteca no responde, el sistema sigue operando con las demas e informa cual fallo.

| Comprobacion | Esperado | Obtenido | Resultado |
| --- | --- | --- | --- |
| El nodo inalcanzable se reporta como caido | `True` | `True` | OK |
| Los nodos vivos siguen respondiendo | `1` | `1` | OK |
| El cliente informa el motivo del fallo | `True` | `True` | OK |
| La consulta distribuida devuelve datos pese al nodo caido | `True` | `True` | OK |
| Ningun dato proviene del nodo caido | `False` | `False` | OK |

**Observacion.** Se consulto a 1 nodo(s) real(es) mas uno apuntando al puerto 59999. El sistema respondio sin lanzar excepciones.

**Estado:** PASA (3.87 s)

### PT-08 - Concurrencia sobre el mismo titulo

**Objetivo.** Varios prestamos simultaneos del mismo titulo no pueden entregar mas ejemplares de los que existen.

| Comprobacion | Esperado | Obtenido | Resultado |
| --- | --- | --- | --- |
| Todas las solicitudes obtuvieron respuesta | `2` | `2` | OK |
| Se entregaron exactamente los ejemplares que existian | `1` | `1` | OK |
| La solicitud sobrante fue rechazada | `1` | `1` | OK |
| El rechazo fue por falta de disponibilidad | `True` | `True` | OK |
| Ningun ejemplar se entrego dos veces | `1` | `1` | OK |
| El inventario quedo en cero | `0` | `0` | OK |
| El inventario se restablece tras la limpieza | `1` | `1` | OK |

**Observacion.** 2 solicitudes simultaneas sobre 'Designing Data-Intensive Applications' con 1 ejemplar(es): 1 aceptadas, 1 rechazada(s). Ejemplares entregados: [14].

**Estado:** PASA (0.04 s)
