"""Lazy symbol imports for optional or heavyweight backend modules."""

from __future__ import annotations

from importlib import import_module
from threading import Lock
from typing import Any


class LazySymbol:
    """Resolve a symbol from a module only when it is first used.

    This keeps the Flask app importable even when optional heavyweight
    simulation dependencies are not installed yet.
    """

    def __init__(self, module_path: str, symbol_name: str):
        self.module_path = module_path
        self.symbol_name = symbol_name
        self._resolved: Any | None = None
        self._lock = Lock()

    def resolve(self) -> Any:
        if self._resolved is None:
            with self._lock:
                if self._resolved is None:
                    module = import_module(self.module_path)
                    self._resolved = getattr(module, self.symbol_name)
        return self._resolved

    def __call__(self, *args, **kwargs):
        return self.resolve()(*args, **kwargs)

    def __getattr__(self, item: str):
        return getattr(self.resolve(), item)

    def __repr__(self) -> str:
        return f"<LazySymbol {self.module_path}:{self.symbol_name}>"


def lazy_symbol(module_path: str, symbol_name: str) -> LazySymbol:
    return LazySymbol(module_path, symbol_name)
