/* ============================================================
   SISTEMA DISTRIBUIDO DE CONSULTA INTELIGENTE DE BIBLIOTECAS
   Script 2 de 2: datos de prueba de un nodo
   Motor: Microsoft SQL Server
   ------------------------------------------------------------
   COMO SE USA

   Ejecutalo DESPUES de SQLQuery_BibliotecasDB.sql, una vez por
   cada nodo. En cada ejecucion cambia las dos lineas senaladas:

        1a ejecucion ->  USE Biblioteca1DB;   @nodo = 1
        2a ejecucion ->  USE Biblioteca2DB;   @nodo = 2
        3a ejecucion ->  USE Biblioteca3DB;   @nodo = 3

   Carga cinco lectores y el catalogo que le corresponde a esa
   sede. Hay titulos repetidos entre bibliotecas a proposito
   (Cien anos de soledad esta en los nodos 1 y 2; El Aleph en el
   2 y el 3), para que la consulta distribuida tenga algo que
   agregar y se note la diferencia entre sedes.

   El script se puede ejecutar mas de una vez sin duplicar datos:
   cada insercion comprueba antes si el registro ya existe.

   Equivale a ejecutar la herramienta en Python:
        python herramientas/cargar_datos.py --nodo 1
   Los dos caminos producen exactamente los mismos datos.
   ============================================================ */

USE Biblioteca1DB;                      -- <<< CAMBIAR AQUI (1 de 2)
GO

DECLARE @nodo INT = 1;                  -- <<< CAMBIAR AQUI (2 de 2)

PRINT 'Cargando datos de prueba del nodo ' + CAST(@nodo AS VARCHAR(1))
      + ' en ' + DB_NAME();


/* ------------------------------------------------------------
   1. LECTORES
   Los mismos cinco en las tres sedes. Ojo: son personas
   distintas aunque se llamen igual, porque cada biblioteca
   lleva su propia tabla Usuario.
   ------------------------------------------------------------ */

INSERT INTO Usuario (nombre, documento, correo, telefono)
SELECT nombre, documento, correo, telefono
FROM (VALUES
    ('Ana Maria Torres',  '1012345678', 'ana.torres@example.com',      '3001112233'),
    ('Carlos Ramirez',    '1023456789', 'carlos.ramirez@example.com',  '3012223344'),
    ('Laura Gomez',       '1034567890', 'laura.gomez@example.com',     '3023334455'),
    ('Julian Castro',     '1045678901', 'julian.castro@example.com',   '3034445566'),
    ('Sofia Herrera',     '1056789012', 'sofia.herrera@example.com',   '3045556677')
) AS nuevos(nombre, documento, correo, telefono)
WHERE NOT EXISTS (
    SELECT 1 FROM Usuario u WHERE u.documento = nuevos.documento
);

PRINT '  Lectores en la sede: ' + CAST((SELECT COUNT(*) FROM Usuario) AS VARCHAR(10));


/* ------------------------------------------------------------
   2. CATALOGO DE LAS TRES SEDES
   Se declara completo y despues se filtra por el nodo que toca.
   La ultima columna es cuantos ejemplares fisicos tiene esa sede
   de ese titulo.
   ------------------------------------------------------------ */

DECLARE @catalogo TABLE (
    nodo       INT,
    isbn       VARCHAR(20),
    titulo     VARCHAR(200),
    autor      VARCHAR(150),
    editorial  VARCHAR(150),
    anio       INT,
    ejemplares INT
);

