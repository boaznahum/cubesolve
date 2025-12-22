# Re-exports for convenience
from .BackendRegistry import BackendRegistry
from .GUIBackendFactory import GUIBackendFactory

# Backward compatibility alias
GUIBackend = GUIBackendFactory

__all__ = [
    'GUIBackendFactory',
    'GUIBackend',  # Alias for backward compatibility
    'BackendRegistry',
]
