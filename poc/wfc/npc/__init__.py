"""
NPC Mind System with ForthLisp Scripting

Features:
- ForthLisp VM for NPC behavior scripts
- Belief/Desire/Intention (BDI) architecture
- Personality traits (Big Five + Archetypes)
- Fractal roles (different behavior at narrative levels)
- NLP command processing for player-NPC interaction
"""

from .forthlisp import ForthLispVM, compile_script
from .mind import NPCMind, Belief, Desire, Personality
from .mind.personality import Archetype
from .archetypes import FractalRole, FractalRoleSystem, ActantRole
from .integration import PlotRoleIntegrator, PlotRoleAssignment

__all__ = [
    'ForthLispVM',
    'compile_script',
    'NPCMind',
    'Belief',
    'Desire',
    'Personality',
    'FractalRole',
    'FractalRoleSystem',
    'ActantRole',
    'Archetype',
    'PlotRoleIntegrator',
    'PlotRoleAssignment',
]
