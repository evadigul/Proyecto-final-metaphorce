"""
Repositorio para operaciones CRUD y consultas avanzadas de Lambrín.

"""

import sqlite3
from decimal import Decimal
from typing import Optional

from models.lambrin import Lambrin
from repositories.database import Database
from utils.logger import configurar_logger

logger = configurar_logger(__name__)


class LambrinRepository:

    def __init__(self, database: Database) -> None:
        self.database = database

    def _row_a_lambrin(self, row: sqlite3.Row) -> Lambrin:
        return Lambrin(
            id=row["id"],
            codigo=row["codigo"],
            nombre=row["nombre"],
            tipo=row["tipo"],
            material=row["material"],
            acabado=row["acabado"],
            largo=row["largo"],
            ancho=row["ancho"],
            espesor=row["espesor"],
            precio_unitario=Decimal(row["precio_unitario"]),
            stock=row["stock"],
            unidad_medida=row["unidad_medida"],
            fecha_ingreso=row["fecha_ingreso"],
            fecha_actualizacion=row["fecha_actualizacion"],
            activo=bool(row["activo"]),
        )


    def crear(self, lambrin: Lambrin) -> int:
        conexion = self.database.obtener_conexion()
        try:
            cursor = conexion.execute(
                """
                INSERT INTO lambrines (
                    codigo, nombre, tipo, material, acabado,
                    largo, ancho, espesor, precio_unitario,
                    stock, unidad_medida
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lambrin.codigo,
                    lambrin.nombre,
                    lambrin.tipo,
                    lambrin.material,
                    lambrin.acabado,
                    lambrin.largo,
                    lambrin.ancho,
                    lambrin.espesor,
                    str(lambrin.precio_unitario),
                    lambrin.stock,
                    lambrin.unidad_medida,
                ),
            )
            conexion.commit()
            lambrin_id = cursor.lastrowid
            logger.info("Lambrín creado: ID=%d, código=%s", lambrin_id, lambrin.codigo)
            return lambrin_id
        finally:
            conexion.close()

    def obtener_por_id(self, lambrin_id: int) -> Optional[Lambrin]:
        conexion = self.database.obtener_conexion()
        try:
            cursor = conexion.execute(
                "SELECT * FROM lambrines WHERE id = ?", (lambrin_id,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_a_lambrin(row)
            return None
        finally:
            conexion.close()

    def obtener_por_codigo(self, codigo: str) -> Optional[Lambrin]:
        conexion = self.database.obtener_conexion()
        try:
            cursor = conexion.execute(
                "SELECT * FROM lambrines WHERE codigo = ?", (codigo,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_a_lambrin(row)
            return None
        finally:
            conexion.close()

    def obtener_todos(self, solo_activos: bool = True) -> list[Lambrin]:
        conexion = self.database.obtener_conexion()
        try:
            if solo_activos:
                cursor = conexion.execute(
                    "SELECT * FROM lambrines WHERE activo = 1 ORDER BY codigo"
                )
            else:
                cursor = conexion.execute(
                    "SELECT * FROM lambrines ORDER BY codigo"
                )
            return [self._row_a_lambrin(row) for row in cursor.fetchall()]
        finally:
            conexion.close()

    def actualizar(self, lambrin: Lambrin) -> bool:
        conexion = self.database.obtener_conexion()
        try:
            cursor = conexion.execute(
                """
                UPDATE lambrines SET
                    nombre = ?,
                    tipo = ?,
                    material = ?,
                    acabado = ?,
                    largo = ?,
                    ancho = ?,
                    espesor = ?,
                    precio_unitario = ?,
                    stock = ?,
                    unidad_medida = ?,
                    fecha_actualizacion = datetime('now', 'localtime'),
                    activo = ?
                WHERE id = ?
                """,
                (
                    lambrin.nombre,
                    lambrin.tipo,
                    lambrin.material,
                    lambrin.acabado,
                    lambrin.largo,
                    lambrin.ancho,
                    lambrin.espesor,
                    str(lambrin.precio_unitario),
                    lambrin.stock,
                    lambrin.unidad_medida,
                    1 if lambrin.activo else 0,
                    lambrin.id,
                ),
            )
            conexion.commit()
            actualizado = cursor.rowcount > 0
            if actualizado:
                logger.info("Lambrín actualizado: ID=%d", lambrin.id)
            return actualizado
        finally:
            conexion.close()

    def desactivar(self, lambrin_id: int) -> bool:
        conexion = self.database.obtener_conexion()
        try:
            cursor = conexion.execute(
                """
                UPDATE lambrines SET
                    activo = 0,
                    fecha_actualizacion = datetime('now', 'localtime')
                WHERE id = ?
                """,
                (lambrin_id,),
            )
            conexion.commit()
            desactivado = cursor.rowcount > 0
            if desactivado:
                logger.info("Lambrín desactivado: ID=%d", lambrin_id)
            return desactivado
        finally:
            conexion.close()

    def actualizar_stock(self, lambrin_id: int, nuevo_stock: int) -> bool:
        conexion = self.database.obtener_conexion()
        try:
            cursor = conexion.execute(
                """
                UPDATE lambrines SET
                    stock = ?,
                    fecha_actualizacion = datetime('now', 'localtime')
                WHERE id = ?
                """,
                (nuevo_stock, lambrin_id),
            )
            conexion.commit()
            return cursor.rowcount > 0
        finally:
            conexion.close()


    def buscar_por_tipo(self, tipo: str) -> list[Lambrin]:
        conexion = self.database.obtener_conexion()
        try:
            cursor = conexion.execute(
                """
                SELECT * FROM lambrines
                WHERE tipo LIKE ? AND activo = 1
                ORDER BY nombre
                """,
                (f"%{tipo}%",),
            )
            return [self._row_a_lambrin(row) for row in cursor.fetchall()]
        finally:
            conexion.close()

    def buscar_por_material(self, material: str) -> list[Lambrin]:
        conexion = self.database.obtener_conexion()
        try:
            cursor = conexion.execute(
                """
                SELECT * FROM lambrines
                WHERE material LIKE ? AND activo = 1
                ORDER BY nombre
                """,
                (f"%{material}%",),
            )
            return [self._row_a_lambrin(row) for row in cursor.fetchall()]
        finally:
            conexion.close()

    def buscar_compatibles(
        self,
        largo: float,
        ancho: float,
        espesor: float,
        tipo: str = "",
    ) -> list[Lambrin]:
        conexion = self.database.obtener_conexion()
        try:
            query = """
                SELECT * FROM lambrines
                WHERE activo = 1
                    AND ABS(largo - ?) < 0.001
                    AND ABS(ancho - ?) < 0.001
                    AND ABS(espesor - ?) < 0.001
            """
            params: list = [largo, ancho, espesor]

            if tipo:
                query += " AND tipo LIKE ?"
                params.append(f"%{tipo}%")

            query += " ORDER BY nombre"
            cursor = conexion.execute(query, params)
            return [self._row_a_lambrin(row) for row in cursor.fetchall()]
        finally:
            conexion.close()

    def obtener_stock_bajo(self, umbral: int = 10) -> list[Lambrin]:
        conexion = self.database.obtener_conexion()
        try:
            cursor = conexion.execute(
                """
                SELECT * FROM lambrines
                WHERE activo = 1 AND stock <= ?
                ORDER BY stock ASC
                """,
                (umbral,),
            )
            return [self._row_a_lambrin(row) for row in cursor.fetchall()]
        finally:
            conexion.close()

    def obtener_antiguos(self, dias: int = 90) -> list[Lambrin]:
        conexion = self.database.obtener_conexion()
        try:
            cursor = conexion.execute(
                """
                SELECT *,
                    CAST(julianday('now', 'localtime') - julianday(fecha_ingreso) AS INTEGER)
                        AS dias_en_inventario
                FROM lambrines
                WHERE activo = 1
                    AND julianday('now', 'localtime') - julianday(fecha_ingreso) > ?
                ORDER BY fecha_ingreso ASC
                """,
                (dias,),
            )
            return [self._row_a_lambrin(row) for row in cursor.fetchall()]
        finally:
            conexion.close()

    def obtener_precio_promedio_por_tipo(self) -> list[dict]:
        conexion = self.database.obtener_conexion()
        try:
            cursor = conexion.execute(
                """
                SELECT
                    tipo,
                    COUNT(*) AS cantidad,
                    ROUND(AVG(CAST(precio_unitario AS REAL)), 2) AS precio_promedio
                FROM lambrines
                WHERE activo = 1
                GROUP BY tipo
                ORDER BY tipo
                """
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conexion.close()

    def obtener_inventario_agrupado(self) -> list[dict]:
        conexion = self.database.obtener_conexion()
        try:
            cursor = conexion.execute(
                """
                SELECT
                    tipo,
                    COUNT(*) AS total_productos,
                    SUM(stock) AS stock_total,
                    SUM(stock * CAST(precio_unitario AS REAL)) AS valor_total
                FROM lambrines
                WHERE activo = 1
                GROUP BY tipo
                ORDER BY tipo
                """
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conexion.close()

    def obtener_valor_total_inventario(self) -> dict:
        conexion = self.database.obtener_conexion()
        try:
            cursor = conexion.execute(
                """
                SELECT
                    COUNT(*) AS total_productos,
                    COALESCE(SUM(stock), 0) AS total_piezas,
                    COALESCE(SUM(stock * CAST(precio_unitario AS REAL)), 0) AS valor_total
                FROM lambrines
                WHERE activo = 1
                """
            )
            return dict(cursor.fetchone())
        finally:
            conexion.close()

    def codigo_existe(self, codigo: str) -> bool:
        conexion = self.database.obtener_conexion()
        try:
            cursor = conexion.execute(
                "SELECT COUNT(*) FROM lambrines WHERE codigo = ?", (codigo,)
            )
            return cursor.fetchone()[0] > 0
        finally:
            conexion.close()
