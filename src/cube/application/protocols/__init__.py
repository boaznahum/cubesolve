"""
Application layer protocol definitions.

These protocols define interfaces that the application layer needs.
Presentation layer implements these protocols.
"""

from cube.application.protocols.AnimatableViewer import AnimatableViewer
from cube.application.protocols.EventLoop import EventLoop

__all__ = [
    "EventLoop",
    "AnimatableViewer",
]
