-- Ejemplo didáctico: productos y categorías.
-- Datos inventados. Compatible con SQLite.
DROP TABLE IF EXISTS productos;
DROP TABLE IF EXISTS categorias;

CREATE TABLE categorias (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE
);

CREATE TABLE productos (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    precio REAL NOT NULL CHECK (precio >= 0),
    categoria_id INTEGER NOT NULL,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id)
);

INSERT INTO categorias (id, nombre) VALUES
    (1, 'Accesorios'),
    (2, 'Informática'),
    (3, 'Oficina');

INSERT INTO productos (id, nombre, precio, categoria_id) VALUES
    (1, 'Ratón', 20.00, 2),
    (2, 'Teclado', 45.00, 2),
    (3, 'Funda', 15.00, 1),
    (4, 'Mochila', 60.00, 1),
    (5, 'Cuaderno', 5.00, 3);

-- Consulta 1: ordenar productos por precio, de mayor a menor.
SELECT nombre, precio
FROM productos
ORDER BY precio DESC;

-- Consulta 2: filtrar los productos cuyo precio es mayor de 30.
SELECT nombre, precio
FROM productos
WHERE precio > 30
ORDER BY precio DESC;

-- Consulta 3: relacionar categorías y productos mediante JOIN.
SELECT p.nombre AS producto, c.nombre AS categoria, p.precio
FROM productos AS p
INNER JOIN categorias AS c ON c.id = p.categoria_id
ORDER BY p.precio DESC;
