"""
Servicio de cotización para LAMBRINSTOCK.

Contiene las reglas de negocio principales del sistema de cotización:
- Selección de lambrín por el cliente.
- Cálculo de piezas necesarias para cubrir una superficie.
- Aplicación de porcentaje de desperdicio configurable.
- Verificación de stock suficiente.
- Cálculo de mano de obra por m².
- Descuento de stock al confirmar.
- Protección contra stock negativo.
- Eliminación de clientes con preservación de historial.
"""

import json
import math
import os
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from typing import Optional

from models.lambrin import Lambrin
from models.cliente import Cliente
from models.cotizacion import Cotizacion
from models.detalle_cotizacion import DetalleCotizacion
from repositories.lambrin_repository import LambrinRepository
from repositories.cliente_repository import ClienteRepository
from repositories.cotizacion_repository import CotizacionRepository
from exceptions.domain_exceptions import (
    StockInsuficienteError,
    LambrinNoDisponibleError,
    MedidasNoCompatiblesError,
    CotizacionInvalidaError,
    ClienteNoEncontradoError,
)
from utils.logger import configurar_logger

logger = configurar_logger(__name__)


class CotizacionService:
    """Servicio con reglas de negocio para cotizaciones.

    Implementa el flujo completo de cotización incluyendo:
    - Listado de productos disponibles.
    - Cálculo de piezas por superficie.
    - Aplicación de desperdicio.
    - Verificación de stock.
    - Cálculo de costos (material + mano de obra).
    - Confirmación con descuento de inventario.
    - Registro de auditoría.
    - Eliminación de clientes.

    """

    def __init__(
        self,
        lambrin_repo: LambrinRepository,
        cliente_repo: ClienteRepository,
        cotizacion_repo: CotizacionRepository,
    ) -> None:
        self.lambrin_repo = lambrin_repo
        self.cliente_repo = cliente_repo
        self.cotizacion_repo = cotizacion_repo
        self.config = self._cargar_config()

    def _cargar_config(self) -> dict:
        """Carga la configuración desde config.json."""
        directorio_base = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
        config_path = os.path.join(directorio_base, "config.json")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logger.warning("No se pudo cargar config.json, usando valores por defecto")
            return {
                "costo_mano_obra_m2": 180.00,
                "porcentaje_desperdicio": 10,
                "moneda": "MXN",
                "simbolo_moneda": "$",
            }

    def verificar_cliente(self, cliente_id: int) -> Cliente:
        """Verifica que el cliente existe en el sistema.

        """
        cliente = self.cliente_repo.obtener_por_id(cliente_id)
        if cliente is None:
            raise ClienteNoEncontradoError(cliente_id)
        return cliente

    def obtener_lambrines_disponibles(self) -> list[Lambrin]:
        """Obtiene todos los lambrines activos con stock disponible.

        """
        lambrines = self.lambrin_repo.obtener_todos(solo_activos=True)
        return [l for l in lambrines if l.stock > 0]

    def calcular_piezas_necesarias(
        self,
        lambrin: Lambrin,
        ancho_superficie: float,
        alto_superficie: float,
        porcentaje_desperdicio: float,
    ) -> dict:
        """Calcula la cantidad de piezas necesarias para cubrir una superficie.

        Fórmulas:
            area_superficie = ancho_superficie × alto_superficie
            area_por_pieza = lambrin.largo × lambrin.ancho
            cantidad_teorica = area_superficie / area_por_pieza
            cantidad_con_desperdicio = cantidad_teorica × (1 + porcentaje/100)
            cantidad_final = math.ceil(cantidad_con_desperdicio)

        """
        area_superficie = ancho_superficie * alto_superficie
        area_por_pieza = lambrin.largo * lambrin.ancho

        cantidad_teorica = area_superficie / area_por_pieza
        cantidad_con_desperdicio = cantidad_teorica * (1 + porcentaje_desperdicio / 100)
        cantidad_final = math.ceil(cantidad_con_desperdicio)

        return {
            "area_superficie": round(area_superficie, 4),
            "area_por_pieza": round(area_por_pieza, 4),
            "cantidad_teorica": round(cantidad_teorica, 4),
            "cantidad_con_desperdicio": round(cantidad_con_desperdicio, 4),
            "cantidad_final": cantidad_final,
        }

    def verificar_stock(self, lambrin: Lambrin, cantidad: int) -> None:
        """Verifica que haya suficiente stock para la cantidad solicitada.

        REGLA 1: No se puede realizar una cotización si el stock
        disponible es menor que la cantidad solicitada.

        REGLA 8: No debe permitirse que el stock termine en valores negativos.

        """
        if not lambrin.activo:
            raise LambrinNoDisponibleError(
                f"El lambrín '{lambrin.codigo}' no está disponible "
                f"(desactivado del inventario)"
            )

        if lambrin.stock < cantidad:
            raise StockInsuficienteError(
                lambrin.codigo, lambrin.stock, cantidad
            )

    def calcular_subtotal_material(
        self,
        precio_unitario: Decimal,
        cantidad: int,
    ) -> Decimal:
        """Calcula el subtotal del material.

        """
        subtotal = precio_unitario * cantidad
        return subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def calcular_mano_de_obra(
        self,
        area_superficie: float,
        incluir: bool,
    ) -> Decimal:
        """Calcula el costo de mano de obra basado en la superficie.

        REGLA 4: El precio de mano de obra debe calcularse de manera
        independiente al material.

        REGLA 5: Si el cliente solicita mano de obra, se debe
        agregarla al costo final.

        REGLA 6: Si el cliente selecciona sin mano de obra, el costo
        de mano de obra no se cobra.

        Fórmula:
            mano_de_obra = area_superficie × costo_por_m²

        El costo_por_m² se obtiene de config.json.

        """

        if not incluir:
            return Decimal("0.00")

        # Regla 4: Cálculo independiente al material
        costo_por_m2 = Decimal(str(self.config.get("costo_mano_obra_m2", 180.00)))
        area_decimal = Decimal(str(area_superficie))
        mano_de_obra = area_decimal * costo_por_m2

        return mano_de_obra.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def calcular_total(
        self,
        subtotal_material: Decimal,
        costo_mano_obra: Decimal,
    ) -> Decimal:
        """Calcula el total de la cotización.

        REGLA 5: Si incluye mano de obra, se suma al total.

        Args:
            subtotal_material: Subtotal del material.
            costo_mano_obra: Costo de mano de obra.

        Returns:
            Total de la cotización.
        """
        total = subtotal_material + costo_mano_obra
        return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def crear_cotizacion(
        self,
        cliente_id: int,
        lambrin_id: int,
        ancho_superficie: float,
        alto_superficie: float,
        orientacion: str,
        incluir_mano_obra: bool,
        porcentaje_desperdicio: float = None,
    ) -> dict:
        """Crea una cotización completa (sin confirmar).

        Flujo:
        1. Verificar cliente.
        2. Obtener lambrín.
        3. Calcular piezas necesarias (con desperdicio).
        4. Verificar stock.
        5. Calcular costos (material + mano de obra).

        Args:
            cliente_id: ID del cliente.
            lambrin_id: ID del lambrín seleccionado.
            ancho_superficie: Ancho de la superficie a cubrir (m).
            alto_superficie: Alto de la superficie a cubrir (m).
            orientacion: 'Vertical' u 'Horizontal'.
            incluir_mano_obra: Si incluir mano de obra.
            porcentaje_desperdicio: Porcentaje de desperdicio (si None, usa config).

        Returns:
            Diccionario con toda la información de la cotización.

        Raises:
            ClienteNoEncontradoError: Si el cliente no existe.
            LambrinNoDisponibleError: Si el lambrín no existe o está inactivo.
            StockInsuficienteError: Si no hay stock suficiente.
        """
        # Verificar cliente
        cliente = self.verificar_cliente(cliente_id)

        # Obtener lambrín
        lambrin = self.lambrin_repo.obtener_por_id(lambrin_id)
        if lambrin is None:
            raise LambrinNoDisponibleError(
                f"No se encontró el lambrín con ID {lambrin_id}"
            )

        # Obtener porcentaje de desperdicio
        if porcentaje_desperdicio is None:
            porcentaje_desperdicio = self.config.get("porcentaje_desperdicio", 10)

        # Calcular piezas necesarias
        calculo = self.calcular_piezas_necesarias(
            lambrin, ancho_superficie, alto_superficie, porcentaje_desperdicio
        )
        cantidad = calculo["cantidad_final"]

        # Regla 1: Verificar stock
        self.verificar_stock(lambrin, cantidad)

        # Calcular costos
        subtotal_material = self.calcular_subtotal_material(
            lambrin.precio_unitario, cantidad
        )
        costo_mano_obra = self.calcular_mano_de_obra(
            calculo["area_superficie"], incluir_mano_obra
        )
        total = self.calcular_total(subtotal_material, costo_mano_obra)

        return {
            "cliente": cliente,
            "lambrin": lambrin,
            "cantidad": cantidad,
            "ancho_superficie": ancho_superficie,
            "alto_superficie": alto_superficie,
            "area_superficie": calculo["area_superficie"],
            "area_por_pieza": calculo["area_por_pieza"],
            "cantidad_teorica": calculo["cantidad_teorica"],
            "cantidad_con_desperdicio": calculo["cantidad_con_desperdicio"],
            "porcentaje_desperdicio": porcentaje_desperdicio,
            "orientacion": orientacion,
            "precio_unitario": lambrin.precio_unitario,
            "subtotal_material": subtotal_material,
            "costo_mano_obra": costo_mano_obra,
            "total": total,
            "incluye_mano_obra": incluir_mano_obra,
        }

    def confirmar_cotizacion(self, datos_cotizacion: dict) -> int:
        """Confirma una cotización: la guarda en BD y descuenta stock.

        REGLA 7: Cuando una cotización se confirma, el stock del lambrín
        debe disminuir según la cantidad utilizada.

        REGLA 8: No debe permitirse que el stock termine en valores negativos.

        Args:
            datos_cotizacion: Diccionario con datos de la cotización
                (generado por crear_cotizacion).

        Returns:
            ID de la cotización confirmada.

        Raises:
            StockInsuficienteError: Si el stock ya no es suficiente
                (pudo cambiar entre la creación y la confirmación).
            CotizacionInvalidaError: Si los datos son inválidos.
        """
        cliente = datos_cotizacion.get("cliente")
        lambrin = datos_cotizacion.get("lambrin")
        cantidad = datos_cotizacion.get("cantidad")

        if not cliente or not lambrin or not cantidad:
            raise CotizacionInvalidaError(
                "Datos de cotización incompletos. No se puede confirmar."
            )

        # Regla 1 y 8: Re-verificar stock antes de confirmar
        lambrin_actual = self.lambrin_repo.obtener_por_id(lambrin.id)
        if lambrin_actual is None:
            raise LambrinNoDisponibleError(
                f"El lambrín '{lambrin.codigo}' ya no existe en el sistema"
            )

        self.verificar_stock(lambrin_actual, cantidad)

        # Guardar cotización
        cotizacion = Cotizacion(
            cliente_id=cliente.id,
            subtotal_material=datos_cotizacion["subtotal_material"],
            costo_mano_obra=datos_cotizacion["costo_mano_obra"],
            total=datos_cotizacion["total"],
            incluye_mano_obra=datos_cotizacion["incluye_mano_obra"],
            estado="confirmada",
        )
        cotizacion_id = self.cotizacion_repo.crear_cotizacion(cotizacion)

        # Guardar detalle
        detalle = DetalleCotizacion(
            cotizacion_id=cotizacion_id,
            lambrin_id=lambrin.id,
            cantidad=cantidad,
            precio_unitario=datos_cotizacion["precio_unitario"],
            subtotal=datos_cotizacion["subtotal_material"],
            ancho_superficie=datos_cotizacion["ancho_superficie"],
            alto_superficie=datos_cotizacion["alto_superficie"],
            area_superficie=datos_cotizacion["area_superficie"],
            area_por_pieza=datos_cotizacion["area_por_pieza"],
            porcentaje_desperdicio=datos_cotizacion["porcentaje_desperdicio"],
            orientacion=datos_cotizacion["orientacion"],
        )
        self.cotizacion_repo.crear_detalle(detalle)

        # Regla 7: Descontar stock
        nuevo_stock = lambrin_actual.stock - cantidad

        # Regla 8: Protección final contra stock negativo
        if nuevo_stock < 0:
            raise StockInsuficienteError(
                lambrin.codigo, lambrin_actual.stock, cantidad
            )

        self.lambrin_repo.actualizar_stock(lambrin.id, nuevo_stock)

        logger.info(
            "Cotización #%05d confirmada. Lambrín %s: stock %d → %d",
            cotizacion_id, lambrin.codigo, lambrin_actual.stock, nuevo_stock,
        )

        # Registrar auditoría
        self._registrar_auditoria(
            operacion="CONFIRMAR_COTIZACION",
            entidad="cotizacion",
            entidad_id=cotizacion_id,
            descripcion=(
                f"Cotización confirmada para {cliente.nombre}. "
                f"Lambrín: {lambrin.codigo}, Cantidad: {cantidad}, "
                f"Superficie: {datos_cotizacion['ancho_superficie']}x"
                f"{datos_cotizacion['alto_superficie']}m, "
                f"Total: ${datos_cotizacion['total']}"
            ),
        )

        return cotizacion_id

    # ===== GESTIÓN DE CLIENTES =====

    def eliminar_cliente(self, cliente_id: int) -> None:
        """Elimina un cliente del sistema.

        Verifica que el cliente exista antes de eliminarlo.
        Las cotizaciones históricas se conservan gracias a ON DELETE SET NULL.

        Args:
            cliente_id: ID del cliente a eliminar.

        Raises:
            ClienteNoEncontradoError: Si el cliente no existe.
        """
        cliente = self.cliente_repo.obtener_por_id(cliente_id)
        if cliente is None:
            raise ClienteNoEncontradoError(cliente_id)

        self.cliente_repo.eliminar(cliente_id)

        logger.info(
            "Cliente eliminado: ID=%d, nombre=%s", cliente_id, cliente.nombre
        )

        self._registrar_auditoria(
            operacion="ELIMINAR_CLIENTE",
            entidad="cliente",
            entidad_id=cliente_id,
            descripcion=f"Cliente eliminado: {cliente.nombre}",
        )

    def _registrar_auditoria(
        self,
        operacion: str,
        entidad: str,
        entidad_id: int,
        descripcion: str,
    ) -> None:
        """Registra una operación en el archivo de auditoría JSON.

        Args:
            operacion: Tipo de operación (e.g., 'CONFIRMAR_COTIZACION').
            entidad: Entidad afectada (e.g., 'cotizacion').
            entidad_id: ID de la entidad.
            descripcion: Descripción de la operación.
        """
        directorio_base = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
        directorio_backups = os.path.join(directorio_base, "backups")
        os.makedirs(directorio_backups, exist_ok=True)

        archivo_auditoria = os.path.join(directorio_backups, "auditoria.json")

        registro = {
            "fecha": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "operacion": operacion,
            "entidad": entidad,
            "id": entidad_id,
            "descripcion": descripcion,
        }

        # Cargar registros existentes
        registros = []
        if os.path.exists(archivo_auditoria):
            try:
                with open(archivo_auditoria, "r", encoding="utf-8") as f:
                    registros = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                registros = []

        registros.append(registro)

        with open(archivo_auditoria, "w", encoding="utf-8") as f:
            json.dump(registros, f, ensure_ascii=False, indent=4)

        logger.info("Auditoría registrada: %s - %s", operacion, descripcion)
