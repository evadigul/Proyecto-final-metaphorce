"""
Gestión de la conexión y configuración de la base de datos SQLite.

Se encarga de:
- Crear la base de datos si no existe.
- Ejecutar el esquema SQL.
- Activar FOREIGN KEY support.
- Cargar datos iniciales de ejemplo.
"""

import os
import sqlite3
from decimal import Decimal

from utils.logger import configurar_logger

logger = configurar_logger(__name__)


class Database:

    def __init__(self, db_path: str = "") -> None:
        if not db_path:
            directorio_base = os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )
            db_path = os.path.join(directorio_base, "database", "lambrinstock.db")

        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def obtener_conexion(self) -> sqlite3.Connection:
        conexion = sqlite3.connect(self.db_path)
        conexion.execute("PRAGMA foreign_keys = ON")
        conexion.row_factory = sqlite3.Row
        return conexion

    def inicializar(self) -> None:
        self._crear_tablas()
        self._migrar_esquema()
        self._cargar_datos_iniciales()
        logger.info("Base de datos inicializada correctamente: %s", self.db_path)

    def _migrar_esquema(self) -> None:
        conexion = self.obtener_conexion()
        try:
            cursor = conexion.execute("PRAGMA table_info(detalle_cotizacion)")
            columnas = [row["name"] for row in cursor.fetchall()]

            if "espesor_solicitado" not in columnas:
                return  # Ya migrado o esquema nuevo

            logger.info("Detectado esquema v1.0 — iniciando migración a v1.1")

            conexion.execute("PRAGMA foreign_keys = OFF")

            conexion.execute("""
                CREATE TABLE IF NOT EXISTS cotizaciones_nueva (
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
                )
            """)
            conexion.execute("""
                INSERT INTO cotizaciones_nueva
                    (id, cliente_id, fecha_creacion, subtotal_material,
                     costo_mano_obra, total, incluye_mano_obra, estado)
                SELECT id, cliente_id, fecha_creacion, subtotal_material,
                       costo_mano_obra, total, incluye_mano_obra, estado
                FROM cotizaciones
            """)
            conexion.execute("DROP TABLE cotizaciones")
            conexion.execute("ALTER TABLE cotizaciones_nueva RENAME TO cotizaciones")

            conexion.execute("""
                CREATE TABLE IF NOT EXISTS detalle_cotizacion_nueva (
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
                )
            """)
            conexion.execute("""
                INSERT INTO detalle_cotizacion_nueva
                    (id, cotizacion_id, lambrin_id, cantidad,
                     precio_unitario, subtotal,
                     ancho_superficie, alto_superficie,
                     area_superficie, area_por_pieza,
                     porcentaje_desperdicio, orientacion)
                SELECT id, cotizacion_id, lambrin_id, cantidad,
                       precio_unitario, subtotal,
                       ancho_solicitado, largo_solicitado,
                       ancho_solicitado * largo_solicitado, 0,
                       0, 'Vertical'
                FROM detalle_cotizacion
            """)
            conexion.execute("DROP TABLE detalle_cotizacion")
            conexion.execute("ALTER TABLE detalle_cotizacion_nueva RENAME TO detalle_cotizacion")

            # Recrear índices
            conexion.execute("""
                CREATE INDEX IF NOT EXISTS idx_cotizaciones_cliente
                    ON cotizaciones(cliente_id)
            """)
            conexion.execute("""
                CREATE INDEX IF NOT EXISTS idx_detalle_cotizacion
                    ON detalle_cotizacion(cotizacion_id)
            """)
            conexion.execute("""
                CREATE INDEX IF NOT EXISTS idx_detalle_lambrin
                    ON detalle_cotizacion(lambrin_id)
            """)


            conexion.execute("PRAGMA foreign_keys = ON")
            conexion.commit()
            logger.info("Migración a v1.1 completada exitosamente")
        finally:
            conexion.close()

    def _crear_tablas(self) -> None:
        directorio_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        schema_path = os.path.join(directorio_base, "database", "schema.sql")

        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        conexion = self.obtener_conexion()
        try:
            conexion.executescript(schema_sql)
            conexion.commit()
        finally:
            conexion.close()

    def _cargar_datos_iniciales(self) -> None:
        conexion = self.obtener_conexion()
        try:
            cursor = conexion.execute("SELECT COUNT(*) FROM lambrines")
            conteo = cursor.fetchone()[0]

            if conteo > 0:
                return  

            datos_lambrines = [
                (
                    "LAM-001", "Lambrín Nogal Clásico", "Decorativo",
                    "Nogal", "Natural", 2.90, 0.15, 0.012,
                    str(Decimal("350.00")), 120, "pieza",
                ),
                (
                    "LAM-002", "Lambrín Roble Premium", "Decorativo",
                    "Roble", "Barnizado", 2.44, 0.12, 0.010,
                    str(Decimal("375.00")), 80, "pieza",
                ),
                (
                    "LAM-003", "Lambrín Cerezo Elegante", "Decorativo",
                    "Cerezo", "Satinado", 3.05, 0.15, 0.015,
                    str(Decimal("420.00")), 60, "pieza",
                ),
                (
                    "LAM-004", "Lambrín Encino Rústico", "Rústico",
                    "Encino", "Texturizado", 2.44, 0.10, 0.012,
                    str(Decimal("310.00")), 150, "pieza",
                ),
                (
                    "LAM-005", "Lambrín Wengué Moderno", "Moderno",
                    "Wengué", "Mate", 2.90, 0.12, 0.010,
                    str(Decimal("450.00")), 45, "pieza",
                ),
                (
                    "LAM-006", "Lambrín Nogal Oscuro", "Interior",
                    "Nogal", "Oscuro", 1.83, 0.15, 0.008,
                    str(Decimal("295.00")), 200, "pieza",
                ),
                (
                    "LAM-007", "Lambrín Roble Blanco", "Minimalista",
                    "Roble", "Blanco", 2.44, 0.20, 0.012,
                    str(Decimal("390.00")), 90, "pieza",
                ),
                (
                    "LAM-008", "Lambrín Cerezo Vintage", "Rústico",
                    "Cerezo", "Envejecido", 3.05, 0.10, 0.010,
                    str(Decimal("365.00")), 70, "pieza",
                ),
                (
                    "LAM-009", "Lambrín Encino Natural", "Exterior",
                    "Encino", "Natural", 2.90, 0.15, 0.015,
                    str(Decimal("340.00")), 100, "pieza",
                ),
                (
                    "LAM-010", "Lambrín Wengué Premium", "Decorativo",
                    "Wengué", "Brillante", 2.44, 0.12, 0.012,
                    str(Decimal("480.00")), 35, "pieza",
                ),
            ]

            conexion.executemany(
                """
                INSERT INTO lambrines (
                    codigo, nombre, tipo, material, acabado,
                    largo, ancho, espesor, precio_unitario,
                    stock, unidad_medida
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                datos_lambrines,
            )


            datos_clientes = [
                ("Juan Pérez", "5551234567", "juan@email.com", "Av. Reforma 123"),
                ("María García", "5559876543", "maria@email.com", "Calle Juárez 456"),
                ("Carlos López", "5554567890", "carlos@email.com", "Blvd. Norte 789"),
            ]

            conexion.executemany(
                """
                INSERT INTO clientes (nombre, telefono, email, direccion)
                VALUES (?, ?, ?, ?)
                """,
                datos_clientes,
            )

            conexion.commit()
            logger.info("Datos iniciales cargados: %d lambrines, %d clientes",
                        len(datos_lambrines), len(datos_clientes))
        finally:
            conexion.close()
