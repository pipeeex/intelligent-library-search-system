# Plan de pruebas

**Sistema Distribuido de Consulta Inteligente de Bibliotecas**
Universidad Manuela Beltrán · Ingeniería de Software · Sistemas Transaccionales
Grupo 5 · Noviembre de 2026

---

## 1. Objetivo

Verificar que el prototipo cumple los requerimientos definidos en el apartado 12
del documento maestro, y dejar evidencia de esa verificación en una forma que
cualquiera pueda revisar sin tener que ejecutar el sistema.

El plan cubre dos cosas que a menudo se confunden. Una es comprobar que las
funciones hacen lo que dicen. La otra es comprobar que el sistema se comporta
correctamente cuando algo sale mal: cuando un nodo se cae, cuando dos personas
piden el mismo libro al mismo tiempo, cuando una operación se interrumpe a la
mitad. En un sistema transaccional distribuido, la segunda parte es la que
cuenta.

## 2. Alcance

### 2.1. Qué se prueba

| Elemento | Nivel |
|---|---|
| Operaciones del contrato gRPC de cada nodo | Integración |
| Reglas de préstamo y devolución | Integración |
| Comportamiento transaccional sobre SQL Server | Integración |
| Consulta distribuida a las tres sedes | Sistema |
| Tolerancia a la caída de un nodo | Sistema |
| Aplicación de escritorio y navegación | Sistema / aceptación |
| Instalación siguiendo el manual | Aceptación |

### 2.2. Qué no se prueba, y por qué

| Elemento | Motivo |
|---|---|
| Autenticación y control de roles (RF-01, RNF-01) | No está implementado. Queda declarado como brecha abierta. |
| Gestión de libros y ejemplares desde la interfaz (RF-03, RF-04) | La aplicación consulta el catálogo pero no permite crearlo ni editarlo. Los datos se cargan por script. |
| Reportes exportables (RF-10) | La información se consulta en pantalla pero no se exporta. |
| Intérprete de lenguaje natural | Documentado en el apartado 18 del documento maestro, sin implementar. Se prueba la pantalla y el aviso de su estado, no la interpretación. |
| Rendimiento con cargas altas | Fuera del alcance académico. El RNF-04 se verifica con el volumen de datos de ejemplo. |

Declarar lo que no se prueba es parte del plan. Un informe que no dice dónde no
miró da una impresión de cobertura que no corresponde.

## 3. Estrategia

### 3.1. Dos caminos que se complementan

**Pruebas automatizadas.** La suite `herramientas/pruebas_transaccionales.py`
cubre los ocho casos del comportamiento transaccional. Se ejecutan contra los
nodos reales, con SQL Server por debajo, y comparan el estado de la base antes y
después de cada operación. No dependen de lo que informe la aplicación sino de
lo que quedó efectivamente guardado.

**Pruebas manuales.** Todo lo que pasa por la interfaz: navegación, validación de
formularios, mensajes, adaptación a distintas pantallas e instalación. Son 31
casos documentados en el catálogo.

### 3.2. Tipos de prueba aplicados

| Tipo | Dónde aparece |
|---|---|
| Funcional | Consulta de catálogo, préstamo, devolución, gestión de lectores |
| Integración | Los ocho casos transaccionales contra los nodos |
| Regresión | Los tres errores corregidos en fases anteriores, convertidos en casos permanentes |
| Usabilidad | Validación de formularios, claridad de los mensajes, navegación |
| Compatibilidad | Resoluciones de pantalla, escalado de Windows, instalación desde cero |
| Rendimiento | Tiempo de la consulta distribuida (RNF-04) |
| Aceptación | Instalación siguiendo únicamente el manual |

### 3.3. Sobre los casos de regresión

Tres casos del catálogo existen porque esos errores ya ocurrieron: los lectores
de las sedes 2 y 3 que no aparecían, el aviso de éxito que empujaba los botones
fuera de la pantalla, y el usuario creado en SQL Server que no se veía hasta
reiniciar. Un error corregido que no deja un caso de prueba detrás tiende a
volver.

