"""
Validadores de entrada para LAMBRINSTOCK.

Funciones de validación para datos ingresados por el usuario.
Estas son validaciones de formato/tipo, NO reglas de negocio.
Las reglas de negocio se implementan en la capa de servicios.
"""

from decimal import Decimal, InvalidOperation


def validar_numero_positivo(valor: str, nombre_campo: str = "valor") -> float:
    """Valida que el valor sea un número positivo.

    """
    try:
        numero = float(valor)
    except ValueError:
        raise ValueError(f"'{nombre_campo}' debe ser un número válido.")

    if numero <= 0:
        raise ValueError(f"'{nombre_campo}' debe ser mayor que cero.")

    return numero


def validar_precio(valor: str, nombre_campo: str = "precio") -> Decimal:
    """Valida que el valor sea un precio válido (positivo, con precisión decimal).

    """
    try:
        precio = Decimal(valor)
    except InvalidOperation:
        raise ValueError(f"'{nombre_campo}' debe ser un valor monetario válido.")

    if precio <= 0:
        raise ValueError(f"'{nombre_campo}' debe ser mayor que cero.")

    return precio


def validar_stock(valor: str) -> int:
    """Valida que el valor sea un stock válido (entero no negativo).

    """
    try:
        stock = int(valor)
    except ValueError:
        raise ValueError("El stock debe ser un número entero.")

    if stock < 0:
        raise ValueError("El stock no puede ser negativo.")

    return stock


def validar_medida(valor: str, nombre_campo: str = "medida") -> float:
    """Valida que el valor sea una medida válida (número positivo).

    """
    return validar_numero_positivo(valor, nombre_campo)


def validar_cantidad(valor: str) -> int:
    """Valida que el valor sea una cantidad válida (entero mayor a cero).

    """
    try:
        cantidad = int(valor)
    except ValueError:
        raise ValueError("La cantidad debe ser un número entero.")

    if cantidad <= 0:
        raise ValueError("La cantidad debe ser mayor que cero.")

    return cantidad


def validar_codigo(valor: str) -> str:
    """Valida que el código del producto sea válido.

    """
    codigo = valor.strip().upper()
    if not codigo:
        raise ValueError("El código del producto no puede estar vacío.")
    return codigo


def validar_texto_no_vacio(valor: str, nombre_campo: str = "campo") -> str:
    """Valida que el texto no esté vacío.

    """
    texto = valor.strip()
    if not texto:
        raise ValueError(f"'{nombre_campo}' no puede estar vacío.")
    return texto


def validar_opcion_menu(valor: str, opciones_validas: list[int]) -> int:
    """Valida que la opción seleccionada sea válida.

    """
    try:
        opcion = int(valor)
    except ValueError:
        raise ValueError("Debe ingresar un número válido.")

    if opcion not in opciones_validas:
        raise ValueError(
            f"Opción inválida. Opciones disponibles: "
            f"{', '.join(str(o) for o in opciones_validas)}"
        )

    return opcion
