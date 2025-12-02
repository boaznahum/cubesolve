"""Registry for celebration effect types."""
from __future__ import annotations

from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from cube.presentation.gui.effects.CelebrationEffect import CelebrationEffect
    from cube.presentation.gui.protocols.Renderer import Renderer
    from cube.application.state import ApplicationAndViewState

# Factory function type: (renderer, vs, backend_name) -> CelebrationEffect
EffectFactory = Callable[["Renderer", "ApplicationAndViewState", str], "CelebrationEffect"]


class EffectRegistry:
    """Registry for celebration effect types.

    Similar to BackendRegistry, this provides a central place to register
    and retrieve celebration effects by name.

    Usage:
        # Register an effect
        EffectRegistry.register("confetti", lambda r, vs, b: ConfettiEffect(r, vs, b))

        # Get an effect instance
        effect = EffectRegistry.get_effect("confetti", renderer, vs, "pyglet2")
    """

    _effects: dict[str, EffectFactory] = {}
    _initialized: bool = False

    @classmethod
    def _ensure_initialized(cls) -> None:
        """Ensure default effects are registered."""
        if cls._initialized:
            return
        cls._initialized = True

        # Import and register default effects
        from cube.presentation.gui.effects.effects.NoneEffect import NoneEffect
        from cube.presentation.gui.effects.effects.ConfettiEffect import ConfettiEffect
        from cube.presentation.gui.effects.effects.VictorySpinEffect import VictorySpinEffect

        cls.register("none", lambda r, vs, b: NoneEffect(r, vs, b))
        cls.register("confetti", lambda r, vs, b: ConfettiEffect(r, vs, b))
        cls.register("victory_spin", lambda r, vs, b: VictorySpinEffect(r, vs, b))
        # TODO: Add sparkle, glow, combo effects

    @classmethod
    def register(cls, name: str, factory: EffectFactory) -> None:
        """Register an effect factory by name.

        Args:
            name: Unique name for the effect (e.g., "confetti", "glow").
            factory: Callable that creates an effect instance.
        """
        cls._effects[name] = factory

    @classmethod
    def get_effect(
        cls,
        name: str,
        renderer: "Renderer",
        vs: "ApplicationAndViewState",
        backend_name: str,
    ) -> "CelebrationEffect":
        """Create an effect instance by name.

        Args:
            name: Effect name to create.
            renderer: Renderer for drawing the effect.
            vs: Application state containing effect settings.
            backend_name: Current backend name for compatibility checking.

        Returns:
            An effect instance ready to use.

        Note:
            Falls back to "none" effect if the requested effect is not found.
        """
        cls._ensure_initialized()

        if name not in cls._effects:
            # Fallback to none effect
            name = "none"

        factory = cls._effects[name]
        effect = factory(renderer, vs, backend_name)

        # Check if effect is supported on this backend
        if not effect.is_supported(backend_name):
            # Fall back to none effect
            none_factory = cls._effects.get("none")
            if none_factory:
                return none_factory(renderer, vs, backend_name)

        return effect

    @classmethod
    def list_effects(cls) -> list[str]:
        """List all registered effect names.

        Returns:
            List of effect names that can be used with get_effect().
        """
        cls._ensure_initialized()
        return list(cls._effects.keys())

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Check if an effect is registered.

        Args:
            name: Effect name to check.

        Returns:
            True if the effect is registered.
        """
        cls._ensure_initialized()
        return name in cls._effects
