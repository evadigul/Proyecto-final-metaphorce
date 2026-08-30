"""
LAMBRINSTOCK - Sistema de Control de Inventario y Cotización de Lambrín.

Punto de entrada principal de la aplicación.
Maneja la interfaz de consola, menús y captura de excepciones específicas.
NO contiene reglas de negocio ni acceso directo a la base de datos.
"""

import json
import os
import sys
import sqlite3
from decimal import Decimal

# Agregar el directorio del proyecto al path
directorio_base = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, directorio_base)

from models.lambrin import Lambrin
from models.cliente import Cliente
from repositories.database import Database
from repositories.lambrin_repository import LambrinRepository
from repositories.cliente_repository import ClienteRepository
from repositories.cotizacion_repository import CotizacionRepository
from services.inventario_service import InventarioService
from services.cotizacion_service import CotizacionService
from services.reporte_service import ReporteService
from exceptions.domain_exceptions import (
    StockInsuficienteError,
    LambrinNoDisponibleError,
    RegistroDuplicadoError,
    MedidasNoCompatiblesError,
    CotizacionInvalidaError,
    ClienteNoEncontradoError,
)
from utils.logger import configurar_logger
from utils.validators import (
    validar_numero_positivo,
    validar_precio,
    validar_stock,
    validar_medida,
    validar_cantidad,
    validar_codigo,
    validar_texto_no_vacio,
    validar_opcion_menu,
)


logger = configurar_logger("lambrinstock")


# ============================================================
# FUNCIONES DE FORMATO DE CONSOLA
# ============================================================

def limpiar_pantalla() -> None:
    """Limpia la pantalla de la consola."""
    os.system("cls" if os.name == "nt" else "clear")


def imprimir_encabezado() -> None:
    """Muestra el encabezado del sistema."""
    print()
    print("=" * 58)
    print("               LAMBRINSTOCK".center(58))
    print("   SISTEMA DE INVENTARIO Y COTIZACIÓN DE LAMBRÍN".center(58))
    print("=" * 58)
    print()


def imprimir_separador() -> None:
    """Imprime un separador visual."""
    print("-" * 58)


def imprimir_tabla(
    encabezados: list[str],
    filas: list[list],
    anchos: list[int] = None,
) -> None:
    """Imprime una tabla alineada en consola.

    Args:
        encabezados: Lista de nombres de columnas.
        filas: Lista de listas con los datos.
        anchos: Anchos de columna (opcional, se calculan automáticamente).
    """
    if not anchos:
        anchos = []
        for i, enc in enumerate(encabezados):
            max_ancho = len(str(enc))
            for fila in filas:
                if i < len(fila):
                    max_ancho = max(max_ancho, len(str(fila[i])))
            anchos.append(min(max_ancho + 2, 30))

    linea = "+" + "+".join("-" * a for a in anchos) + "+"
    print(linea)

    cabecera = "|"
    for i, enc in enumerate(encabezados):
        cabecera += f" {str(enc):<{anchos[i]-1}}" if i > 0 else f" {str(enc):<{anchos[i]-1}}"
        cabecera += "|"
    print(cabecera)
    print(linea)

    for fila in filas:
        fila_str = "|"
        for i, val in enumerate(fila):
            if i < len(anchos):
                fila_str += f" {str(val):<{anchos[i]-1}}|"
        print(fila_str)

    print(linea)


def pausar() -> None:
    """Pausa hasta que el usuario presione Enter."""
    print()
    input("Presione Enter para continuar...")


def confirmar(mensaje: str = "¿Desea continuar?") -> bool:
    """Solicita confirmación al usuario.

    Args:
        mensaje: Mensaje de confirmación.

    Returns:
        True si el usuario confirma.
    """
    respuesta = input(f"\n{mensaje} [s/n]: ").strip().lower()
    return respuesta in ("s", "si", "sí", "y", "yes")


# ============================================================
# MENÚ PRINCIPAL
# ============================================================

def menu_principal(
    inventario_service: InventarioService,
    cotizacion_service: CotizacionService,
    reporte_service: ReporteService,
    cliente_repo: ClienteRepository,
) -> None:
    """Menú principal del sistema."""
    while True:
        limpiar_pantalla()
        imprimir_encabezado()
        print("  1. Gestión de inventario")
        print("  2. Nueva cotización")
        print("  3. Clientes")
        print("  4. Reportes")
        print("  5. Exportar inventario (CSV)")
        print("  6. Respaldos")
        print("  7. Configuración")
        print("  8. Salir")
        imprimir_separador()

        opcion = input("\n  Seleccione una opción: ").strip()

        try:
            opcion_num = validar_opcion_menu(opcion, [1, 2, 3, 4, 5, 6, 7, 8])
        except ValueError as e:
            print(f"\n  ⚠ {e}")
            pausar()
            continue

        if opcion_num == 1:
            menu_inventario(inventario_service)
        elif opcion_num == 2:
            menu_nueva_cotizacion(
                cotizacion_service, inventario_service, cliente_repo
            )
        elif opcion_num == 3:
            menu_clientes(cliente_repo, cotizacion_service)
        elif opcion_num == 4:
            menu_reportes(reporte_service, inventario_service)
        elif opcion_num == 5:
            accion_exportar_csv(reporte_service)
        elif opcion_num == 6:
            accion_respaldo(reporte_service)
        elif opcion_num == 7:
            menu_configuracion()
        elif opcion_num == 8:
            print("\n  ¡Hasta luego! Gracias por usar LAMBRINSTOCK.")
            logger.info("Sistema cerrado por el usuario")
            break


# ============================================================
# MENÚ DE INVENTARIO
# ============================================================