## 4. Entorno de pruebas

| Componente | Configuración |
|---|---|
| Sistema operativo | Microsoft Windows |
| Lenguaje | Python 3.10 o superior |
| Base de datos | Microsoft SQL Server con las tres bases del proyecto |
| Controlador | ODBC Driver 17 o 18 for SQL Server |
| Datos | Los de `SQLQuery_DatosPrueba.sql` o `herramientas/cargar_datos.py` |
| Nodos | Los tres levantados, salvo en los casos que exigen uno caído |

Los casos de compatibilidad exigen además configurar la pantalla a 1366×768 y el
escalado de Windows al 150 %, uno por prueba.

## 5. Criterios de entrada y de salida

### 5.1. Para empezar a probar

- Las tres bases de datos creadas con su estructura y sus datos de prueba.
- Los tres nodos arrancan sin error.
- La aplicación abre y reporta los tres nodos en línea.
- El catálogo de casos está cargado en la herramienta de gestión.

### 5.2. Para dar la ronda por terminada

- Los ocho casos automatizados pasan.
- Todos los casos de prioridad alta están ejecutados.
- No queda ningún defecto abierto de severidad *blocker* o *critical*.
- El informe de la suite está guardado en `docs/evidencias/`.
- Las capturas de las evidencias están en `docs/capturas/`.

El criterio sobre los defectos es el que importa: un caso puede fallar y la ronda
darse por terminada si el defecto es menor y queda registrado. Lo que no se
admite es cerrar con un defecto que impide usar el sistema.

## 6. Roles

| Rol | Responsabilidad |
|---|---|
| Responsable de pruebas | Mantiene el catálogo, decide cuándo se ejecuta una ronda y consolida el informe |
| Ejecutor | Corre los casos manuales y adjunta la evidencia de cada uno |
| Desarrollador | Corrige los defectos y confirma la corrección con el caso que los detectó |

Los tres integrantes rotan por los tres roles. Quien escribió el código de una
función no debería ser quien ejecuta sus casos manuales: se tiende a probar lo
que uno sabe que funciona.

## 7. Organización de los casos

El catálogo tiene 39 casos repartidos en siete suites que siguen la estructura de
la aplicación:

| Suite | Casos | Requerimientos principales |
|---|---|---|
| Catálogo y disponibilidad | 6 | RF-05, RNF-03 |
| Préstamos y devoluciones | 11 | RF-06, RF-07, RF-08, RNF-02 |
| Usuarios | 4 | RF-02 |
| Consulta en lenguaje natural | 3 | RF-09, RNF-03 |
| Sistema distribuido y tolerancia a fallos | 5 | RNF-04, RNF-05 |
| Interfaz y navegación | 6 | RNF-06 |
| Instalación y compatibilidad | 4 | RNF-07, RNF-09 |

De esos 39, ocho están marcados como automatizados y corresponden uno a uno con
los casos PT de la suite de Python.

## 8. Herramienta de gestión

Se usa **Qase** en su plan gratuito, que admite hasta cuatro usuarios y permite
enviar resultados por API. La elección se tomó comparándola con Testiny, Tuskr y
Kiwi TCMS; el criterio decisivo fue que es la única gratuita que admite tanto a
los tres integrantes más un observador como el envío automático de resultados.

**Limitación conocida.** El plan gratuito conserva treinta días de historial. Por
eso la herramienta es la vitrina y el repositorio es el archivo: cada ronda deja
su informe fechado en `docs/evidencias/`, que no caduca.

### 8.1. Procedimiento de una ronda de pruebas

1. Levantar los tres nodos y verificar que la aplicación los ve.
2. Ejecutar `python herramientas/pruebas_transaccionales.py --nodo 1`, y repetir
   para los nodos 2 y 3.
