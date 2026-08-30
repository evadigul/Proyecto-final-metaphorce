-- ============================================================
-- LAMBRINSTOCK - Esquema de Base de Datos
-- Sistema de control de inventario y cotización de lambrín
-- ============================================================


PRAGMA foreign_keys = ON;


-- TABLA: clientes
-- Almacena información de los clientes del sistema.

CREATE TABLE IF NOT EXISTS clientes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT    NOT NULL,
    telefono        TEXT,
    email           TEXT,
    direccion       TEXT,
    fecha_registro  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    activo          INTEGER NOT NULL DEFAULT 1
);


-- TABLA: lambrines
-- Catálogo de productos de lambrín disponibles.
-- El campo 'codigo' es único para evitar duplicados.
-- Los precios se almacenan como TEXT para preservar precisión al utilizar Decimal en Python.

CREATE TABLE IF NOT EXISTS lambrines (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo              TEXT    NOT NULL UNIQUE,
    nombre              TEXT    NOT NULL,
    tipo                TEXT    NOT NULL,
    material            TEXT    NOT NULL,
    acabado             TEXT    NOT NULL,
    largo               REAL    NOT NULL,
    ancho               REAL    NOT NULL,
    espesor             REAL    NOT NULL,
    precio_unitario     TEXT    NOT NULL,
    stock               INTEGER NOT NULL DEFAULT 0,
    unidad_medida       TEXT    NOT NULL DEFAULT 'pieza',
    fecha_ingreso       TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    fecha_actualizacion TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    activo              INTEGER NOT NULL DEFAULT 1
);


-- TABLA: cotizaciones
-- Encabezado de cada cotización hecha por el cliente.
-- Relación 1:N con clientes (un cliente puede tener muchas
-- cotizaciones).

CREATE TABLE IF NOT EXISTS cotizaciones (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id          INTEGER,
    fecha_creacion      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    subtotal_material   TEXT    NOT NULL DEFAULT '0',
    costo_mano_obra     TEXT    NOT NULL DEFAULT '0',
    total               TEXT    NOT NULL DEFAULT '0',
    incluye_mano_obra   INTEGER NOT NULL DEFAULT 0,
    estado              TEXT    NOT NULL DEFAULT 'pendiente',
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);


-- TABLA: detalle_cotizacion
-- Líneas de detalle de cada cotización.
-- Relación 1:N con cotizaciones (una cotización puede tener
-- múltiples líneas de detalle).
-- Referencia al lambrín cotizado.

CREATE TABLE IF NOT EXISTS detalle_cotizacion (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    cotizacion_id           INTEGER NOT NULL,
    lambrin_id              INTEGER NOT NULL,
    cantidad                INTEGER NOT NULL,
    precio_unitario         TEXT    NOT NULL,
    subtotal                TEXT    NOT NULL,
    ancho_superficie        REAL    NOT NULL DEFAULT 0,
    alto_superficie         REAL    NOT NULL DEFAULT 0,
    area_superficie         REAL    NOT NULL DEFAULT 0,
    area_por_pieza          REAL    NOT NULL DEFAULT 0,
    porcentaje_desperdicio  REAL    NOT NULL DEFAULT 0,
    orientacion             TEXT    NOT NULL DEFAULT 'Vertical',
    FOREIGN KEY (cotizacion_id) REFERENCES cotizaciones(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    FOREIGN KEY (lambrin_id) REFERENCES lambrines(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);


-- ÍNDICES

CREATE INDEX IF NOT EXISTS idx_lambrines_codigo
    ON lambrines(codigo);

CREATE INDEX IF NOT EXISTS idx_lambrines_tipo
    ON lambrines(tipo);

CREATE INDEX IF NOT EXISTS idx_cotizaciones_cliente
    ON cotizaciones(cliente_id);

CREATE INDEX IF NOT EXISTS idx_detalle_cotizacion
    ON detalle_cotizacion(cotizacion_id);

CREATE INDEX IF NOT EXISTS idx_detalle_lambrin
    ON detalle_cotizacion(lambrin_id);
