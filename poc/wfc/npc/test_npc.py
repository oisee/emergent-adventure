#!/usr/bin/env python3
"""
Test script for the NPC Mind System

Tests all components:
- ForthLisp VM
- Beliefs, Desires, Personality
- Memory and Relationships
- Fractal Roles
- NLP Processing
"""

import sys


def test_forthlisp():
    """Test ForthLisp lexer, parser, and VM"""
    print("=== Testing ForthLisp ===\n")

    from .forthlisp.lexer import Lexer
    from .forthlisp.parser import Parser
    from .forthlisp.vm import ForthLispVM

    source = '''
    ; Simple arithmetic
    2 3 + dup *

    ; Conditional
    true if
        "yes" say
    else
        "no" say
    then
    '''

    lexer = Lexer(source)
    tokens = lexer.tokenize()
    print(f"Tokens: {len(tokens)}")

    parser = Parser(tokens)
    ast = parser.parse()
    print(f"AST children: {len(ast.children)}")

    vm = ForthLispVM()
    bytecode = vm.compile(ast)
    print(f"Bytecode: {len(bytecode)} bytes")

    state = vm.execute(bytecode)
    print(f"Stack: {state.data_stack}")
    print(f"Output: {state.output}")
    print(f"Error: {state.error}")

    assert state.data_stack == [25], f"Expected [25], got {state.data_stack}"
    assert "yes" in state.output, f"Expected 'yes' in output"
    print("\nForthLisp: PASSED\n")


def test_beliefs():
    """Test belief system"""
    print("=== Testing Beliefs ===\n")

    from .mind.beliefs import BeliefSystem, BeliefSource

    beliefs = BeliefSystem()
    beliefs.set("hero-trustworthy", True, confidence=0.8, source=BeliefSource.OBSERVATION)
    beliefs.set("world-is-dangerous", True, confidence=0.6)

    val, conf = beliefs.get("hero-trustworthy")
    print(f"hero-trustworthy: {val} ({conf:.0%})")
    assert val == True and conf == 0.8

    assert beliefs.believes("hero-trustworthy", True, 0.5)
    assert not beliefs.believes("unknown-belief")

    # Test alignment
    alignment = beliefs.alignment_with({"hero-trustworthy": True})
    print(f"Alignment with hero-trustworthy=True: {alignment:.2f}")
    assert alignment > 0

    print("\nBeliefs: PASSED\n")


def test_desires():
    """Test desire system"""
    print("=== Testing Desires ===\n")

    from .mind.desires import DesireSystem, DesireState

    desires = DesireSystem()
    desires.add("protect-village", priority=0.9)
    desires.add("find-treasure", priority=0.5)
    desires.add("rest", priority=0.3)

    # Activate desires
    desires.desires["protect-village"].activate()
    desires.desires["find-treasure"].activate()

    active = desires.get_active()
    print(f"Active desires: {[d.key for d in active]}")
    assert len(active) == 2
    assert active[0].key == "protect-village"  # Highest priority first

    top = desires.get_top_desire()
    print(f"Top desire: {top.key} ({top.priority:.0%})")
    assert top.key == "protect-village"

    print("\nDesires: PASSED\n")


def test_personality():
    """Test personality system"""
    print("=== Testing Personality ===\n")

    from .mind.personality import Personality, Archetype

    # Create random personality
    p = Personality.random(Archetype.SAGE)
    print(f"Random Sage: {p.describe()}")
    print(f"Trust threshold: {p.get_trust_threshold():.2f}")
    print(f"Speech style: {p.get_speech_style()}")

    # Test willingness modification
    base = 0.5
    modified = p.modify_willingness(base)
    print(f"Willingness: {base:.0%} -> {modified:.0%}")

    print("\nPersonality: PASSED\n")


