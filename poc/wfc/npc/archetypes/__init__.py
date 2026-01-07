"""
Archetypes and Fractal Roles

Implements the fractal narrative concept from storygen-book:
- NPCs can have different roles at different narrative levels
- Hero at macro-level can be Opponent at meso-level
- Roles affect NPC behavior and responses
"""

from .fractal_roles import (
    FractalRole,
    NarrativeLevel,
    ActantRole,
    RoleTransition,
    FractalRoleSystem,
)

__all__ = [
    'FractalRole',
    'NarrativeLevel',
    'ActantRole',
    'RoleTransition',
    'FractalRoleSystem',
]
