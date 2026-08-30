"""
Modelo de datos para Cliente.

"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Cliente:
    """Entidad que representa un cliente del sistema."""

    nombre: str
    telefono: str = ""
    email: str = ""
    direccion: str = ""
    id: Optional[int] = None
    fecha_registro: Optional[str] = None
    activo: bool = True

    def __str__(self) -> str:
        return f"[{self.id}] {self.nombre} - Tel: {self.telefono}"
