"""
NLP Command Processing

Handles player-NPC interaction through:
- Command types: suggest, convince, persuade, command, manipulate
- Willingness calculation
- Response generation
"""

from .commands import (
    CommandType,
    NPCCommand,
    parse_command,
)
from .processing import (
    NPCInteractionProcessor,
    InteractionResult,
)

__all__ = [
    'CommandType',
    'NPCCommand',
    'parse_command',
    'NPCInteractionProcessor',
    'InteractionResult',
]
