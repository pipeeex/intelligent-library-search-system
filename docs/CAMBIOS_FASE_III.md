# Fase III — Cambios implementados y dificultades encontradas

Universidad Manuela Beltrán · Ingeniería de Software · Sistemas Transaccionales
Grupo 5 · Noviembre de 2026

---

## 1. Qué se hizo en esta fase

La fase anterior dejó un backend funcional y una interfaz mínima. Esta fase se
concentró en tres frentes: reorganizar el código, rehacer la interfaz y
demostrar con pruebas que el comportamiento transaccional es el que se promete.

### 1.1. Reorganización en cuatro capas

El código estaba repartido entre una carpeta de backend y otra de interfaz, con
las reglas de negocio mezcladas con el acceso a datos. Se reorganizó en cuatro
capas con una regla de dependencia en un solo sentido:

```
presentacion/   interfaz de escritorio y contrato gRPC
negocio/        reglas de préstamo, devolución y catálogo
entidades/      objetos del dominio
datos/          repositorios y conexión a SQL Server
configuracion/  ajustes transversales
```

Las sentencias SQL quedaron confinadas a `datos/repositorios/`. La capa de
negocio no sabe qué motor de base de datos hay debajo ni qué protocolo se usa
arriba, que es la condición que exige el requerimiento RNF-07.

### 1.2. Interfaz de escritorio

La interfaz se rehízo completa. Lo más visible:

- **Navegación permanente.** Menú lateral con las cinco secciones del sistema,
  marca de sección activa, atajos de teclado de `Ctrl+1` a `Ctrl+5` y `F5` para
  recargar. Desde el panel de inicio hay accesos directos a las operaciones
  frecuentes, y se vuelve a la pantalla principal desde cualquier punto.
- **Identidad visual uniforme.** Una paleta institucional y una escala
  tipográfica únicas para toda la aplicación, definidas en un solo archivo.
- **Mensajes diferenciados.** Cuatro estados —éxito, advertencia, error e
  información— con color y texto propios. El aviso es flotante y se retira solo,
  de modo que no desplaza el contenido ni empuja los botones fuera de la vista.
- **Validación antes de enviar.** Los formularios marcan en rojo el campo con
  problema y explican qué falta, antes de que la operación llegue a la base de
  datos.
- **Adaptación a la pantalla.** La interfaz se mide a partir del DPI real del
  monitor en lugar de píxeles fijos, las tablas reparten el ancho por proporción
  y las vistas que no caben ganan una barra de desplazamiento.
- **Estado de los nodos en vivo.** Un monitor consulta las tres bibliotecas cada
  seis segundos y avisa cuando una deja de responder o vuelve, sin que el
  usuario tenga que cambiar de pantalla.

### 1.3. Operación principal completa

El registro de préstamo quedó implementado de extremo a extremo: selección de
sede, lector y título, validación, ejecución transaccional contra el nodo y
actualización inmediata del inventario y de la lista de préstamos del lector. La
devolución funciona igual, y es la operación de actualización del CRUD.

### 1.4. Pruebas transaccionales

Se construyó `herramientas/pruebas_transaccionales.py`, una suite de ocho casos
y treinta y seis comprobaciones que se ejecuta contra los nodos reales y deja un
informe fechado en `docs/evidencias/`. Cubre disponibilidad distribuida,
sincronización entre sedes, préstamo, devolución, códigos de error, atomicidad,
caída de un nodo y concurrencia sobre el último ejemplar.

### 1.5. Scripts de base de datos

El script de estructura se corrigió y se separó en dos: uno crea las ocho tablas
con sus restricciones e índices, y otro carga los datos de prueba. El segundo
produce exactamente los mismos datos que la herramienta en Python, de modo que
da igual cuál de los dos caminos se use.

---

## 2. Dificultades encontradas

### 2.1. El archivo de configuración se ignoraba en silencio