def menu_inventario(inventario_service: InventarioService) -> None:
    """Submenú de gestión de inventario."""
    while True:
        limpiar_pantalla()
        print()
        print("=" * 58)
        print("          GESTIÓN DE INVENTARIO".center(58))
        print("=" * 58)
        print()
        print("  1. Ver inventario completo")
        print("  2. Buscar lambrín por código")
        print("  3. Buscar por tipo")
        print("  4. Buscar por material")
        print("  5. Registrar nuevo lambrín")
        print("  6. Actualizar lambrín")
        print("  7. Desactivar lambrín")
        print("  8. Volver al menú principal")
        imprimir_separador()

        opcion = input("\n  Seleccione una opción: ").strip()

        try:
            opcion_num = validar_opcion_menu(opcion, [1, 2, 3, 4, 5, 6, 7, 8])
        except ValueError as e:
            print(f"\n  ⚠ {e}")
            pausar()
            continue

        if opcion_num == 1:
            ver_inventario(inventario_service)
        elif opcion_num == 2:
            buscar_por_codigo(inventario_service)
        elif opcion_num == 3:
            buscar_por_tipo(inventario_service)
        elif opcion_num == 4:
            buscar_por_material(inventario_service)
        elif opcion_num == 5:
            registrar_lambrin(inventario_service)
        elif opcion_num == 6:
            actualizar_lambrin(inventario_service)
        elif opcion_num == 7:
            desactivar_lambrin(inventario_service)
        elif opcion_num == 8:
            break


def ver_inventario(inventario_service: InventarioService) -> None:
    """Muestra el inventario completo en tabla formateada."""
    limpiar_pantalla()
    print("\n  === INVENTARIO COMPLETO ===\n")

    lambrines = inventario_service.listar_lambrines()

    if not lambrines:
        print("  No hay lambrines registrados en el inventario.")
        pausar()
        return

    encabezados = ["ID", "Código", "Nombre", "Material", "Medidas (m)", "Stock", "Precio"]
    filas = []
    for l in lambrines:
        filas.append([
            l.id,
            l.codigo,
            l.nombre[:22],
            l.material,
            f"{l.largo}x{l.ancho}x{l.espesor}",
            l.stock,
            f"${l.precio_unitario}",
        ])

    imprimir_tabla(encabezados, filas, [5, 10, 24, 10, 18, 7, 11])
    print(f"\n  Total de productos: {len(lambrines)}")
    pausar()


def buscar_por_codigo(inventario_service: InventarioService) -> None:
    """Busca un lambrín por código y muestra sus detalles."""
    print("\n  === BUSCAR POR CÓDIGO ===\n")
    try:
        codigo = validar_codigo(input("  Código del lambrín: "))
        lambrin = inventario_service.obtener_lambrin_por_codigo(codigo)
        _mostrar_detalle_lambrin(lambrin)
    except ValueError as e:
        print(f"\n  ⚠ {e}")
    except LambrinNoDisponibleError as e:
        print(f"\n  ⚠ {e}")
    pausar()


def buscar_por_tipo(inventario_service: InventarioService) -> None:
    """Busca lambrines por tipo."""
    print("\n  === BUSCAR POR TIPO ===\n")
    tipo = input("  Tipo de lambrín: ").strip()
    if not tipo:
        print("\n  ⚠ Debe ingresar un tipo.")
        pausar()
        return

    lambrines = inventario_service.buscar_por_tipo(tipo)
    if not lambrines:
        print(f"\n  No se encontraron lambrines de tipo '{tipo}'.")
    else:
        print(f"\n  Se encontraron {len(lambrines)} resultado(s):\n")
        for l in lambrines:
            print(f"  [{l.codigo}] {l.nombre} | {l.material} | Stock: {l.stock}")
    pausar()


def buscar_por_material(inventario_service: InventarioService) -> None:
    """Busca lambrines por material."""
    print("\n  === BUSCAR POR MATERIAL ===\n")
    material = input("  Material: ").strip()
    if not material:
        print("\n  ⚠ Debe ingresar un material.")
        pausar()
        return

    lambrines = inventario_service.buscar_por_material(material)
    if not lambrines:
        print(f"\n  No se encontraron lambrines de material '{material}'.")
    else:
        print(f"\n  Se encontraron {len(lambrines)} resultado(s):\n")
        for l in lambrines:
            print(f"  [{l.codigo}] {l.nombre} | {l.acabado} | Stock: {l.stock}")
    pausar()


def registrar_lambrin(inventario_service: InventarioService) -> None:
    """Registra un nuevo lambrín en el inventario."""
    limpiar_pantalla()
    print("\n  === REGISTRAR NUEVO LAMBRÍN ===\n")

    try:
        codigo = validar_codigo(input("  Código (ej: LAM-011): "))
        nombre = validar_texto_no_vacio(input("  Nombre: "), "nombre")
        tipo = validar_texto_no_vacio(input("  Tipo (ej: Decorativo): "), "tipo")
        material = validar_texto_no_vacio(input("  Material (ej: Nogal): "), "material")
        acabado = validar_texto_no_vacio(input("  Acabado (ej: Natural): "), "acabado")
        largo = validar_medida(input("  Largo en metros (ej: 2.90): "), "largo")
        ancho = validar_medida(input("  Ancho en metros (ej: 0.15): "), "ancho")
        espesor = validar_medida(input("  Espesor en metros (ej: 0.012): "), "espesor")
        precio = validar_precio(input("  Precio unitario: "))
        stock = validar_stock(input("  Stock inicial: "))
        unidad = input("  Unidad de medida (pieza): ").strip() or "pieza"

        lambrin = Lambrin(
            codigo=codigo,
            nombre=nombre,
            tipo=tipo,
            material=material,
            acabado=acabado,
            largo=largo,
            ancho=ancho,
            espesor=espesor,
            precio_unitario=precio,
            stock=stock,
            unidad_medida=unidad,
        )

        if confirmar("¿Desea registrar este lambrín?"):
            lambrin_id = inventario_service.registrar_lambrin(lambrin)
            print(f"\n  ✓ Lambrín registrado con éxito. ID: {lambrin_id}")
        else:
            print("\n  Operación cancelada.")

    except ValueError as e:
        print(f"\n  ⚠ Error de entrada: {e}")
    except RegistroDuplicadoError as e:
        print(f"\n  ⚠ Error: {e}")
    except sqlite3.IntegrityError as e:
        print(f"\n  ⚠ Error de integridad en la base de datos: {e}")

    pausar()


