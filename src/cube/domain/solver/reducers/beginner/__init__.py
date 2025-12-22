"""Beginner reducer - standard NxN to 3x3 reduction.

This package contains the beginner reduction method for NxN cubes:
- BeginnerReducer - Standard reduction using center solving + edge pairing

Layer: 3b
Can import: protocols/ (Layer 1), common/ (Layer 2), common/big_cube/
Cannot import: 3x3/ (Layer 3a), direct/ (Layer 3c)
"""

from cube.domain.solver.reducers.beginner.BeginnerReducer import BeginnerReducer

__all__ = ["BeginnerReducer"]
