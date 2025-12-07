"""Annotation type enumeration - Re-export from domain for backward compatibility."""

# AnnWhat has moved to domain layer.
# This re-export maintains backward compatibility.
from cube.domain.solver.AnnWhat import AnnWhat

__all__ = ['AnnWhat']
