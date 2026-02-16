"""Accumulated block solving statistics with topic tracking.

Tracks block sizes solved (1x1, 2x1, 3x1, etc.) per topic/solver.
Topics identify which solver/helper contributed the statistics.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BlockStatistics:
    """Accumulated block solving statistics with topic tracking.

    Tracks block sizes solved (1x1, 2x1, 3x1, etc.) per topic/solver.
    Topics identify which solver/helper contributed the statistics.

    Example:
        stats = BlockStatistics()
        stats.add_block(topic="L1Centers", block_size=3)
        stats.add_block(topic="L2Centers", block_size=1)
        stats.accumulate(other_stats)  # Merge another BlockStatistics
    """

    # topic -> {block_size -> count}
    _stats_by_topic: dict[str, dict[int, int]] = field(default_factory=dict)

    def add_block(self, topic: str, block_size: int) -> None:
        """Record that a block of given size was solved by given topic."""
        if topic not in self._stats_by_topic:
            self._stats_by_topic[topic] = {}
        topic_stats = self._stats_by_topic[topic]
        topic_stats[block_size] = topic_stats.get(block_size, 0) + 1

    def accumulate(self, other: BlockStatistics) -> None:
        """Merge another BlockStatistics into this one."""
        for topic, sizes in other._stats_by_topic.items():
            if topic not in self._stats_by_topic:
                self._stats_by_topic[topic] = {}
            for size, count in sizes.items():
                self._stats_by_topic[topic][size] = \
                    self._stats_by_topic[topic].get(size, 0) + count

    def get_topic_stats(self, topic: str) -> dict[int, int]:
        """Get statistics for a specific topic (block_size -> count)."""
        return self._stats_by_topic.get(topic, {}).copy()

    def get_all_topics(self) -> list[str]:
        """Get all topic names that have statistics."""
        return list(self._stats_by_topic.keys())

    def get_summary_stats(self) -> dict[int, int]:
        """Get aggregated statistics across all topics (block_size -> count)."""
        summary: dict[int, int] = {}
        for topic_stats in self._stats_by_topic.values():
            for size, count in topic_stats.items():
                summary[size] = summary.get(size, 0) + count
        return summary

    def is_empty(self) -> bool:
        """Check if any statistics have been recorded."""
        return not self._stats_by_topic

    def reset(self) -> None:
        """Clear all statistics."""
        self._stats_by_topic.clear()
