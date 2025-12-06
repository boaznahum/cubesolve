# State Mechanism for Documentation Project

This folder contains Claude's internal state for the documentation project.
All files here are git-controlled to enable session continuity.

## Files

- `session-status.md` - Current status, what's done, what's in progress
- `insights.md` - Key learnings and understanding gained during research
- `task-queue.md` - Detailed task breakdown and progress
- `checksums.md` - Track file hashes to avoid repeating work on unchanged inputs

## Purpose

This mechanism ensures:
1. New Claude sessions can continue exactly where the previous left off
2. Work is not repeated if inputs haven't changed
3. All insights are preserved across sessions
4. Progress is always visible and trackable
