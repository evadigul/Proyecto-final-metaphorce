"""
Configuración del módulo de logging para LAMBRINSTOCK.

Registra eventos importantes del sistema en logs/lambrinstock.log.
"""

import logging
import os


def configurar_logger(
    nombre: str = "lambrinstock",
    directorio_logs: str = "",
) -> logging.Logger:
    """Configura y retorna un logger para la aplicación.

    """
    logger = logging.getLogger(nombre)

    # Evitar agregar handlers duplicados
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Determinar directorio de logs
    if not directorio_logs:
        directorio_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        directorio_logs = os.path.join(directorio_base, "logs")

    os.makedirs(directorio_logs, exist_ok=True)

    archivo_log = os.path.join(directorio_logs, "lambrinstock.log")

    # Handler para archivo
    handler_archivo = logging.FileHandler(
        archivo_log, encoding="utf-8"
    )
    handler_archivo.setLevel(logging.DEBUG)
    formato_archivo = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler_archivo.setFormatter(formato_archivo)

    # Handler para consola (solo errores)
    handler_consola = logging.StreamHandler()
    handler_consola.setLevel(logging.ERROR)
    formato_consola = logging.Formatter(
        "[%(levelname)s] %(message)s"
    )
    handler_consola.setFormatter(formato_consola)

    logger.addHandler(handler_archivo)
    logger.addHandler(handler_consola)

    return logger
