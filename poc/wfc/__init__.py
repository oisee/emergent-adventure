"""
Emergent Adventure POC - Bitwise WFC Engine

Procedural narrative generation for ZX Spectrum-style adventures.

Components:
- core.py: Bitwise WFC engine with reachability testing
- geography.py: 16-tile geography generator
- plot.py: Backward plot generation using Propp functions
- integration.py: Plot-geography integration
- test_harness.py: Batch testing and validation
"""

from .core import BitwiseWFC, WFCCell, popcount, check_reachability, find_path
from .geography import GeographyGenerator, TileType, TILE_CHARS
from .plot import (
    BackwardPlotGenerator, PlotGraph, PlotNode,
    ProppFunction, Requirement, Provides
)
from .integration import WorldGenerator, WorldState
from .engine import GameEngine, play_text_adventure

__all__ = [
    'BitwiseWFC', 'WFCCell', 'popcount', 'check_reachability', 'find_path',
    'GeographyGenerator', 'TileType', 'TILE_CHARS',
    'BackwardPlotGenerator', 'PlotGraph', 'PlotNode',
    'ProppFunction', 'Requirement', 'Provides',
    'WorldGenerator', 'WorldState',
    'GameEngine', 'play_text_adventure',
]