def actualizar_lambrin(inventario_service: InventarioService) -> None:
    """Actualiza la información de un lambrín existente."""
    limpiar_pantalla()
    print("\n  === ACTUALIZAR LAMBRÍN ===\n")

    try:
        id_str = input("  ID del lambrín a actualizar: ").strip()
        lambrin_id = int(id_str)
        lambrin = inventario_service.obtener_lambrin(lambrin_id)

        print(f"\n  Lambrín actual: [{lambrin.codigo}] {lambrin.nombre}")
        print("  (Deje vacío para mantener el valor actual)\n")

        nombre = input(f"  Nombre [{lambrin.nombre}]: ").strip() or lambrin.nombre
        tipo = input(f"  Tipo [{lambrin.tipo}]: ").strip() or lambrin.tipo
        material = input(f"  Material [{lambrin.material}]: ").strip() or lambrin.material
        acabado = input(f"  Acabado [{lambrin.acabado}]: ").strip() or lambrin.acabado

        largo_str = input(f"  Largo [{lambrin.largo}]: ").strip()
        largo = validar_medida(largo_str, "largo") if largo_str else lambrin.largo

        ancho_str = input(f"  Ancho [{lambrin.ancho}]: ").strip()
        ancho = validar_medida(ancho_str, "ancho") if ancho_str else lambrin.ancho

        espesor_str = input(f"  Espesor [{lambrin.espesor}]: ").strip()
        espesor = validar_medida(espesor_str, "espesor") if espesor_str else lambrin.espesor

        precio_str = input(f"  Precio [{lambrin.precio_unitario}]: ").strip()
        precio = validar_precio(precio_str) if precio_str else lambrin.precio_unitario

        stock_str = input(f"  Stock [{lambrin.stock}]: ").strip()
        stock = validar_stock(stock_str) if stock_str else lambrin.stock

        lambrin.nombre = nombre
        lambrin.tipo = tipo
        lambrin.material = material
        lambrin.acabado = acabado
        lambrin.largo = largo
        lambrin.ancho = ancho
        lambrin.espesor = espesor
        lambrin.precio_unitario = precio
        lambrin.stock = stock

        if confirmar("¿Desea guardar los cambios?"):
            inventario_service.actualizar_lambrin(lambrin)
            print("\n  ✓ Lambrín actualizado correctamente.")
        else:
            print("\n  Operación cancelada.")

    except ValueError as e:
        print(f"\n  ⚠ Error de entrada: {e}")
    except LambrinNoDisponibleError as e:
        print(f"\n  ⚠ {e}")
    except sqlite3.Error as e:
        print(f"\n  ⚠ Error de base de datos: {e}")

    pausar()


def desactivar_lambrin(inventario_service: InventarioService) -> None:
    """Desactiva un lambrín (eliminación lógica)."""
    print("\n  === DESACTIVAR LAMBRÍN ===\n")

    try:
        id_str = input("  ID del lambrín a desactivar: ").strip()
        lambrin_id = int(id_str)
        lambrin = inventario_service.obtener_lambrin(lambrin_id)

        print(f"\n  Lambrín: [{lambrin.codigo}] {lambrin.nombre}")
        print(f"  Stock actual: {lambrin.stock}")

        if confirmar("¿Está seguro de desactivar este lambrín?"):
            inventario_service.desactivar_lambrin(lambrin_id)
            print("\n  ✓ Lambrín desactivado correctamente.")
        else:
            print("\n  Operación cancelada.")

    except ValueError:
        print("\n  ⚠ Debe ingresar un ID numérico válido.")
    except LambrinNoDisponibleError as e:
        print(f"\n  ⚠ {e}")
    except sqlite3.Error as e:
        print(f"\n  ⚠ Error de base de datos: {e}")

    pausar()


def _mostrar_detalle_lambrin(lambrin: Lambrin) -> None:
    """Muestra los detalles de un lambrín."""
    print()
    imprimir_separador()
    print(f"  ID:            {lambrin.id}")
    print(f"  Código:        {lambrin.codigo}")
    print(f"  Nombre:        {lambrin.nombre}")
    print(f"  Tipo:          {lambrin.tipo}")
    print(f"  Material:      {lambrin.material}")
    print(f"  Acabado:       {lambrin.acabado}")
    print(f"  Largo:         {lambrin.largo} m")
    print(f"  Ancho:         {lambrin.ancho} m")
    print(f"  Espesor:       {lambrin.espesor} m")
    print(f"  Precio:        ${lambrin.precio_unitario}")
    print(f"  Stock:         {lambrin.stock} {lambrin.unidad_medida}(s)")
    print(f"  Fecha ingreso: {lambrin.fecha_ingreso}")
    print(f"  Actualizado:   {lambrin.fecha_actualizacion}")
    print(f"  Estado:        {'Activo' if lambrin.activo else 'Inactivo'}")
    imprimir_separador()


