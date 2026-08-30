# LAMBRINSTOCK - Documentación de Conflicto Git

## Información del Conflicto

Este documento describe el conflicto de Git provocado intencionalmente como parte de los requisitos del proyecto, y cómo fue resuelto.

---

## 1. Ramas que participaron

- `feature/inventario`: Rama donde se desarrolló el módulo de gestión de inventario.
- `feature/cotizaciones`: Rama donde se desarrolló el módulo de cotizaciones.

Ambas ramas fueron creadas desde `main` de forma independiente.

## 2. Archivo que produjo el conflicto

**`services/__init__.py`**

Este archivo es el punto de entrada del paquete de servicios y contiene los imports de los módulos que expone.

## 3. Por qué ocurrió el conflicto

Ambas ramas modificaron el archivo `services/__init__.py` en las mismas líneas, cada una agregando imports diferentes:

- `feature/inventario` agregó:
  ```python
  from .inventario_service import InventarioService
  ```
  
- `feature/cotizaciones` agregó:
  ```python
  from .cotizacion_service import CotizacionService
  ```

Git no puede determinar automáticamente cómo combinar ambos cambios porque ocurrieron en las mismas líneas del archivo.

## 4. Contenido en conflicto

Al intentar hacer merge, Git marcó el archivo así:

```
<<<<<<< HEAD
"""Paquete de servicios (reglas de negocio) para LAMBRINSTOCK."""

from .inventario_service import InventarioService

__all__ = ["InventarioService"]
=======
"""Paquete de servicios (reglas de negocio) para LAMBRINSTOCK."""

from .cotizacion_service import CotizacionService

__all__ = ["CotizacionService"]
>>>>>>> feature/cotizaciones
```

## 5. Cómo se resolvió

Se combinaron manualmente ambos cambios, incluyendo los imports de ambas ramas:

```python
"""Paquete de servicios (reglas de negocio) para LAMBRINSTOCK."""

from .inventario_service import InventarioService
from .cotizacion_service import CotizacionService

__all__ = ["InventarioService", "CotizacionService"]
```

## 6. Verificación posterior

Después de resolver el conflicto, se verificó:

1. **Importación correcta**: Se verificó que ambos servicios se importan sin error.
2. **Ejecución del sistema**: Se ejecutó `python main.py` para confirmar que el sistema inicia correctamente.
3. **Pruebas automatizadas**: Se ejecutaron las pruebas con `python -m pytest tests/ -v` para confirmar que todas pasan.

## 7. Comandos Git utilizados

```bash
# Desde main, después de haber mergeado feature/inventario exitosamente:
git merge feature/cotizaciones

# Git reportó conflicto en services/__init__.py
# Se editó el archivo manualmente para combinar ambos cambios

# Después de resolver:
git add services/__init__.py
git commit -m "merge: resolver conflicto entre inventario y cotizaciones en services/__init__.py"
```

---

## Instrucciones para reproducir el conflicto

Si el conflicto no fue ejecutado automáticamente, siga estos pasos exactos:

### Paso 1: Inicializar el repositorio
```bash
cd lambrinstock
git init
git add .
git commit -m "Inicio del proyecto LAMBRINSTOCK - estructura base"
```

### Paso 2: Crear feature/inventario
```bash
git checkout -b feature/inventario
```

Modifique `services/__init__.py` para que contenga SOLAMENTE:
```python
"""Paquete de servicios (reglas de negocio) para LAMBRINSTOCK."""

from .inventario_service import InventarioService

__all__ = ["InventarioService"]
```

```bash
git add services/__init__.py
git commit -m "feat: módulo de inventario - servicio de inventario"
```

### Paso 3: Crear feature/cotizaciones (desde main)
```bash
git checkout main
git checkout -b feature/cotizaciones
```

Modifique `services/__init__.py` para que contenga SOLAMENTE:
```python
"""Paquete de servicios (reglas de negocio) para LAMBRINSTOCK."""

from .cotizacion_service import CotizacionService

__all__ = ["CotizacionService"]
```

```bash
git add services/__init__.py
git commit -m "feat: módulo de cotizaciones - servicio de cotización"
```

### Paso 4: Merge sin conflicto
```bash
git checkout main
git merge feature/inventario
# Merge exitoso, sin conflicto
```

### Paso 5: Provocar el conflicto
```bash
git merge feature/cotizaciones
# CONFLICTO en services/__init__.py
```

### Paso 6: Resolver el conflicto
Edite `services/__init__.py` y combine ambos contenidos:
```python
"""Paquete de servicios (reglas de negocio) para LAMBRINSTOCK."""

from .inventario_service import InventarioService
from .cotizacion_service import CotizacionService
from .reporte_service import ReporteService

__all__ = ["InventarioService", "CotizacionService", "ReporteService"]
```

```bash
git add services/__init__.py
git commit -m "merge: resolver conflicto entre inventario y cotizaciones en services/__init__.py"
```

### Paso 7: Crear y merge feature/reportes
```bash
git checkout -b feature/reportes
git add .
git commit -m "feat: módulo de reportes completo"
git checkout main
git merge feature/reportes
```

### Paso 8: Verificar
```bash
python main.py
python -m pytest tests/ -v
```
