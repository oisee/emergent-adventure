"""
NLP Interaction Processing

Handles the full pipeline of player-NPC interaction:
1. Parse command
2. Evaluate willingness
3. Generate response
4. Update relationships
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import random

from .commands import (
    CommandType, NPCCommand, COMMAND_PROPERTIES,
    parse_command, get_response_template
)


@dataclass
class InteractionResult:
    """Result of an NPC interaction"""
    success: bool                    # Did the NPC agree?
    willingness: float              # 0.0-1.0 willingness score
    response_type: str              # 'agree', 'refuse', 'hesitate'
    response_text: str              # What the NPC says
    relationship_change: float      # How relationship changed
    detected_manipulation: bool     # Was manipulation detected?
    additional_effects: Dict[str, Any] = field(default_factory=dict)


class NPCInteractionProcessor:
    """
    Processes player-NPC interactions.

    Uses NPC's mind state to determine:
    - Whether they will comply
    - How they respond
    - How the interaction affects the relationship
    """

    def __init__(self):
        # Modifiers that can be added dynamically
        self.global_modifiers: Dict[str, float] = {}

    def process(self, npc_mind, command: NPCCommand,
                player_authority: float = 0.5,
                fractal_role=None) -> InteractionResult:
        """
        Process an interaction between player and NPC.

        Args:
            npc_mind: NPCMind instance
            command: Parsed command
            player_authority: Player's authority level (0-1)
            fractal_role: Optional FractalRole for behavior modifiers

        Returns:
            InteractionResult
        """
        # Get command properties
        props = command.get_properties()

        # Start with base success rate
        willingness = props['base_success']

        # Get relationship with player
        relationship = npc_mind.relationships.get("player")

        # Trust modifier
        trust_effect = relationship.trust * props['trust_modifier']
        willingness += trust_effect

        # Relationship modifier (based on overall disposition)
        disposition = relationship.get_disposition()
        rel_effect = disposition * props['relationship_modifier']
        willingness += rel_effect

        # Personality modifiers
        personality = npc_mind.personality
        agree_effect = (personality.agreeableness - 0.5) * props['agreeableness_modifier']
        willingness += agree_effect

        # Intelligence/openness effect (for convince)
        if props['intelligence_modifier'] != 0:
            intel_effect = (personality.openness - 0.5) * props['intelligence_modifier']
            willingness += intel_effect

        # Authority effect (for command)
        if props['authority_modifier'] != 0:
            auth_effect = player_authority * props['authority_modifier']
            willingness += auth_effect
            # Fear also helps commands
            willingness += relationship.fear * 0.2

        # Fractal role modifiers
        if fractal_role:
            behavior = fractal_role.get_effective_behavior()
            willingness += behavior.get('help_tendency', 0) * 0.3

            # Opponents are much less likely to help
            if fractal_role.is_hostile():
                willingness *= 0.3

        # Check for belief alignment
        # (In a full implementation, we'd analyze the action against beliefs)
        # For now, use a simplified check
        action_lower = command.action.lower()
        if 'help' in action_lower or 'assist' in action_lower:
            if npc_mind.beliefs.believes("hero-is-trustworthy"):
                willingness += 0.2
        elif 'attack' in action_lower or 'harm' in action_lower:
            if personality.agreeableness > 0.6:
                willingness -= 0.3

        # Check for desire alignment
        top_desire = npc_mind.desires.get_top_desire()
        if top_desire:
            # If action helps their desire, more willing
            if top_desire.key in action_lower or 'help' in action_lower:
                willingness += 0.2

        # Evidence bonus (for convince)
        if command.evidence:
            willingness += 0.1 * len(command.evidence)

        # Emotional appeal bonus (for persuade)
        if command.emotional_appeal:
            willingness += 0.1

        # Energy check
        if npc_mind.energy < 0.3:
            willingness -= 0.2

        # Apply global modifiers
        for modifier_value in self.global_modifiers.values():
            willingness += modifier_value

        # Clamp willingness
        willingness = max(0.0, min(1.0, willingness))

        # Check manipulation detection
        detected_manipulation = False
        if command.command_type == CommandType.MANIPULATE:
            detection_risk = props['detection_risk']
            # Smarter NPCs detect manipulation more often
            detection_risk += (personality.openness - 0.5) * 0.2
            if random.random() < detection_risk:
                detected_manipulation = True
                willingness = 0.0  # Automatic refusal if caught

        # Determine outcome
        roll = random.random()
        if willingness > 0.7 or roll < willingness:
            response_type = 'agree'
            success = True
        elif willingness > 0.3:
            response_type = 'hesitate'
            success = False
        else:
            response_type = 'refuse'
            success = False

        # Generate response text
        if detected_manipulation:
            response_text = "Do you think me a fool? I see through your manipulation!"
            response_type = 'refuse'
            success = False
        else:
            # Determine mood based on disposition and response
            if response_type == 'agree':
                if disposition > 0.3:
                    mood = 'supportive'
                elif disposition < -0.3:
                    mood = 'reluctant'
                else:
                    mood = 'neutral'
            elif response_type == 'refuse':
                if disposition > 0:
                    mood = 'polite'
                elif relationship.fear > 0.5:
                    mood = 'polite'  # Fearful but refusing
                else:
                    mood = 'firm' if disposition > -0.5 else 'hostile'
            else:  # hesitate
                if len(command.conditions) > 0:
                    mood = 'conditional'
                else:
                    mood = 'uncertain'

            response_text = get_response_template(response_type, mood)

        # Calculate relationship change
        relationship_change = 0.0
        if success:
            # Successful interaction slightly improves relationship
            relationship_change = 0.05
        elif detected_manipulation:
            # Getting caught manipulating damages trust significantly
            relationship_change = -0.3
        elif response_type == 'refuse' and command.command_type == CommandType.COMMAND:
            # Resisting commands can build resentment
            relationship_change = -0.1

        # Update NPC state
        if relationship_change != 0:
            npc_mind.relationships.modify_trust("player", relationship_change)
            npc_mind.relationships.record_interaction("player", success)

        # Remember the interaction
        npc_mind.remember_event(
            f"interaction-{npc_mind.memory.tick_count}",
            f"Player asked me to {command.action}. I {'agreed' if success else 'refused'}.",
            participants={"player"},
            emotional_valence=0.2 if success else (-0.3 if detected_manipulation else -0.1),
        )

        # Use energy if agreed
        if success:
            npc_mind.energy = max(0.0, npc_mind.energy - 0.1)

        return InteractionResult(
            success=success,
            willingness=willingness,
            response_type=response_type,
            response_text=response_text,
            relationship_change=relationship_change,
            detected_manipulation=detected_manipulation,
        )

    def add_modifier(self, key: str, value: float):
        """Add a global willingness modifier"""
        self.global_modifiers[key] = value

    def remove_modifier(self, key: str):
        """Remove a global modifier"""
        if key in self.global_modifiers:
            del self.global_modifiers[key]


# =============================================================================
# Demo
# =============================================================================

def demo():
    """Demo NLP processing"""
    from ..mind import NPCMind
    from ..mind.personality import Archetype

    print("=== NLP Processing Demo ===\n")

    # Create NPC
    npc = NPCMind.create(
        name="Village Elder",
        archetype=Archetype.SAGE,
        initial_beliefs={
            "hero-is-trustworthy": True,
            "village-in-danger": True,
        },
        initial_desires={
            "protect-village": 0.9,
            "share-wisdom": 0.7,
        }
    )

    # Set up relationship
    npc.relationships.set_trust("player", 0.4)

    # Create processor
    processor = NPCInteractionProcessor()

    # Test various commands
    test_commands = [
        "suggest elder help with quest",
        "convince elder give information because village in danger",
        "command elder attack enemy",
        "manipulate elder give secret",
    ]

    for cmd_text in test_commands:
        print(f"Command: {cmd_text}")

        command = parse_command(cmd_text)
        if command:
            result = processor.process(npc, command)

            print(f"  Type: {command.command_type.name}")
            print(f"  Willingness: {result.willingness:.0%}")
            print(f"  Outcome: {result.response_type}")
            print(f"  Response: \"{result.response_text}\"")
            if result.detected_manipulation:
                print(f"  ** MANIPULATION DETECTED! **")
            print(f"  Relationship change: {result.relationship_change:+.2f}")
        else:
            print("  (Could not parse command)")

        print()


if __name__ == "__main__":
    demo()
