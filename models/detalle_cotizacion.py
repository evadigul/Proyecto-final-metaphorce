"""
Modelo de datos para Detalle de Cotización.

"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class DetalleCotizacion:
    """Entidad que representa una línea de detalle de cotización"""

    cotizacion_id: int
    lambrin_id: int
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal
    ancho_superficie: float = 0.0
    alto_superficie: float = 0.0
    area_superficie: float = 0.0
    area_por_pieza: float = 0.0
    porcentaje_desperdicio: float = 0.0
    orientacion: str = "Vertical"
    id: Optional[int] = None

    def __post_init__(self) -> None:
        if not isinstance(self.precio_unitario, Decimal):
            self.precio_unitario = Decimal(str(self.precio_unitario))
        if not isinstance(self.subtotal, Decimal):
            self.subtotal = Decimal(str(self.subtotal))
