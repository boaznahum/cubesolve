#!/usr/bin/env python3
"""
Algorithm Parser REPL - Interactive tool for testing cube algorithms.

Usage:
    python parse_alg.py [--size N]

Commands:
    <algorithm>     Parse and apply algorithm (e.g., "R U R' U'")
    reset           Reset cube to solved state
    scramble [n]    Apply random scramble (optional length n)
    size N          Change cube size to NxN
    undo            Undo last algorithm
    help            Show this help
    quit/exit       Exit the REPL

Examples:
    >>> R U R' U'
    >>> [1:2]M F [1:1]M' F'
    >>> scramble 20
    >>> size 5
"""

import sys
import argparse
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(__file__).replace("parse_alg.py", "src"))

try:
    from rich.console import Console
    from rich.prompt import Prompt
    _HAS_RICH = True
    console = Console()
except ImportError:
    _HAS_RICH = False
    console = None

from cube.application.AbstractApp import AbstractApp
from cube.domain.algs import Algs
from cube.domain.algs.Alg import Alg
from cube.utils.text_cube_viewer import print_cube, print_cube_with_info


class AlgRepl:
    """Interactive REPL for testing algorithms."""

    def __init__(self, cube_size: int = 3) -> None:
        self.cube_size = cube_size
        self.app: Optional[AbstractApp] = None
        self.history: list[Alg] = []
        self._create_cube()

    def _create_cube(self) -> None:
        """Create a new cube of the current size."""
        self.app = AbstractApp.create_non_default(
            cube_size=self.cube_size,
            animation=False
        )
        self.history = []

    def reset(self) -> None:
        """Reset the cube to solved state."""
        self._create_cube()
        self._print_status("Cube reset to solved state")

    def set_size(self, size: int) -> None:
        """Change cube size."""
        if size < 2 or size > 10:
            self._print_error("Size must be between 2 and 10")
            return
        self.cube_size = size
        self._create_cube()
        self._print_status(f"Cube size changed to {size}x{size}")

    def scramble(self, length: int = 20) -> None:
        """Apply a random scramble."""
        scramble = Algs.scramble(self.cube_size, seq_length=length)
        scramble.play(self.app.cube)
        self.history.append(scramble)
        self._print_status(f"Applied scramble ({length} moves)")
        self._print_alg(str(scramble.to_printable()))

    def undo(self) -> None:
        """Undo the last algorithm."""
        if not self.history:
            self._print_error("Nothing to undo")
            return
        last_alg = self.history.pop()
        last_alg.inv().play(self.app.cube)
        self._print_status("Undid last algorithm")

    def apply_alg(self, alg_str: str) -> None:
        """Parse and apply an algorithm."""
        try:
            alg = Algs.parse(alg_str)
            alg.play(self.app.cube)
            self.history.append(alg)
            self._print_status(f"Applied: {alg}")
        except Exception as e:
            self._print_error(f"Parse error: {e}")

    def show_help(self) -> None:
        """Show help message."""
        help_text = """
Commands:
  <algorithm>     Parse and apply algorithm (e.g., "R U R' U'")
  reset           Reset cube to solved state
  scramble [n]    Apply random scramble (optional length n)
  size N          Change cube size to NxN
  undo            Undo last algorithm
  help            Show this help
  quit/exit       Exit the REPL

Algorithm Examples:
  R U R' U'       Basic moves
  [1:2]M          Slice notation (for 4x4+)
  (R U R' U')2    Repeat 2 times
  [R U [1:1]M]    Nested sequences
"""
        if _HAS_RICH:
            console.print("[green]=== Help ===[/green]")
            console.print(help_text.strip())
        else:
            print("=== Help ===")
            print(help_text)

    def _print_status(self, message: str) -> None:
        """Print a status message."""
        if _HAS_RICH:
            console.print(f"[green]OK[/green] {message}")
        else:
            print(f"[OK] {message}")

    def _print_error(self, message: str) -> None:
        """Print an error message."""
        if _HAS_RICH:
            console.print(f"[red]ERROR[/red] {message}")
        else:
            print(f"[ERROR] {message}")

    def _print_alg(self, alg_str: str) -> None:
        """Print an algorithm string."""
        if _HAS_RICH:
            console.print(f"  [cyan]{alg_str}[/cyan]")
        else:
            print(f"  {alg_str}")

    def print_cube(self) -> None:
        """Print the current cube state."""
        print_cube_with_info(self.app.cube)

    def run(self) -> None:
        """Run the REPL loop."""
        if _HAS_RICH:
            console.print("[blue]=== Algorithm Parser REPL ===[/blue]")
            console.print(f"Cube Size: {self.cube_size}x{self.cube_size}")
            console.print("Type 'help' for commands, 'quit' to exit")
        else:
            print("=" * 40)
            print("Algorithm Parser REPL")
            print(f"Cube Size: {self.cube_size}x{self.cube_size}")
            print("Type 'help' for commands, 'quit' to exit")
            print("=" * 40)

        self.print_cube()

        while True:
            try:
                if _HAS_RICH:
                    user_input = Prompt.ask("\n[bold cyan]>>>[/bold cyan]")
                else:
                    user_input = input("\n>>> ").strip()

                if not user_input:
                    continue

                # Parse command
                parts = user_input.split()
                cmd = parts[0].lower()

                if cmd in ("quit", "exit", "q"):
                    if _HAS_RICH:
                        console.print("[yellow]Goodbye![/yellow]")
                    else:
                        print("Goodbye!")
                    break

                elif cmd == "reset":
                    self.reset()
                    self.print_cube()

                elif cmd == "help":
                    self.show_help()

                elif cmd == "undo":
                    self.undo()
                    self.print_cube()

                elif cmd == "size":
                    if len(parts) < 2:
                        self._print_error("Usage: size N")
                    else:
                        try:
                            self.set_size(int(parts[1]))
                            self.print_cube()
                        except ValueError:
                            self._print_error("Size must be a number")

                elif cmd == "scramble":
                    length = 20
                    if len(parts) > 1:
                        try:
                            length = int(parts[1])
                        except ValueError:
                            pass
                    self.scramble(length)
                    self.print_cube()

                elif cmd == "show":
                    self.print_cube()

                else:
                    # Treat as algorithm
                    self.apply_alg(user_input)
                    self.print_cube()

            except KeyboardInterrupt:
                print("\nUse 'quit' to exit")
            except EOFError:
                break


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Algorithm Parser REPL - Interactive cube algorithm testing"
    )
    parser.add_argument(
        "--size", "-s",
        type=int,
        default=3,
        help="Initial cube size (default: 3)"
    )
    parser.add_argument(
        "--alg", "-a",
        type=str,
        help="Apply algorithm and exit (non-interactive mode)"
    )

    args = parser.parse_args()

    repl = AlgRepl(cube_size=args.size)

    if args.alg:
        # Non-interactive mode
        repl.apply_alg(args.alg)
        repl.print_cube()
    else:
        # Interactive REPL
        repl.run()


if __name__ == "__main__":
    main()
