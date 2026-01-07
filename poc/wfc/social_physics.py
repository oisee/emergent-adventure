"""
Social Physics Engine

Emergent NPC behavior through simple trait interactions.
Like Dwarf Fortress, but in 32 bytes per character.

Each NPC has:
- 1 byte traits (8 binary flags)
- 1 byte trust toward hero (0-255)
- 1 byte role (HELPER, VILLAIN, NEUTRAL, HIDDEN_*)
- 1 byte location

When SITUATION meets TRAITS, emergent drama happens.
No scripted "betrayal scene" - betrayal EMERGES from conditions.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, Any
from enum import IntEnum, IntFlag
import struct


# =============================================================================
# NPC TRAITS (1 byte = 8 flags)
# =============================================================================

class Trait(IntFlag):
    """
    Binary personality traits.
    Each NPC has 1 byte = 8 possible traits.
    """
    NONE = 0

    # Positive traits
    HONEST = 0x01       # Won't lie, reveals truth
    LOYAL = 0x02        # Stands by allies
    BRAVE = 0x04        # Won't flee from danger
    KIND = 0x08         # Helps others in need

    # Negative traits
    GREEDY = 0x10       # Wants treasure/power
    COWARD = 0x20       # Flees from danger
    VENGEFUL = 0x40     # Remembers slights
    AMBITIOUS = 0x80    # Wants to rise in power


# Trait combinations with names
TRAIT_ARCHETYPES = {
    Trait.HONEST | Trait.LOYAL | Trait.BRAVE: "True Hero",
    Trait.HONEST | Trait.KIND: "Gentle Soul",
    Trait.LOYAL | Trait.BRAVE: "Stalwart Defender",
    Trait.GREEDY | Trait.COWARD: "Sniveling Wretch",
    Trait.GREEDY | Trait.AMBITIOUS: "Power-Hungry",
    Trait.VENGEFUL | Trait.AMBITIOUS: "Dark Schemer",
    Trait.BRAVE | Trait.VENGEFUL: "Fierce Avenger",
    Trait.KIND | Trait.COWARD: "Reluctant Helper",
    Trait.HONEST | Trait.GREEDY: "Honest Merchant",
    Trait.LOYAL | Trait.VENGEFUL: "Protective Guardian",
}


# =============================================================================
# NPC ROLES
# =============================================================================

class Role(IntEnum):
    """
    Current apparent role of NPC.
    Can change during gameplay!
    """
    NEUTRAL = 0
    HELPER = 1
    MENTOR = 2
    VILLAIN = 3
    RIVAL = 4

    # Hidden roles (revealed later)
    HIDDEN_ALLY = 5      # Appears villain, secretly helper
    HIDDEN_VILLAIN = 6   # Appears helper, secretly villain
    HIDDEN_MENTOR = 7    # Appears neutral, secretly mentor

    # Dead/Gone
    DEAD = 8
    DEPARTED = 9


# =============================================================================
# SITUATION TYPES
# =============================================================================

class Situation(IntEnum):
    """
    Story situations that can trigger trait-based reactions.
    """
    NONE = 0

    # Positive situations
    TREASURE_FOUND = 1      # Gold/artifact discovered
    VICTORY = 2             # Battle won
    KINDNESS_SHOWN = 3      # Hero was kind
    TRUTH_REVEALED = 4      # Secret uncovered

    # Negative situations
    DANGER = 5              # Combat/threat
    BETRAYAL = 6            # Someone betrayed someone
    LOSS = 7                # Defeat/death
    INSULT = 8              # Honor challenged

    # Neutral situations
    CHOICE = 9              # Decision point
    MEETING = 10            # New NPC encounter
    TRAVEL = 11             # Journey
    REST = 12               # Safe haven


# =============================================================================
# NPC STRUCTURE (4 bytes)
# =============================================================================

@dataclass
class NPC:
    """
    Minimal NPC structure - Z80 friendly.
    Only 4 bytes per character!
    """
    id: int
    name: str  # Not stored in Z80, just for Python reference

    traits: Trait = Trait.NONE
    trust: int = 128        # 0-255, starts neutral (128)
    role: Role = Role.NEUTRAL
    location: int = 0       # Tile/room ID

    # Hidden state (for reveals)
    true_role: Role = None  # If different from role, can be revealed

    # Memory (simplified - just last interaction)
    last_interaction: Situation = Situation.NONE
    grudge: int = 0         # Accumulated resentment (0-255)

    def __post_init__(self):
        if self.true_role is None:
            self.true_role = self.role

    def to_bytes(self) -> bytes:
        """Pack to 4 bytes for Z80"""
        return struct.pack('BBBB',
            self.traits & 0xFF,
            self.trust & 0xFF,
            self.role & 0x0F | ((self.true_role & 0x0F) << 4),  # Both roles in 1 byte
            self.location & 0xFF
        )

    @classmethod
    def from_bytes(cls, data: bytes, id: int, name: str = "?") -> 'NPC':
        """Unpack from 4 bytes"""
        traits, trust, roles, location = struct.unpack('BBBB', data)
        role = Role(roles & 0x0F)
        true_role = Role((roles >> 4) & 0x0F)
        return cls(id=id, name=name, traits=Trait(traits),
                   trust=trust, role=role, true_role=true_role,
                   location=location)

    def get_archetype(self) -> str:
        """Get personality archetype from traits"""
        for traits, name in TRAIT_ARCHETYPES.items():
            if (self.traits & traits) == traits:
                return name
        return "Unknown"

    def has_trait(self, trait: Trait) -> bool:
        return bool(self.traits & trait)

    def is_hidden(self) -> bool:
        """Does NPC have a hidden role?"""
        return self.role != self.true_role


# =============================================================================
# REACTION RULES
# =============================================================================

@dataclass
class ReactionRule:
    """
    Rule: IF traits AND situation THEN reaction.

    Example:
        IF GREEDY and TREASURE_FOUND and trust < 50 → BETRAYAL
    """
    required_traits: Trait
    forbidden_traits: Trait
    situation: Situation
    trust_threshold: Tuple[int, int]  # (min, max) or None
    reaction: str  # Action to take
    trust_change: int = 0
    grudge_change: int = 0
    role_change: Optional[Role] = None
    reveals_true_role: bool = False


# The emergent drama rules
REACTION_RULES: List[ReactionRule] = [
    # === BETRAYAL CONDITIONS ===
    ReactionRule(
        required_traits=Trait.GREEDY,
        forbidden_traits=Trait.LOYAL,
        situation=Situation.TREASURE_FOUND,
        trust_threshold=(0, 80),
        reaction="ATTEMPT_STEAL",
        trust_change=-30,
        grudge_change=10,
    ),
    ReactionRule(
        required_traits=Trait.GREEDY | Trait.AMBITIOUS,
        forbidden_traits=Trait.HONEST,
        situation=Situation.VICTORY,
        trust_threshold=(0, 50),
        reaction="CLAIM_CREDIT",
        trust_change=-20,
    ),
    ReactionRule(
        required_traits=Trait.AMBITIOUS,
        forbidden_traits=Trait.LOYAL,
        situation=Situation.CHOICE,
        trust_threshold=(0, 60),
        reaction="SIDE_WITH_POWER",
        role_change=Role.RIVAL,
    ),

    # === COWARDICE ===
    ReactionRule(
        required_traits=Trait.COWARD,
        forbidden_traits=Trait.LOYAL,
        situation=Situation.DANGER,
        trust_threshold=(0, 150),
        reaction="FLEE",
        trust_change=-10,
    ),
    ReactionRule(
        required_traits=Trait.COWARD,
        forbidden_traits=Trait.NONE,
        situation=Situation.LOSS,
        trust_threshold=(0, 255),
        reaction="BEG_MERCY",
    ),

    # === LOYALTY ===
    ReactionRule(
        required_traits=Trait.LOYAL,
        forbidden_traits=Trait.COWARD,
        situation=Situation.DANGER,
        trust_threshold=(100, 255),
        reaction="PROTECT_HERO",
        trust_change=10,
    ),
    ReactionRule(
        required_traits=Trait.LOYAL | Trait.BRAVE,
        forbidden_traits=Trait.NONE,
        situation=Situation.BETRAYAL,
        trust_threshold=(100, 255),
        reaction="DEFEND_HONOR",
        trust_change=20,
    ),

    # === VENGEANCE ===
    ReactionRule(
        required_traits=Trait.VENGEFUL,
        forbidden_traits=Trait.KIND,
        situation=Situation.INSULT,
        trust_threshold=(0, 255),
        reaction="PLOT_REVENGE",
        grudge_change=30,
    ),
    ReactionRule(
        required_traits=Trait.VENGEFUL,
        forbidden_traits=Trait.NONE,
        situation=Situation.LOSS,
        trust_threshold=(0, 100),
        reaction="BLAME_HERO",
        trust_change=-20,
        grudge_change=20,
    ),

    # === KINDNESS ===
    ReactionRule(
        required_traits=Trait.KIND,
        forbidden_traits=Trait.NONE,
        situation=Situation.KINDNESS_SHOWN,
        trust_threshold=(0, 255),
        reaction="RECIPROCATE",
        trust_change=15,
    ),
    ReactionRule(
        required_traits=Trait.KIND | Trait.BRAVE,
        forbidden_traits=Trait.NONE,
        situation=Situation.DANGER,
        trust_threshold=(0, 255),
        reaction="SACRIFICE_SELF",
        trust_change=30,
    ),

    # === HONESTY ===
    ReactionRule(
        required_traits=Trait.HONEST,
        forbidden_traits=Trait.NONE,
        situation=Situation.TRUTH_REVEALED,
        trust_threshold=(0, 255),
        reaction="CONFIRM_TRUTH",
        reveals_true_role=True,
    ),
    ReactionRule(
        required_traits=Trait.HONEST,
        forbidden_traits=Trait.COWARD,
        situation=Situation.CHOICE,
        trust_threshold=(0, 255),
        reaction="SPEAK_TRUTH",
    ),

    # === HIDDEN ROLE REVEALS ===
    ReactionRule(
        required_traits=Trait.NONE,
        forbidden_traits=Trait.NONE,
        situation=Situation.TRUTH_REVEALED,
        trust_threshold=(0, 255),
        reaction="REVEAL_TRUE_SELF",
        reveals_true_role=True,
    ),
]


# =============================================================================
# SOCIAL PHYSICS ENGINE
# =============================================================================

class SocialPhysicsEngine:
    """
    Simulates NPC interactions and emergent drama.

    Usage:
        engine = SocialPhysicsEngine()
        engine.add_npc(NPC(...))
        reactions = engine.trigger_situation(Situation.TREASURE_FOUND)
        # → ["Grimbold ATTEMPT_STEAL", "Elara PROTECT_HERO"]
    """

    def __init__(self, seed: int = 0):
        self.npcs: Dict[int, NPC] = {}
        self.seed = seed
        self.rng_state = seed
        self.event_log: List[str] = []

    def _lcg_random(self) -> int:
        """Z80-compatible random number generator"""
        self.rng_state = (self.rng_state * 1103515245 + 12345) & 0x7FFFFFFF
        return self.rng_state >> 16

    def add_npc(self, npc: NPC):
        """Add NPC to simulation"""
        self.npcs[npc.id] = npc

    def create_npc(self, id: int, name: str, archetype: str = None,
                   role: Role = Role.NEUTRAL, hidden_role: Role = None) -> NPC:
        """Create NPC with optional archetype"""
        # Generate traits from seed
        self.rng_state = self.seed + id * 256
        traits = Trait(self._lcg_random() & 0xFF)

        # Or use archetype
        if archetype:
            for trait_combo, arch_name in TRAIT_ARCHETYPES.items():
                if arch_name.lower() == archetype.lower():
                    traits = trait_combo
                    break

        npc = NPC(
            id=id,
            name=name,
            traits=traits,
            trust=128,
            role=role,
            true_role=hidden_role or role,
        )
        self.add_npc(npc)
        return npc

    def trigger_situation(self, situation: Situation,
                          location: int = None) -> List[Tuple[NPC, str]]:
        """
        Trigger a situation and get NPC reactions.

        Returns list of (NPC, reaction_name) tuples.
        """
        reactions = []

        for npc in self.npcs.values():
            # Skip if not at location (if specified)
            if location is not None and npc.location != location:
                continue

            # Skip dead/departed
            if npc.role in (Role.DEAD, Role.DEPARTED):
                continue

            # Check each rule
            for rule in REACTION_RULES:
                if self._rule_matches(npc, rule, situation):
                    # Rule triggered!
                    reaction = self._apply_rule(npc, rule)
                    reactions.append((npc, reaction))
                    break  # Only one reaction per NPC per situation

        return reactions

    def _rule_matches(self, npc: NPC, rule: ReactionRule,
                      situation: Situation) -> bool:
        """Check if rule applies to NPC in situation"""
        # Check situation
        if rule.situation != situation:
            return False

        # Check required traits (must have ALL)
        if rule.required_traits and not (npc.traits & rule.required_traits) == rule.required_traits:
            return False

        # Check forbidden traits (must have NONE)
        if rule.forbidden_traits and (npc.traits & rule.forbidden_traits):
            return False

        # Check trust threshold
        min_trust, max_trust = rule.trust_threshold
        if not (min_trust <= npc.trust <= max_trust):
            return False

        # Random factor (20% chance to NOT trigger even if conditions met)
        if (self._lcg_random() % 100) < 20:
            return False

        return True

    def _apply_rule(self, npc: NPC, rule: ReactionRule) -> str:
        """Apply rule effects and return reaction name"""
        # Update trust
        npc.trust = max(0, min(255, npc.trust + rule.trust_change))

        # Update grudge
        npc.grudge = max(0, min(255, npc.grudge + rule.grudge_change))

        # Change role
        if rule.role_change is not None:
            npc.role = rule.role_change

        # Reveal true role
        if rule.reveals_true_role and npc.is_hidden():
            npc.role = npc.true_role

        # Log event
        self.event_log.append(f"{npc.name}: {rule.reaction}")

        return rule.reaction

    def check_betrayal_conditions(self, npc: NPC) -> Optional[str]:
        """
        Special check for betrayal - the signature emergent event.

        Betrayal happens when:
        - GREEDY + TREASURE + low trust
        - OR AMBITIOUS + POWER_VACUUM + low trust
        - OR VENGEFUL + high grudge
        """
        if npc.has_trait(Trait.LOYAL) and npc.trust > 100:
            return None  # Loyal + high trust = never betray

        if npc.has_trait(Trait.GREEDY) and npc.trust < 50:
            return "GREED_BETRAYAL"

        if npc.has_trait(Trait.AMBITIOUS) and npc.trust < 40:
            return "POWER_BETRAYAL"

        if npc.has_trait(Trait.VENGEFUL) and npc.grudge > 100:
            return "REVENGE_BETRAYAL"

        return None

    def simulate_scene(self, scene_type: str, location: int = 0) -> List[str]:
        """
        Simulate a full scene with multiple situation triggers.

        Returns narrative events that emerged.
        """
        events = []

        # Map scene types to situations
        scene_situations = {
            'battle': [Situation.DANGER, Situation.VICTORY],
            'treasure': [Situation.TREASURE_FOUND],
            'meeting': [Situation.MEETING],
            'revelation': [Situation.TRUTH_REVEALED],
            'crisis': [Situation.DANGER, Situation.CHOICE],
            'rest': [Situation.REST, Situation.KINDNESS_SHOWN],
        }

        situations = scene_situations.get(scene_type, [Situation.NONE])

        for sit in situations:
            reactions = self.trigger_situation(sit, location)
            for npc, reaction in reactions:
                events.append(f"{npc.name} → {reaction}")

        return events

    def get_drama_potential(self) -> Dict[str, Any]:
        """Analyze potential for emergent drama"""
        conflicts = []

        npcs = list(self.npcs.values())
        for i, npc1 in enumerate(npcs):
            for npc2 in npcs[i+1:]:
                # Check for trait conflicts
                if npc1.has_trait(Trait.HONEST) and npc2.is_hidden():
                    conflicts.append(f"{npc1.name} may expose {npc2.name}")
                if npc1.has_trait(Trait.GREEDY) and npc2.has_trait(Trait.GREEDY):
                    conflicts.append(f"{npc1.name} and {npc2.name} will compete")
                if npc1.has_trait(Trait.VENGEFUL) and npc1.grudge > 50:
                    conflicts.append(f"{npc1.name} seeks revenge")

        # Check betrayal potential
        potential_betrayers = []
        for npc in npcs:
            betrayal = self.check_betrayal_conditions(npc)
            if betrayal:
                potential_betrayers.append((npc.name, betrayal))

        return {
            'conflicts': conflicts,
            'potential_betrayers': potential_betrayers,
            'hidden_roles': [npc.name for npc in npcs if npc.is_hidden()],
            'total_npcs': len(npcs),
            'total_bytes': len(npcs) * 4,
        }

    def to_bytes(self) -> bytes:
        """Export all NPCs as Z80-ready bytes"""
        # Header: NPC count (1 byte)
        data = struct.pack('B', len(self.npcs))

        # NPC data
        for npc in sorted(self.npcs.values(), key=lambda n: n.id):
            data += npc.to_bytes()

        return data

    def to_asm(self) -> str:
        """Export as Z80 assembly data"""
        lines = [
            "; Social Physics NPC Data",
            f"; NPCs: {len(self.npcs)}",
            f"; Total: {len(self.npcs) * 4 + 1} bytes",
            "",
            "NPC_DATA:",
            f"    db {len(self.npcs)}      ; NPC count",
            "",
        ]

        for npc in sorted(self.npcs.values(), key=lambda n: n.id):
            traits_str = ' | '.join(t.name for t in Trait if npc.traits & t and t != Trait.NONE)
            lines.append(f"    ; NPC {npc.id}: {npc.name}")
            lines.append(f"    ; Traits: {traits_str or 'NONE'}")
            lines.append(f"    ; Role: {npc.role.name} (true: {npc.true_role.name})")
            lines.append(f"    db ${npc.traits:02X}, ${npc.trust:02X}, "
                        f"${(npc.role | (npc.true_role << 4)):02X}, ${npc.location:02X}")
            lines.append("")

        return '\n'.join(lines)


# =============================================================================
# DEMO
# =============================================================================

def demo():
    """Demonstrate emergent drama from social physics"""
    print("=" * 60)
    print("SOCIAL PHYSICS ENGINE DEMO")
    print("=" * 60)
    print()

    engine = SocialPhysicsEngine(seed=12345)

    # Create cast
    engine.create_npc(0, "Hero", role=Role.HELPER)
    engine.npcs[0].traits = Trait.HONEST | Trait.BRAVE | Trait.KIND

    engine.create_npc(1, "Grimbold", archetype="Power-Hungry",
                      role=Role.HELPER, hidden_role=Role.HIDDEN_VILLAIN)
    engine.npcs[1].trust = 60  # Suspicious

    engine.create_npc(2, "Elara", archetype="Gentle Soul", role=Role.HELPER)
    engine.npcs[2].trust = 180  # Very trusting

    engine.create_npc(3, "Valdris", archetype="Fierce Avenger", role=Role.NEUTRAL)
    engine.npcs[3].grudge = 80  # Has grudge

    # Print cast
    print("CAST:")
    print("-" * 40)
    for npc in engine.npcs.values():
        hidden = " [HIDDEN: " + npc.true_role.name + "]" if npc.is_hidden() else ""
        print(f"  {npc.name}: {npc.get_archetype()}")
        print(f"    Role: {npc.role.name}{hidden}")
        print(f"    Trust: {npc.trust}, Grudge: {npc.grudge}")
    print()

    # Analyze drama potential
    print("DRAMA POTENTIAL:")
    print("-" * 40)
    analysis = engine.get_drama_potential()
    for conflict in analysis['conflicts']:
        print(f"  ! {conflict}")
    for name, betrayal in analysis['potential_betrayers']:
        print(f"  !! {name} may commit {betrayal}")
    print()

    # Simulate scenes
    print("SCENE SIMULATIONS:")
    print("-" * 40)

    scenes = ['battle', 'treasure', 'revelation']
    for scene in scenes:
        print(f"\n  Scene: {scene.upper()}")
        events = engine.simulate_scene(scene)
        for event in events:
            print(f"    → {event}")

    # Show Z80 output
    print("\n" + "=" * 60)
    print("Z80 ASSEMBLY OUTPUT")
    print("=" * 60)
    print(engine.to_asm())

    # Size analysis
    print(f"\nTotal size: {len(engine.to_bytes())} bytes for {len(engine.npcs)} NPCs")


if __name__ == '__main__':
    demo()
