/* ============================================================
   SISTEMA DISTRIBUIDO DE CONSULTA INTELIGENTE DE LIBROS
   Base de datos para un nodo bibliotecario
   Tecnologia: Microsoft SQL Server
   ============================================================ */


/* ============================================================
   1. CREACION DE LA BASE DE DATOS
   ============================================================ */

IF DB_ID('BibliotecaDB') IS NOT NULL
BEGIN
    DROP DATABASE BibliotecaDB;
END;
GO

CREATE DATABASE BibliotecaDB;
GO

USE BibliotecaDB;
GO


/* ============================================================
   2. CREACION DE LA TABLA BIBLIOTECA
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
   3. CREACION DE LA TABLA LIBRO
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
   4. CREACION DE LA TABLA USUARIO
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
   5. CREACION DE LA TABLA EJEMPLAR
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


/* ============================================================
   6. CREACION DE LA TABLA PRESTAMO
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


/* ============================================================
   7. CREACION DE LA TABLA DEVOLUCION
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
   8. CREACION DE LA TABLA CONSULTA
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
   9. CREACION DE LA TABLA RESULTADO_CONSULTA
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
   10. INSERCION INICIAL DE LAS BIBLIOTECAS
   ============================================================ */

INSERT INTO Biblioteca (nombre, direccion, estado)
VALUES
    ('Biblioteca 1', 'Direcci�n Biblioteca 1', 'ACTIVA'),
    ('Biblioteca 2', 'Direcci�n Biblioteca 2', 'ACTIVA'),
    ('Biblioteca 3', 'Direcci�n Biblioteca 3', 'ACTIVA');
GO


/* ============================================================
   11. CONSULTA DE VERIFICACI�N
   ============================================================ */

SELECT * FROM Biblioteca;
SELECT * FROM Libro;
SELECT * FROM Usuario;
SELECT * FROM Ejemplar;
SELECT * FROM Prestamo;
SELECT * FROM Devolucion;
SELECT * FROM Consulta;
SELECT * FROM Resultado_Consulta;
GO