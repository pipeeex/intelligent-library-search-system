/* ============================================================
   SISTEMA DISTRIBUIDO DE CONSULTA INTELIGENTE DE BIBLIOTECAS
   Script 1 de 2: estructura de la base de datos de un nodo
   Motor: Microsoft SQL Server
   ------------------------------------------------------------
   COMO SE USA

   Cada biblioteca es un nodo independiente con su propia base de
   datos. Este script crea la estructura de UNA de ellas, asi que
   hay que ejecutarlo tres veces.

   En cada ejecucion cambia unicamente el nombre que aparece en el
   bloque marcado mas abajo:

        1a ejecucion ->  Biblioteca1DB
        2a ejecucion ->  Biblioteca2DB
        3a ejecucion ->  Biblioteca3DB

   El nombre aparece dos veces seguidas y estan senaladas. Despues
   de crear la estructura, ejecuta el script de datos de prueba
   SQLQuery_DatosPrueba.sql sobre esa misma base.
   ============================================================ */


/* ============================================================
   1. CREACION DE LA BASE DE DATOS

   >>> CAMBIA EL NOMBRE EN LAS DOS LINEAS SENALADAS <<<

   El script no borra nada: si la base ya existe, se detiene y
   avisa, para no destruir datos de un companero por accidente.
   ============================================================ */

IF DB_ID('Biblioteca1DB') IS NOT NULL      -- <<< CAMBIAR AQUI (1 de 2)
BEGIN
    RAISERROR('La base de datos ya existe. Borrala a mano si quieres recrearla.', 16, 1);
    SET NOEXEC ON;
END;
GO

CREATE DATABASE Biblioteca1DB;             -- <<< CAMBIAR AQUI (2 de 2)
GO

USE Biblioteca1DB;                         -- <<< CAMBIAR AQUI (3 de 3)
GO

PRINT 'Creando la estructura en: ' + DB_NAME();
GO


/* ============================================================
   2. TABLA BIBLIOTECA
   Ficha de cada sede. Las tres filas son iguales en los tres
   nodos, de modo que un ejemplar pueda decir a que sede pertenece.
   ============================================================ */

CREATE TABLE Biblioteca (
    id_biblioteca INT IDENTITY(1,1) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    direccion VARCHAR(200) NOT NULL,
    estado VARCHAR(20) NOT NULL,

    CONSTRAINT PK_Biblioteca
        PRIMARY KEY (id_biblioteca),

    CONSTRAINT CK_Biblioteca_Estado
        CHECK (estado IN ('ACTIVA', 'INACTIVA'))
);
GO


/* ============================================================
   3. TABLA LIBRO
   El titulo como obra: lo que identifica el ISBN. No confundir
   con el ejemplar, que es la copia fisica.
   ============================================================ */

CREATE TABLE Libro (
    id_libro INT IDENTITY(1,1) NOT NULL,
    isbn VARCHAR(20) NOT NULL,
    titulo VARCHAR(200) NOT NULL,
    autor VARCHAR(150) NOT NULL,
    editorial VARCHAR(150) NULL,
    anio_publicacion INT NULL,

    CONSTRAINT PK_Libro
        PRIMARY KEY (id_libro),

    CONSTRAINT UQ_Libro_ISBN
        UNIQUE (isbn),

    CONSTRAINT CK_Libro_Anio
        CHECK (
            anio_publicacion IS NULL
            OR anio_publicacion BETWEEN 1000 AND YEAR(GETDATE())
        )
);
GO


/* ============================================================
   4. TABLA USUARIO
   Los lectores de ESTA sede. Cada nodo lleva su propia tabla,
   asi que el mismo id_usuario puede ser otra persona en otra
   biblioteca y un lector solo recibe prestamos donde esta inscrito.
   ============================================================ */

CREATE TABLE Usuario (
    id_usuario INT IDENTITY(1,1) NOT NULL,
    nombre VARCHAR(150) NOT NULL,
    documento VARCHAR(30) NOT NULL,
    correo VARCHAR(150) NULL,
    telefono VARCHAR(30) NULL,

    CONSTRAINT PK_Usuario
        PRIMARY KEY (id_usuario),

    CONSTRAINT UQ_Usuario_Documento
        UNIQUE (documento)
);
GO


/* ============================================================
   5. TABLA EJEMPLAR
   La copia fisica. La disponibilidad se cuenta aqui, no en Libro.
   ============================================================ */

CREATE TABLE Ejemplar (
    id_ejemplar INT IDENTITY(1,1) NOT NULL,
    id_libro INT NOT NULL,
    id_biblioteca INT NOT NULL,
    codigo_inventario VARCHAR(50) NOT NULL,
    estado VARCHAR(20) NOT NULL,

    CONSTRAINT PK_Ejemplar
        PRIMARY KEY (id_ejemplar),

    CONSTRAINT UQ_Ejemplar_Codigo
        UNIQUE (codigo_inventario),

    CONSTRAINT FK_Ejemplar_Libro
        FOREIGN KEY (id_libro)
        REFERENCES Libro(id_libro),

    CONSTRAINT FK_Ejemplar_Biblioteca
        FOREIGN KEY (id_biblioteca)
        REFERENCES Biblioteca(id_biblioteca),

    CONSTRAINT CK_Ejemplar_Estado
        CHECK (
            estado IN (
                'DISPONIBLE',
                'PRESTADO',
                'MANTENIMIENTO',
                'BAJA'
            )
        )
);
GO

