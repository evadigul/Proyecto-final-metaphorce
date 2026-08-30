"""
Excepciones de dominio para LAMBRINSTOCK.

"""


class StockInsuficienteError(Exception):
    """Se lanza cuando la cantidad solicitada supera el stock disponible.
    """

    def __init__(self, codigo: str, stock_actual: int, cantidad_solicitada: int):
        self.codigo = codigo
        self.stock_actual = stock_actual
        self.cantidad_solicitada = cantidad_solicitada
        super().__init__(
            f"Stock insuficiente para '{codigo}': "
            f"disponible={stock_actual}, solicitado={cantidad_solicitada}"
        )


class LambrinNoDisponibleError(Exception):
    """Se lanza cuando el lambrín solicitado no existe o está desactivado.
    """

    def __init__(self, mensaje: str):
        super().__init__(mensaje)


class RegistroDuplicadoError(Exception):
    """Se lanza cuando se intenta registrar un lambrín con un código
    que ya existe en el sistema.
    """

    def __init__(self, codigo: str):
        self.codigo = codigo
        super().__init__(
            f"Ya existe un lambrín registrado con el código '{codigo}'"
        )


class MedidasNoCompatiblesError(Exception):
    """Se lanza cuando las medidas solicitadas por el cliente no
    coinciden con las medidas disponibles del lambrín.
    """

    def __init__(self, mensaje: str):
        super().__init__(mensaje)


class CotizacionInvalidaError(Exception):
    """Se lanza cuando una cotización no cumple con los requisitos
    mínimos para ser procesada.

    Por ejemplo: datos incompletos, estado inválido, o intento
    de confirmar una cotización ya cancelada.
    """

    def __init__(self, mensaje: str):
        super().__init__(mensaje)


class ClienteNoEncontradoError(Exception):
    """Se lanza cuando se intenta operar con un cliente que no existe
    en el sistema.
    """

    def __init__(self, cliente_id: int):
        self.cliente_id = cliente_id
        super().__init__(
            f"No se encontró el cliente con ID {cliente_id}"
        )
