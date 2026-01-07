"""
NLP Commands

Defines command types for player-NPC interaction.

Command types with increasing coerciveness:
- suggest: Gentle hint (relies on NPC goodwill)
- convince: Logical argument (relies on evidence)
- persuade: Emotional appeal (relies on relationship)
- command: Direct order (relies on authority)
- manipulate: Deceptive coercion (relies on cunning)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from enum import IntEnum, auto


class CommandType(IntEnum):
    """Types of NPC commands with increasing coerciveness"""
    SUGGEST = 0      # Gentle, relies on goodwill
    CONVINCE = 1     # Logical, relies on evidence
    PERSUADE = 2     # Emotional, relies on relationship
    COMMAND = 3      # Direct, relies on authority
    MANIPULATE = 4   # Deceptive, relies on cunning


# Base success rates and modifiers for each command type
COMMAND_PROPERTIES = {
    CommandType.SUGGEST: {
        'base_success': 0.30,
        'trust_modifier': 0.4,      # How much trust helps
        'relationship_modifier': 0.3,
        'agreeableness_modifier': 0.3,  # Personality effect
        'intelligence_modifier': 0.0,
        'authority_modifier': 0.0,
        'detection_risk': 0.0,      # Risk of being caught manipulating
    },
    CommandType.CONVINCE: {
        'base_success': 0.40,
        'trust_modifier': 0.2,
        'relationship_modifier': 0.1,
        'agreeableness_modifier': 0.1,
        'intelligence_modifier': 0.3,  # Openness to reason
        'authority_modifier': 0.0,
        'detection_risk': 0.0,
    },
    CommandType.PERSUADE: {
        'base_success': 0.50,
        'trust_modifier': 0.3,
        'relationship_modifier': 0.5,
        'agreeableness_modifier': 0.2,
        'intelligence_modifier': 0.0,
        'authority_modifier': 0.0,
        'detection_risk': 0.0,
    },
    CommandType.COMMAND: {
        'base_success': 0.60,
        'trust_modifier': 0.1,
        'relationship_modifier': 0.1,
        'agreeableness_modifier': -0.2,  # Independent people resist
        'intelligence_modifier': 0.0,
        'authority_modifier': 0.5,
        'detection_risk': 0.0,
    },
    CommandType.MANIPULATE: {
        'base_success': 0.70,
        'trust_modifier': 0.3,
        'relationship_modifier': 0.2,
        'agreeableness_modifier': 0.2,
        'intelligence_modifier': -0.3,  # Smart people see through it
        'authority_modifier': 0.0,
        'detection_risk': 0.4,  # Risk of being caught
    },
}


@dataclass
class NPCCommand:
    """A parsed NPC command"""
    command_type: CommandType
    target_npc: str
    action: str
    conditions: List[str] = field(default_factory=list)  # "when X", "if Y"
    evidence: List[str] = field(default_factory=list)    # For convince
    emotional_appeal: str = ""                           # For persuade

    def get_base_success(self) -> float:
        """Get base success rate for this command type"""
        return COMMAND_PROPERTIES[self.command_type]['base_success']

    def get_properties(self) -> Dict[str, float]:
        """Get properties for this command type"""
        return COMMAND_PROPERTIES[self.command_type].copy()


def parse_command(text: str) -> Optional[NPCCommand]:
    """
    Parse player input into an NPC command.

    Examples:
    - "suggest elder help with quest"
    - "convince guard let me pass because I have the king's seal"
    - "persuade merchant give discount"
    - "command soldier attack enemy"
    - "talk to sage"

    Returns None if not a valid command.
    """
    text = text.strip().lower()
    words = text.split()

    if not words:
        return None

    # Determine command type
    command_word = words[0]
    command_type_map = {
        'suggest': CommandType.SUGGEST,
        'hint': CommandType.SUGGEST,
        'ask': CommandType.SUGGEST,
        'convince': CommandType.CONVINCE,
        'argue': CommandType.CONVINCE,
        'explain': CommandType.CONVINCE,
        'persuade': CommandType.PERSUADE,
        'plead': CommandType.PERSUADE,
        'beg': CommandType.PERSUADE,
        'command': CommandType.COMMAND,
        'order': CommandType.COMMAND,
        'demand': CommandType.COMMAND,
        'manipulate': CommandType.MANIPULATE,
        'trick': CommandType.MANIPULATE,
        'deceive': CommandType.MANIPULATE,
        'talk': CommandType.SUGGEST,  # Default talk is suggest
    }

    if command_word not in command_type_map:
        return None

    command_type = command_type_map[command_word]

    # Find target NPC (first word after command, or after "to")
    remaining = words[1:]
    target_npc = ""
    action_words = []

    i = 0
    while i < len(remaining):
        word = remaining[i]
        if word == "to" and i + 1 < len(remaining):
            i += 1
            target_npc = remaining[i]
        elif not target_npc and word not in ('to', 'that', 'the'):
            target_npc = word
        else:
            action_words.append(word)
        i += 1

    if not target_npc:
        return None

    action = ' '.join(action_words) if action_words else "interact"

    # Parse conditions ("when", "if", "because")
    conditions = []
    evidence = []
    emotional_appeal = ""

    full_text = ' '.join(words)

    if ' because ' in full_text:
        parts = full_text.split(' because ')
        if len(parts) > 1:
            evidence.append(parts[1])

    if ' when ' in full_text:
        parts = full_text.split(' when ')
        if len(parts) > 1:
            conditions.append(parts[1])

    if ' if ' in full_text:
        parts = full_text.split(' if ')
        if len(parts) > 1:
            conditions.append(parts[1])

    if ' please ' in full_text:
        emotional_appeal = "polite"

    return NPCCommand(
        command_type=command_type,
        target_npc=target_npc,
        action=action,
        conditions=conditions,
        evidence=evidence,
        emotional_appeal=emotional_appeal,
    )


# Response templates based on outcome
RESPONSE_TEMPLATES = {
    'agree': {
        'supportive': [
            "Of course, I'll help you with that.",
            "Consider it done.",
            "I'd be glad to assist.",
        ],
        'neutral': [
            "Very well.",
            "Fine, I'll do it.",
            "Alright.",
        ],
        'reluctant': [
            "I suppose I can do that...",
            "*sigh* If I must.",
            "This once, but don't expect it again.",
        ],
    },
    'refuse': {
        'polite': [
            "I'm afraid I cannot do that.",
            "I must respectfully decline.",
            "That's not something I can help with.",
        ],
        'firm': [
            "No.",
            "Absolutely not.",
            "I will not do that.",
        ],
        'hostile': [
            "How dare you ask me that!",
            "Get away from me.",
            "Don't ever ask me again.",
        ],
    },
    'hesitate': {
        'uncertain': [
            "I'm not sure...",
            "Let me think about it.",
            "That's a difficult request.",
        ],
        'conditional': [
            "Perhaps, if you could prove yourself first.",
            "I might, but I need something in return.",
            "Show me you can be trusted.",
        ],
    },
}


def get_response_template(outcome: str, mood: str) -> str:
    """Get a response template based on outcome and mood"""
    import random
    templates = RESPONSE_TEMPLATES.get(outcome, {}).get(mood, ["..."])
    return random.choice(templates)
