"""Paquete de modelos de LAMBRINSTOCK:)."""

from .lambrin import Lambrin
from .cliente import Cliente
from .cotizacion import Cotizacion
from .detalle_cotizacion import DetalleCotizacion

__all__ = ["Lambrin", "Cliente", "Cotizacion", "DetalleCotizacion"]
