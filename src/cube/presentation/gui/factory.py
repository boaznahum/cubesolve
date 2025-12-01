# Re-exports for backward compatibility
from .GUIBackend import GUIBackend
from .BackendRegistry import BackendRegistry, _BackendEntry, register_backend

__all__ = [
    'GUIBackend',
    'BackendRegistry',
    '_BackendEntry',
    'register_backend',
]