/* Indice de apoyo: la consulta de disponibilidad agrupa los
   ejemplares por libro y estado, y es la operacion mas frecuente. */
CREATE INDEX IX_Ejemplar_Libro_Estado
    ON Ejemplar (id_libro, estado);
GO


/* ============================================================
   6. TABLA PRESTAMO
   ============================================================ */

CREATE TABLE Prestamo (
    id_prestamo INT IDENTITY(1,1) NOT NULL,
    id_usuario INT NOT NULL,
    id_ejemplar INT NOT NULL,
    fecha_prestamo DATETIME2 NOT NULL,
    fecha_vencimiento DATETIME2 NOT NULL,
    estado VARCHAR(20) NOT NULL,

    CONSTRAINT PK_Prestamo
        PRIMARY KEY (id_prestamo),

    CONSTRAINT FK_Prestamo_Usuario
        FOREIGN KEY (id_usuario)
        REFERENCES Usuario(id_usuario),

    CONSTRAINT FK_Prestamo_Ejemplar
        FOREIGN KEY (id_ejemplar)
        REFERENCES Ejemplar(id_ejemplar),

    CONSTRAINT CK_Prestamo_Estado
        CHECK (
            estado IN (
                'ACTIVO',
                'DEVUELTO',
                'VENCIDO'
            )
        ),

    CONSTRAINT CK_Prestamo_Fechas
        CHECK (fecha_vencimiento >= fecha_prestamo)
);
GO

/* Indice de apoyo: el control de cupo busca los prestamos activos
   de un lector antes de autorizar uno nuevo. */
CREATE INDEX IX_Prestamo_Usuario_Estado
    ON Prestamo (id_usuario, estado);
GO


/* ============================================================
   7. TABLA DEVOLUCION
   Un prestamo se devuelve una sola vez: de ahi la restriccion
   UNIQUE sobre id_prestamo.
   ============================================================ */

CREATE TABLE Devolucion (
    id_devolucion INT IDENTITY(1,1) NOT NULL,
    id_prestamo INT NOT NULL,
    fecha_devolucion DATETIME2 NOT NULL,
    observacion VARCHAR(300) NULL,

    CONSTRAINT PK_Devolucion
        PRIMARY KEY (id_devolucion),

    CONSTRAINT FK_Devolucion_Prestamo
        FOREIGN KEY (id_prestamo)
        REFERENCES Prestamo(id_prestamo),

    CONSTRAINT UQ_Devolucion_Prestamo
        UNIQUE (id_prestamo)
);
GO


/* ============================================================
   8. TABLA CONSULTA
   Bitacora de lo que los usuarios preguntan al modulo de IA.
   ============================================================ */

CREATE TABLE Consulta (
    id_consulta INT IDENTITY(1,1) NOT NULL,
    pregunta VARCHAR(500) NOT NULL,
    fecha_hora DATETIME2 NOT NULL
        CONSTRAINT DF_Consulta_FechaHora
        DEFAULT SYSDATETIME(),
    tipo_consulta VARCHAR(50) NOT NULL,

    CONSTRAINT PK_Consulta
        PRIMARY KEY (id_consulta)
);
GO


/* ============================================================
   9. TABLA RESULTADO_CONSULTA
   Lo que respondio cada sede a una consulta. Es la evidencia de
   que la cifra mostrada al usuario salio de los nodos.
   ============================================================ */

CREATE TABLE Resultado_Consulta (
    id_resultado INT IDENTITY(1,1) NOT NULL,
    id_consulta INT NOT NULL,
    id_biblioteca INT NOT NULL,
    disponibilidad VARCHAR(30) NOT NULL,
    cantidad_disponible INT NOT NULL,
    mensaje VARCHAR(500) NULL,

    CONSTRAINT PK_Resultado_Consulta
        PRIMARY KEY (id_resultado),

    CONSTRAINT FK_Resultado_Consulta_Consulta
        FOREIGN KEY (id_consulta)
        REFERENCES Consulta(id_consulta),

    CONSTRAINT FK_Resultado_Consulta_Biblioteca
        FOREIGN KEY (id_biblioteca)
        REFERENCES Biblioteca(id_biblioteca),

    CONSTRAINT CK_Resultado_Cantidad
        CHECK (cantidad_disponible >= 0)
);
GO


/* ============================================================
   10. FICHA DE LAS TRES SEDES
   Se insertan las tres en cada nodo para que id_biblioteca
   signifique lo mismo en las tres bases de datos.
   ============================================================ */

INSERT INTO Biblioteca (nombre, direccion, estado)
VALUES
    ('Biblioteca 1', 'Sede Norte - Calle 100 No. 15-20', 'ACTIVA'),
    ('Biblioteca 2', 'Sede Centro - Carrera 7 No. 40-53', 'ACTIVA'),
    ('Biblioteca 3', 'Sede Sur - Avenida 68 No. 24-10', 'ACTIVA');
GO


/* ============================================================
   11. VERIFICACION
   Si todo salio bien, aqui se ven ocho tablas y tres bibliotecas.
   ============================================================ */

PRINT 'Estructura creada en: ' + DB_NAME();
GO

SELECT TABLE_NAME AS tabla
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_NAME;

SELECT * FROM Biblioteca;
GO

SET NOEXEC OFF;
GO
