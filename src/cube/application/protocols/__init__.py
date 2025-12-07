"""
Application layer protocol definitions.

These protocols define interfaces that the application layer needs.
Presentation layer implements these protocols.
"""

from cube.application.protocols.EventLoop import EventLoop
from cube.application.protocols.AnimatableViewer import AnimatableViewer

__all__ = [
    "EventLoop",
    "AnimatableViewer",
]
