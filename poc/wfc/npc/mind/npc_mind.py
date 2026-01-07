"""
NPC Mind

The main class that integrates all mind components:
- Beliefs
- Desires
- Personality
- Memory
- Relationships
- ForthLisp VM for behavior scripts
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Callable
import random

from .beliefs import BeliefSystem, BeliefSource
from .desires import DesireSystem, DesireState
from .personality import Personality, Archetype
from .memory import MemorySystem, MemoryType
from .relationships import RelationshipSystem, RelationshipType


@dataclass
class NPCMind:
    """
    Complete NPC mind integrating all cognitive systems.

    The mind is driven by:
    1. Beliefs - What the NPC thinks is true
    2. Desires - What the NPC wants
    3. Personality - How the NPC behaves
    4. Memory - What the NPC remembers
    5. Relationships - How the NPC views others
    """

    name: str
    personality: Personality = field(default_factory=Personality)

    # Cognitive systems
    beliefs: BeliefSystem = field(default_factory=BeliefSystem)
    desires: DesireSystem = field(default_factory=DesireSystem)
    memory: MemorySystem = field(default_factory=MemorySystem)
    relationships: RelationshipSystem = field(default_factory=RelationshipSystem)

    # Behavior script (ForthLisp)
    behavior_script: str = ""
    compiled_behavior: bytes = field(default_factory=bytes)

    # Current state
    current_location: Optional[Tuple[int, int]] = None
    is_alive: bool = True
    energy: float = 1.0

    def __post_init__(self):
        self.personality.name = self.name

    @classmethod
    def create(cls, name: str,
               archetype: Archetype = None,
               initial_beliefs: Dict[str, Any] = None,
               initial_desires: Dict[str, float] = None) -> 'NPCMind':
        """Create a new NPC with random personality"""
        npc = cls(
            name=name,
            personality=Personality.random(archetype),
        )

        # Set initial beliefs
        if initial_beliefs:
            for key, value in initial_beliefs.items():
                npc.beliefs.set(key, value, source=BeliefSource.INNATE)

        # Set initial desires
        if initial_desires:
            for key, priority in initial_desires.items():
                npc.desires.add(key, priority)

        return npc

    def tick(self):
        """Update all systems for one game tick"""
        # Decay beliefs
        self.beliefs.tick()

        # Update desires based on beliefs
        self.desires.tick(lambda k: self.beliefs.believes(k))

        # Decay memories
        self.memory.tick()

        # Energy recovery
        if self.energy < 1.0:
            self.energy = min(1.0, self.energy + 0.05)

    # =========================================================================
    # Belief Interface (for VM)
    # =========================================================================

    def get_belief(self, key: str) -> Tuple[Any, float]:
        """Get belief value and confidence"""
        return self.beliefs.get(key)

    def set_belief(self, key: str, value: Any, confidence: float = 1.0):
        """Set a belief"""
        self.beliefs.set(key, value, confidence, source=BeliefSource.TOLD)

    # =========================================================================
    # Desire Interface (for VM)
    # =========================================================================

    def get_desire_priority(self, key: str) -> float:
        """Get desire priority"""
        return self.desires.get_priority(key)

    def set_desire_priority(self, key: str, priority: float):
        """Set desire priority"""
        self.desires.set_priority(key, priority)

    # =========================================================================
    # Memory Interface (for VM)
    # =========================================================================

    def remember_event(self, key: str, content: str,
                       participants: set = None,
                       emotional_valence: float = 0.0):
        """Remember an event"""
        self.memory.remember(
            key=key,
            content=content,
            memory_type=MemoryType.EVENT,
            participants=participants or set(),
            emotional_valence=emotional_valence,
        )

    def is_remembered(self, key: str) -> bool:
        """Check if something is remembered"""
        return self.memory.is_remembered(key)

    def recall_memory(self, key: str) -> Optional[str]:
        """Recall a memory"""
        return self.memory.get_value(key)

    def store_fact(self, key: str, value: Any):
        """Store a simple fact"""
        self.memory.store(key, value)

    # =========================================================================
    # Relationship Interface (for VM)
    # =========================================================================

    def get_trust(self, target: str) -> float:
        """Get trust for target"""
        return self.relationships.get_trust(target)

    def set_trust(self, target: str, value: float):
        """Set trust for target"""
        self.relationships.set_trust(target, value)

    def get_fear(self, target: str) -> float:
        """Get fear of target"""
        return self.relationships.get_fear(target)

    def set_fear(self, target: str, value: float):
        """Set fear of target"""
        self.relationships.set_fear(target, value)

    def get_loyalty(self, target: str) -> float:
        """Get loyalty to target"""
        return self.relationships.get_loyalty(target)

    def set_loyalty(self, target: str, value: float):
        """Set loyalty to target"""
        self.relationships.set_loyalty(target, value)

    # =========================================================================
    # Request Evaluation
    # =========================================================================

    def evaluate_request(self, requester: str, action: str,
                         action_beliefs: Dict[str, Any] = None,
                         action_effects: Dict[str, bool] = None,
                         command_type: str = "suggest") -> Tuple[float, str]:
        """
        Evaluate a request and return willingness score.

        Args:
            requester: Who is making the request
            action: What they want the NPC to do
            action_beliefs: Belief requirements for action
            action_effects: How action affects desires
            command_type: Type of command (suggest, convince, persuade, command)

        Returns:
            (willingness: 0-1, response_type: agree/refuse/hesitate)
        """
        # Base willingness by command type
        base_willingness = {
            'suggest': 0.3,
            'convince': 0.4,
            'persuade': 0.5,
            'command': 0.6,
            'manipulate': 0.7,
        }.get(command_type, 0.4)

        score = base_willingness

        # Check belief alignment
        if action_beliefs:
            belief_score = self.beliefs.alignment_with(action_beliefs)
            if belief_score < -0.3:
                return (0.0, "refuse")  # Strongly conflicts with beliefs
            score += belief_score * 0.3

        # Check desire alignment
        if action_effects:
            desire_score = self.desires.alignment_with(action_effects)
            score += desire_score * 0.3

        # Check relationship with requester
        relationship = self.relationships.get(requester)
        score += relationship.trust * 0.2
        score -= relationship.fear * 0.1  # Fear motivates but breeds resentment

        # Personality modifiers
        score = self.personality.modify_willingness(
            score,
            request_type='normal',
            requester_known=(relationship.interactions > 0)
        )

        # Energy check
        if self.energy < 0.3:
            score -= 0.2

        # Check trust threshold
        trust_threshold = self.personality.get_trust_threshold()
        if relationship.trust < trust_threshold and command_type not in ('command', 'manipulate'):
            score *= 0.5  # Halve willingness if trust is low

        # Determine response
        score = max(0.0, min(1.0, score))

        if score > 0.7:
            return (score, "agree")
        elif score > 0.4:
            return (score, "hesitate")
        else:
            return (score, "refuse")

    def process_request_outcome(self, requester: str, agreed: bool):
        """Process the outcome of a request"""
        if agreed:
            self.relationships.record_interaction(requester, positive=True)
            self.energy -= 0.1
        else:
            # Refusing doesn't necessarily mean negative interaction
            pass

    # =========================================================================
    # Autonomous Actions
    # =========================================================================

    def evaluate_autonomous_action(self) -> Optional[Tuple[str, Any]]:
        """
        Determine what action the NPC wants to take on their own.

        Returns (action_type, action_data) or None.
        """
        if self.energy < 0.2:
            return ('rest', None)

        # Get top desire
        top_desire = self.desires.get_top_desire()
        if not top_desire:
            return None

        # Map desires to actions
        desire_actions = {
            'protect-village': ('patrol', {'area': 'village'}),
            'find-treasure': ('search', {'type': 'treasure'}),
            'help-hero': ('follow', {'target': 'hero'}),
            'defeat-enemy': ('attack', {'target': 'enemy'}),
            'gather-information': ('investigate', None),
            'rest': ('rest', None),
        }

        if top_desire.key in desire_actions:
            return desire_actions[top_desire.key]

        # Default to archetype preference
        action_pref = self.personality.get_archetype_action()
        return (action_pref, None)

    # =========================================================================
    # Speech Generation
    # =========================================================================

    def generate_response(self, context: str, mood: str = "neutral") -> str:
        """Generate a response based on personality and context"""
        style = self.personality.get_speech_style()

        # This would ideally use templates or more sophisticated generation
        # For now, return placeholder
        if mood == "refuse":
            if style.get('formality', 0.5) > 0.7:
                return "I'm afraid I cannot assist with that."
            else:
                return "Nope, not doing that."
        elif mood == "agree":
            if style.get('warmth', 0.5) > 0.7:
                return "Of course! I'd be happy to help."
            else:
                return "Fine, I'll do it."
        elif mood == "hesitate":
            return "I'm not sure... let me think about it."
        else:
            return "..."

    # =========================================================================
    # Serialization
    # =========================================================================

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            'name': self.name,
            'personality': self.personality.to_dict(),
            'beliefs': self.beliefs.to_dict(),
            'desires': self.desires.to_dict(),
            'memory': self.memory.to_dict(),
            'relationships': self.relationships.to_dict(),
            'behavior_script': self.behavior_script,
            'current_location': self.current_location,
            'is_alive': self.is_alive,
            'energy': self.energy,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NPCMind':
        """Deserialize from dictionary"""
        npc = cls(
            name=data['name'],
            personality=Personality.from_dict(data['personality']),
            beliefs=BeliefSystem.from_dict(data['beliefs']),
            desires=DesireSystem.from_dict(data['desires']),
            memory=MemorySystem.from_dict(data['memory']),
            relationships=RelationshipSystem.from_dict(data['relationships']),
            behavior_script=data.get('behavior_script', ''),
            current_location=data.get('current_location'),
            is_alive=data.get('is_alive', True),
            energy=data.get('energy', 1.0),
        )
        return npc

    def describe(self) -> str:
        """Get human-readable description of NPC"""
        lines = [
            f"=== {self.name} ===",
            self.personality.describe(),
            "",
            f"Energy: {self.energy:.0%}",
            f"Location: {self.current_location}",
            "",
            "Strong Beliefs:",
        ]

        for belief in self.beliefs.get_strong_beliefs()[:5]:
            lines.append(f"  - {belief.key}: {belief.value} ({belief.confidence:.0%})")

        lines.append("")
        lines.append("Active Desires:")
        for desire in self.desires.get_active()[:5]:
            lines.append(f"  - {desire.key} (priority: {desire.effective_priority():.0%})")

        lines.append("")
        lines.append("Relationships:")
        for target, rel in list(self.relationships.relationships.items())[:5]:
            disp = rel.get_disposition()
            lines.append(f"  - {target}: {disp:+.2f} (trust: {rel.trust:+.2f})")

        return '\n'.join(lines)


# =============================================================================
# Demo
# =============================================================================

def demo():
    """Demo NPC Mind"""
    print("=== NPC Mind Demo ===\n")

    # Create NPC
    npc = NPCMind.create(
        name="Elder Sage",
        archetype=Archetype.SAGE,
        initial_beliefs={
            "magic-is-dangerous": True,
            "hero-is-chosen": True,
            "village-needs-protection": True,
        },
        initial_desires={
            "protect-village": 0.9,
            "share-wisdom": 0.7,
            "find-apprentice": 0.5,
        }
    )

    # Set up some relationships
    npc.relationships.set_trust("hero", 0.6)
    npc.relationships.set_trust("stranger", 0.0)
    npc.relationships.set_type("hero", RelationshipType.ALLY)

    # Remember some things
    npc.remember_event("hero-saved-child", "The hero saved a child from the river",
                       participants={"hero"}, emotional_valence=0.8)

    print(npc.describe())
    print()

    # Evaluate requests
    print("=== Request Evaluation ===\n")

    # Request from trusted hero
    score, response = npc.evaluate_request(
        requester="hero",
        action="help-with-quest",
        action_effects={"protect-village": True}
    )
    print(f"Hero asks for help with quest: {response} ({score:.0%} willingness)")

    # Request from stranger
    score, response = npc.evaluate_request(
        requester="stranger",
        action="give-artifact",
        action_beliefs={"magic-is-dangerous": False}  # Conflicts
    )
    print(f"Stranger asks for artifact: {response} ({score:.0%} willingness)")

    # Command from hero
    score, response = npc.evaluate_request(
        requester="hero",
        action="dangerous-mission",
        command_type="command"
    )
    print(f"Hero commands dangerous mission: {response} ({score:.0%} willingness)")


if __name__ == "__main__":
    demo()
