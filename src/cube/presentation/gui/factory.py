# Re-exports for convenience
from .GUIBackendFactory import GUIBackendFactory
from .BackendRegistry import BackendRegistry

# Backward compatibility alias
GUIBackend = GUIBackendFactory

__all__ = [
    'GUIBackendFactory',
    'GUIBackend',  # Alias for backward compatibility
    'BackendRegistry',
]
