# 🏗️ LAMBRINSTOCK

**Sistema de Control de Inventario y Cotización de Lambrín para Construcción**

---

## 📋 Descripción

LAMBRINSTOCK es un sistema de escritorio basado en consola que permite administrar el inventario de diferentes tipos de lambrín decorativo utilizado como material de construcción, y generar cotizaciones detalladas para clientes.

## 🎯 Problema que resuelve

En el negocio de materiales de construcción, es común manejar múltiples tipos de lambrín con diferentes materiales, medidas, acabados y precios. LAMBRINSTOCK centraliza la gestión de este inventario y automatiza el proceso de cotización, incluyendo el cálculo de mano de obra.

## ✨ Características principales

- **CRUD completo** de lambrines con eliminación lógica
- **Sistema de cotizaciones** con cálculo automático de costos
- **Cálculo de mano de obra** configurable por metro cuadrado
- **8 reglas de negocio** implementadas en la capa de servicios
- **Reportes avanzados** con SQL (JOIN, GROUP BY, SUM, AVG, COUNT)
- **Exportación a CSV** del inventario completo
- **Respaldos en JSON** con datos completos del sistema
- **Logging** de eventos del sistema
- **Excepciones de dominio** con manejo específico
- **Interfaz de consola** con menús y tablas formateadas

## 🛠️ Tecnologías utilizadas

| Tecnología | Uso |
|-----------|-----|
| Python 3 | Lenguaje principal |
| SQLite (sqlite3) | Base de datos / persistencia |
| dataclasses | Modelos de entidades |
| Decimal | Precisión monetaria |
| csv | Exportación de inventario |
| json | Configuración, respaldos y auditoría |
| logging | Registro de eventos |
| datetime | Manejo de fechas y antigüedad |



## 🏛️ Arquitectura

El proyecto utiliza **Arquitectura en Capas** con separación clara de responsabilidades:

```
┌──────────────────────────────────────────────────┐
│                 main.py                          │
│           (Presentación / Consola)               │
│  - Menús, tablas, captura de excepciones         │
├──────────────────────────────────────────────────┤
│               services/                          │
│          (Reglas de Negocio)                     │
│  - Verificación de stock                         │
│  - Compatibilidad de medidas                     │
│  - Cálculo de mano de obra                       │
│  - Descuento de inventario                       │
├──────────────────────────────────────────────────┤
│             repositories/                        │
│           (Acceso a Datos)                       │
│  - CRUD con SQLite                               │
│  - Consultas SQL avanzadas                       │
│  - Consultas parametrizadas                      │
├──────────────────────────────────────────────────┤
│               SQLite                             │
│          (Base de Datos)                         │
│  - lambrines, clientes, cotizaciones, detalle    │
└──────────────────────────────────────────────────┘
```

## 📁 Estructura de carpetas

```
lambrinstock/
├── main.py                          # Punto de entrada, interfaz de consola
├── config.json                      # Configuración del sistema
├── requirements.txt                 # Dependencias (solo stdlib)
├── README.md                        # Este archivo
├── CONFLICTOS.md                    # Documentación del conflicto Git
├── .gitignore                       # Archivos excluidos de Git
│
├── models/                          # Capa de modelos (dataclasses)
│   ├── __init__.py
│   ├── lambrin.py                   # Modelo Lambrín
│   ├── cliente.py                   # Modelo Cliente
│   ├── cotizacion.py                # Modelo Cotización
│   └── detalle_cotizacion.py        # Modelo Detalle de Cotización
│
├── repositories/                    # Capa de acceso a datos
│   ├── __init__.py
│   ├── database.py                  # Gestión de conexión y BD
│   ├── lambrin_repository.py        # CRUD + consultas de lambrines
│   ├── cliente_repository.py        # CRUD + consultas de clientes
│   └── cotizacion_repository.py     # CRUD + consultas de cotizaciones
│
├── services/                        # Capa de reglas de negocio
│   ├── __init__.py
│   ├── inventario_service.py        # Reglas de inventario
│   ├── cotizacion_service.py        # Reglas de cotización
│   └── reporte_service.py           # Reportes, CSV, respaldos
│
├── exceptions/                      # Excepciones de dominio
│   ├── __init__.py
│   └── domain_exceptions.py         # Excepciones específicas
│
├── utils/                           # Utilidades
│   ├── __init__.py
│   ├── validators.py                # Validadores de entrada
│   └── logger.py                    # Configuración de logging
│
├── database/                        # Esquema de BD
│   └── schema.sql                   # DDL con FOREIGN KEY
│
│
├── exports/                         # CSV exportados (generado)
├── backups/                         # Respaldos JSON (generado)
└── logs/                            # Logs del sistema (generado)
```

## 🗃️ Modelo de base de datos

