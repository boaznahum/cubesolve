# Lazy import to avoid loading pyglet in headless mode
def __getattr__(name):
    if name == "Window":
        from .Window import Window
        return Window
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["Window"]
