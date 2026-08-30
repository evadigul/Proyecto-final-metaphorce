"""
Modelo de datos para Cotización.

"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional, List


@dataclass
class Cotizacion:
    """Entidad que representa una cotización."""

    cliente_id: Optional[int] = None
    subtotal_material: Decimal = Decimal("0")
    costo_mano_obra: Decimal = Decimal("0")
    total: Decimal = Decimal("0")
    incluye_mano_obra: bool = False
    estado: str = "pendiente"
    id: Optional[int] = None
    fecha_creacion: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.subtotal_material, Decimal):
            self.subtotal_material = Decimal(str(self.subtotal_material))
        if not isinstance(self.costo_mano_obra, Decimal):
            self.costo_mano_obra = Decimal(str(self.costo_mano_obra))
        if not isinstance(self.total, Decimal):
            self.total = Decimal(str(self.total))
