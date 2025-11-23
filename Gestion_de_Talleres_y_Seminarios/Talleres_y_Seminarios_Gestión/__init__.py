from __future__ import annotations
import logging
import pkgutil
from importlib import import_module
from typing import List

"""
Talleres_y_Seminarios_Gestión package initializer.

Provides:
- package metadata (__version__, __author__)
- automatic discovery of submodules in the package directory
- a convenience function `import_submodules()` to import all discovered submodules
- a package logger
"""



__all__: List[str] = [name for _, name, _ in pkgutil.iter_modules(__path__)]
__version__ = "0.1.0"
__author__ = "GitHub Copilot"

# Package logger
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def import_submodules() -> List[str]:
    """
    Import all top-level submodules found in this package directory.

    Returns a list of imported module names.
    """
    imported = []
    for name in __all__:
        full_name = f"{__name__}.{name}"
        try:
            import_module(full_name)
            imported.append(name)
        except Exception:
            logger.exception("Failed to import submodule %s", full_name)
    return imported