def test_memory():
    """Test memory system"""
    print("=== Testing Memory ===\n")

    from .mind.memory import MemorySystem, MemoryType

    memory = MemorySystem()

    memory.remember(
        "saved-child",
        "Hero saved a child from drowning",
        memory_type=MemoryType.EVENT,
        participants={"hero", "child"},
        emotional_valence=0.8
    )

    assert memory.is_remembered("saved-child")
    print(f"saved-child remembered: {memory.is_remembered('saved-child')}")

    # Recall
    m = memory.recall("saved-child")
    print(f"Recalled: {m.content}")
    assert "Hero" in m.content

    # Find by participant
    hero_memories = memory.find_by_participant("hero")
    print(f"Memories involving hero: {len(hero_memories)}")
    assert len(hero_memories) == 1

    print("\nMemory: PASSED\n")


def test_relationships():
    """Test relationship system"""
    print("=== Testing Relationships ===\n")

    from .mind.relationships import RelationshipSystem, RelationshipType

    rels = RelationshipSystem()

    # Set up relationship
    rels.set_trust("hero", 0.7)
    rels.set_fear("dark_lord", 0.9)
    rels.set_type("hero", RelationshipType.ALLY)

    print(f"Trust for hero: {rels.get_trust('hero'):.2f}")
    print(f"Fear of dark_lord: {rels.get_fear('dark_lord'):.2f}")
    print(f"Disposition toward hero: {rels.get_disposition('hero'):.2f}")

    assert rels.get_trust("hero") == 0.7
    assert rels.get_fear("dark_lord") == 0.9

    friends = rels.get_friends()
    print(f"Friends: {friends}")
    assert "hero" in friends

    print("\nRelationships: PASSED\n")


def test_fractal_roles():
    """Test fractal role system"""
    print("=== Testing Fractal Roles ===\n")

    from .archetypes.fractal_roles import (
        FractalRoleSystem, FractalRole, ActantRole, NarrativeLevel
    )

    system = FractalRoleSystem()

    # Assign roles
    system.assign_role("sage",
                       macro_role=ActantRole.MENTOR,
                       meso_role=ActantRole.SENDER)

    system.assign_role("knight",
                       macro_role=ActantRole.HELPER,
                       meso_role=ActantRole.OPPONENT)

    # Add betrayal transition
    system.add_transition("knight",
                          from_role=ActantRole.HELPER,
                          to_role=ActantRole.SHADOW,
                          trigger="betrayal",
                          at_level=NarrativeLevel.MACRO)

    # Check roles
    sage_role = system.get_role("sage")
    print(f"Sage macro role: {sage_role.macro_role.name}")
    print(f"Sage is helpful: {sage_role.is_helpful()}")
    assert sage_role.is_helpful()

    knight_role = system.get_role("knight")
    print(f"Knight meso role: {knight_role.meso_role.name}")
    assert knight_role.meso_role == ActantRole.OPPONENT

    # Trigger betrayal
    system.trigger_event("betrayal")
    knight_role = system.get_role("knight")
    print(f"Knight macro role after betrayal: {knight_role.macro_role.name}")
    assert knight_role.macro_role == ActantRole.SHADOW

    print("\nFractal Roles: PASSED\n")


def test_npc_mind():
    """Test complete NPC mind"""
    print("=== Testing NPC Mind ===\n")

    from .mind.npc_mind import NPCMind
    from .mind.personality import Archetype

    npc = NPCMind.create(
        name="Elder Sage",
        archetype=Archetype.SAGE,
        initial_beliefs={"hero-trustworthy": True},
        initial_desires={"protect-village": 0.9}
    )

    print(npc.describe())
    print()

    # Test request evaluation
    npc.relationships.set_trust("player", 0.6)
    score, response = npc.evaluate_request(
        requester="player",
        action="help with quest"
    )
    print(f"Request evaluation: {response} ({score:.0%})")
    assert 0.0 <= score <= 1.0  # Score should be valid
    assert response in ("agree", "refuse", "hesitate")  # Response should be valid

    print("\nNPC Mind: PASSED\n")


def test_nlp_commands():
    """Test NLP command parsing"""
    print("=== Testing NLP Commands ===\n")

    from .nlp.commands import parse_command, CommandType

    tests = [
        ("suggest elder help", CommandType.SUGGEST, "elder"),
        ("convince guard let pass because danger", CommandType.CONVINCE, "guard"),
        ("command soldier attack", CommandType.COMMAND, "soldier"),
    ]

    for text, expected_type, expected_target in tests:
        cmd = parse_command(text)
        print(f"'{text}' -> {cmd.command_type.name}, target={cmd.target_npc}")
        assert cmd is not None
        assert cmd.command_type == expected_type
        assert cmd.target_npc == expected_target

    print("\nNLP Commands: PASSED\n")


