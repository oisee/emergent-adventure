"""
Fractal Roles System

Based on the storygen-book concept of fractal narratives:
- Characters have different roles at different narrative levels
- A character can be Hero on macro-level but Opponent on meso-level
- Roles influence behavior, dialogue, and willingness to help

Narrative Levels:
- Mega: World-spanning events (very rare in this game)
- Macro: The main story quest
- Meso: Current subplot or scene sequence
- Micro: Current scene/encounter
- Nano: Individual action/dialogue

Actant Roles (Greimas):
- Subject (Hero): Protagonist pursuing Object
- Object: Goal being pursued
- Sender: Who gives the quest
- Receiver: Who benefits from success
- Helper: Assists the Subject
- Opponent: Opposes the Subject
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set, Tuple
from enum import IntEnum, auto


class NarrativeLevel(IntEnum):
    """Levels of narrative structure (fractal)"""
    NANO = 0      # Individual action/line
    MICRO = 1     # Single scene/encounter
    MESO = 2      # Subplot or scene sequence
    MACRO = 3     # Main story quest
    MEGA = 4      # World-spanning (rare)


class ActantRole(IntEnum):
    """Greimas actant roles"""
    NONE = 0
    SUBJECT = 1    # Hero pursuing goal
    OBJECT = 2     # Goal being pursued
    SENDER = 3     # Quest giver
    RECEIVER = 4   # Beneficiary
    HELPER = 5     # Assists hero
    OPPONENT = 6   # Opposes hero

    # Extended roles
    MENTOR = 7     # Teaches/guides hero
    SHADOW = 8     # Dark reflection/antagonist
    TRICKSTER = 9  # Unpredictable agent
    THRESHOLD_GUARDIAN = 10  # Tests hero's worthiness


# How roles typically relate to player interactions
ROLE_BEHAVIORS = {
    ActantRole.SUBJECT: {
        'help_tendency': 0.0,  # They're the hero, not helping
        'share_info': 0.3,
        'follow_orders': 0.0,
        'speech_style': 'heroic',
    },
    ActantRole.HELPER: {
        'help_tendency': 0.9,
        'share_info': 0.8,
        'follow_orders': 0.7,
        'speech_style': 'supportive',
    },
    ActantRole.OPPONENT: {
        'help_tendency': -0.5,  # May actively hinder
        'share_info': 0.1,
        'follow_orders': 0.0,
        'speech_style': 'antagonistic',
    },
    ActantRole.SENDER: {
        'help_tendency': 0.3,
        'share_info': 0.9,
        'follow_orders': 0.2,
        'speech_style': 'authoritative',
    },
    ActantRole.MENTOR: {
        'help_tendency': 0.7,
        'share_info': 0.95,
        'follow_orders': 0.3,
        'speech_style': 'wise',
    },
    ActantRole.SHADOW: {
        'help_tendency': -0.8,
        'share_info': 0.2,  # May reveal dark truths
        'follow_orders': 0.0,
        'speech_style': 'dark',
    },
    ActantRole.TRICKSTER: {
        'help_tendency': 0.0,  # Unpredictable
        'share_info': 0.5,
        'follow_orders': 0.2,
        'speech_style': 'playful',
    },
    ActantRole.THRESHOLD_GUARDIAN: {
        'help_tendency': 0.4,  # Helps if hero proves worthy
        'share_info': 0.3,
        'follow_orders': 0.1,
        'speech_style': 'challenging',
    },
}


@dataclass
class RoleTransition:
    """
    Describes when and how a role changes.

    Example: A Helper who becomes Opponent after betrayal twist
    """
    from_role: ActantRole
    to_role: ActantRole
    trigger: str              # What causes the transition
    at_level: NarrativeLevel  # Which level this affects
    conditions: List[str] = field(default_factory=list)  # Belief keys required

    def describe(self) -> str:
        return f"{self.from_role.name} -> {self.to_role.name} ({self.trigger})"


@dataclass
class FractalRole:
    """
    A character's roles at different narrative levels.

    Example:
    - Macro: Helper (overall story ally)
    - Meso: Opponent (current subplot rivalry)
    - Micro: Subject (takes lead in this scene)
    """

    # Roles at each level (can be None if not relevant)
    mega_role: Optional[ActantRole] = None
    macro_role: Optional[ActantRole] = None
    meso_role: Optional[ActantRole] = None
    micro_role: Optional[ActantRole] = None
    nano_role: Optional[ActantRole] = None

    # Potential transitions
    transitions: List[RoleTransition] = field(default_factory=list)

    # Current active level (what's most relevant now)
    active_level: NarrativeLevel = NarrativeLevel.MICRO

    def get_role(self, level: NarrativeLevel = None) -> Optional[ActantRole]:
        """Get role at specified or active level"""
        if level is None:
            level = self.active_level

        role_map = {
            NarrativeLevel.MEGA: self.mega_role,
            NarrativeLevel.MACRO: self.macro_role,
            NarrativeLevel.MESO: self.meso_role,
            NarrativeLevel.MICRO: self.micro_role,
            NarrativeLevel.NANO: self.nano_role,
        }

        # Get role at requested level, fall back to higher levels
        role = role_map.get(level)
        if role is not None:
            return role

        # Try higher levels
        for higher_level in [NarrativeLevel.MESO, NarrativeLevel.MACRO, NarrativeLevel.MEGA]:
            if higher_level > level:
                role = role_map.get(higher_level)
                if role is not None:
                    return role

        return ActantRole.NONE

    def set_role(self, level: NarrativeLevel, role: ActantRole):
        """Set role at a level"""
        if level == NarrativeLevel.MEGA:
            self.mega_role = role
        elif level == NarrativeLevel.MACRO:
            self.macro_role = role
        elif level == NarrativeLevel.MESO:
            self.meso_role = role
        elif level == NarrativeLevel.MICRO:
            self.micro_role = role
        elif level == NarrativeLevel.NANO:
            self.nano_role = role

    def get_effective_behavior(self) -> Dict[str, float]:
        """
        Get behavior modifiers based on current roles.

        Combines roles from active level and higher, with priority to lower levels.
        """
        behavior = {
            'help_tendency': 0.0,
            'share_info': 0.5,
            'follow_orders': 0.3,
        }

        # Get relevant roles (active and above)
        weights = []
        for level in NarrativeLevel:
            if level >= self.active_level:
                role = self.get_role(level)
                if role and role in ROLE_BEHAVIORS:
                    # Lower levels have higher weight
                    weight = 1.0 / (1 + level - self.active_level)
                    weights.append((role, weight))

        if not weights:
            return behavior

        # Weighted average of behaviors
        total_weight = sum(w for _, w in weights)
        for role, weight in weights:
            role_behavior = ROLE_BEHAVIORS.get(role, {})
            normalized_weight = weight / total_weight
            for key in behavior:
                if key in role_behavior:
                    behavior[key] += role_behavior[key] * normalized_weight

        return behavior

    def get_speech_style(self) -> str:
        """Get speech style based on most relevant role"""
        role = self.get_role()
        return ROLE_BEHAVIORS.get(role, {}).get('speech_style', 'neutral')

    def check_transition(self, trigger: str, belief_checker=None) -> Optional[RoleTransition]:
        """Check if a transition should occur"""
        for transition in self.transitions:
            if transition.trigger == trigger:
                # Check conditions
                if transition.conditions and belief_checker:
                    if not all(belief_checker(c) for c in transition.conditions):
                        continue
                return transition
        return None

    def apply_transition(self, transition: RoleTransition):
        """Apply a role transition"""
        self.set_role(transition.at_level, transition.to_role)

    def is_helpful(self) -> bool:
        """Check if currently in a helpful role"""
        role = self.get_role()
        return role in (ActantRole.HELPER, ActantRole.MENTOR, ActantRole.SENDER)

    def is_hostile(self) -> bool:
        """Check if currently in a hostile role"""
        role = self.get_role()
        return role in (ActantRole.OPPONENT, ActantRole.SHADOW)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            'mega_role': self.mega_role.name if self.mega_role else None,
            'macro_role': self.macro_role.name if self.macro_role else None,
            'meso_role': self.meso_role.name if self.meso_role else None,
            'micro_role': self.micro_role.name if self.micro_role else None,
            'nano_role': self.nano_role.name if self.nano_role else None,
            'active_level': self.active_level.name,
            'transitions': [
                {
                    'from_role': t.from_role.name,
                    'to_role': t.to_role.name,
                    'trigger': t.trigger,
                    'at_level': t.at_level.name,
                    'conditions': t.conditions,
                }
                for t in self.transitions
            ],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FractalRole':
        """Deserialize from dictionary"""
        def parse_role(name):
            return ActantRole[name] if name else None

        role = cls(
            mega_role=parse_role(data.get('mega_role')),
            macro_role=parse_role(data.get('macro_role')),
            meso_role=parse_role(data.get('meso_role')),
            micro_role=parse_role(data.get('micro_role')),
            nano_role=parse_role(data.get('nano_role')),
            active_level=NarrativeLevel[data.get('active_level', 'MICRO')],
        )

        for t_data in data.get('transitions', []):
            role.transitions.append(RoleTransition(
                from_role=ActantRole[t_data['from_role']],
                to_role=ActantRole[t_data['to_role']],
                trigger=t_data['trigger'],
                at_level=NarrativeLevel[t_data['at_level']],
                conditions=t_data.get('conditions', []),
            ))

        return role


class FractalRoleSystem:
    """
    Manages fractal roles for all NPCs in the game.

    Handles:
    - Role assignment based on plot
    - Role transitions on plot events
    - Behavior modifications
    """

    def __init__(self):
        self.npc_roles: Dict[str, FractalRole] = {}
        self.current_narrative_level: NarrativeLevel = NarrativeLevel.MICRO

    def assign_role(self, npc_name: str,
                    macro_role: ActantRole = None,
                    meso_role: ActantRole = None,
                    micro_role: ActantRole = None):
        """Assign roles to an NPC"""
        if npc_name not in self.npc_roles:
            self.npc_roles[npc_name] = FractalRole()

        role = self.npc_roles[npc_name]
        if macro_role:
            role.macro_role = macro_role
        if meso_role:
            role.meso_role = meso_role
        if micro_role:
            role.micro_role = micro_role

    def add_transition(self, npc_name: str,
                       from_role: ActantRole,
                       to_role: ActantRole,
                       trigger: str,
                       at_level: NarrativeLevel = NarrativeLevel.MESO,
                       conditions: List[str] = None):
        """Add a potential role transition for an NPC"""
        if npc_name not in self.npc_roles:
            self.npc_roles[npc_name] = FractalRole()

        self.npc_roles[npc_name].transitions.append(RoleTransition(
            from_role=from_role,
            to_role=to_role,
            trigger=trigger,
            at_level=at_level,
            conditions=conditions or [],
        ))

    def get_role(self, npc_name: str) -> Optional[FractalRole]:
        """Get fractal role for an NPC"""
        return self.npc_roles.get(npc_name)

    def get_behavior(self, npc_name: str) -> Dict[str, float]:
        """Get behavior modifiers for an NPC"""
        role = self.get_role(npc_name)
        if role:
            return role.get_effective_behavior()
        return {'help_tendency': 0.0, 'share_info': 0.5, 'follow_orders': 0.3}

    def set_narrative_level(self, level: NarrativeLevel):
        """Update current narrative level for all NPCs"""
        self.current_narrative_level = level
        for role in self.npc_roles.values():
            role.active_level = level

    def trigger_event(self, event_name: str, belief_checker=None):
        """Trigger potential transitions for all NPCs"""
        for npc_name, role in self.npc_roles.items():
            transition = role.check_transition(event_name, belief_checker)
            if transition:
                role.apply_transition(transition)

    def get_helpers(self) -> List[str]:
        """Get NPCs in helper roles"""
        return [name for name, role in self.npc_roles.items() if role.is_helpful()]

    def get_opponents(self) -> List[str]:
        """Get NPCs in opponent roles"""
        return [name for name, role in self.npc_roles.items() if role.is_hostile()]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            'npc_roles': {
                name: role.to_dict()
                for name, role in self.npc_roles.items()
            },
            'current_narrative_level': self.current_narrative_level.name,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FractalRoleSystem':
        """Deserialize from dictionary"""
        system = cls()
        system.current_narrative_level = NarrativeLevel[data.get('current_narrative_level', 'MICRO')]

        for name, role_data in data.get('npc_roles', {}).items():
            system.npc_roles[name] = FractalRole.from_dict(role_data)

        return system


# =============================================================================
# Demo
# =============================================================================

def demo():
    """Demo fractal roles"""
    print("=== Fractal Roles Demo ===\n")

    # Create system
    system = FractalRoleSystem()

    # Assign roles
    system.assign_role("Elder Sage",
                       macro_role=ActantRole.MENTOR,
                       meso_role=ActantRole.SENDER)

    system.assign_role("Dark Knight",
                       macro_role=ActantRole.HELPER,
                       meso_role=ActantRole.OPPONENT)  # Rival subplot!

    system.assign_role("Mysterious Stranger",
                       macro_role=ActantRole.TRICKSTER)

    # Add betrayal transition
    system.add_transition("Dark Knight",
                          from_role=ActantRole.HELPER,
                          to_role=ActantRole.SHADOW,
                          trigger="betrayal_revealed",
                          at_level=NarrativeLevel.MACRO)

    # Show roles
    for name in ["Elder Sage", "Dark Knight", "Mysterious Stranger"]:
        role = system.get_role(name)
        behavior = system.get_behavior(name)
        print(f"{name}:")
        print(f"  Macro: {role.macro_role.name if role.macro_role else 'None'}")
        print(f"  Meso: {role.meso_role.name if role.meso_role else 'None'}")
        print(f"  Help tendency: {behavior['help_tendency']:.2f}")
        print(f"  Speech style: {role.get_speech_style()}")
        print()

    # Trigger betrayal
    print("=== Triggering 'betrayal_revealed' ===\n")
    system.trigger_event("betrayal_revealed")

    role = system.get_role("Dark Knight")
    behavior = system.get_behavior("Dark Knight")
    print("Dark Knight after betrayal:")
    print(f"  Macro: {role.macro_role.name if role.macro_role else 'None'}")
    print(f"  Help tendency: {behavior['help_tendency']:.2f}")
    print(f"  Speech style: {role.get_speech_style()}")


if __name__ == "__main__":
    demo()
