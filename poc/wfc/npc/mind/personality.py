"""
Personality System

Personality combines:
- Big Five traits (OCEAN)
- Jungian/Campbell archetypes
- Behavioral modifiers
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import IntEnum, auto
import random


class Archetype(IntEnum):
    """12 Jungian archetypes + shadow aspects"""
    # Ego types (order)
    HERO = 0
    MAGICIAN = 1
    RULER = 2

    # Soul types (freedom)
    EXPLORER = 3
    SAGE = 4
    INNOCENT = 5

    # Self types (social)
    LOVER = 6
    JESTER = 7
    EVERYMAN = 8

    # Order types (legacy)
    CAREGIVER = 9
    CREATOR = 10
    REBEL = 11


# Shadow aspects of each archetype
ARCHETYPE_SHADOWS = {
    Archetype.HERO: "Tyrant",
    Archetype.MAGICIAN: "Manipulator",
    Archetype.RULER: "Despot",
    Archetype.EXPLORER: "Wanderer",
    Archetype.SAGE: "Hermit",
    Archetype.INNOCENT: "Naive",
    Archetype.LOVER: "Obsessive",
    Archetype.JESTER: "Fool",
    Archetype.EVERYMAN: "Conformist",
    Archetype.CAREGIVER: "Martyr",
    Archetype.CREATOR: "Perfectionist",
    Archetype.REBEL: "Anarchist",
}

# Archetype behavioral tendencies
ARCHETYPE_TRAITS = {
    Archetype.HERO: {
        'courage': 0.8, 'self_sacrifice': 0.7, 'arrogance': 0.4,
        'trust_threshold': 0.3, 'action_preference': 'fight',
    },
    Archetype.MAGICIAN: {
        'wisdom': 0.8, 'manipulation': 0.5, 'detachment': 0.6,
        'trust_threshold': 0.5, 'action_preference': 'transform',
    },
    Archetype.RULER: {
        'authority': 0.9, 'responsibility': 0.7, 'control': 0.8,
        'trust_threshold': 0.6, 'action_preference': 'command',
    },
    Archetype.EXPLORER: {
        'curiosity': 0.9, 'restlessness': 0.7, 'commitment': 0.3,
        'trust_threshold': 0.4, 'action_preference': 'explore',
    },
    Archetype.SAGE: {
        'wisdom': 0.9, 'patience': 0.8, 'connection': 0.3,
        'trust_threshold': 0.5, 'action_preference': 'advise',
    },
    Archetype.INNOCENT: {
        'optimism': 0.9, 'faith': 0.8, 'denial': 0.5,
        'trust_threshold': 0.2, 'action_preference': 'hope',
    },
    Archetype.LOVER: {
        'passion': 0.9, 'empathy': 0.8, 'jealousy': 0.5,
        'trust_threshold': 0.3, 'action_preference': 'connect',
    },
    Archetype.JESTER: {
        'humor': 0.9, 'irreverence': 0.7, 'responsibility': 0.3,
        'trust_threshold': 0.3, 'action_preference': 'lighten',
    },
    Archetype.EVERYMAN: {
        'relatability': 0.9, 'loyalty': 0.7, 'ambition': 0.3,
        'trust_threshold': 0.4, 'action_preference': 'belong',
    },
    Archetype.CAREGIVER: {
        'nurturing': 0.9, 'self_sacrifice': 0.8, 'boundaries': 0.3,
        'trust_threshold': 0.2, 'action_preference': 'help',
    },
    Archetype.CREATOR: {
        'creativity': 0.9, 'vision': 0.8, 'perfectionism': 0.6,
        'trust_threshold': 0.5, 'action_preference': 'create',
    },
    Archetype.REBEL: {
        'independence': 0.9, 'disruption': 0.7, 'destruction': 0.5,
        'trust_threshold': 0.7, 'action_preference': 'rebel',
    },
}


@dataclass
class Personality:
    """
    NPC Personality combining Big Five and Archetypes.

    Big Five (OCEAN):
    - Openness: curiosity, creativity, preference for variety
    - Conscientiousness: organization, dependability, self-discipline
    - Extraversion: energy, assertiveness, sociability
    - Agreeableness: cooperation, trust, altruism
    - Neuroticism: emotional instability, anxiety, moodiness
    """

    # Big Five traits (0.0 - 1.0)
    openness: float = 0.5
    conscientiousness: float = 0.5
    extraversion: float = 0.5
    agreeableness: float = 0.5
    neuroticism: float = 0.5

    # Archetype
    primary_archetype: Archetype = Archetype.EVERYMAN
    shadow_archetype: Optional[str] = None  # From ARCHETYPE_SHADOWS
    shadow_strength: float = 0.0  # How much shadow influences (0-1)

    # Name for display
    name: str = ""

    def __post_init__(self):
        if self.shadow_archetype is None:
            self.shadow_archetype = ARCHETYPE_SHADOWS.get(self.primary_archetype, "Unknown")

    @classmethod
    def random(cls, archetype: Archetype = None) -> 'Personality':
        """Generate random personality"""
        if archetype is None:
            archetype = random.choice(list(Archetype))

        # Generate Big Five with archetype influence
        traits = ARCHETYPE_TRAITS.get(archetype, {})

        # Base random with archetype tendencies
        openness = random.gauss(0.5, 0.15)
        conscientiousness = random.gauss(0.5, 0.15)
        extraversion = random.gauss(0.5, 0.15)
        agreeableness = random.gauss(0.5, 0.15)
        neuroticism = random.gauss(0.5, 0.15)

        # Adjust based on archetype
        if archetype == Archetype.EXPLORER:
            openness += 0.2
        elif archetype == Archetype.RULER:
            conscientiousness += 0.2
            extraversion += 0.1
        elif archetype == Archetype.SAGE:
            openness += 0.1
            conscientiousness += 0.1
            extraversion -= 0.2
        elif archetype == Archetype.CAREGIVER:
            agreeableness += 0.3
        elif archetype == Archetype.REBEL:
            agreeableness -= 0.2
            openness += 0.1
        elif archetype == Archetype.INNOCENT:
            neuroticism -= 0.2
            agreeableness += 0.2

        # Clamp to 0-1
        def clamp(x): return max(0.0, min(1.0, x))

        return cls(
            openness=clamp(openness),
            conscientiousness=clamp(conscientiousness),
            extraversion=clamp(extraversion),
            agreeableness=clamp(agreeableness),
            neuroticism=clamp(neuroticism),
            primary_archetype=archetype,
            shadow_strength=random.uniform(0.1, 0.4),
        )

    def get_trust_threshold(self) -> float:
        """Get trust threshold for accepting requests"""
        base = ARCHETYPE_TRAITS.get(self.primary_archetype, {}).get('trust_threshold', 0.5)
        # Agreeableness lowers threshold
        base -= (self.agreeableness - 0.5) * 0.3
        # Neuroticism raises threshold
        base += (self.neuroticism - 0.5) * 0.2
        return max(0.0, min(1.0, base))

    def modify_willingness(self, base_willingness: float,
                           request_type: str = None,
                           requester_known: bool = False) -> float:
        """
        Modify willingness based on personality.

        Returns modified willingness score.
        """
        score = base_willingness

        # Agreeableness increases willingness
        score += (self.agreeableness - 0.5) * 0.3

        # High conscientiousness makes them more reliable but cautious
        if self.conscientiousness > 0.7:
            score += 0.1 if requester_known else -0.1

        # High extraversion increases for social requests
        if self.extraversion > 0.6:
            score += 0.1

        # High neuroticism decreases willingness (fear of failure)
        if self.neuroticism > 0.6:
            score -= 0.15

        # Openness increases for new/unusual requests
        if self.openness > 0.7 and request_type == 'unusual':
            score += 0.15

        # Shadow influence can increase negative behaviors
        if self.shadow_strength > 0.5:
            # Shadow makes them more self-serving
            score -= 0.1

        return max(0.0, min(1.0, score))

    def get_speech_style(self) -> Dict[str, Any]:
        """Get speech style modifiers based on personality"""
        style = {
            'verbosity': self.extraversion,
            'formality': self.conscientiousness,
            'warmth': self.agreeableness,
            'emotionality': self.neuroticism,
            'creativity': self.openness,
        }

        # Archetype influences
        if self.primary_archetype == Archetype.SAGE:
            style['verbosity'] += 0.2
            style['formality'] += 0.1
        elif self.primary_archetype == Archetype.JESTER:
            style['humor'] = 0.8
        elif self.primary_archetype == Archetype.RULER:
            style['formality'] += 0.3
            style['authority'] = 0.7
        elif self.primary_archetype == Archetype.REBEL:
            style['formality'] -= 0.3
            style['defiance'] = 0.6

        return style

    def get_archetype_action(self) -> str:
        """Get preferred action type based on archetype"""
        return ARCHETYPE_TRAITS.get(self.primary_archetype, {}).get('action_preference', 'wait')

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            'openness': self.openness,
            'conscientiousness': self.conscientiousness,
            'extraversion': self.extraversion,
            'agreeableness': self.agreeableness,
            'neuroticism': self.neuroticism,
            'primary_archetype': self.primary_archetype.name,
            'shadow_archetype': self.shadow_archetype,
            'shadow_strength': self.shadow_strength,
            'name': self.name,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Personality':
        """Deserialize from dictionary"""
        return cls(
            openness=data['openness'],
            conscientiousness=data['conscientiousness'],
            extraversion=data['extraversion'],
            agreeableness=data['agreeableness'],
            neuroticism=data['neuroticism'],
            primary_archetype=Archetype[data['primary_archetype']],
            shadow_archetype=data.get('shadow_archetype'),
            shadow_strength=data.get('shadow_strength', 0.0),
            name=data.get('name', ''),
        )

    def describe(self) -> str:
        """Get human-readable description"""
        traits = []

        if self.openness > 0.7:
            traits.append("curious and creative")
        elif self.openness < 0.3:
            traits.append("traditional")

        if self.conscientiousness > 0.7:
            traits.append("organized and reliable")
        elif self.conscientiousness < 0.3:
            traits.append("spontaneous")

        if self.extraversion > 0.7:
            traits.append("outgoing")
        elif self.extraversion < 0.3:
            traits.append("reserved")

        if self.agreeableness > 0.7:
            traits.append("kind and cooperative")
        elif self.agreeableness < 0.3:
            traits.append("competitive")

        if self.neuroticism > 0.7:
            traits.append("anxious")
        elif self.neuroticism < 0.3:
            traits.append("calm")

        archetype_desc = self.primary_archetype.name.title()

        if not traits:
            return f"A balanced {archetype_desc}"

        return f"A {', '.join(traits)} {archetype_desc}"
