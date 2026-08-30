"""
Servicio de inventario para LAMBRINSTOCK.

Contiene las reglas de negocio relacionadas con la gestión del
inventario de lambrines. No se realizan operaciones directas de BD;
delega al repositorio correspondiente.
"""

import sqlite3
from datetime import datetime
from typing import Optional

from models.lambrin import Lambrin
from repositories.lambrin_repository import LambrinRepository
from exceptions.domain_exceptions import (
    RegistroDuplicadoError,
    LambrinNoDisponibleError,
)
from utils.logger import configurar_logger

logger = configurar_logger(__name__)


class InventarioService:
    """Servicio con reglas de negocio para gestión de inventario.

    """

    def __init__(self, lambrin_repo: LambrinRepository) -> None:
        self.lambrin_repo = lambrin_repo

    def registrar_lambrin(self, lambrin: Lambrin) -> int:
        """Registra un nuevo lambrín en el inventario.

        REGLA 3: No se debe permitir registrar dos lambrines con
        el mismo código.

        REGLA 8: No se permite stock negativo.

        """
        # Regla 3: Verificar código duplicado
        if self.lambrin_repo.codigo_existe(lambrin.codigo):
            logger.warning(
                "Intento de registrar código duplicado: %s", lambrin.codigo
            )
            raise RegistroDuplicadoError(lambrin.codigo)

        # Regla 8: Stock no negativo
        if lambrin.stock < 0:
            lambrin.stock = 0

        lambrin_id = self.lambrin_repo.crear(lambrin)
        logger.info(
            "Lambrín registrado exitosamente: ID=%d, código=%s",
            lambrin_id, lambrin.codigo,
        )
        return lambrin_id

    def obtener_lambrin(self, lambrin_id: int) -> Lambrin:
        """Obtiene un lambrín por su ID.

        """
        lambrin = self.lambrin_repo.obtener_por_id(lambrin_id)
        if lambrin is None:
            raise LambrinNoDisponibleError(
                f"No se encontró el lambrín con ID {lambrin_id}"
            )
        return lambrin

    def obtener_lambrin_por_codigo(self, codigo: str) -> Lambrin:
        """Obtiene un lambrín por su código.

        """
        lambrin = self.lambrin_repo.obtener_por_codigo(codigo)
        if lambrin is None:
            raise LambrinNoDisponibleError(
                f"No se encontró el lambrín con código '{codigo}'"
            )
        return lambrin

    def listar_lambrines(self, solo_activos: bool = True) -> list[Lambrin]:
        """Lista todos los lambrines del inventario.

        """
        return self.lambrin_repo.obtener_todos(solo_activos)

    def actualizar_lambrin(self, lambrin: Lambrin) -> bool:
        """Actualiza la información de un lambrín.

        REGLA 8: No se permite stock negativo.
.
        """
        existente = self.lambrin_repo.obtener_por_id(lambrin.id)
        if existente is None:
            raise LambrinNoDisponibleError(
                f"No se encontró el lambrín con ID {lambrin.id}"
            )

        # Regla 8: Stock no negativo
        if lambrin.stock < 0:
            lambrin.stock = 0

        resultado = self.lambrin_repo.actualizar(lambrin)
        if resultado:
            logger.info("Lambrín actualizado: ID=%d", lambrin.id)
        return resultado

    def desactivar_lambrin(self, lambrin_id: int) -> bool:
        """Desactiva un lambrín (eliminación lógica).

        No elimina físicamente para preservar historial de cotizaciones.

        """
        existente = self.lambrin_repo.obtener_por_id(lambrin_id)
        if existente is None:
            raise LambrinNoDisponibleError(
                f"No se encontró el lambrín con ID {lambrin_id}"
            )

        resultado = self.lambrin_repo.desactivar(lambrin_id)
        if resultado:
            logger.info(
                "Lambrín desactivado: ID=%d, código=%s",
                lambrin_id, existente.codigo,
            )
        return resultado

    def buscar_por_tipo(self, tipo: str) -> list[Lambrin]:
        """Busca lambrines por tipo."""
        return self.lambrin_repo.buscar_por_tipo(tipo)

    def buscar_por_material(self, material: str) -> list[Lambrin]:
        """Busca lambrines por material."""
        return self.lambrin_repo.buscar_por_material(material)

    def obtener_stock_bajo(self, umbral: int = 10) -> list[Lambrin]:
        """Obtiene lambrines con stock menor al umbral."""
        return self.lambrin_repo.obtener_stock_bajo(umbral)

    def obtener_productos_antiguos(self, dias: int = 90) -> list[Lambrin]:
        """Obtiene productos que llevan más de X días en inventario.

        Alerta sobre productos que llevan mucho tiempo almacenados.

        """
        productos = self.lambrin_repo.obtener_antiguos(dias)
        if productos:
            logger.info(
                "Alerta: %d productos con más de %d días en inventario",
                len(productos), dias,
            )
        return productos

    def calcular_antiguedad(self, lambrin: Lambrin) -> int:
        """Calcula la antigüedad de un producto en días.

        """
        if lambrin.fecha_ingreso:
            fecha_ingreso = datetime.strptime(
                lambrin.fecha_ingreso, "%Y-%m-%d %H:%M:%S"
            )
            delta = datetime.now() - fecha_ingreso
            return delta.days
        return 0
