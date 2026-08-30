"""
Repositorio para operaciones de Cotización y Detalle de Cotización.

"""

import sqlite3
from decimal import Decimal
from typing import Optional

from models.cotizacion import Cotizacion
from models.detalle_cotizacion import DetalleCotizacion
from repositories.database import Database
from utils.logger import configurar_logger

logger = configurar_logger(__name__)


class CotizacionRepository:

    def __init__(self, database: Database) -> None:
        self.database = database

    def _row_a_cotizacion(self, row: sqlite3.Row) -> Cotizacion:
        return Cotizacion(
            id=row["id"],
            cliente_id=row["cliente_id"],  # Puede ser None (ON DELETE SET NULL)
            fecha_creacion=row["fecha_creacion"],
            subtotal_material=Decimal(row["subtotal_material"]),
            costo_mano_obra=Decimal(row["costo_mano_obra"]),
            total=Decimal(row["total"]),
            incluye_mano_obra=bool(row["incluye_mano_obra"]),
            estado=row["estado"],
        )

    def _row_a_detalle(self, row: sqlite3.Row) -> DetalleCotizacion:
        return DetalleCotizacion(
            id=row["id"],
            cotizacion_id=row["cotizacion_id"],
            lambrin_id=row["lambrin_id"],
            cantidad=row["cantidad"],
            precio_unitario=Decimal(row["precio_unitario"]),
            subtotal=Decimal(row["subtotal"]),
            ancho_superficie=row["ancho_superficie"],
            alto_superficie=row["alto_superficie"],
            area_superficie=row["area_superficie"],
            area_por_pieza=row["area_por_pieza"],
            porcentaje_desperdicio=row["porcentaje_desperdicio"],
            orientacion=row["orientacion"],
        )

    def crear_cotizacion(self, cotizacion: Cotizacion) -> int:
        conexion = self.database.obtener_conexion()
        try:
            cursor = conexion.execute(
                """
                INSERT INTO cotizaciones (
                    cliente_id, subtotal_material, costo_mano_obra,
                    total, incluye_mano_obra, estado
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    cotizacion.cliente_id,
                    str(cotizacion.subtotal_material),
                    str(cotizacion.costo_mano_obra),
                    str(cotizacion.total),
                    1 if cotizacion.incluye_mano_obra else 0,
                    cotizacion.estado,
                ),
            )
            conexion.commit()
            cotizacion_id = cursor.lastrowid
            logger.info("Cotización creada: ID=%d", cotizacion_id)
            return cotizacion_id
        finally:
            conexion.close()

    def crear_detalle(self, detalle: DetalleCotizacion) -> int:
        conexion = self.database.obtener_conexion()
        try:
            cursor = conexion.execute(
                """
                INSERT INTO detalle_cotizacion (
                    cotizacion_id, lambrin_id, cantidad,
                    precio_unitario, subtotal,
                    ancho_superficie, alto_superficie,
                    area_superficie, area_por_pieza,
                    porcentaje_desperdicio, orientacion
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    detalle.cotizacion_id,
                    detalle.lambrin_id,
                    detalle.cantidad,
                    str(detalle.precio_unitario),
                    str(detalle.subtotal),
                    detalle.ancho_superficie,
                    detalle.alto_superficie,
                    detalle.area_superficie,
                    detalle.area_por_pieza,
                    detalle.porcentaje_desperdicio,
                    detalle.orientacion,
                ),
            )
            conexion.commit()
            return cursor.lastrowid
        finally:
            conexion.close()

    def obtener_por_id(self, cotizacion_id: int) -> Optional[Cotizacion]:
        conexion = self.database.obtener_conexion()
        try:
            cursor = conexion.execute(
                "SELECT * FROM cotizaciones WHERE id = ?", (cotizacion_id,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_a_cotizacion(row)
            return None
        finally:
            conexion.close()

    def obtener_detalles(self, cotizacion_id: int) -> list[DetalleCotizacion]:
        conexion = self.database.obtener_conexion()
        try:
            cursor = conexion.execute(
                """
                SELECT * FROM detalle_cotizacion
                WHERE cotizacion_id = ?
                ORDER BY id
                """,
                (cotizacion_id,),
            )
            return [self._row_a_detalle(row) for row in cursor.fetchall()]
        finally:
            conexion.close()

    def actualizar_estado(self, cotizacion_id: int, estado: str) -> bool:
        conexion = self.database.obtener_conexion()
        try:
            cursor = conexion.execute(
                "UPDATE cotizaciones SET estado = ? WHERE id = ?",
                (estado, cotizacion_id),
            )
            conexion.commit()
            return cursor.rowcount > 0
        finally:
            conexion.close()

    def obtener_todas(self) -> list[Cotizacion]:
        conexion = self.database.obtener_conexion()
        try:
            cursor = conexion.execute(
                "SELECT * FROM cotizaciones ORDER BY fecha_creacion DESC"
            )
            return [self._row_a_cotizacion(row) for row in cursor.fetchall()]
        finally:
            conexion.close()

    # ===== CONSULTAS AVANZADAS CON JOIN, SUM, GROUP BY =====

    def obtener_historial_completo(self) -> list[dict]:
        conexion = self.database.obtener_conexion()
        try:
            cursor = conexion.execute(
                """
                SELECT
                    co.id AS cotizacion_id,
                    COALESCE(c.nombre, 'Cliente eliminado') AS cliente,
                    co.fecha_creacion,
                    l.codigo AS codigo_lambrin,
                    l.nombre AS nombre_lambrin,
                    l.tipo AS tipo_lambrin,
                    dc.cantidad,
                    dc.precio_unitario AS precio_unit,
                    dc.subtotal AS subtotal_linea,
                    co.subtotal_material,
                    co.costo_mano_obra,
                    co.total,
                    co.estado
                FROM cotizaciones co
                LEFT JOIN clientes c ON co.cliente_id = c.id
                INNER JOIN detalle_cotizacion dc ON co.id = dc.cotizacion_id
                INNER JOIN lambrines l ON dc.lambrin_id = l.id
                ORDER BY co.fecha_creacion DESC
                """
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conexion.close()

    def obtener_total_por_tipo_lambrin(self) -> list[dict]:
        conexion = self.database.obtener_conexion()
        try:
            cursor = conexion.execute(
                """
                SELECT
                    l.tipo,
                    COUNT(DISTINCT co.id) AS total_cotizaciones,
                    SUM(dc.cantidad) AS total_piezas,
                    ROUND(SUM(CAST(dc.subtotal AS REAL)), 2) AS total_cotizado
                FROM detalle_cotizacion dc
                INNER JOIN lambrines l ON dc.lambrin_id = l.id
                INNER JOIN cotizaciones co ON dc.cotizacion_id = co.id
                GROUP BY l.tipo
                ORDER BY total_cotizado DESC
                """
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conexion.close()

    def obtener_cotizaciones_por_cliente(self, cliente_id: int) -> list[dict]:
        conexion = self.database.obtener_conexion()
        try:
            cursor = conexion.execute(
                """
                SELECT
                    co.id AS cotizacion_id,
                    co.fecha_creacion,
                    co.subtotal_material,
                    co.costo_mano_obra,
                    co.total,
                    co.estado,
                    COUNT(dc.id) AS total_items
                FROM cotizaciones co
                LEFT JOIN detalle_cotizacion dc ON co.id = dc.cotizacion_id
                WHERE co.cliente_id = ?
                GROUP BY co.id
                ORDER BY co.fecha_creacion DESC
                """,
                (cliente_id,),
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conexion.close()

    def obtener_cotizaciones_recientes(self, dias: int = 30) -> list[dict]:
        conexion = self.database.obtener_conexion()
        try:
            cursor = conexion.execute(
                """
                SELECT
                    co.id AS cotizacion_id,
                    COALESCE(c.nombre, 'Cliente eliminado') AS cliente,
                    co.fecha_creacion,
                    co.total,
                    co.estado
                FROM cotizaciones co
                LEFT JOIN clientes c ON co.cliente_id = c.id
                WHERE julianday('now', 'localtime') - julianday(co.fecha_creacion) <= ?
                ORDER BY co.fecha_creacion DESC
                """,
                (dias,),
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conexion.close()