```
┌──────────┐       ┌──────────────┐       ┌─────────────────────┐
│ clientes │──1:N──│ cotizaciones │──1:N──│ detalle_cotizacion  │
└──────────┘       └──────────────┘       └─────────────────────┘
                                                    │
                                               N:1  │
                                          ┌─────────┘
                                          ▼
                                    ┌──────────┐
                                    │ lambrines│
                                    └──────────┘
```

**Relaciones:**
- Un **cliente** puede tener muchas **cotizaciones** (1:N)
- Una **cotización** puede tener muchos **detalles** (1:N)
- Cada **detalle** referencia a un **lambrín** (N:1)

Las FOREIGN KEY están activas (`PRAGMA foreign_keys = ON`).

## 📏 Reglas de negocio

| # | Regla | Ubicación |
|---|-------|-----------|
| 1 | No se puede cotizar si el stock disponible es menor que la cantidad calculada | `cotizacion_service.py` |
| 2 | La cantidad de piezas se calcula automáticamente según la superficie a cubrir | `cotizacion_service.py` |
| 3 | No se permite registrar dos lambrines con el mismo código | `inventario_service.py` |
| 4 | La mano de obra se calcula independientemente del material (por m² de superficie) | `cotizacion_service.py` |
| 5 | Si el cliente solicita mano de obra, se agrega al costo final | `cotizacion_service.py` |
| 6 | Sin mano de obra → costo de mano de obra = $0 | `cotizacion_service.py` |
| 7 | Al confirmar una cotización, el stock se descuenta | `cotizacion_service.py` |
| 8 | El stock nunca puede ser negativo | `inventario_service.py` / `cotizacion_service.py` |
| 9 | Se aplica un porcentaje de desperdicio configurable al cálculo de piezas | `cotizacion_service.py` |
| 10 | La cantidad de piezas siempre se redondea hacia arriba (math.ceil) | `cotizacion_service.py` |
| 11 | Al eliminar un cliente, sus cotizaciones históricas se conservan (ON DELETE SET NULL) | `schema.sql` / `cotizacion_service.py` |


### Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/lambrinstock.git
cd lambrinstock
```


## 🚀 Ejecución

```bash
# Desde el directorio lambrinstock/
python main.py
```

La base de datos se crea automáticamente en la primera ejecución con 10 tipos de lambrín de ejemplo y 3 clientes.

## ⚙️ Configuración

El archivo `config.json` permite modificar:

```json
{
    "nombre_negocio": "LAMBRINSTOCK",
    "moneda": "MXN",
    "simbolo_moneda": "$",
    "costo_mano_obra_m2": 180.00,
    "dias_alerta_antiguedad": 90,
    "stock_minimo_alerta": 10,
    "porcentaje_desperdicio": 10
}
```

### Cálculo de mano de obra

La fórmula utilizada es:

```
mano_de_obra = metros_cuadrados_totales × costo_por_m²
```

Donde:

```
metros_cuadrados_totales = largo × ancho × cantidad
```

El `costo_por_m²` se configura en `config.json` (`costo_mano_obra_m2`).
Este valor puede modificarse sin cambiar el código.

**Ejemplo:**
- Lambrín de 2.90m × 0.15m, 20 piezas
- Metros cuadrados: 2.90 × 0.15 × 20 = 8.70 m²
- Costo mano de obra: 8.70 × $180.00 = $1,566.00

### Flujo de cotización

El sistema sigue estos pasos para crear una cotización:

1. Seleccionar o registrar cliente.
2. Mostrar catálogo de lambrines disponibles (con stock, medidas, precio).
3. El usuario selecciona un lambrín por ID.
4. Mostrar dimensiones del lambrín seleccionado.
5. Solicitar dimensiones de la superficie a cubrir (ancho × alto).
6. Solicitar orientación de instalación (Vertical / Horizontal).
7. Calcular automáticamente: área superficie, área pieza, cantidad con desperdicio.
8. Verificar stock suficiente.
9. Solicitar si incluye mano de obra.
10. Mostrar resumen completo → confirmar / cancelar.
11. Al confirmar: guardar cotización + detalle, descontar stock.

### Cálculo de piezas (con desperdicio)

```
area_superficie         = ancho × alto
area_por_pieza          = largo_lambrin × ancho_lambrin
cantidad_teorica        = area_superficie / area_por_pieza
cantidad_con_desperdicio = cantidad_teorica × (1 + porcentaje_desperdicio / 100)
cantidad_final          = math.ceil(cantidad_con_desperdicio)
```

El `porcentaje_desperdicio` se configura en `config.json` (por defecto 10%).

### Cálculo de mano de obra

La fórmula utilizada es:

```
mano_de_obra = area_superficie × costo_por_m²
```

El `costo_por_m²` se configura en `config.json` (`costo_mano_obra_m2`).
Este valor puede modificarse sin cambiar el código.

### Ejemplo de cotización
```
==========================================================
          RESUMEN DE COTIZACIÓN
