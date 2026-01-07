"""
NPC Mind Module

Implements Belief-Desire-Intention (BDI) architecture with:
- Beliefs: Key-value pairs with confidence
- Desires: Goals with priorities
- Personality: Big Five traits + Archetypes
- Memory: Episodic memory with decay
- Relationships: Trust/fear/loyalty per target
"""

from .beliefs import Belief, BeliefSystem
from .desires import Desire, DesireSystem
from .personality import Personality, Archetype
from .memory import Memory, MemorySystem
from .relationships import Relationship, RelationshipSystem

# Import NPCMind last to avoid circular imports
from .npc_mind import NPCMind

__all__ = [
    'Belief',
    'BeliefSystem',
    'Desire',
    'DesireSystem',
    'Personality',
    'Archetype',
    'Memory',
    'MemorySystem',
    'Relationship',
    'RelationshipSystem',
    'NPCMind',
]