# ============================================================
# NUEVA COTIZACIÓN
# ============================================================

def menu_nueva_cotizacion(
    cotizacion_service: CotizacionService,
    inventario_service: InventarioService,
    cliente_repo: ClienteRepository,
) -> None:
    """Flujo completo para crear una nueva cotización."""
    limpiar_pantalla()
    print()
    print("=" * 58)
    print("           NUEVA COTIZACIÓN".center(58))
    print("=" * 58)
    print()

    try:
        # Paso 1: Datos del cliente
        print("  --- DATOS DEL CLIENTE ---\n")
        clientes = cliente_repo.obtener_todos()
        if clientes:
            print("  Clientes registrados:")
            for c in clientes:
                print(f"    [{c.id}] {c.nombre} - {c.telefono}")
            print(f"    [0] Registrar nuevo cliente")
            print()

        cliente_opcion = input("  ID del cliente (0 para nuevo): ").strip()
        try:
            cliente_id = int(cliente_opcion)
        except ValueError:
            print("\n  ⚠ Debe ingresar un número válido.")
            pausar()
            return

        if cliente_id == 0:
            cliente_id = _registrar_cliente_rapido(cliente_repo)
            if cliente_id is None:
                return

        # Verificar que el cliente existe
        cliente = cotizacion_service.verificar_cliente(cliente_id)
        print(f"\n  Cliente: {cliente.nombre}")

        # Paso 2: Mostrar lambrines disponibles
        print("\n  --- LAMBRINES DISPONIBLES ---\n")
        lambrines = cotizacion_service.obtener_lambrines_disponibles()

        if not lambrines:
            print("  No hay lambrines disponibles en inventario.")
            pausar()
            return

        encabezados = ["ID", "Código", "Lambrín", "Material", "Medidas (m)", "Precio", "Stock"]
        filas = []
        for l in lambrines:
            filas.append([
                l.id,
                l.codigo,
                l.nombre[:20],
                l.material,
                f"{l.largo}x{l.ancho}",
                f"${l.precio_unitario}",
                l.stock,
            ])
        imprimir_tabla(encabezados, filas, [5, 10, 22, 10, 12, 11, 7])

        # Paso 3: Seleccionar lambrín
        print()
        sel_str = input("  Seleccione el ID del lambrín: ").strip()
        try:
            lambrin_id = int(sel_str)
        except ValueError:
            print("\n  ⚠ Debe ingresar un número válido.")
            pausar()
            return

        # Buscar el lambrín seleccionado
        lambrin_seleccionado = None
        for l in lambrines:
            if l.id == lambrin_id:
                lambrin_seleccionado = l
                break

        if lambrin_seleccionado is None:
            print("\n  ⚠ No se encontró un lambrín con ese ID.")
            pausar()
            return

        # Paso 4: Mostrar dimensiones del lambrín seleccionado
        print()
        imprimir_separador()
        print("  LAMBRÍN SELECCIONADO")
        imprimir_separador()
        print(f"  Código:           {lambrin_seleccionado.codigo}")
        print(f"  Nombre:           {lambrin_seleccionado.nombre}")
        print(f"  Material:         {lambrin_seleccionado.material} - {lambrin_seleccionado.acabado}")
        print(f"  Largo de pieza:   {lambrin_seleccionado.largo} m")
        print(f"  Ancho de pieza:   {lambrin_seleccionado.ancho} m")
        print(f"  Espesor:          {lambrin_seleccionado.espesor} m")
        print(f"  Precio:           ${lambrin_seleccionado.precio_unitario}")
        print(f"  Stock:            {lambrin_seleccionado.stock} piezas")
        imprimir_separador()

        # Paso 5: Solicitar dimensiones de la superficie
        print("\n  --- SUPERFICIE A CUBRIR ---\n")
        ancho_superficie = validar_medida(
            input("  Ancho de la superficie (metros): "), "ancho de superficie"
        )
        alto_superficie = validar_medida(
            input("  Alto de la superficie (metros): "), "alto de superficie"
        )

        # Paso 6: Orientación de instalación
        print("\n  Orientación de instalación:")
        print("    [1] Vertical")
        print("    [2] Horizontal")
        ori_opcion = input("\n  Opción: ").strip()
        orientacion = "Horizontal" if ori_opcion == "2" else "Vertical"

        # Paso 7: ¿Incluir mano de obra?
        print("\n  ¿Incluir mano de obra?")
        print("    [1] Sí")
        print("    [2] No")
        mo_opcion = input("\n  Opción: ").strip()
        incluir_mano_obra = (mo_opcion == "1")

        # Paso 8: Calcular cotización
        datos = cotizacion_service.crear_cotizacion(
            cliente_id=cliente.id,
            lambrin_id=lambrin_seleccionado.id,
            ancho_superficie=ancho_superficie,
            alto_superficie=alto_superficie,
            orientacion=orientacion,
            incluir_mano_obra=incluir_mano_obra,
        )

        # Paso 9: Mostrar resumen
        _mostrar_cotizacion_detallada(datos)

        # Paso 10: Confirmar o cancelar
        if confirmar("¿Desea confirmar esta cotización?"):
            cotizacion_id = cotizacion_service.confirmar_cotizacion(datos)
            print(f"\n  ✓ Cotización #{cotizacion_id:05d} confirmada exitosamente.")
            print(f"    Stock actualizado: {lambrin_seleccionado.stock} → "
                  f"{lambrin_seleccionado.stock - datos['cantidad']}")
        else:
            print("\n  Cotización cancelada.")

    except ClienteNoEncontradoError as e:
        print(f"\n  ⚠ {e}")
    except StockInsuficienteError as e:
        print(f"\n  ⚠ Error de inventario: {e}")
    except LambrinNoDisponibleError as e:
        print(f"\n  ⚠ Producto no disponible: {e}")
    except CotizacionInvalidaError as e:
        print(f"\n  ⚠ Cotización inválida: {e}")
    except ValueError as e:
        print(f"\n  ⚠ Error de entrada: {e}")
    except sqlite3.Error as e:
        print(f"\n  ⚠ Error de base de datos: {e}")

    pausar()


