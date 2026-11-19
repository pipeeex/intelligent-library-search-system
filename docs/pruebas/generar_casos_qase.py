"""Genera el catalogo de casos de prueba en el formato CSV que importa Qase.

Por que un generador y no un CSV escrito a mano: el importador de Qase es
estricto con los encabezados y no ofrece una pantalla para mapear columnas. Si
rechaza el archivo, se cambia un detalle aqui y se vuelve a generar, en lugar
de editar treinta y cinco filas a mano.

Uso:
    python generar_casos_qase.py                 -> casos_prueba_qase.csv
    python generar_casos_qase.py --plural        -> usa el encabezado steps_results

La opcion --plural existe porque la documentacion de Qase se contradice: una
pagina llama a esa columna steps_result y otra steps_results. Si la importacion
falla, se prueba con la otra.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

# ---------------------------------------------------------------------------
# Encabezados del formato CSV de Qase, en el orden que espera el importador.
# ---------------------------------------------------------------------------
ENCABEZADOS = [
    "id", "title", "description", "preconditions", "postconditions", "tags",
    "priority", "severity", "type", "behavior", "automation", "status",
    "is_flaky", "layer", "steps_type", "steps_actions", "steps_result",
    "steps_data", "milestone_id", "milestone", "suite_id", "suite_parent_id",
    "suite", "suite_without_cases", "parameters", "is_muted",
]

# ---------------------------------------------------------------------------
# Suites. Se declaran antes que los casos, como exige el formato.
# ---------------------------------------------------------------------------
SUITES = [
    (1, "Catalogo y disponibilidad"),
    (2, "Prestamos y devoluciones"),
    (3, "Usuarios"),
    (4, "Consulta en lenguaje natural"),
    (5, "Sistema distribuido y tolerancia a fallos"),
    (6, "Interfaz y navegacion"),
    (7, "Instalacion y compatibilidad"),
]


def caso(suite, titulo, descripcion, precondiciones, pasos, resultados,
         etiquetas, prioridad="medium", severidad="normal", tipo="functional",
         automatizacion="is-not-automated", capa="e2e", comportamiento="positive"):
    """Arma un caso. `pasos` y `resultados` son listas de la misma longitud."""
    if len(pasos) != len(resultados):
        raise ValueError(f"'{titulo}': {len(pasos)} pasos y {len(resultados)} resultados")
    return {
        "suite": suite,
        "title": titulo,
        "description": descripcion,
        "preconditions": precondiciones,
        "tags": ",".join(etiquetas),
        "priority": prioridad,
        "severity": severidad,
        "type": tipo,
        "behavior": comportamiento,
        "automation": automatizacion,
        "layer": capa,
        "steps_actions": "\n".join(f"{i}. {p}" for i, p in enumerate(pasos, 1)),
        "steps_result": "\n".join(f"{i}. {r}" for i, r in enumerate(resultados, 1)),
    }


TRES_NODOS = "Los tres nodos estan levantados y los datos de ejemplo cargados."
UN_NODO = "Al menos el nodo 1 esta levantado con datos de ejemplo."


CASOS = [
    # =====================================================================
    # 1. CATALOGO Y DISPONIBILIDAD
    # =====================================================================
    caso(1, "Consultar disponibilidad de un titulo por su nombre",
         "Verifica la operacion basica de consulta del catalogo desde la interfaz.",
         TRES_NODOS,
         ["Abrir la aplicacion y entrar a la seccion Catalogo.",
          "Escribir 'Clean Code' en la caja de busqueda.",
          "Pulsar Buscar."],
         ["La seccion muestra la tabla de resultados vacia y el buscador activo.",
          "El texto queda escrito en la caja.",
          "Se listan las filas de 'Clean Code' con una fila por sede, indicando ejemplares disponibles y totales."],
         ["RF-05", "Catalogo"], prioridad="high", severidad="critical"),

    caso(1, "Consulta distribuida a las tres bibliotecas",
         "La consulta llega a las tres sedes y el resultado se presenta unificado. "
         "Equivale al caso automatizado PT-01.",
         TRES_NODOS,
         ["Entrar a la seccion Catalogo.",
          "Pulsar 'Ver todo' sin escribir ningun criterio.",
          "Revisar la columna Biblioteca de la tabla."],
         ["La seccion queda lista para consultar.",
          "Se carga el catalogo completo.",
          "Aparecen filas de las bibliotecas 1, 2 y 3, y en ninguna fila los disponibles superan el total."],
         ["RF-05", "RNF-04", "PT-01"], prioridad="high", severidad="blocker",
         automatizacion="automated", tipo="integration"),

    caso(1, "Buscar por autor",
         "La busqueda acepta el nombre del autor ademas del titulo.",
         TRES_NODOS,
         ["Entrar a la seccion Catalogo.",
          "Escribir 'Borges' y pulsar Buscar."],
         ["La seccion esta disponible.",
          "Se listan los titulos de Jorge Luis Borges presentes en las sedes 2 y 3."],
         ["RF-05", "Catalogo"]),

    caso(1, "Buscar por ISBN",
         "El ISBN identifica un titulo de forma exacta.",
         TRES_NODOS,
         ["Entrar a la seccion Catalogo.",
          "Escribir '9780132350884' y pulsar Buscar."],
         ["La seccion esta disponible.",
          "Se listan unicamente las filas de 'Clean Code', en las sedes 1 y 2."],
         ["RF-05", "Catalogo"], prioridad="low"),

    caso(1, "Una busqueda sin coincidencias se distingue de un error",
         "Comprueba que el sistema informa que no encontro nada, en lugar de mostrar "
         "una tabla vacia sin explicacion.",
         TRES_NODOS,
         ["Entrar a la seccion Catalogo.",
          "Escribir 'xyzxyz' y pulsar Buscar."],
         ["La seccion esta disponible.",
          "La tabla queda vacia y aparece un mensaje indicando que no hubo resultados."],
         ["RF-05", "Usabilidad"], tipo="usability", comportamiento="negative"),

    caso(1, "Un titulo agotado se distingue de un titulo inexistente",
         "Es la diferencia entre 'no lo tenemos' y 'lo tenemos pero esta prestado', "
         "que para el usuario no es lo mismo.",
         TRES_NODOS + " El titulo consultado tiene todos sus ejemplares prestados en una sede.",
         ["Prestar todos los ejemplares de un titulo en la sede 1.",
          "Entrar a la seccion Catalogo y buscar ese titulo."],
         ["Los prestamos quedan registrados.",
          "La fila de la sede 1 aparece con 0 disponibles y marcada en rojo, no desaparece de la tabla."],
         ["RF-05", "RNF-03"], prioridad="high"),

    # =====================================================================
    # 2. PRESTAMOS Y DEVOLUCIONES
    # =====================================================================
    caso(2, "Registrar un prestamo con datos validos",
         "Operacion principal del sistema. Equivale al caso automatizado PT-03.",
         TRES_NODOS,
         ["Entrar a la seccion Prestamos.",
          "Seleccionar la biblioteca 1.",
          "Seleccionar un lector de la lista.",
          "Seleccionar un titulo con ejemplares disponibles.",
          "Dejar los dias en 15 y pulsar 'Registrar prestamo'."],
         ["Se muestra el formulario con la biblioteca 1 preseleccionada.",
          "Se cargan los lectores y el catalogo de esa sede.",
          "El lector queda elegido y se muestran sus prestamos vigentes.",
          "Debajo del campo aparece cuantos ejemplares hay disponibles.",
          "Aparece el aviso verde de exito, el inventario del titulo baja en uno y el prestamo aparece en la tabla de la derecha."],
         ["RF-06", "RNF-02", "PT-03"], prioridad="high", severidad="blocker",
         automatizacion="automated"),

    caso(2, "Registrar una devolucion",
         "Cierra el prestamo y devuelve el ejemplar al inventario. "
         "Equivale al caso automatizado PT-04.",
         TRES_NODOS + " Existe un prestamo activo del lector seleccionado.",
         ["Entrar a la seccion Prestamos y seleccionar el lector con el prestamo activo.",
          "Seleccionar el prestamo en la tabla de la derecha.",
          "Pulsar 'Registrar devolucion'."],
         ["Se listan los prestamos del lector.",
          "El boton 'Registrar devolucion' se habilita.",
          "Aparece el aviso de exito, el prestamo pasa a DEVUELTO y el inventario del titulo sube en uno."],
         ["RF-07", "RNF-02", "PT-04"], prioridad="high", severidad="critical",
         automatizacion="automated"),

    caso(2, "El formulario rechaza los campos obligatorios vacios",
         "La validacion ocurre antes de enviar nada a la base de datos.",
         UN_NODO,
         ["Entrar a la seccion Prestamos.",
          "Sin seleccionar lector ni titulo, pulsar 'Registrar prestamo'."],
         ["Se muestra el formulario vacio.",
          "Los campos Usuario y Libro quedan marcados en rojo con su mensaje, aparece un aviso de error y no se registra ningun prestamo."],
         ["RF-06", "RNF-06"], prioridad="high", tipo="usability",
         comportamiento="negative"),

    caso(2, "Los dias de prestamo fuera de rango se rechazan",
         "El rango admitido es de 1 a 30 dias.",
         UN_NODO,
         ["Entrar a la seccion Prestamos y completar biblioteca, lector y titulo.",
          "Escribir 45 en el campo de dias.",
          "Pulsar 'Registrar prestamo'."],
         ["El formulario queda completo.",
          "El valor queda escrito.",
          "El campo se marca en rojo indicando que debe estar entre 1 y 30, y no se registra el prestamo."],
         ["RF-06"], comportamiento="negative"),

    caso(2, "No se puede prestar un titulo sin ejemplares disponibles",
         "La interfaz avisa antes de intentar la operacion, y el nodo la rechaza si "
         "alguien se adelanto.",
         UN_NODO + " El titulo elegido tiene cero ejemplares disponibles.",
         ["Entrar a la seccion Prestamos y seleccionar ese titulo.",
          "Pulsar 'Registrar prestamo'."],
         ["Debajo del campo aparece 'Sin ejemplares disponibles en esta sede'.",
          "El campo se marca en rojo y no se registra nada."],
         ["RF-06", "RNF-02"], prioridad="high", comportamiento="negative"),

    caso(2, "Una operacion rechazada no deja rastro",
         "Atomicidad de la transaccion. Equivale al caso automatizado PT-06.",
         UN_NODO,
         ["Ejecutar python herramientas/pruebas_transaccionales.py --nodo 1.",
          "Revisar el caso PT-06 en el informe generado."],
         ["La suite se ejecuta y escribe el informe en docs/evidencias/.",
          "PT-06 aparece como PASA: el inventario queda intacto y no se creo ningun prestamo."],
         ["RNF-02", "PT-06"], prioridad="high", severidad="blocker",
         automatizacion="automated", tipo="integration", comportamiento="negative"),

    caso(2, "Las operaciones invalidas devuelven el codigo de error correcto",
         "Equivale al caso automatizado PT-05.",
         UN_NODO,
         ["Ejecutar la suite de pruebas transaccionales sobre el nodo 1.",
          "Revisar el caso PT-05 en el informe."],
         ["La suite termina sin excepciones.",
          "Devolver dos veces da FAILED_PRECONDITION, libro o usuario inexistente da NOT_FOUND, y el nodo sigue en pie."],
         ["RNF-02", "PT-05"], automatizacion="automated", tipo="integration",
         comportamiento="negative"),

    caso(2, "Concurrencia sobre el ultimo ejemplar",
         "Varias solicitudes simultaneas no pueden entregar mas ejemplares de los que "
         "existen. Equivale al caso automatizado PT-08.",
         UN_NODO + " Hay un titulo con un solo ejemplar disponible.",
         ["Ejecutar la suite de pruebas transaccionales sobre el nodo 1.",
          "Revisar el caso PT-08 en el informe."],
         ["La suite lanza las solicitudes sincronizadas con una barrera.",
          "Se acepta exactamente el numero de ejemplares que existian, el resto se rechaza por falta de disponibilidad y ningun ejemplar se entrega dos veces."],
         ["RNF-02", "PT-08"], prioridad="high", severidad="blocker",
         automatizacion="automated", tipo="integration"),

    caso(2, "Devolver dos veces el mismo prestamo se rechaza",
         "Comprobacion manual del mismo comportamiento que verifica PT-05.",
         UN_NODO + " Existe un prestamo ya devuelto.",
         ["Entrar a Prestamos y seleccionar el lector.",
          "Seleccionar en la tabla el prestamo marcado como DEVUELTO.",
          "Observar el boton de devolucion."],
         ["Se listan los prestamos del lector.",
          "La fila queda seleccionada.",
          "El boton 'Registrar devolucion' permanece deshabilitado."],
         ["RF-07"], comportamiento="negative"),

    caso(2, "Los prestamos vencidos quedan senalados",
         "El sistema marca los prestamos cuya fecha de vencimiento ya paso.",
         UN_NODO + " Existe un prestamo con fecha de vencimiento anterior a hoy. "
         "Se puede provocar editando fecha_vencimiento en la tabla Prestamo desde SSMS.",
         ["Entrar a la seccion Prestamos.",
          "Seleccionar el lector que tiene el prestamo vencido.",
          "Revisar la tabla de la derecha y el resumen del pie."],
         ["Se muestra el formulario.",
          "Se cargan los prestamos del lector.",
          "La fila del prestamo vencido aparece en rojo con estado VENCIDO y el resumen indica cuantos hay vencidos."],
         ["RF-08"], prioridad="high"),

    caso(2, "Un prestamo se refleja de inmediato en la vista global",
         "Demuestra que la coherencia entre sedes no necesita replicacion. "
         "Equivale al caso automatizado PT-02.",
         TRES_NODOS,
         ["Anotar los disponibles de un titulo en la seccion Catalogo.",
          "Registrar un prestamo de ese titulo en la seccion Prestamos.",
          "Volver a la seccion Catalogo y consultar el mismo titulo."],
         ["Se anota la cifra inicial.",
          "El prestamo queda registrado.",
          "La cifra de disponibles bajo en uno, sin reiniciar la aplicacion ni sincronizar nada a mano."],
         ["RF-05", "RNF-08", "PT-02"], prioridad="high", severidad="critical",
         automatizacion="automated", tipo="integration"),

    # =====================================================================
    # 3. USUARIOS
    # =====================================================================
    caso(3, "Listar los lectores de una sede",
         "Cada biblioteca administra su propia tabla de usuarios.",
         TRES_NODOS,
         ["Entrar a la seccion Usuarios.",
          "Revisar la columna Biblioteca."],
         ["Se listan los lectores registrados.",
          "Cada fila indica a que sede pertenece el lector."],
         ["RF-02"]),

    caso(3, "Un lector creado directamente en SQL Server aparece sin reiniciar",
         "Verifica la recarga de datos al navegar entre secciones.",
         TRES_NODOS,
         ["Insertar un lector nuevo en la tabla Usuario de Biblioteca1DB desde SSMS.",
          "En la aplicacion, salir de la seccion Usuarios y volver a entrar.",
          "Entrar a la seccion Prestamos y desplegar la lista de lectores."],
         ["El registro queda insertado en la base.",
          "El lector nuevo aparece en el listado.",
          "El lector nuevo tambien aparece en la lista desplegable del formulario de prestamo."],
         ["RF-02"], prioridad="high", tipo="regression"),

    caso(3, "Los lectores de la sede 3 solo aparecen al elegir la sede 3",
         "Comprueba que la consulta de usuarios viaja con el nodo al que pertenece. "
         "Es la regresion del error detectado en la fase anterior.",
         TRES_NODOS,
         ["Entrar a la seccion Prestamos.",
          "Seleccionar la biblioteca 3 en el primer campo.",
          "Desplegar la lista de lectores."],
         ["Se muestra el formulario.",
          "Se recargan los datos de esa sede.",
          "Aparecen los lectores inscritos en la biblioteca 3, y no los de la biblioteca 1."],
         ["RF-02"], prioridad="high", severidad="critical", tipo="regression"),

    caso(3, "Buscar un lector por nombre o documento",
         "",
         TRES_NODOS,
         ["Entrar a la seccion Usuarios.",
          "Escribir '1012345678' y pulsar Buscar."],
         ["Se muestra el listado completo.",
          "Se filtra el listado al lector con ese documento."],
         ["RF-02"], prioridad="low"),

    # =====================================================================
    # 4. CONSULTA EN LENGUAJE NATURAL
    # =====================================================================
    caso(4, "Una pregunta en lenguaje natural devuelve disponibilidad real",
         "La respuesta se arma solo con datos de los nodos.",
         TRES_NODOS,
         ["Entrar a la seccion Consulta IA.",
          "Escribir '¿Tienen Clean Code?' y pulsar Preguntar.",
          "Contrastar las cifras con la seccion Catalogo."],
         ["Se muestra la pantalla de consulta.",
          "La respuesta indica en que sedes hay ejemplares y cuantos.",
          "Las cifras coinciden exactamente con las de la seccion Catalogo."],
         ["RF-09", "RNF-03"], prioridad="high", severidad="critical"),

    caso(4, "La respuesta advierte que el interprete aun no esta implementado",
         "Honestidad sobre el estado del modulo: no debe presentarse como IA "
         "funcionando cuando todavia busca por coincidencia de texto.",
         UN_NODO,
         ["Entrar a la seccion Consulta IA.",
          "Formular cualquier pregunta."],
         ["Se muestra el aviso informativo sobre el estado del modulo.",
          "La respuesta incluye la nota de que la busqueda es por coincidencia de texto."],
         ["RF-09", "RNF-03"], tipo="acceptance"),

    caso(4, "Una pregunta sin criterio identificable pide precision",
         "El sistema no debe devolver un resultado aproximado cuando no entendio. "
         "Es el criterio del requerimiento RNF-03.",
         UN_NODO,
         ["Entrar a la seccion Consulta IA.",
          "Escribir '¿a que hora cierran?' y pulsar Preguntar."],
         ["Se muestra la pantalla de consulta.",
          "El sistema informa que no identifico un criterio de busqueda y pide precisar, sin mostrar titulos aproximados."],
         ["RF-09", "RNF-03"], prioridad="high", comportamiento="negative"),

    # =====================================================================
    # 5. SISTEMA DISTRIBUIDO
    # =====================================================================
    caso(5, "El sistema sigue operando con un nodo caido",
         "Tolerancia a fallos parciales. Equivale al caso automatizado PT-07.",
         TRES_NODOS,
         ["Entrar a la seccion Catalogo y pulsar 'Ver todo'.",
          "Detener el servidor del nodo 2.",
          "Esperar unos segundos y volver a pulsar 'Ver todo'."],
         ["Se listan resultados de las tres sedes.",
          "El servidor se detiene.",
          "Se listan los resultados de las sedes 1 y 3, y la barra inferior indica que el nodo 2 no responde."],
         ["RNF-05", "PT-07"], prioridad="high", severidad="blocker",
         automatizacion="automated", tipo="integration"),

    caso(5, "El monitor detecta la caida sin cambiar de seccion",
         "El estado de los nodos se actualiza solo cada seis segundos.",
         TRES_NODOS,
         ["Dejar la aplicacion abierta en la seccion Inicio.",
          "Detener el servidor del nodo 3 desde su terminal.",
          "Esperar sin tocar la aplicacion y observar la barra inferior."],
         ["Se muestran los tres nodos en linea.",
          "El servidor se detiene.",
          "En menos de diez segundos la barra inferior pasa a indicar 2 de 3 nodos en linea y aparece el aviso del nodo caido."],
         ["RNF-05"], prioridad="high"),

    caso(5, "Un nodo que vuelve reaparece sin reiniciar la aplicacion",
         "Como no hay replicacion, el nodo que regresa no tiene nada que poner al dia.",
         "La aplicacion esta abierta y el nodo 3 esta detenido.",
         ["Volver a levantar el servidor del nodo 3.",
          "Esperar sin tocar la aplicacion.",
          "Consultar el catalogo."],
         ["El servidor arranca.",
          "La barra inferior vuelve a indicar 3 de 3 nodos en linea y aparece el aviso correspondiente.",
          "Los titulos de la sede 3 vuelven a aparecer en el resultado."],
         ["RNF-05"], prioridad="high"),

    caso(5, "La consulta distribuida responde en menos de tres segundos",
         "Criterio de aceptacion del requerimiento RNF-04.",
         TRES_NODOS,
         ["Entrar a la seccion Catalogo.",
          "Cronometrar desde que se pulsa 'Ver todo' hasta que la tabla queda cargada.",
          "Repetir la medicion tres veces."],
         ["La seccion esta disponible.",
          "Se registra el tiempo transcurrido.",
          "Las tres mediciones quedan por debajo de tres segundos."],
         ["RNF-04"], prioridad="high", tipo="performance"),

    caso(5, "Sin ningun nodo disponible la aplicacion conmuta a modo demostracion",
         "Permite sustentar aunque falten los servidores.",
         "Ningun servidor de nodo esta levantado.",
         ["Ejecutar python aplicacion.py.",
          "Observar la barra inferior.",
          "Navegar por las secciones."],
         ["La aplicacion abre sin error.",
          "La barra inferior muestra la etiqueta DEMO y explica que son datos de prueba en memoria.",
          "Todas las secciones funcionan con los datos de ejemplo."],
         ["RNF-05"], tipo="acceptance"),

    # =====================================================================
    # 6. INTERFAZ Y NAVEGACION
    # =====================================================================
    caso(6, "Navegacion entre las cinco secciones",
         "Criterio 2.2 de la entrega: acceso organizado a los modulos.",
         UN_NODO,
         ["Abrir la aplicacion.",
          "Pulsar sucesivamente Inicio, Catalogo, Prestamos, Usuarios y Consulta IA en el menu lateral.",
          "Desde la ultima seccion, volver a Inicio."],
         ["Se abre en la seccion Inicio con esa opcion marcada.",
          "Cada seccion se muestra y el menu marca la opcion activa con la barra granate.",
          "Se regresa a la pantalla principal."],
         ["RNF-06"], prioridad="high", tipo="usability"),

    caso(6, "Atajos de teclado",
         "",
         UN_NODO,
         ["Pulsar Ctrl+3.",
          "Pulsar Ctrl+1.",
          "Pulsar F5."],
         ["Se abre la seccion Prestamos.",
          "Se vuelve a la seccion Inicio.",
          "Los datos de la seccion se recargan."],
         ["RNF-06"], prioridad="low", tipo="usability"),

    caso(6, "Los mensajes distinguen exito, error y advertencia",
         "Criterio 2.1 de la entrega: mensajes claros segun el resultado.",
         UN_NODO,
         ["Registrar un prestamo valido y observar el aviso.",
          "Intentar registrar un prestamo con campos vacios y observar el aviso.",
          "Detener un nodo y observar el aviso."],
         ["Aparece un aviso verde con el detalle del prestamo.",
          "Aparece un aviso rojo indicando que hay campos sin completar.",
          "Aparece un aviso ambar indicando que el nodo dejo de responder."],
         ["RNF-06"], prioridad="high", tipo="usability"),

    caso(6, "El aviso de exito no desplaza los botones",
         "Regresion del error reportado en la fase anterior: el aviso empujaba los "
         "botones fuera de la pantalla.",
         UN_NODO,
         ["Entrar a Prestamos y registrar un prestamo valido.",
          "Observar la posicion de los botones mientras el aviso esta visible.",
          "Esperar unos segundos."],
         ["Aparece el aviso de exito flotando en la esquina inferior derecha.",
          "Los botones siguen en su sitio y visibles.",
          "El aviso se retira solo."],
         ["RNF-06"], tipo="regression"),

    caso(6, "La interfaz se adapta a una pantalla de 1366x768",
         "Resolucion tipica de portatil, donde antes se cortaba el boton de registrar.",
         UN_NODO + " La pantalla esta configurada a 1366x768 con escalado al 100 %.",
         ["Abrir la aplicacion.",
          "Recorrer las cinco secciones.",
          "Entrar a Prestamos y buscar el boton 'Registrar prestamo'."],
         ["La ventana cabe completa en la pantalla.",
          "Ningun texto queda cortado en ninguna seccion.",
          "El boton es visible o se alcanza con la barra de desplazamiento."],
         ["RNF-06", "RNF-09"], prioridad="high", tipo="compatibility"),

    caso(6, "La interfaz se adapta al escalado de Windows al 150 %",
         "Comprueba la conciencia de DPI.",
         UN_NODO + " El escalado de Windows esta al 150 %.",
         ["Abrir la aplicacion.",
          "Recorrer las cinco secciones.",
          "Revisar los encabezados de las tablas y los botones."],
         ["La ventana abre con un tamano proporcionado y el texto nitido, no borroso.",
          "Ningun texto queda cortado.",
          "Los encabezados de las tablas se leen completos."],
         ["RNF-06", "RNF-09"], prioridad="high", tipo="compatibility"),

    # =====================================================================
    # 7. INSTALACION Y COMPATIBILIDAD
    # =====================================================================
    caso(7, "Instalacion desde cero siguiendo unicamente el README",
         "Criterio de aceptacion del requerimiento RNF-09. Conviene hacerlo en un "
         "equipo donde el proyecto nunca se ha ejecutado.",
         "Equipo con Python 3.10 o superior, SQL Server y el controlador ODBC instalados.",
         ["Clonar el repositorio y crear el entorno virtual como indica el README.",
          "Instalar las dependencias y copiar .env.example a .env.",
          "Ejecutar python herramientas/generar_protos.py.",
          "Ejecutar los dos scripts SQL sobre las tres bases.",
          "Levantar un nodo y abrir la aplicacion."],
         ["El repositorio queda clonado y el entorno creado.",
          "Las dependencias se instalan y el archivo de configuracion queda listo para editar.",
          "Se generan los archivos del contrato gRPC sin error.",
          "Las tres bases quedan creadas con sus ocho tablas y sus datos de prueba.",
          "La aplicacion abre y se conecta al nodo sin pasos adicionales no documentados."],
         ["RNF-09"], prioridad="high", severidad="critical", tipo="acceptance"),

    caso(7, "La herramienta de diagnostico orienta cuando la conexion falla",
         "",
         "El archivo .env tiene un nombre de servidor incorrecto a proposito.",
         ["Ejecutar python herramientas/diagnostico.py.",
          "Leer la salida."],
         ["La herramienta prueba las combinaciones de controlador y servidor.",
          "Indica cual combinacion funciona y que valores poner en el archivo .env."],
         ["RNF-09"], tipo="usability"),

    caso(7, "Las reglas de negocio no contienen SQL ni referencias al protocolo",
         "Criterio de aceptacion del requerimiento RNF-07, que se verifica por "
         "revision de codigo y no ejecutando la aplicacion.",
         "El repositorio esta clonado.",
         ["Buscar SELECT, INSERT, UPDATE y DELETE dentro de la carpeta negocio/.",
          "Buscar las palabras grpc y stub dentro de la carpeta negocio/.",
          "Buscar sentencias SQL dentro de datos/repositorios/."],
         ["No aparece ninguna sentencia SQL en la capa de negocio.",
          "No aparece ninguna referencia al protocolo en la capa de negocio.",
          "Las sentencias SQL aparecen unicamente en los repositorios."],
         ["RNF-07"], tipo="other", capa="unit", automatizacion="to-be-automated"),

    caso(7, "Los scripts SQL crean las tres bases de datos",
         "Comprueba que la estructura y los datos de prueba se obtienen solo con SQL, "
         "sin ejecutar Python.",
         "SQL Server instalado y sin las bases del proyecto creadas.",
         ["Ejecutar SQLQuery_BibliotecasDB.sql tres veces, cambiando el nombre marcado.",
          "Ejecutar SQLQuery_DatosPrueba.sql tres veces, cambiando el nombre y el numero de nodo.",
          "Revisar la consulta de verificacion del final."],
         ["Quedan creadas Biblioteca1DB, Biblioteca2DB y Biblioteca3DB con ocho tablas cada una.",
          "Cada base queda con sus cinco lectores y su catalogo propio.",
          "El inventario mostrado coincide con el catalogo definido para esa sede."],
         ["RNF-09"], prioridad="high", tipo="acceptance"),
]


def generar(destino: Path, plural: bool) -> None:
    encabezados = list(ENCABEZADOS)
    if plural:
        encabezados[encabezados.index("steps_result")] = "steps_results"
    clave_resultado = "steps_results" if plural else "steps_result"

    nombres = {n: t for n, t in SUITES}
    filas = []

    # Las suites van primero: el importador las necesita declaradas antes
    # de encontrarse con los casos que las referencian.
    for numero, titulo in SUITES:
        fila = {c: "" for c in encabezados}
        fila.update({"suite_id": numero, "suite": titulo, "suite_without_cases": 1})
        filas.append(fila)

    for c in CASOS:
        fila = {col: "" for col in encabezados}
        fila.update({
            "title": c["title"],
            "description": c["description"],
            "preconditions": c["preconditions"],
            "tags": c["tags"],
            "priority": c["priority"],
            "severity": c["severity"],
            "type": c["type"],
            "behavior": c["behavior"],
            "automation": c["automation"],
            "status": "actual",
            "is_flaky": "no",
            "layer": c["layer"],
            "steps_type": "classic",
            "steps_actions": c["steps_actions"],
            clave_resultado: c["steps_result"],
            "suite_id": c["suite"],
            "suite": nombres[c["suite"]],
        })
        filas.append(fila)

    # utf-8-sig: Excel abre el archivo con los acentos correctos.
    with destino.open("w", encoding="utf-8-sig", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=encabezados, quoting=csv.QUOTE_MINIMAL)
        escritor.writeheader()
        escritor.writerows(filas)

    print(f"{destino.name}: {len(SUITES)} suites y {len(CASOS)} casos de prueba.")
    por_suite: dict[int, int] = {}
    for c in CASOS:
        por_suite[c["suite"]] = por_suite.get(c["suite"], 0) + 1
    for numero, titulo in SUITES:
        print(f"   {por_suite.get(numero, 0):>2}  {titulo}")
    automatizados = sum(1 for c in CASOS if c["automation"] == "automated")
    print(f"\n   {automatizados} automatizados, {len(CASOS) - automatizados} manuales")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", default="casos_prueba_qase.csv")
    parser.add_argument("--plural", action="store_true",
                        help="Usar el encabezado steps_results en lugar de steps_result")
    args = parser.parse_args()
    generar(Path(args.salida), args.plural)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
