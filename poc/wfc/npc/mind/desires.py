"""
Desire System

Desires are goals with:
- Priority (0.0 - 1.0)
- Conditions (when to activate)
- Conflicts (mutually exclusive desires)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any, Callable
from enum import IntEnum, auto


class DesireState(IntEnum):
    """Current state of a desire"""
    DORMANT = 0       # Not currently active
    ACTIVE = 1        # Actively pursuing
    BLOCKED = 2       # Cannot pursue (conflict/missing requirements)
    SATISFIED = 3     # Goal achieved
    ABANDONED = 4     # Given up


@dataclass
class Desire:
    """A single desire/goal"""
    key: str
    priority: float = 0.5
    state: DesireState = DesireState.DORMANT

    # Descriptive
    description: str = ""

    # Conditions
    activation_conditions: List[str] = field(default_factory=list)  # Belief keys that activate
    satisfaction_conditions: List[str] = field(default_factory=list)  # Belief keys that satisfy

    # Conflicts
    conflicts_with: Set[str] = field(default_factory=set)  # Other desire keys

    # Temporal
    urgency: float = 0.0  # Increases over time
    urgency_rate: float = 0.0  # How fast urgency grows

    def tick(self):
        """Update urgency over time"""
        if self.state == DesireState.ACTIVE:
            self.urgency = min(1.0, self.urgency + self.urgency_rate)

    def effective_priority(self) -> float:
        """Get priority modified by urgency"""
        return min(1.0, self.priority + self.urgency * 0.5)

    def activate(self):
        """Activate this desire"""
        if self.state in (DesireState.DORMANT, DesireState.BLOCKED):
            self.state = DesireState.ACTIVE

    def block(self):
        """Block this desire"""
        self.state = DesireState.BLOCKED

    def satisfy(self):
        """Mark desire as satisfied"""
        self.state = DesireState.SATISFIED
        self.urgency = 0.0

    def abandon(self):
        """Give up on this desire"""
        self.state = DesireState.ABANDONED


class DesireSystem:
    """
    Manages all desires for an NPC.

    Features:
    - Priority-based selection
    - Conflict resolution
    - Activation based on beliefs
    - Urgency accumulation
    """

    def __init__(self):
        self.desires: Dict[str, Desire] = {}
        self.tick_count: int = 0

    def add(self, key: str, priority: float = 0.5,
            description: str = "",
            activation_conditions: List[str] = None,
            satisfaction_conditions: List[str] = None,
            conflicts_with: Set[str] = None,
            urgency_rate: float = 0.0):
        """Add or update a desire"""
        self.desires[key] = Desire(
            key=key,
            priority=priority,
            description=description,
            activation_conditions=activation_conditions or [],
            satisfaction_conditions=satisfaction_conditions or [],
            conflicts_with=conflicts_with or set(),
            urgency_rate=urgency_rate,
        )

    def remove(self, key: str):
        """Remove a desire"""
        if key in self.desires:
            del self.desires[key]

    def get(self, key: str) -> Optional[Desire]:
        """Get a desire by key"""
        return self.desires.get(key)

    def get_priority(self, key: str) -> float:
        """Get desire priority (0 if not found)"""
        if key in self.desires:
            return self.desires[key].effective_priority()
        return 0.0

    def set_priority(self, key: str, priority: float):
        """Set desire priority"""
        if key in self.desires:
            self.desires[key].priority = max(0.0, min(1.0, priority))

    def tick(self, belief_checker: Callable[[str], bool] = None):
        """
        Update desires each tick.

        belief_checker: function(key) -> bool to check if belief is held
        """
        self.tick_count += 1

        for desire in self.desires.values():
            desire.tick()

            # Check activation
            if desire.state == DesireState.DORMANT and desire.activation_conditions:
                if belief_checker:
                    if all(belief_checker(c) for c in desire.activation_conditions):
                        desire.activate()

            # Check satisfaction
            if desire.state == DesireState.ACTIVE and desire.satisfaction_conditions:
                if belief_checker:
                    if all(belief_checker(c) for c in desire.satisfaction_conditions):
                        desire.satisfy()

        # Resolve conflicts
        self._resolve_conflicts()

    def _resolve_conflicts(self):
        """Resolve conflicting desires (lower priority gets blocked)"""
        for desire in self.desires.values():
            if desire.state != DesireState.ACTIVE:
                continue

            for conflict_key in desire.conflicts_with:
                if conflict_key in self.desires:
                    conflict = self.desires[conflict_key]
                    if conflict.state == DesireState.ACTIVE:
                        # Block lower priority
                        if desire.effective_priority() > conflict.effective_priority():
                            conflict.block()
                        elif conflict.effective_priority() > desire.effective_priority():
                            desire.block()
                            break

    def get_active(self) -> List[Desire]:
        """Get all active desires sorted by effective priority"""
        active = [d for d in self.desires.values() if d.state == DesireState.ACTIVE]
        return sorted(active, key=lambda d: -d.effective_priority())

    def get_top_desire(self) -> Optional[Desire]:
        """Get highest priority active desire"""
        active = self.get_active()
        return active[0] if active else None

    def is_active(self, key: str) -> bool:
        """Check if a desire is active"""
        if key in self.desires:
            return self.desires[key].state == DesireState.ACTIVE
        return False

    def alignment_with(self, action_effects: Dict[str, bool]) -> float:
        """
        Calculate how well an action aligns with desires.

        action_effects: dict of desire_key -> advances(True)/blocks(False)
        Returns: -1.0 to 1.0
        """
        if not action_effects:
            return 0.0

        total_score = 0.0
        total_weight = 0.0

        for key, advances in action_effects.items():
            if key in self.desires:
                desire = self.desires[key]
                if desire.state != DesireState.ACTIVE:
                    continue

                weight = desire.effective_priority()

                if advances:
                    total_score += weight
                else:
                    total_score -= weight * 1.5  # Blocking is worse

                total_weight += weight

        if total_weight == 0:
            return 0.0

        return total_score / total_weight

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            'desires': {
                k: {
                    'priority': v.priority,
                    'state': v.state.name,
                    'description': v.description,
                    'activation_conditions': v.activation_conditions,
                    'satisfaction_conditions': v.satisfaction_conditions,
                    'conflicts_with': list(v.conflicts_with),
                    'urgency': v.urgency,
                    'urgency_rate': v.urgency_rate,
                }
                for k, v in self.desires.items()
            },
            'tick_count': self.tick_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DesireSystem':
        """Deserialize from dictionary"""
        system = cls()
        system.tick_count = data.get('tick_count', 0)

        for key, desire_data in data.get('desires', {}).items():
            system.desires[key] = Desire(
                key=key,
                priority=desire_data['priority'],
                state=DesireState[desire_data['state']],
                description=desire_data.get('description', ''),
                activation_conditions=desire_data.get('activation_conditions', []),
                satisfaction_conditions=desire_data.get('satisfaction_conditions', []),
                conflicts_with=set(desire_data.get('conflicts_with', [])),
                urgency=desire_data.get('urgency', 0.0),
                urgency_rate=desire_data.get('urgency_rate', 0.0),
            )

        return system
