"""3x3 solver implementations.

This package contains all 3x3 cube solvers:
- beginner/ - Layer-by-layer (LBL) beginner method
- cfop/ - Fridrich method (CFOP: Cross, F2L, OLL, PLL)
- kociemba/ - Two-phase Kociemba algorithm (near-optimal)
- shared/ - Components shared between multiple 3x3 solvers

Layer: 3a
Can import: protocols/ (Layer 1), common/ (Layer 2)
Cannot import: reducers/ (Layer 3b), direct/ (Layer 3c)

Note: This package is named '_3x3' (with underscore) because Python
identifiers cannot start with a digit.
"""