==========================================================
  Cliente:            Juan Pérez
  Fecha:              28/08/2026 17:00

  Lambrín seleccionado:
    Lambrín Nogal Clásico
    Código: LAM-NOG-001
    Nogal - Natural

  Medidas de cada pieza:
    2.9 m × 0.15 m

  Orientación:        Vertical

  Superficie a cubrir:
    3.0 m × 2.5 m

----------------------------------------------------------
  Área de superficie: 7.50 m²
  Área por pieza:     0.4350 m²
  Desperdicio:        10%
  Cantidad calculada: 19 piezas
  Stock disponible:   50 piezas
----------------------------------------------------------
  Precio por pieza:   $    350.00
  Subtotal material:  $   6650.00

  ¿Mano de obra?      Sí
  Costo mano de obra: $   1350.00
    (7.50 m² × $180.00/m²)

----------------------------------------------------------
  TOTAL:              $   8000.00
==========================================================
```

### Eliminación de clientes

Desde el menú de clientes: **Opción 4 → Eliminar cliente**

Al eliminar un cliente:
- El cliente se borra de la base de datos.
- Las cotizaciones históricas se **conservan** con `cliente_id = NULL`.
- Los reportes muestran "Cliente eliminado" en lugar del nombre.

Esto se implementa mediante `ON DELETE SET NULL` en la FOREIGN KEY de la tabla `cotizaciones`.


## 📤 Exportación CSV

Desde el menú principal: **Opción 5 → Exportar inventario**

Genera `exports/inventario_lambrines.csv` con columnas:
ID, Código, Nombre, Tipo, Material, Acabado, Largo, Ancho, Espesor, Precio Unitario, Stock, Unidad, Fecha Ingreso, Fecha Actualización, Activo.

El archivo se puede abrir directamente en Excel (codificación UTF-8 BOM).

## 💾 Respaldos JSON

Desde el menú principal: **Opción 6 → Generar respaldo**

Genera `backups/respaldo_YYYYMMDD_HHMMSS.json` con:
- Todos los lambrines
- Todos los clientes
- Todas las cotizaciones con sus detalles

## 📝 Logging

Los eventos del sistema se registran en `logs/lambrinstock.log`:
- Inicio del sistema
- Creación, actualización y desactivación de productos
- Cotizaciones creadas y confirmadas
- Exportaciones y respaldos
- Errores importantes

## 🌿 Flujo Git

```bash
# 1. Inicializar
git init
git add .
git commit -m "Inicio del proyecto LAMBRINSTOCK"

# 2. Rama de inventario
git checkout -b feature/inventario
# ... modificar services/__init__.py (solo inventario)
git add .
git commit -m "feat: módulo de inventario completo"

# 3. Rama de cotizaciones (desde main)
git checkout main
git checkout -b feature/cotizaciones
# ... modificar services/__init__.py (solo cotizaciones)
git add .
git commit -m "feat: módulo de cotizaciones completo"

# 4. Merge inventario (sin conflicto)
git checkout main
git merge feature/inventario

# 5. Merge cotizaciones (CONFLICTO)
git merge feature/cotizaciones
# Resolver el conflicto en services/__init__.py
git add services/__init__.py
git commit -m "merge: resolver conflicto"

# 6. Rama de reportes
git checkout -b feature/reportes
git add .
git commit -m "feat: módulo de reportes"
git checkout main
git merge feature/reportes
```

## ⚠️ Conflicto documentado

Ver [CONFLICTOS.md](CONFLICTOS.md) para la documentación completa del conflicto Git:
- Ramas involucradas
- Archivo afectado
- Causa del conflicto
- Resolución paso a paso
- Comandos utilizados

## 🔮 Posibles mejoras futuras

- [ ] Interfaz gráfica con Tkinter o web con Flask
- [ ] Soporte para múltiples líneas de detalle por cotización
- [ ] Generación de PDF para cotizaciones
- [ ] Sistema de autenticación de usuarios
- [ ] Migración a MySQL/PostgreSQL
- [ ] API REST para integración con otros sistemas
- [ ] Módulo de proveedores
- [ ] Historial de cambios de precio
- [ ] Notificaciones de stock bajo por email
- [ ] Dashboard con gráficas de reportes

---

## 👤 Autor

Proyecto académico desarrollado como práctica de programación en Python con arquitectura en capas.

## 📄 Licencia

Proyecto académico. Uso educativo.
=======
# LambrinStock
Este repositorio es para el proyecto final del curso metaphorce, que se inlcuye como un proyecto que resuelve una problemática propia, acerca del uso de materiales de lambrin para poder hacer cotizaciones, inventariado y control del producto
>>>>>>> 2f0cadb84310102a7c44aaf7db085b4b9c4e782c
