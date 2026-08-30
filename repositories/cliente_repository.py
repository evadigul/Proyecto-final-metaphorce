"""
Repositorio para operaciones CRUD de Cliente.

Incluye consultas con JOIN y GROUP BY para reportes.
"""

import sqlite3
from typing import Optional

from models.cliente import Cliente
from repositories.database import Database
from utils.logger import configurar_logger

logger = configurar_logger(__name__)


class ClienteRepository:
    """Repositorio de acceso a datos para la entidad Cliente."""



    def __init__(self, database: Database) -> None:
        self.database = database

    def _row_a_cliente(self, row: sqlite3.Row) -> Cliente:
        return Cliente(
            id=row["id"],
            nombre=row["nombre"],
            telefono=row["telefono"],
            email=row["email"],
            direccion=row["direccion"],
            fecha_registro=row["fecha_registro"],
            activo=bool(row["activo"]),
        )

    def crear(self, cliente: Cliente) -> int:
        conexion = self.database.obtener_conexion()
        try:
            cursor = conexion.execute(
                """
                INSERT INTO clientes (nombre, telefono, email, direccion)
                VALUES (?, ?, ?, ?)
                """,
                (
                    cliente.nombre,
                    cliente.telefono,
                    cliente.email,
                    cliente.direccion,
                ),
            )
            conexion.commit()
            cliente_id = cursor.lastrowid
            logger.info("Cliente creado: ID=%d, nombre=%s", cliente_id, cliente.nombre)
            return cliente_id
        finally:
            conexion.close()

    def obtener_por_id(self, cliente_id: int) -> Optional[Cliente]:
        conexion = self.database.obtener_conexion()
        try:
            cursor = conexion.execute(
                "SELECT * FROM clientes WHERE id = ?", (cliente_id,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_a_cliente(row)
            return None
        finally:
            conexion.close()

    def obtener_todos(self, solo_activos: bool = True) -> list[Cliente]:
        conexion = self.database.obtener_conexion()
        try:
            if solo_activos:
                cursor = conexion.execute(
                    "SELECT * FROM clientes WHERE activo = 1 ORDER BY nombre"
                )
            else:
                cursor = conexion.execute(
                    "SELECT * FROM clientes ORDER BY nombre"
                )
            return [self._row_a_cliente(row) for row in cursor.fetchall()]
        finally:
            conexion.close()

    def actualizar(self, cliente: Cliente) -> bool:
        conexion = self.database.obtener_conexion()
        try:
            cursor = conexion.execute(
                """
                UPDATE clientes SET
                    nombre = ?,
                    telefono = ?,
                    email = ?,
                    direccion = ?,
                    activo = ?
                WHERE id = ?
                """,
                (
                    cliente.nombre,
                    cliente.telefono,
                    cliente.email,
                    cliente.direccion,
                    1 if cliente.activo else 0,
                    cliente.id,
                ),
            )
            conexion.commit()
            return cursor.rowcount > 0
        finally:
            conexion.close()

    def buscar_por_nombre(self, nombre: str) -> list[Cliente]:
        conexion = self.database.obtener_conexion()
        try:
            cursor = conexion.execute(
                """
                SELECT * FROM clientes
                WHERE nombre LIKE ? AND activo = 1
                ORDER BY nombre
                """,
                (f"%{nombre}%",),
            )
            return [self._row_a_cliente(row) for row in cursor.fetchall()]
        finally:
            conexion.close()

    def eliminar(self, cliente_id: int) -> bool:
        conexion = self.database.obtener_conexion()
        try:
            cursor = conexion.execute(
                "DELETE FROM clientes WHERE id = ?", (cliente_id,)
            )
            conexion.commit()
            eliminado = cursor.rowcount > 0
            if eliminado:
                logger.info("Cliente eliminado: ID=%d", cliente_id)
            return eliminado
        finally:
            conexion.close()

    def obtener_clientes_con_cotizaciones(self) -> list[dict]:
        conexion = self.database.obtener_conexion()
        try:
            cursor = conexion.execute(
                """
                SELECT
                    c.id,
                    c.nombre,
                    c.telefono,
                    c.email,
                    COUNT(co.id) AS total_cotizaciones
                FROM clientes c
                LEFT JOIN cotizaciones co
                    ON c.id = co.cliente_id
                WHERE c.activo = 1
                GROUP BY c.id, c.nombre, c.telefono, c.email
                ORDER BY total_cotizaciones DESC
                """
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conexion.close()
