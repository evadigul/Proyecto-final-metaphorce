"""
Servicio de reportes para LAMBRINSTOCK.

Incluye:
- Reportes basados en consultas SQL avanzadas (JOIN, GROUP BY, etc.)
- Exportación de inventario a CSV.
- Generación de respaldos en JSON.
- Registro de auditoría.
"""

import csv
import json
import os
from datetime import datetime

from repositories.lambrin_repository import LambrinRepository
from repositories.cliente_repository import ClienteRepository
from repositories.cotizacion_repository import CotizacionRepository
from utils.logger import configurar_logger

logger = configurar_logger(__name__)


class ReporteService:
    """Servicio para generación de reportes, exportación y respaldos.
    """

    def __init__(
        self,
        lambrin_repo: LambrinRepository,
        cliente_repo: ClienteRepository,
        cotizacion_repo: CotizacionRepository,
    ) -> None:
        self.lambrin_repo = lambrin_repo
        self.cliente_repo = cliente_repo
        self.cotizacion_repo = cotizacion_repo
        self.directorio_base = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )

    # ===== REPORTES =====

    def reporte_inventario_completo(self) -> list[dict]:
        lambrines = self.lambrin_repo.obtener_todos(solo_activos=False)
        return [
            {
                "ID": l.id,
                "Código": l.codigo,
                "Nombre": l.nombre,
                "Tipo": l.tipo,
                "Material": l.material,
                "Acabado": l.acabado,
                "Largo": l.largo,
                "Ancho": l.ancho,
                "Espesor": l.espesor,
                "Precio Unitario": str(l.precio_unitario),
                "Stock": l.stock,
                "Unidad": l.unidad_medida,
                "Fecha Ingreso": l.fecha_ingreso,
                "Fecha Actualización": l.fecha_actualizacion,
                "Activo": "Sí" if l.activo else "No",
            }
            for l in lambrines
        ]

    def reporte_stock_bajo(self, umbral: int = 10) -> list[dict]:
        lambrines = self.lambrin_repo.obtener_stock_bajo(umbral)
        return [
            {
                "ID": l.id,
                "Código": l.codigo,
                "Nombre": l.nombre,
                "Stock": l.stock,
                "Precio": str(l.precio_unitario),
            }
            for l in lambrines
        ]

    def reporte_productos_antiguos(self, dias: int = 90) -> list[dict]:
        lambrines = self.lambrin_repo.obtener_antiguos(dias)
        resultados = []
        for l in lambrines:
            antiguedad = 0
            if l.fecha_ingreso:
                try:
                    fecha = datetime.strptime(l.fecha_ingreso, "%Y-%m-%d %H:%M:%S")
                    antiguedad = (datetime.now() - fecha).days
                except ValueError:
                    pass
            resultados.append({
                "ID": l.id,
                "Código": l.codigo,
                "Nombre": l.nombre,
                "Días en inventario": antiguedad,
                "Stock": l.stock,
                "Fecha Ingreso": l.fecha_ingreso,
            })
        return resultados

    def reporte_cotizaciones_por_cliente(self) -> list[dict]:
        return self.cliente_repo.obtener_clientes_con_cotizaciones()

    def reporte_total_por_tipo_lambrin(self) -> list[dict]:

        return self.cotizacion_repo.obtener_total_por_tipo_lambrin()

    def reporte_precio_promedio_por_tipo(self) -> list[dict]:

        return self.lambrin_repo.obtener_precio_promedio_por_tipo()

    def reporte_inventario_agrupado(self) -> list[dict]:

        return self.lambrin_repo.obtener_inventario_agrupado()

    def reporte_valor_total_inventario(self) -> dict:

        return self.lambrin_repo.obtener_valor_total_inventario()

    def reporte_historial_cotizaciones(self) -> list[dict]:

        return self.cotizacion_repo.obtener_historial_completo()

    # ===== EXPORTACIÓN CSV =====

    def exportar_inventario_csv(self) -> str:
        """Exporta el inventario completo a un archivo CSV.

        se genera en exports/inventario_lambrines.csv.
        los datos se obtienen directamente de SQLite.

        """
        directorio_exports = os.path.join(self.directorio_base, "exports")
        os.makedirs(directorio_exports, exist_ok=True)

        archivo_csv = os.path.join(directorio_exports, "inventario_lambrines.csv")

        lambrines = self.lambrin_repo.obtener_todos(solo_activos=False)

        encabezados = [
            "ID", "Código", "Nombre", "Tipo", "Material", "Acabado",
            "Largo", "Ancho", "Espesor", "Precio Unitario", "Stock",
            "Unidad", "Fecha Ingreso", "Fecha Actualización", "Activo",
        ]

        with open(archivo_csv, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(encabezados)

            for l in lambrines:
                writer.writerow([
                    l.id,
                    l.codigo,
                    l.nombre,
                    l.tipo,
                    l.material,
                    l.acabado,
                    l.largo,
                    l.ancho,
                    l.espesor,
                    str(l.precio_unitario),
                    l.stock,
                    l.unidad_medida,
                    l.fecha_ingreso,
                    l.fecha_actualizacion,
                    "Sí" if l.activo else "No",
                ])

        logger.info("Inventario exportado a CSV: %s", archivo_csv)
        return archivo_csv

    # ===== RESPALDOS JSON =====

    def generar_respaldo(self) -> str:
        """Genera un respaldo completo del sistema en formato JSON.

        El archivo se guarda en backups.json
        e incluye: lambrines, clientes, cotizaciones y detalles.

        """
        directorio_backups = os.path.join(self.directorio_base, "backups")
        os.makedirs(directorio_backups, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archivo_respaldo = os.path.join(
            directorio_backups, f"respaldo_{timestamp}.json"
        )


        lambrines = self.lambrin_repo.obtener_todos(solo_activos=False)
        clientes = self.cliente_repo.obtener_todos(solo_activos=False)
        cotizaciones = self.cotizacion_repo.obtener_todas()


        cotizaciones_data = []
        for cot in cotizaciones:
            detalles = self.cotizacion_repo.obtener_detalles(cot.id)
            cotizaciones_data.append({
                "id": cot.id,
                "cliente_id": cot.cliente_id,
                "fecha_creacion": cot.fecha_creacion,
                "subtotal_material": str(cot.subtotal_material),
                "costo_mano_obra": str(cot.costo_mano_obra),
                "total": str(cot.total),
                "incluye_mano_obra": cot.incluye_mano_obra,
                "estado": cot.estado,
                "detalles": [
                    {
                        "id": d.id,
                        "lambrin_id": d.lambrin_id,
                        "cantidad": d.cantidad,
                        "precio_unitario": str(d.precio_unitario),
                        "subtotal": str(d.subtotal),
                        "largo_solicitado": d.largo_solicitado,
                        "ancho_solicitado": d.ancho_solicitado,
                        "espesor_solicitado": d.espesor_solicitado,
                    }
                    for d in detalles
                ],
            })

        respaldo = {
            "fecha_respaldo": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "version": "1.0.0",
            "lambrines": [
                {
                    "id": l.id,
                    "codigo": l.codigo,
                    "nombre": l.nombre,
                    "tipo": l.tipo,
                    "material": l.material,
                    "acabado": l.acabado,
                    "largo": l.largo,
                    "ancho": l.ancho,
                    "espesor": l.espesor,
                    "precio_unitario": str(l.precio_unitario),
                    "stock": l.stock,
                    "unidad_medida": l.unidad_medida,
                    "fecha_ingreso": l.fecha_ingreso,
                    "fecha_actualizacion": l.fecha_actualizacion,
                    "activo": l.activo,
                }
                for l in lambrines
            ],
            "clientes": [
                {
                    "id": c.id,
                    "nombre": c.nombre,
                    "telefono": c.telefono,
                    "email": c.email,
                    "direccion": c.direccion,
                    "fecha_registro": c.fecha_registro,
                    "activo": c.activo,
                }
                for c in clientes
            ],
            "cotizaciones": cotizaciones_data,
        }

        with open(archivo_respaldo, "w", encoding="utf-8") as f:
            json.dump(respaldo, f, ensure_ascii=False, indent=4)

        logger.info("Respaldo generado: %s", archivo_respaldo)
        return archivo_respaldo
