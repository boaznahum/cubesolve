"""Solver statistics with typed topic registry.

Providers register and find their own topics by type-safe keys.
Each topic is a concrete class with its own data, merge, and display logic.

Usage:
    # Define keys (module-level constants)
    COMMUTATOR_KEY = TopicKey("Commutator", BlockSizeTopic)
    SLICE_SWAP_KEY = TopicKey("SliceSwap", SliceSwapTopic)

    # In solver:
    stats = SolverStatistics()
    stats.get_topic(COMMUTATOR_KEY).add_block(4)
    stats.get_topic(SLICE_SWAP_KEY).add_swap(grade=6, nn=6)

    # Merge from child:
    parent_stats.accumulate(child_stats, prefix="L1Centers")
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from cube.domain.solver.solver import ParityFix, SolverResults

T = TypeVar("T", bound="StatsTopic")


@dataclass(frozen=True)
class TopicKey(Generic[T]):
    """Type-safe key for a statistics topic.

    Generic parameter T is the concrete topic type, so
    ``stats.get_topic(key)`` returns ``T`` (not ``StatsTopic``).
    """
    name: str
    _topic_type: type[T]

    def __repr__(self) -> str:
        return f"TopicKey({self.name!r})"


class StatsTopic(ABC):
    """Abstract base for statistics topics.

    Each concrete topic defines its own data, merge, and display logic.
    """

    @abstractmethod
    def merge(self, other: StatsTopic) -> None:
        """Merge another topic (same type) into this one."""
        ...

    @abstractmethod
    def format_lines(self) -> list[str]:
        """Format topic data for display. Returns list of display lines."""
        ...

    @abstractmethod
    def is_empty(self) -> bool:
        """True if no data has been recorded."""
        ...

    @abstractmethod
    def reset(self) -> None:
        """Clear all data."""
        ...


class BlockSizeTopic(StatsTopic):
    """Tracks block sizes solved: block_size -> count."""

    def __init__(self) -> None:
        self._sizes: dict[int, int] = {}

    def add_block(self, block_size: int) -> None:
        """Record that a block of given size was solved."""
        self._sizes[block_size] = self._sizes.get(block_size, 0) + 1

    def merge(self, other: StatsTopic) -> None:
        assert isinstance(other, BlockSizeTopic)
        for size, count in other._sizes.items():
            self._sizes[size] = self._sizes.get(size, 0) + count

    def format_lines(self) -> list[str]:
        if not self._sizes:
            return ["(no blocks)"]
        parts: list[str] = [f"{size}x1:{count}" for size, count in sorted(self._sizes.items())]
        total: int = sum(self._sizes.values())
        pieces: int = sum(size * count for size, count in self._sizes.items())
        return [f"{', '.join(parts)} (total: {total} blocks, {pieces} pieces)"]

    def is_empty(self) -> bool:
        return not self._sizes

    def reset(self) -> None:
        self._sizes.clear()

    @property
    def total_blocks(self) -> int:
        return sum(self._sizes.values())

    @property
    def total_pieces(self) -> int:
        return sum(size * count for size, count in self._sizes.items())


class SliceSwapTopic(StatsTopic):
    """Tracks complete slice swap statistics with grade improvements."""

    def __init__(self) -> None:
        self._swap_count: int = 0
        self._total_grade: int = 0
        self._total_pieces: int = 0
        self._grade_histogram: dict[int, int] = {}  # grade -> count

    def add_swap(self, grade: int, nn: int) -> None:
        """Record a slice swap with its grade improvement and slice width."""
        self._swap_count += 1
        self._total_grade += grade
        self._total_pieces += nn
        self._grade_histogram[grade] = self._grade_histogram.get(grade, 0) + 1

    def merge(self, other: StatsTopic) -> None:
        assert isinstance(other, SliceSwapTopic)
        self._swap_count += other._swap_count
        self._total_grade += other._total_grade
        self._total_pieces += other._total_pieces
        for grade, count in other._grade_histogram.items():
            self._grade_histogram[grade] = self._grade_histogram.get(grade, 0) + count

    def format_lines(self) -> list[str]:
        if self._swap_count == 0:
            return ["(no swaps)"]
        avg: float = self._total_grade / self._swap_count
        grades: list[str] = [f"grade:{g}#{c}" for g, c in sorted(self._grade_histogram.items())]
        return [f"{self._swap_count} swaps, {self._total_pieces} pieces, "
                f"avg grade {avg:.1f}, [{', '.join(grades)}]"]

    def is_empty(self) -> bool:
        return self._swap_count == 0

    def reset(self) -> None:
        self._swap_count = 0
        self._total_grade = 0
        self._total_pieces = 0
        self._grade_histogram.clear()

    @property
    def swap_count(self) -> int:
        return self._swap_count

    @property
    def total_grade(self) -> int:
        return self._total_grade


class MoveCountTopic(StatsTopic):
    """Tracks raw and optimized move counts for a solver."""

    def __init__(self) -> None:
        self._move_count: int = 0
        self._optimized_count: int = 0

    def set_counts(self, raw: int, optimized: int) -> None:
        """Set both raw and optimized move counts."""
        self._move_count = raw
        self._optimized_count = optimized

    def merge(self, other: StatsTopic) -> None:
        assert isinstance(other, MoveCountTopic)
        self._move_count += other._move_count
        self._optimized_count += other._optimized_count

    def format_lines(self) -> list[str]:
        if self._move_count == self._optimized_count:
            return [f"Moves: {self._move_count}"]
        return [f"Moves: {self._optimized_count} optimized ({self._move_count} non-optimized)"]

    def is_empty(self) -> bool:
        return self._move_count == 0

    def reset(self) -> None:
        self._move_count = 0
        self._optimized_count = 0


class ParityTopic(StatsTopic):
    """Tracks parity flags detected during solving."""

    def __init__(self) -> None:
        from cube.domain.solver.solver import ParityFix
        self._ParityFix = ParityFix  # keep reference for merge/format
        self._edge_parity: ParityFix | None = None
        self._corner_swap: ParityFix | None = None
        self._partial_edge: ParityFix | None = None

    def set_from_results(self, sr: "SolverResults") -> None:
        """Copy parity flags from SolverResults."""
        self._edge_parity = sr.was_even_edge_parity
        self._corner_swap = sr.was_corner_swap
        self._partial_edge = sr.was_partial_edge_parity

    def merge(self, other: StatsTopic) -> None:
        assert isinstance(other, ParityTopic)
        # Keep non-None (if either detected parity, record it)
        if other._edge_parity is not None:
            self._edge_parity = other._edge_parity
        if other._corner_swap is not None:
            self._corner_swap = other._corner_swap
        if other._partial_edge is not None:
            self._partial_edge = other._partial_edge

    @staticmethod
    def _fmt(name: str, fix: "ParityFix | None") -> str | None:
        if fix is None:
            return None
        suffix = " [Advanced]" if fix.advanced else " [non-Advanced]"
        return name + suffix

    def format_lines(self) -> list[str]:
        parities: list[str] = []
        for name, fix in [
            ("Even Edge(OLL)", self._edge_parity),
            ("Corner(PLL)", self._corner_swap),
            ("Partial Edge", self._partial_edge),
        ]:
            s = self._fmt(name, fix)
            if s:
                parities.append(s)
        if parities:
            return ["Parity: " + ", ".join(parities)]
        return ["Parity: None"]

    def is_empty(self) -> bool:
        return (self._edge_parity is None and
                self._corner_swap is None and
                self._partial_edge is None)

    def reset(self) -> None:
        self._edge_parity = None
        self._corner_swap = None
        self._partial_edge = None


class SolverStatistics:
    """Container for typed statistics topics.

    Topics are created on first access via their key's factory type.
    Providers can add unique topics that only they know about.
    """

    def __init__(self) -> None:
        self._topics: dict[str, StatsTopic] = {}

    def get_topic(self, key: TopicKey[T]) -> T:
        """Get or create a topic by key. Type-safe: returns T."""
        topic: StatsTopic | None = self._topics.get(key.name)
        if topic is None:
            topic = key._topic_type()
            self._topics[key.name] = topic
        return topic  # type: ignore[return-value]

    def accumulate(self, other: SolverStatistics, topic_prefix: str | None = None) -> None:
        """Merge all topics from other into this container.

        Args:
            other: Statistics to merge in.
            topic_prefix: If given, prepend to each topic name (e.g. "L1Centers").
        """
        for name, topic in other._topics.items():
            full_name: str = f"{topic_prefix}:{name}" if topic_prefix else name
            existing: StatsTopic | None = self._topics.get(full_name)
            if existing is None:
                new_topic: StatsTopic = type(topic)()
                new_topic.merge(topic)
                self._topics[full_name] = new_topic
            else:
                existing.merge(topic)

    def is_empty(self) -> bool:
        """True if no topics or all topics are empty."""
        return not self._topics or all(t.is_empty() for t in self._topics.values())

    def reset(self) -> None:
        """Clear all topics."""
        self._topics.clear()

    def get_all_topics(self) -> list[str]:
        """Get all topic names (in insertion order)."""
        return list(self._topics.keys())

    def format_all(self, strip_prefix: str = "") -> list[tuple[str, list[str]]]:
        """Format all topics for display.

        Returns list of (topic_name, lines) tuples.
        """
        result: list[tuple[str, list[str]]] = []
        for name, topic in self._topics.items():
            display_name: str = name.replace(strip_prefix, "") if strip_prefix else name
            result.append((display_name, topic.format_lines()))
        return result
