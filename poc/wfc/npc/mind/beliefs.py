"""
Belief System

Beliefs are key-value pairs with:
- Confidence (0.0 - 1.0)
- Source (observation, told, inferred)
- Timestamp (for decay)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
from enum import IntEnum, auto


class BeliefSource(IntEnum):
    """How the belief was acquired"""
    INNATE = 0        # Part of NPC's nature
    OBSERVATION = 1   # Witnessed firsthand
    TOLD = 2          # Someone told them
    INFERRED = 3      # Reasoned from other beliefs
    RUMOR = 4         # Heard indirectly


@dataclass
class Belief:
    """A single belief"""
    key: str
    value: Any
    confidence: float = 1.0
    source: BeliefSource = BeliefSource.INNATE
    timestamp: int = 0
    decay_rate: float = 0.0  # How fast confidence decays per tick

    def tick(self):
        """Apply time-based decay"""
        if self.decay_rate > 0 and self.source != BeliefSource.INNATE:
            self.confidence = max(0.0, self.confidence - self.decay_rate)

    def strengthen(self, amount: float = 0.1):
        """Strengthen belief (from confirmation)"""
        self.confidence = min(1.0, self.confidence + amount)

    def weaken(self, amount: float = 0.1):
        """Weaken belief (from contradiction)"""
        self.confidence = max(0.0, self.confidence - amount)

    def is_strong(self, threshold: float = 0.7) -> bool:
        """Check if belief is strongly held"""
        return self.confidence >= threshold

    def contradicts(self, other: 'Belief') -> bool:
        """Check if this belief contradicts another"""
        if self.key != other.key:
            return False
        return self.value != other.value


class BeliefSystem:
    """
    Manages all beliefs for an NPC.

    Features:
    - Hierarchical belief keys (domain.subdomain.key)
    - Confidence-based retrieval
    - Contradiction detection
    - Time-based decay
    """

    def __init__(self):
        self.beliefs: Dict[str, Belief] = {}
        self.tick_count: int = 0

    def set(self, key: str, value: Any,
            confidence: float = 1.0,
            source: BeliefSource = BeliefSource.INNATE,
            decay_rate: float = 0.0):
        """Set or update a belief"""
        if key in self.beliefs:
            old = self.beliefs[key]
            # If same value, strengthen; if different, replace if higher confidence
            if old.value == value:
                old.strengthen(0.1)
                old.confidence = max(old.confidence, confidence)
            elif confidence > old.confidence:
                self.beliefs[key] = Belief(
                    key=key,
                    value=value,
                    confidence=confidence,
                    source=source,
                    timestamp=self.tick_count,
                    decay_rate=decay_rate
                )
        else:
            self.beliefs[key] = Belief(
                key=key,
                value=value,
                confidence=confidence,
                source=source,
                timestamp=self.tick_count,
                decay_rate=decay_rate
            )

    def get(self, key: str) -> Tuple[Any, float]:
        """Get belief value and confidence"""
        if key in self.beliefs:
            b = self.beliefs[key]
            return (b.value, b.confidence)
        return (None, 0.0)

    def get_belief(self, key: str) -> Optional[Belief]:
        """Get full belief object"""
        return self.beliefs.get(key)

    def exists(self, key: str) -> bool:
        """Check if belief exists"""
        return key in self.beliefs

    def believes(self, key: str, value: Any = True, min_confidence: float = 0.5) -> bool:
        """Check if NPC believes something with sufficient confidence"""
        if key not in self.beliefs:
            return False
        b = self.beliefs[key]
        return b.value == value and b.confidence >= min_confidence

    def remove(self, key: str):
        """Remove a belief"""
        if key in self.beliefs:
            del self.beliefs[key]

    def tick(self):
        """Process time-based decay"""
        self.tick_count += 1
        to_remove = []

        for key, belief in self.beliefs.items():
            belief.tick()
            if belief.confidence <= 0:
                to_remove.append(key)

        for key in to_remove:
            del self.beliefs[key]

    def get_by_prefix(self, prefix: str) -> Dict[str, Belief]:
        """Get all beliefs starting with prefix"""
        return {k: v for k, v in self.beliefs.items() if k.startswith(prefix)}

    def get_strong_beliefs(self, threshold: float = 0.7) -> List[Belief]:
        """Get all strongly-held beliefs"""
        return [b for b in self.beliefs.values() if b.is_strong(threshold)]

    def find_contradictions(self) -> List[Tuple[Belief, Belief]]:
        """Find contradicting beliefs"""
        contradictions = []
        beliefs = list(self.beliefs.values())

        for i, b1 in enumerate(beliefs):
            for b2 in beliefs[i+1:]:
                if b1.contradicts(b2):
                    contradictions.append((b1, b2))

        return contradictions

    def alignment_with(self, action_beliefs: Dict[str, Any]) -> float:
        """
        Calculate how well an action aligns with beliefs.

        action_beliefs: dict of belief_key -> required_value
        Returns: -1.0 (complete conflict) to 1.0 (perfect alignment)
        """
        if not action_beliefs:
            return 0.0

        total_score = 0.0
        total_weight = 0.0

        for key, required_value in action_beliefs.items():
            if key in self.beliefs:
                belief = self.beliefs[key]
                weight = belief.confidence

                if belief.value == required_value:
                    total_score += weight
                else:
                    total_score -= weight

                total_weight += weight
            else:
                # Unknown belief - slight negative (caution)
                total_weight += 0.5
                total_score -= 0.1

        if total_weight == 0:
            return 0.0

        return total_score / total_weight

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            'beliefs': {
                k: {
                    'value': v.value,
                    'confidence': v.confidence,
                    'source': v.source.name,
                    'timestamp': v.timestamp,
                    'decay_rate': v.decay_rate,
                }
                for k, v in self.beliefs.items()
            },
            'tick_count': self.tick_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BeliefSystem':
        """Deserialize from dictionary"""
        system = cls()
        system.tick_count = data.get('tick_count', 0)

        for key, belief_data in data.get('beliefs', {}).items():
            system.beliefs[key] = Belief(
                key=key,
                value=belief_data['value'],
                confidence=belief_data['confidence'],
                source=BeliefSource[belief_data['source']],
                timestamp=belief_data['timestamp'],
                decay_rate=belief_data.get('decay_rate', 0.0),
            )

        return system