Durante días la aplicación usó el controlador ODBC 17 aunque el `.env` decía 18.
La causa era que la librería que lee ese archivo no estaba instalada, y el
código tenía un bloque que capturaba el error sin hacer nada: el archivo
sencillamente no se leía y nadie se enteraba.

La solución fue escribir un lector propio que no depende de esa librería, y
hacer que la aplicación informe al arrancar si el archivo se cargó y desde
dónde. Un fallo silencioso cuesta más tiempo que uno ruidoso.

### 2.2. Los usuarios de las sedes 2 y 3 no aparecían

Al registrar un lector en la Biblioteca 3 no se veía en la aplicación. Resultó
ser un error de diseño nuestro: la consulta de usuarios preguntaba siempre al
nodo de número menor, asumiendo que la lista era la misma en los tres.

No lo es. Cada biblioteca tiene su propia tabla `Usuario` con su propia
secuencia de identificadores, así que el usuario 5 de la sede 1 y el usuario 5
de la sede 3 son personas distintas. Hubo que hacer que todas las consultas de
usuarios y préstamos viajaran con el nodo al que pertenecen, y añadir la columna
de biblioteca en la pantalla de usuarios. Fue la consecuencia menos obvia de
haber elegido bases de datos autónomas.

### 2.3. La prueba de concurrencia pasaba sin probar nada

Al escribir el caso de concurrencia, pasó a la primera. Eso dio desconfianza, y
con razón: al ejecutarlo contra una versión del servidor sin el bloqueo de filas
—es decir, contra una implementación defectuosa a propósito— **también pasaba**.

El motivo es que el intérprete de Python ejecuta un hilo a la vez, de modo que
la secuencia de buscar un ejemplar libre y marcarlo como prestado terminaba
siendo indivisible por accidente, aunque la base de datos no lo garantizara.
Hubo que introducir una pausa deliberada dentro de la sección crítica para que
los hilos se solaparan de verdad. Con esa pausa, la versión rota falló como
debía, reportando que había entregado dos veces el mismo ejemplar. Solo después
de comprobar que la prueba detecta el error se tomó como válido que la pase la
implementación real.

La lección es que una prueba que nunca ha fallado no demuestra nada.

### 2.4. El texto se veía en unas pantallas y en otras no

Era el problema más reportado y resultaron ser cuatro causas distintas: la
aplicación no declaraba ser consciente del DPI, de modo que Windows la ampliaba
como una imagen cuando el escalado no era del 100 %; la ventana nacía en un
tamaño fijo mayor que el de algunos portátiles; los botones se empaquetaban
después de las cajas de texto, que se quedaban con todo el ancho; y el contenido
que no cabía a lo alto sencillamente quedaba fuera de alcance, sin ninguna barra
de desplazamiento.

La corrección fue medir todo a partir del DPI real, calcular la geometría desde
el tamaño del monitor, invertir el orden de empaquetado y envolver cada vista en
un contenedor desplazable. Se verificó en siete combinaciones de resolución y
escalado, desde 1024×768 hasta 2560×1440 y con escalados del 100 %, 125 % y
150 %.

### 2.5. Diferencias de configuración entre los equipos

Cada integrante tiene una instancia de SQL Server con nombre distinto y un
controlador ODBC diferente, y el proyecto no arrancaba en la máquina del
compañero. Se resolvió sacando toda la configuración a variables de entorno y
escribiendo `herramientas/diagnostico.py`, que prueba las combinaciones posibles
de controlador y servidor e indica cuál poner en el archivo local.

---

## 3. Lo que queda pendiente

| Componente | Estado | Nota |
|---|---|---|
| Autenticación y control de roles (RNF-01) | Pendiente | Es la brecha más visible de la entrega. |
| Intérprete de lenguaje natural | Diseñado, sin implementar | El diseño de la red neuronal está en el apartado 18 del documento maestro. |
| Reportes exportables (RF-10) | Parcial | La información se consulta en pantalla pero no se exporta. |
| Ejecución de las pruebas con los tres nodos activos | Pendiente | La ejecución registrada se hizo con un solo nodo levantado. |
