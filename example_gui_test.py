"""
Example: Simple GUI Test

This example demonstrates how to run automated GUI tests for the Rubik's Cube solver.
"""

from cube.tests.test_gui import run_gui_test, GUITestResult


def example_basic_test():
    """Example: Test scramble and solve on 3x3 cube."""
    print("Example 1: Basic scramble and solve test")
    print("-" * 50)

    # Run test: Scramble with key '1', solve with '/', quit with 'q'
    result = run_gui_test(
        key_sequence="1/q",
        timeout_sec=60.0,
        cube_size=3,
        enable_animation=False,
        debug=True
    )

    if result.success:
        print("\n[PASS] Test PASSED!")
        print(f"  {result.message}")
    else:
        print("\n[FAIL] Test FAILED!")
        print(f"  {result.message}")
        if result.error:
            print(f"  Error type: {type(result.error).__name__}")
            print(f"  Error details: {result.error}")

    return result


def example_multiple_operations():
    """Example: Test multiple scrambles and operations."""
    print("\n\nExample 2: Multiple operations test")
    print("-" * 50)

    # Run test: Multiple scrambles, then solve
    result = run_gui_test(
        key_sequence="123/q",  # Scramble 3 times, solve, quit
        timeout_sec=90.0,
        cube_size=3,
        enable_animation=False,
        debug=True
    )

    if result.success:
        print("\n[PASS] Test PASSED!")
    else:
        print("\n[FAIL] Test FAILED!")
        print(f"  Error: {result.error}")

    return result


def example_4x4_test():
    """Example: Test on 4x4 cube."""
    print("\n\nExample 3: Testing on 4x4 cube")
    print("-" * 50)

    result = run_gui_test(
        key_sequence="1/q",
        timeout_sec=120.0,  # 4x4 takes longer to solve
        cube_size=4,
        enable_animation=False,
        debug=True
    )

    if result.success:
        print("\n[PASS] Test PASSED!")
    else:
        print("\n[FAIL] Test FAILED!")
        print(f"  Error: {result.error}")

    return result


def example_with_animation():
    """Example: Test with animation enabled (slower but visual)."""
    print("\n\nExample 4: Test with animation enabled")
    print("-" * 50)
    print("Note: This will be slower but animations will run")

    result = run_gui_test(
        key_sequence="1/q",
        timeout_sec=120.0,  # Longer timeout for animations
        cube_size=3,
        enable_animation=True,  # Enable animations
        debug=True
    )

    if result.success:
        print("\n[PASS] Test PASSED!")
    else:
        print("\n[FAIL] Test FAILED!")
        print(f"  Error: {result.error}")

    return result


def example_custom_moves():
    """Example: Test custom move sequences."""
    print("\n\nExample 5: Custom move sequences")
    print("-" * 50)

    # Test a specific sequence of moves
    result = run_gui_test(
        key_sequence="rrrluuufq",  # R R R L U U U F, then quit
        timeout_sec=30.0,
        cube_size=3,
        enable_animation=False,
        debug=True
    )

    if result.success:
        print("\n[PASS] Test PASSED!")
    else:
        print("\n[FAIL] Test FAILED!")
        print(f"  Error: {result.error}")

    return result


def main():
    """Run a single example test."""
    print("=" * 70)
    print("GUI Testing Examples for Rubik's Cube Solver")
    print("=" * 70)
    print()
    print("These examples demonstrate automated GUI testing using keyboard sequences.")
    print("Each test injects keys into the GUI and verifies the application behavior.")
    print()
    print("NOTE: Due to pyglet limitations, only one test can run per process.")
    print("Run the file multiple times or call functions individually to test others.")
    print()

    # Run one example (due to pyglet event loop limitations)
    print("Running: Basic scramble and solve example")
    print("-" * 50)

    result = example_basic_test()

    # Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)

    status = "[PASS]" if result.success else "[FAIL]"
    print(f"{status} Basic scramble and solve")

    if result.success:
        print("\nExample completed successfully!")
        print("\nOther available examples (call individually):")
        print("  - example_basic_test()")
        print("  - example_multiple_operations()")
        print("  - example_4x4_test()")
        print("  - example_with_animation()")
        print("  - example_custom_moves()")
    else:
        print(f"\nExample failed: {result.error}")


if __name__ == "__main__":
    main()