3. Ejecutar `python publicar_en_qase.py` para subir los resultados.
4. Crear en Qase una ejecución con los casos manuales de prioridad alta.
5. Ejecutarlos adjuntando una captura por cada resultado observable.
6. Registrar como defecto cada caso fallido, con su severidad.
7. Exportar el informe de la ejecución y guardarlo junto a los de la suite.

## 9. Matriz de trazabilidad

| Requerimiento | Casos | Estado |
|---|---|---|
| RF-01 Iniciar sesión | 0 | Sin cubrir: no implementado |
| RF-02 Gestionar usuarios | 4 | Cubierto |
| RF-03 Gestionar libros | 0 | Sin cubrir: no implementado en la interfaz |
| RF-04 Gestionar ejemplares | 0 | Sin cubrir: no implementado en la interfaz |
| RF-05 Consultar disponibilidad | 7 | Cubierto |
| RF-06 Registrar préstamo | 4 | Cubierto |
| RF-07 Registrar devolución | 2 | Cubierto |
| RF-08 Controlar préstamos vencidos | 1 | Cubierto |
| RF-09 Consultar en lenguaje natural | 3 | Cubierto parcialmente: la pantalla, no el intérprete |
| RF-10 Generar reportes | 0 | Sin cubrir: no implementado |
| RNF-01 Seguridad | 0 | Sin cubrir: no implementado |
| RNF-02 Integridad de los datos | 6 | Cubierto |
| RNF-03 Veracidad de la información | 4 | Cubierto |
| RNF-04 Eficiencia de desempeño | 2 | Cubierto |
| RNF-05 Disponibilidad | 4 | Cubierto |
| RNF-06 Capacidad de interacción | 7 | Cubierto |
| RNF-07 Mantenibilidad | 1 | Cubierto por revisión de código |
| RNF-08 Trazabilidad | 1 | Cubierto |
| RNF-09 Compatibilidad | 5 | Cubierto |

Catorce de los diecinueve requerimientos quedan cubiertos. Los cinco restantes
no tienen casos porque la funcionalidad no está construida, no porque se hayan
pasado por alto. Cuando se implementen, cada uno necesita sus casos antes de
darse por terminado.

## 10. Gestión de defectos

Cada defecto se registra con el caso que lo detectó, los pasos para reproducirlo,
lo que se esperaba, lo que ocurrió y su severidad.

| Severidad | Significado | Qué hacer |
|---|---|---|
| Blocker | Impide seguir probando o usar el sistema | Se corrige antes de continuar la ronda |
| Critical | Una operación principal da un resultado incorrecto | Se corrige antes de cerrar la ronda |
| Major | Función secundaria incorrecta, con forma de rodearlo | Se corrige en la iteración |
| Minor | Molestia de interfaz o de texto | Se registra y se agenda |

Un defecto corregido se cierra volviendo a ejecutar el caso que lo detectó, no
por afirmación del desarrollador.

## 11. Riesgos de la actividad de pruebas

| Riesgo | Medida |
|---|---|
| Los tres nodos dependen de tres equipos encendidos a la vez | Ejecutar la suite por nodo y consolidar; para la ronda completa, acordar una franja |
| El historial gratuito de Qase caduca a los treinta días | Exportar el informe de cada ronda al repositorio |
| Las pruebas manuales se ejecutan sin registrar evidencia | Exigir una captura adjunta por caso; sin captura el caso no se da por ejecutado |
| Una prueba automatizada pasa sin comprobar nada | Verificar cada caso crítico contra una implementación rota a propósito, como se hizo con PT-08 |

El último riesgo es el que menos se vigila y el más caro. Una suite verde que no
detecta errores es peor que no tener suite, porque da confianza sin fundamento.

## 12. Entregables

| Entregable | Ubicación |
|---|---|
| Este plan | `docs/Plan_de_pruebas.md` |
| Catálogo de casos | `docs/pruebas/casos_prueba_qase.csv` |
| Informes de la suite automatizada | `docs/evidencias/` |
| Capturas de las pruebas manuales | `docs/capturas/` |
| Informe exportado de cada ronda | `docs/evidencias/` |
