"""Paquete de excepciones de dominio para LAMBRINSTOCK."""

from .domain_exceptions import (
    StockInsuficienteError,
    LambrinNoDisponibleError,
    RegistroDuplicadoError,
    MedidasNoCompatiblesError,
    CotizacionInvalidaError,
    ClienteNoEncontradoError,
)

__all__ = [
    "StockInsuficienteError",
    "LambrinNoDisponibleError",
    "RegistroDuplicadoError",
    "MedidasNoCompatiblesError",
    "CotizacionInvalidaError",
    "ClienteNoEncontradoError",
]
