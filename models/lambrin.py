"""
Modelo de datos para Lambrín.

"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional


@dataclass
class Lambrin:
    """Entidad que representa un tipo de lambrín en el inventario"""

    codigo: str
    nombre: str
    tipo: str
    material: str
    acabado: str
    largo: float
    ancho: float
    espesor: float
    precio_unitario: Decimal
    stock: int
    unidad_medida: str = "pieza"
    id: Optional[int] = None
    fecha_ingreso: Optional[str] = None
    fecha_actualizacion: Optional[str] = None
    activo: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.precio_unitario, Decimal):
            self.precio_unitario = Decimal(str(self.precio_unitario))

    @property
    def area_unitaria(self) -> float:
        return self.largo * self.ancho

    def __str__(self) -> str:
        estado = "Activo" if self.activo else "Inactivo"
        return (
            f"[{self.codigo}] {self.nombre} - {self.material} {self.acabado} | "
            f"{self.largo}x{self.ancho}x{self.espesor}m | "
            f"${self.precio_unitario} | Stock: {self.stock} | {estado}"
        )