def test_nlp_processing():
    """Test NLP interaction processing"""
    print("=== Testing NLP Processing ===\n")

    from .mind.npc_mind import NPCMind
    from .mind.personality import Archetype
    from .nlp.commands import parse_command
    from .nlp.processing import NPCInteractionProcessor

    npc = NPCMind.create(
        name="Guard",
        archetype=Archetype.RULER,
        initial_beliefs={"duty-first": True},
        initial_desires={"protect-gate": 0.9}
    )
    npc.relationships.set_trust("player", 0.3)

    processor = NPCInteractionProcessor()

    command = parse_command("suggest guard let me pass")
    result = processor.process(npc, command)

    print(f"Willingness: {result.willingness:.0%}")
    print(f"Outcome: {result.response_type}")
    print(f"Response: {result.response_text}")

    print("\nNLP Processing: PASSED\n")


def test_plot_role_integration():
    """Test plot-role integration"""
    print("=== Testing Plot-Role Integration ===\n")

    from .integration.plot_roles import PlotRoleIntegrator, PROPP_ROLE_INVOLVEMENT
    from .archetypes.fractal_roles import ActantRole, NarrativeLevel
    from ..plot_fractal import (
        FractalPlotGenerator, FractalPlot, FractalPlotNode,
        ProppFunc, NarrativeLevel as PlotLevel, GENRES
    )

    # Create integrator
    integrator = PlotRoleIntegrator()

    # Register NPCs
    integrator.register_npc("Elder Sage", ActantRole.MENTOR)
    integrator.register_npc("Dark Knight", ActantRole.OPPONENT)
    integrator.register_npc("Loyal Squire", ActantRole.HELPER)

    assert len(integrator.npc_names) == 3
    print(f"Registered NPCs: {integrator.npc_names}")

    # Generate a plot
    gen = FractalPlotGenerator(GENRES["fantasy"], seed=42)
    gen.generate(PlotLevel.MACRO, depth=2, finale=ProppFunc.VICTORY)
    plot = gen.plot

    assert len(plot.nodes) > 0
    print(f"Generated plot with {plot.get_total_node_count()} total nodes")

    # Assign roles
    npc_roster = {
        "Elder Sage": ActantRole.MENTOR,
        "Dark Knight": ActantRole.OPPONENT,
        "Loyal Squire": ActantRole.HELPER,
    }
    assignment = integrator.assign_plot_roles(plot, npc_roster=npc_roster)

    assert len(assignment.assignments) > 0
    print(f"NPCs assigned: {list(assignment.assignments.keys())}")

    # Check fractal roles were updated
    sage_role = integrator.role_system.get_role("Elder Sage")
    assert sage_role is not None
    print(f"Elder Sage role: {sage_role.get_role().name if sage_role.get_role() else 'None'}")

    # Test cast list generation
    cast_list = integrator.generate_cast_list()
    assert "MENTOR" in cast_list or "Elder Sage" in cast_list
    print(f"\nCast list generated ({len(cast_list)} chars)")

    # Test plot event handling
    integrator.on_plot_event(ProppFunc.RECOGNITION)
    print("Plot event RECOGNITION processed")

    # Test serialization
    data = integrator.to_dict()
    assert "role_system" in data
    assert "npc_names" in data
    print(f"Serialized to dict with {len(data)} keys")

    print("\nPlot-Role Integration: PASSED\n")


def main():
    """Run all tests"""
    print("=" * 60)
    print("NPC MIND SYSTEM TEST SUITE")
    print("=" * 60)
    print()

    try:
        test_forthlisp()
        test_beliefs()
        test_desires()
        test_personality()
        test_memory()
        test_relationships()
        test_fractal_roles()
        test_npc_mind()
        test_nlp_commands()
        test_nlp_processing()
        test_plot_role_integration()

        print("=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