INSERT INTO @catalogo (nodo, isbn, titulo, autor, editorial, anio, ejemplares)
VALUES
    -- Nodo 1
    (1, '9780307474728', 'Cien anos de soledad',                  'Gabriel Garcia Marquez', 'Vintage',         1967, 3),
    (1, '9788437604947', 'La ciudad y los perros',                'Mario Vargas Llosa',     'Catedra',         1963, 2),
    (1, '9789500720885', 'Rayuela',                               'Julio Cortazar',         'Sudamericana',    1963, 2),
    (1, '9780132350884', 'Clean Code',                            'Robert C. Martin',       'Prentice Hall',   2008, 4),
    (1, '9780201633610', 'Design Patterns',                       'Erich Gamma',            'Addison-Wesley',  1994, 2),
    (1, '9781449373320', 'Designing Data-Intensive Applications', 'Martin Kleppmann',       'O''Reilly',       2017, 1),
    -- Nodo 2
    (2, '9780307474728', 'Cien anos de soledad',                  'Gabriel Garcia Marquez', 'Vintage',         1967, 1),
    (2, '9788420412146', 'El Aleph',                              'Jorge Luis Borges',      'Alianza',         1949, 3),
    (2, '9788497592208', 'Pedro Paramo',                          'Juan Rulfo',             'Catedra',         1955, 2),
    (2, '9780132350884', 'Clean Code',                            'Robert C. Martin',       'Prentice Hall',   2008, 1),
    (2, '9780134685991', 'Effective Java',                        'Joshua Bloch',           'Addison-Wesley',  2018, 3),
    (2, '9781593279288', 'Eloquent JavaScript',                   'Marijn Haverbeke',       'No Starch Press', 2018, 2),
    -- Nodo 3
    (3, '9788437604947', 'La ciudad y los perros',                'Mario Vargas Llosa',     'Catedra',         1963, 1),
    (3, '9788420412146', 'El Aleph',                              'Jorge Luis Borges',      'Alianza',         1949, 1),
    (3, '9789505115952', 'El tunel',                              'Ernesto Sabato',         'Seix Barral',     1948, 2),
    (3, '9780596007126', 'Head First Design Patterns',            'Eric Freeman',           'O''Reilly',       2004, 2),
    (3, '9781491950357', 'Building Microservices',                'Sam Newman',             'O''Reilly',       2015, 3),
    (3, '9780262033848', 'Introduction to Algorithms',            'Thomas H. Cormen',       'MIT Press',       2009, 2);


/* ------------------------------------------------------------
   3. TITULOS DE ESTA SEDE
   ------------------------------------------------------------ */

INSERT INTO Libro (isbn, titulo, autor, editorial, anio_publicacion)
SELECT c.isbn, c.titulo, c.autor, c.editorial, c.anio
FROM @catalogo c
WHERE c.nodo = @nodo
  AND NOT EXISTS (SELECT 1 FROM Libro l WHERE l.isbn = c.isbn);

PRINT '  Titulos en el catalogo: ' + CAST((SELECT COUNT(*) FROM Libro) AS VARCHAR(10));


/* ------------------------------------------------------------
   4. EJEMPLARES FISICOS
   Se genera uno por cada copia declarada. El codigo de
   inventario sigue el formato N<nodo>-<ultimos 5 del ISBN>-<nn>,
   el mismo que produce herramientas/cargar_datos.py.
   ------------------------------------------------------------ */

;WITH numeros AS (
    SELECT n FROM (VALUES (1), (2), (3), (4), (5)) AS t(n)
)
INSERT INTO Ejemplar (id_libro, id_biblioteca, codigo_inventario, estado)
SELECT
    l.id_libro,
    @nodo,
    'N' + CAST(@nodo AS VARCHAR(1)) + '-' + RIGHT(c.isbn, 5) + '-'
        + RIGHT('0' + CAST(n.n AS VARCHAR(2)), 2),
    'DISPONIBLE'
FROM @catalogo c
JOIN Libro l   ON l.isbn = c.isbn
JOIN numeros n ON n.n <= c.ejemplares
WHERE c.nodo = @nodo
  AND NOT EXISTS (
      SELECT 1 FROM Ejemplar e
      WHERE e.codigo_inventario =
            'N' + CAST(@nodo AS VARCHAR(1)) + '-' + RIGHT(c.isbn, 5) + '-'
                + RIGHT('0' + CAST(n.n AS VARCHAR(2)), 2)
  );

PRINT '  Ejemplares registrados: ' + CAST((SELECT COUNT(*) FROM Ejemplar) AS VARCHAR(10));
GO


/* ============================================================
   5. VERIFICACION
   Inventario de la sede: cuantos ejemplares hay de cada titulo
   y cuantos estan libres. Es la misma cifra que muestra la
   aplicacion en la pantalla de catalogo.
   ============================================================ */

SELECT
    l.id_libro,
    l.isbn,
    l.titulo,
    l.autor,
    COUNT(e.id_ejemplar) AS total_ejemplares,
    SUM(CASE WHEN e.estado = 'DISPONIBLE' THEN 1 ELSE 0 END) AS disponibles,
    SUM(CASE WHEN e.estado = 'PRESTADO'   THEN 1 ELSE 0 END) AS prestados
FROM Libro l
LEFT JOIN Ejemplar e ON e.id_libro = l.id_libro
GROUP BY l.id_libro, l.isbn, l.titulo, l.autor
ORDER BY l.titulo;

SELECT id_usuario, nombre, documento FROM Usuario ORDER BY id_usuario;
GO
