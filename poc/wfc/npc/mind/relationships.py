"""
Relationship System

Tracks relationships between NPC and others:
- Trust: How much they trust the target
- Fear: How afraid they are of the target
- Loyalty: How loyal they are to the target
- History: Past interactions
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from enum import IntEnum, auto


class RelationshipType(IntEnum):
    """Type of relationship"""
    STRANGER = 0      # Never met
    ACQUAINTANCE = 1  # Met briefly
    FRIEND = 2        # Positive relationship
    ALLY = 3          # Working together
    RIVAL = 4         # Competitive
    ENEMY = 5         # Hostile
    FAMILY = 6        # Family bond
    MASTER = 7        # They are above (authority)
    SERVANT = 8       # They are below


@dataclass
class Relationship:
    """Relationship with a specific target"""
    target: str
    relationship_type: RelationshipType = RelationshipType.STRANGER

    # Core metrics (-1.0 to 1.0 for trust, 0.0 to 1.0 for others)
    trust: float = 0.0       # -1.0 (distrust) to 1.0 (full trust)
    fear: float = 0.0        # 0.0 (no fear) to 1.0 (terrified)
    loyalty: float = 0.0     # 0.0 (no loyalty) to 1.0 (absolute)
    respect: float = 0.5     # 0.0 (no respect) to 1.0 (high respect)

    # History
    interactions: int = 0
    positive_interactions: int = 0
    negative_interactions: int = 0

    def modify_trust(self, amount: float):
        """Modify trust level"""
        self.trust = max(-1.0, min(1.0, self.trust + amount))

    def modify_fear(self, amount: float):
        """Modify fear level"""
        self.fear = max(0.0, min(1.0, self.fear + amount))

    def modify_loyalty(self, amount: float):
        """Modify loyalty level"""
        self.loyalty = max(0.0, min(1.0, self.loyalty + amount))

    def record_interaction(self, positive: bool):
        """Record an interaction"""
        self.interactions += 1
        if positive:
            self.positive_interactions += 1
            self.modify_trust(0.05)
        else:
            self.negative_interactions += 1
            self.modify_trust(-0.08)

    def get_disposition(self) -> float:
        """Get overall disposition toward target"""
        # Combine trust, fear (negative), and loyalty
        return self.trust * 0.5 + self.loyalty * 0.3 - self.fear * 0.2 + self.respect * 0.1

    def is_positive(self) -> bool:
        """Check if relationship is overall positive"""
        return self.get_disposition() > 0.2

    def is_negative(self) -> bool:
        """Check if relationship is overall negative"""
        return self.get_disposition() < -0.2

    def can_request(self, difficulty: float = 0.5) -> bool:
        """Check if target can make requests of NPC"""
        # Need sufficient trust and/or respect to make requests
        threshold = difficulty * 0.5
        return self.trust > threshold or self.respect > threshold or self.fear > 0.5


class RelationshipSystem:
    """
    Manages all relationships for an NPC.

    Features:
    - Target-based lookup
    - Trust/fear/loyalty tracking
    - Interaction history
    - Disposition calculation
    """

    def __init__(self):
        self.relationships: Dict[str, Relationship] = {}

    def get(self, target: str) -> Relationship:
        """Get or create relationship with target"""
        if target not in self.relationships:
            self.relationships[target] = Relationship(target=target)
        return self.relationships[target]

    def get_trust(self, target: str) -> float:
        """Get trust level for target"""
        return self.get(target).trust

    def set_trust(self, target: str, value: float):
        """Set trust level for target"""
        self.get(target).trust = max(-1.0, min(1.0, value))

    def modify_trust(self, target: str, amount: float):
        """Modify trust level for target"""
        self.get(target).modify_trust(amount)

    def get_fear(self, target: str) -> float:
        """Get fear level for target"""
        return self.get(target).fear

    def set_fear(self, target: str, value: float):
        """Set fear level for target"""
        self.get(target).fear = max(0.0, min(1.0, value))

    def modify_fear(self, target: str, amount: float):
        """Modify fear level for target"""
        self.get(target).modify_fear(amount)

    def get_loyalty(self, target: str) -> float:
        """Get loyalty level for target"""
        return self.get(target).loyalty

    def set_loyalty(self, target: str, value: float):
        """Set loyalty level for target"""
        self.get(target).loyalty = max(0.0, min(1.0, value))

    def modify_loyalty(self, target: str, amount: float):
        """Modify loyalty level for target"""
        self.get(target).modify_loyalty(amount)

    def set_type(self, target: str, rel_type: RelationshipType):
        """Set relationship type"""
        self.get(target).relationship_type = rel_type

    def record_interaction(self, target: str, positive: bool):
        """Record interaction with target"""
        self.get(target).record_interaction(positive)

    def get_disposition(self, target: str) -> float:
        """Get disposition toward target"""
        return self.get(target).get_disposition()

    def get_friends(self) -> List[str]:
        """Get all targets with positive relationships"""
        return [
            t for t, r in self.relationships.items()
            if r.is_positive()
        ]

    def get_enemies(self) -> List[str]:
        """Get all targets with negative relationships"""
        return [
            t for t, r in self.relationships.items()
            if r.is_negative()
        ]

    def get_most_trusted(self) -> Optional[Tuple[str, float]]:
        """Get most trusted target"""
        if not self.relationships:
            return None

        best = max(self.relationships.items(), key=lambda x: x[1].trust)
        return (best[0], best[1].trust)

    def get_most_feared(self) -> Optional[Tuple[str, float]]:
        """Get most feared target"""
        if not self.relationships:
            return None

        best = max(self.relationships.items(), key=lambda x: x[1].fear)
        return (best[0], best[1].fear) if best[1].fear > 0 else None

    def can_request(self, target: str, difficulty: float = 0.5) -> bool:
        """Check if target can make requests"""
        return self.get(target).can_request(difficulty)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            'relationships': {
                t: {
                    'relationship_type': r.relationship_type.name,
                    'trust': r.trust,
                    'fear': r.fear,
                    'loyalty': r.loyalty,
                    'respect': r.respect,
                    'interactions': r.interactions,
                    'positive_interactions': r.positive_interactions,
                    'negative_interactions': r.negative_interactions,
                }
                for t, r in self.relationships.items()
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RelationshipSystem':
        """Deserialize from dictionary"""
        system = cls()

        for target, rel_data in data.get('relationships', {}).items():
            system.relationships[target] = Relationship(
                target=target,
                relationship_type=RelationshipType[rel_data['relationship_type']],
                trust=rel_data['trust'],
                fear=rel_data['fear'],
                loyalty=rel_data['loyalty'],
                respect=rel_data.get('respect', 0.5),
                interactions=rel_data['interactions'],
                positive_interactions=rel_data['positive_interactions'],
                negative_interactions=rel_data['negative_interactions'],
            )

        return system