def _mostrar_cotizacion_detallada(datos: dict) -> None:
    """Muestra el resumen de cotización con todos los cálculos."""
    cliente = datos["cliente"]
    lambrin = datos["lambrin"]
    from datetime import datetime

    print()
    print("=" * 58)
    print("          RESUMEN DE COTIZACIÓN".center(58))
    print("=" * 58)
    print(f"  Cliente:            {cliente.nombre}")
    print(f"  Fecha:              {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print()
    print(f"  Lambrín seleccionado:")
    print(f"    {lambrin.nombre}")
    print(f"    Código: {lambrin.codigo}")
    print(f"    {lambrin.material} - {lambrin.acabado}")
    print()
    print(f"  Medidas de cada pieza:")
    print(f"    {lambrin.largo} m × {lambrin.ancho} m")
    print()
    print(f"  Orientación:        {datos['orientacion']}")
    print()
    print(f"  Superficie a cubrir:")
    print(f"    {datos['ancho_superficie']} m × {datos['alto_superficie']} m")
    print()
    imprimir_separador()
    print(f"  Área de superficie: {datos['area_superficie']:.2f} m²")
    print(f"  Área por pieza:     {datos['area_por_pieza']:.4f} m²")
    print(f"  Desperdicio:        {datos['porcentaje_desperdicio']}%")
    print(f"  Cantidad calculada: {datos['cantidad']} piezas")
    print(f"  Stock disponible:   {lambrin.stock} piezas")
    imprimir_separador()
    print(f"  Precio por pieza:   ${datos['precio_unitario']:>10}")
    print(f"  Subtotal material:  ${datos['subtotal_material']:>10}")
    print()
    if datos["incluye_mano_obra"]:
        print(f"  ¿Mano de obra?      Sí")
        print(f"  Costo mano de obra: ${datos['costo_mano_obra']:>10}")
        costo_m2 = datos.get('costo_por_m2', Decimal('180.00'))
        print(f"    ({datos['area_superficie']:.2f} m² × ${costo_m2}/m²)")
    else:
        print(f"  ¿Mano de obra?      No")
        print(f"  Costo mano de obra: ${'0.00':>10}")
    print()
    imprimir_separador()
    print(f"  TOTAL:              ${datos['total']:>10}")
    print("=" * 58)


def _registrar_cliente_rapido(cliente_repo: ClienteRepository) -> int:
    """Registra un nuevo cliente de forma rápida.

    Returns:
        ID del cliente creado, o None si se canceló.
    """
    print("\n  --- NUEVO CLIENTE ---\n")
    try:
        nombre = validar_texto_no_vacio(input("  Nombre: "), "nombre")
        telefono = input("  Teléfono: ").strip()
        email = input("  Email: ").strip()
        direccion = input("  Dirección: ").strip()

        cliente = Cliente(
            nombre=nombre,
            telefono=telefono,
            email=email,
            direccion=direccion,
        )
        cliente_id = cliente_repo.crear(cliente)
        print(f"\n  ✓ Cliente registrado. ID: {cliente_id}")
        return cliente_id

    except ValueError as e:
        print(f"\n  ⚠ {e}")
        pausar()
        return None
    except sqlite3.Error as e:
        print(f"\n  ⚠ Error de base de datos: {e}")
        pausar()
        return None


# ============================================================
# MENÚ DE CLIENTES
# ============================================================

def menu_clientes(
    cliente_repo: ClienteRepository,
    cotizacion_service: CotizacionService,
) -> None:
    """Submenú de gestión de clientes."""
    while True:
        limpiar_pantalla()
        print()
        print("=" * 58)
        print("            GESTIÓN DE CLIENTES".center(58))
        print("=" * 58)
        print()
        print("  1. Registrar cliente")
        print("  2. Consultar clientes")
        print("  3. Actualizar cliente")
        print("  4. Eliminar cliente")
        print("  5. Regresar")
        imprimir_separador()

        opcion = input("\n  Seleccione una opción: ").strip()

        try:
            opcion_num = validar_opcion_menu(opcion, [1, 2, 3, 4, 5])
        except ValueError as e:
            print(f"\n  ⚠ {e}")
            pausar()
            continue

        if opcion_num == 1:
            _registrar_cliente_rapido(cliente_repo)
            pausar()
        elif opcion_num == 2:
            _consultar_clientes(cliente_repo)
        elif opcion_num == 3:
            _actualizar_cliente(cliente_repo)
        elif opcion_num == 4:
            _eliminar_cliente(cliente_repo, cotizacion_service)
        elif opcion_num == 5:
            break


def _consultar_clientes(cliente_repo: ClienteRepository) -> None:
    """Muestra todos los clientes y permite buscar por nombre."""
    limpiar_pantalla()
    print("\n  === CONSULTAR CLIENTES ===\n")
    clientes = cliente_repo.obtener_todos()
    if clientes:
        encabezados = ["ID", "Nombre", "Teléfono", "Email"]
        filas = [[c.id, c.nombre, c.telefono, c.email] for c in clientes]
        imprimir_tabla(encabezados, filas, [5, 25, 15, 25])
    else:
        print("  No hay clientes registrados.")

    print()
    nombre = input("  Buscar por nombre (o Enter para volver): ").strip()
    if nombre:
        resultados = cliente_repo.buscar_por_nombre(nombre)
        if resultados:
            print(f"\n  Resultados para '{nombre}':")
            for c in resultados:
                print(f"    [{c.id}] {c.nombre} - {c.telefono} - {c.email}")
        else:
            print(f"\n  No se encontraron clientes con '{nombre}'.")
    pausar()


def _actualizar_cliente(cliente_repo: ClienteRepository) -> None:
    """Actualiza la información de un cliente existente."""
    limpiar_pantalla()
    print("\n  === ACTUALIZAR CLIENTE ===\n")

    # Mostrar clientes existentes
    clientes = cliente_repo.obtener_todos()
    if clientes:
        for c in clientes:
            print(f"    [{c.id}] {c.nombre} - {c.telefono}")
    else:
        print("  No hay clientes registrados.")
        pausar()
        return

    try:
        id_str = input("\n  ID del cliente a actualizar: ").strip()
        cliente_id = int(id_str)
        cliente = cliente_repo.obtener_por_id(cliente_id)

        if cliente is None:
            print(f"\n  ⚠ No existe un cliente con el ID {cliente_id}.")
            pausar()
            return

        print(f"\n  Cliente: [{cliente.id}] {cliente.nombre}")
        print("  (Deje vacío para mantener el valor actual)\n")

        nombre = input(f"  Nombre [{cliente.nombre}]: ").strip() or cliente.nombre
        telefono = input(f"  Teléfono [{cliente.telefono}]: ").strip() or cliente.telefono
        email = input(f"  Email [{cliente.email}]: ").strip() or cliente.email
        direccion = input(f"  Dirección [{cliente.direccion}]: ").strip() or cliente.direccion

        cliente.nombre = nombre
        cliente.telefono = telefono
        cliente.email = email
        cliente.direccion = direccion

        if confirmar("¿Desea guardar los cambios?"):
            cliente_repo.actualizar(cliente)
            print("\n  ✓ Cliente actualizado correctamente.")
        else:
            print("\n  Operación cancelada.")

    except ValueError:
        print("\n  ⚠ Debe ingresar un ID numérico válido.")
    except sqlite3.Error as e:
        print(f"\n  ⚠ Error de base de datos: {e}")

    pausar()


def _eliminar_cliente(
    cliente_repo: ClienteRepository,
    cotizacion_service: CotizacionService,
) -> None:
    """Elimina un cliente del sistema."""
    limpiar_pantalla()
    print("\n  === ELIMINAR CLIENTE ===\n")

    # Mostrar clientes existentes
    clientes = cliente_repo.obtener_todos()
    if clientes:
        encabezados = ["ID", "Nombre", "Teléfono", "Email"]
        filas = [[c.id, c.nombre, c.telefono, c.email] for c in clientes]
        imprimir_tabla(encabezados, filas, [5, 25, 15, 25])
    else:
        print("  No hay clientes registrados.")
        pausar()
        return

    try:
        id_str = input("\n  ID del cliente a eliminar: ").strip()
        cliente_id = int(id_str)
        cliente = cliente_repo.obtener_por_id(cliente_id)

        if cliente is None:
            print(f"\n  ⚠ No existe un cliente con el ID {cliente_id}.")
            pausar()
            return

        # Mostrar información del cliente
        print()
        imprimir_separador()
        print(f"  ID:        {cliente.id}")
        print(f"  Nombre:    {cliente.nombre}")
        print(f"  Teléfono:  {cliente.telefono}")
        print(f"  Email:     {cliente.email}")
        print(f"  Dirección: {cliente.direccion}")
        imprimir_separador()

        print("\n  ¿Está seguro de que desea eliminar este cliente?")
        print("    [1] Sí")
        print("    [2] No")
        opcion = input("\n  Opción: ").strip()

        if opcion == "1":
            cotizacion_service.eliminar_cliente(cliente_id)
            print(f"\n  ✓ Cliente '{cliente.nombre}' eliminado correctamente.")
            print("    Las cotizaciones históricas se conservan.")
        else:
            print("\n  Operación cancelada.")

    except ValueError:
        print("\n  ⚠ Debe ingresar un ID numérico válido.")
    except ClienteNoEncontradoError as e:
        print(f"\n  ⚠ {e}")
    except sqlite3.Error as e:
        print(f"\n  ⚠ Error de base de datos: {e}")

    pausar()


# ============================================================
# MENÚ DE REPORTES
# ============================================================

def menu_reportes(
    reporte_service: ReporteService,
    inventario_service: InventarioService,
) -> None:
    """Submenú de reportes."""
    while True:
        limpiar_pantalla()
        print()
        print("=" * 58)
        print("                REPORTES".center(58))
        print("=" * 58)
        print()
        print("  1. Inventario completo")
        print("  2. Productos con stock bajo")
        print("  3. Productos con mayor antigüedad")
        print("  4. Cotizaciones por cliente")
        print("  5. Total cotizado por tipo de lambrín")
        print("  6. Cantidad de cotizaciones por cliente")
        print("  7. Precio promedio por tipo")
        print("  8. Valor total del inventario")
        print("  9. Historial de cotizaciones")
        print("  0. Volver al menú principal")
        imprimir_separador()

        opcion = input("\n  Seleccione una opción: ").strip()

        try:
            opcion_num = validar_opcion_menu(opcion, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        except ValueError as e:
            print(f"\n  ⚠ {e}")
            pausar()
            continue

        if opcion_num == 0:
            break
        elif opcion_num == 1:
            _reporte_inventario(reporte_service)
        elif opcion_num == 2:
            _reporte_stock_bajo(reporte_service)
        elif opcion_num == 3:
            _reporte_antiguedad(reporte_service)
        elif opcion_num == 4:
            _reporte_cotizaciones_cliente_detalle(reporte_service)
        elif opcion_num == 5:
            _reporte_total_tipo(reporte_service)
        elif opcion_num == 6:
            _reporte_cotizaciones_por_cliente(reporte_service)
        elif opcion_num == 7:
            _reporte_precio_promedio(reporte_service)
        elif opcion_num == 8:
            _reporte_valor_inventario(reporte_service)
        elif opcion_num == 9:
            _reporte_historial(reporte_service)


def _reporte_inventario(reporte_service: ReporteService) -> None:
    limpiar_pantalla()
    print("\n  === INVENTARIO COMPLETO ===\n")
    datos = reporte_service.reporte_inventario_completo()
    if datos:
        encabezados = ["ID", "Código", "Nombre", "Tipo", "Stock", "Precio", "Activo"]
        filas = [
            [d["ID"], d["Código"], d["Nombre"][:20], d["Tipo"][:12],
             d["Stock"], f"${d['Precio Unitario']}", d["Activo"]]
            for d in datos
        ]
        imprimir_tabla(encabezados, filas, [5, 10, 22, 14, 7, 11, 7])
    else:
        print("  Sin datos.")
    pausar()


def _reporte_stock_bajo(reporte_service: ReporteService) -> None:
    limpiar_pantalla()
    print("\n  === PRODUCTOS CON STOCK BAJO ===\n")
    try:
        umbral_str = input("  Umbral de stock mínimo [10]: ").strip() or "10"
        umbral = int(umbral_str)
    except ValueError:
        umbral = 10

    datos = reporte_service.reporte_stock_bajo(umbral)
    if datos:
        encabezados = ["ID", "Código", "Nombre", "Stock", "Precio"]
        filas = [[d["ID"], d["Código"], d["Nombre"][:22], d["Stock"], f"${d['Precio']}"]
                 for d in datos]
        imprimir_tabla(encabezados, filas, [5, 10, 24, 7, 11])
        print(f"\n  ⚠ {len(datos)} producto(s) con stock ≤ {umbral}")
    else:
        print(f"  No hay productos con stock ≤ {umbral}.")
    pausar()


def _reporte_antiguedad(reporte_service: ReporteService) -> None:
    limpiar_pantalla()
    print("\n  === PRODUCTOS CON MAYOR ANTIGÜEDAD ===\n")
    try:
        dias_str = input("  Días mínimos en inventario [90]: ").strip() or "90"
        dias = int(dias_str)
    except ValueError:
        dias = 90

    datos = reporte_service.reporte_productos_antiguos(dias)
    if datos:
        encabezados = ["ID", "Código", "Nombre", "Días", "Stock"]
        filas = [[d["ID"], d["Código"], d["Nombre"][:22],
                  d["Días en inventario"], d["Stock"]]
                 for d in datos]
        imprimir_tabla(encabezados, filas, [5, 10, 24, 7, 7])
    else:
        print(f"  No hay productos con más de {dias} días en inventario.")
    pausar()


def _reporte_cotizaciones_cliente_detalle(reporte_service: ReporteService) -> None:
    limpiar_pantalla()
    print("\n  === HISTORIAL DE COTIZACIONES (detalle) ===\n")
    datos = reporte_service.reporte_historial_cotizaciones()
    if datos:
        encabezados = ["Cot.#", "Cliente", "Lambrín", "Cant", "Total", "Estado"]
        filas = [
            [f"{d['cotizacion_id']:05d}", d["cliente"][:18],
             d["codigo_lambrin"], d["cantidad"],
             f"${d['total']}", d["estado"]]
            for d in datos
        ]
        imprimir_tabla(encabezados, filas, [7, 20, 10, 6, 12, 12])
    else:
        print("  No hay cotizaciones registradas.")
    pausar()


def _reporte_total_tipo(reporte_service: ReporteService) -> None:
    """Total cotizado por tipo de lambrín (JOIN + SUM + GROUP BY)."""
    limpiar_pantalla()
    print("\n  === TOTAL COTIZADO POR TIPO DE LAMBRÍN ===\n")
    datos = reporte_service.reporte_total_por_tipo_lambrin()
    if datos:
        encabezados = ["Tipo", "Cotizaciones", "Piezas", "Total Cotizado"]
        filas = [
            [d["tipo"], d["total_cotizaciones"],
             d["total_piezas"], f"${d['total_cotizado']:,.2f}"]
            for d in datos
        ]
        imprimir_tabla(encabezados, filas, [16, 14, 8, 16])
    else:
        print("  No hay datos de cotizaciones aún.")
    pausar()


def _reporte_cotizaciones_por_cliente(reporte_service: ReporteService) -> None:
    """Cantidad de cotizaciones por cliente (LEFT JOIN + COUNT + GROUP BY)."""
    limpiar_pantalla()
    print("\n  === COTIZACIONES POR CLIENTE ===\n")
    datos = reporte_service.reporte_cotizaciones_por_cliente()
    if datos:
        encabezados = ["ID", "Cliente", "Teléfono", "Total Cot."]
        filas = [
            [d["id"], d["nombre"][:22], d["telefono"], d["total_cotizaciones"]]
            for d in datos
        ]
        imprimir_tabla(encabezados, filas, [5, 24, 15, 12])
    else:
        print("  No hay clientes registrados.")
    pausar()


def _reporte_precio_promedio(reporte_service: ReporteService) -> None:
    """Precio promedio por tipo de lambrín (AVG + GROUP BY)."""
    limpiar_pantalla()
    print("\n  === PRECIO PROMEDIO POR TIPO ===\n")
    datos = reporte_service.reporte_precio_promedio_por_tipo()
    if datos:
        encabezados = ["Tipo", "Productos", "Precio Promedio"]
        filas = [
            [d["tipo"], d["cantidad"], f"${d['precio_promedio']:,.2f}"]
            for d in datos
        ]
        imprimir_tabla(encabezados, filas, [16, 12, 16])
    else:
        print("  No hay datos.")
    pausar()


def _reporte_valor_inventario(reporte_service: ReporteService) -> None:
    """Valor total del inventario (SUM)."""
    limpiar_pantalla()
    print("\n  === VALOR TOTAL DEL INVENTARIO ===\n")
    datos = reporte_service.reporte_valor_total_inventario()
    imprimir_separador()
    print(f"  Total de productos:  {datos['total_productos']}")
    print(f"  Total de piezas:     {datos['total_piezas']}")
    print(f"  Valor total:         ${datos['valor_total']:,.2f}")
    imprimir_separador()
    pausar()


def _reporte_historial(reporte_service: ReporteService) -> None:
    """Historial completo de cotizaciones (JOIN múltiple)."""
    limpiar_pantalla()
    print("\n  === HISTORIAL COMPLETO DE COTIZACIONES ===\n")
    datos = reporte_service.reporte_historial_cotizaciones()
    if datos:
        for d in datos:
            imprimir_separador()
            print(f"  Cotización #{d['cotizacion_id']:05d}")
            print(f"    Cliente:      {d['cliente']}")
            print(f"    Fecha:        {d['fecha_creacion']}")
            print(f"    Lambrín:      [{d['codigo_lambrin']}] {d['nombre_lambrin']}")
            print(f"    Tipo:         {d['tipo_lambrin']}")
            print(f"    Cantidad:     {d['cantidad']}")
            print(f"    P. Unitario:  ${d['precio_unit']}")
            print(f"    Subtotal:     ${d['subtotal_material']}")
            print(f"    Mano de obra: ${d['costo_mano_obra']}")
            print(f"    TOTAL:        ${d['total']}")
            print(f"    Estado:       {d['estado']}")
        imprimir_separador()
    else:
        print("  No hay cotizaciones registradas.")
    pausar()


# ============================================================
# EXPORTAR CSV Y RESPALDOS
# ============================================================

def accion_exportar_csv(reporte_service: ReporteService) -> None:
    """Exporta el inventario a CSV."""
    limpiar_pantalla()
    print("\n  === EXPORTAR INVENTARIO A CSV ===\n")
    try:
        ruta = reporte_service.exportar_inventario_csv()
        print(f"  ✓ Inventario exportado exitosamente.")
        print(f"    Archivo: {ruta}")
    except (OSError, PermissionError) as e:
        print(f"\n  ⚠ Error al exportar: {e}")
    pausar()


def accion_respaldo(reporte_service: ReporteService) -> None:
    """Genera un respaldo del sistema."""
    limpiar_pantalla()
    print("\n  === GENERAR RESPALDO ===\n")
    if confirmar("¿Desea generar un respaldo completo del sistema?"):
        try:
            ruta = reporte_service.generar_respaldo()
            print(f"\n  ✓ Respaldo generado exitosamente.")
            print(f"    Archivo: {ruta}")
        except (OSError, PermissionError) as e:
            print(f"\n  ⚠ Error al generar respaldo: {e}")
    else:
        print("\n  Operación cancelada.")
    pausar()


# ============================================================
# CONFIGURACIÓN
# ============================================================

def menu_configuracion() -> None:
    """Menú para ver y modificar la configuración."""
    limpiar_pantalla()
    print("\n  === CONFIGURACIÓN ===\n")

    config_path = os.path.join(directorio_base, "config.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        print("  Configuración actual:")
        imprimir_separador()
        for clave, valor in config.items():
            print(f"    {clave}: {valor}")
        imprimir_separador()

        if confirmar("\n  ¿Desea modificar el costo de mano de obra por m²?"):
            try:
                nuevo_costo = validar_precio(
                    input(f"\n  Nuevo costo por m² [{config.get('costo_mano_obra_m2', 180)}]: ")
                )
                config["costo_mano_obra_m2"] = float(nuevo_costo)
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, ensure_ascii=False, indent=4)
                print("\n  ✓ Configuración actualizada.")
            except ValueError as e:
                print(f"\n  ⚠ {e}")

    except FileNotFoundError:
        print("  ⚠ No se encontró config.json")
    except json.JSONDecodeError:
        print("  ⚠ Error al leer config.json")

    pausar()


# ============================================================
# PUNTO DE ENTRADA
# ============================================================

def main() -> None:
    """Punto de entrada principal de la aplicación."""
    logger.info("=" * 50)
    logger.info("LAMBRINSTOCK iniciado")
    logger.info("=" * 50)

    # Inicializar base de datos
    database = Database()
    database.inicializar()

    # Crear repositorios
    lambrin_repo = LambrinRepository(database)
    cliente_repo = ClienteRepository(database)
    cotizacion_repo = CotizacionRepository(database)

    # Crear servicios
    inventario_service = InventarioService(lambrin_repo)
    cotizacion_service = CotizacionService(
        lambrin_repo, cliente_repo, cotizacion_repo
    )
    reporte_service = ReporteService(
        lambrin_repo, cliente_repo, cotizacion_repo
    )

    # Iniciar menú principal
    menu_principal(
        inventario_service,
        cotizacion_service,
        reporte_service,
        cliente_repo,
    )


if __name__ == "__main__":
    main()
