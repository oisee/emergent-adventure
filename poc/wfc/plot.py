"""
Backward Plot Generator using Propp Functions

Generates story structure by working BACKWARD from finale.
Each node PROVIDES requirements that later nodes NEED.

Non-linear: multiple valid orderings allowed.
"""

from dataclasses import dataclass, field
from typing import List, Set, Tuple, Dict, Optional
from enum import IntEnum, IntFlag
import random


class ProppFunction(IntEnum):
    """8 essential Propp narrative functions"""
    LACK = 0        # Something missing/wrong (inciting incident)
    DEPARTURE = 1   # Hero sets out
    DONOR_TEST = 2  # Prove worthiness
    ACQUISITION = 3 # Get magic item/info
    GUIDANCE = 4    # Travel to goal
    STRUGGLE = 5    # Fight villain
    VICTORY = 6     # Defeat villain
    RETURN = 7      # Come home changed


class Requirement(IntFlag):
    """What a plot node needs to be reachable (8-bit+)"""
    NONE = 0
    HERO_EXISTS = 1 << 0   # Story has protagonist
    HAS_WEAPON = 1 << 1    # Combat capability
    HAS_KEY = 1 << 2       # Access item
    HAS_INFO = 1 << 3      # Knowledge gained
    HAS_ALLY = 1 << 4      # Helper joined
    HAS_ACCESS = 1 << 5    # Can reach location
    VILLAIN_WEAK = 1 << 6  # Vulnerability known
    AT_GOAL = 1 << 7       # Reached destination
    QUEST_COMPLETE = 1 << 8  # Extended for POC


class Provides(IntFlag):
    """What a plot node gives when completed (8-bit)"""
    NONE = 0
    HERO_EXISTS = 1 << 0
    HAS_WEAPON = 1 << 1
    HAS_KEY = 1 << 2
    HAS_INFO = 1 << 3
    HAS_ALLY = 1 << 4
    HAS_ACCESS = 1 << 5
    VILLAIN_WEAK = 1 << 6
    AT_GOAL = 1 << 7
    QUEST_COMPLETE = 1 << 8  # Extended beyond 8-bit for POC


# Propp function display names
PROPP_NAMES = {
    ProppFunction.LACK: "LACK",
    ProppFunction.DEPARTURE: "DEPARTURE",
    ProppFunction.DONOR_TEST: "DONOR_TEST",
    ProppFunction.ACQUISITION: "ACQUISITION",
    ProppFunction.GUIDANCE: "GUIDANCE",
    ProppFunction.STRUGGLE: "STRUGGLE",
    ProppFunction.VICTORY: "VICTORY",
    ProppFunction.RETURN: "RETURN",
}


@dataclass
class PlotNode:
    """Single node in plot graph (24-bit: func|req|provides)"""
    function: ProppFunction
    requires: int  # Bitmask of requirements
    provides: int  # Bitmask of what this provides

    # Runtime fields
    id: int = -1
    description: str = ""
    location_hint: str = ""  # Where this should happen
    actor_hint: str = ""     # Who is involved

    def __repr__(self):
        return f"PlotNode({PROPP_NAMES[self.function]}, req=0x{self.requires:02x}, prov=0x{self.provides:02x})"


# =============================================================================
# Plot Node Templates
# =============================================================================

# Each template defines: (function, base_requires, base_provides, description, location_hint)
# Multiple variants per function for variety

PLOT_TEMPLATES = {
    ProppFunction.LACK: [
        (Requirement.NONE, Provides.HERO_EXISTS,
         "Hero discovers the village is threatened", "village"),
        (Requirement.NONE, Provides.HERO_EXISTS,
         "Hero's mentor is kidnapped", "home"),
        (Requirement.NONE, Provides.HERO_EXISTS,
         "A great treasure is stolen from the realm", "castle"),
    ],

    ProppFunction.DEPARTURE: [
        (Requirement.HERO_EXISTS, Provides.HAS_ACCESS,
         "Hero leaves home to seek adventure", "road"),
        (Requirement.HERO_EXISTS, Provides.HAS_ACCESS,
         "Hero is banished and must prove worth", "clearing"),
        (Requirement.HERO_EXISTS | Requirement.HAS_INFO, Provides.HAS_ACCESS,
         "Hero follows the clue to distant lands", "road"),
    ],

    ProppFunction.DONOR_TEST: [
        (Requirement.HAS_ACCESS, Provides.NONE,
         "A wise sage tests the hero's courage", "temple"),
        (Requirement.HAS_ACCESS, Provides.NONE,
         "A mysterious stranger poses a riddle", "tavern"),
        (Requirement.HAS_ACCESS, Provides.VILLAIN_WEAK,
         "An ancient spirit reveals the enemy's weakness", "ruins"),
    ],

    ProppFunction.ACQUISITION: [
        (Requirement.HAS_ACCESS, Provides.HAS_WEAPON,
         "Hero receives a magic sword", "cave"),
        (Requirement.HAS_ACCESS, Provides.HAS_KEY,
         "Hero obtains the key to the dark fortress", "tower"),
        (Requirement.HAS_ACCESS, Provides.HAS_INFO,
         "Hero learns the secret path", "temple"),
        (Requirement.HAS_ACCESS, Provides.HAS_ALLY,
         "A loyal companion joins the quest", "tavern"),
    ],

    ProppFunction.GUIDANCE: [
        (Requirement.HAS_ACCESS, Provides.AT_GOAL,
         "Hero travels through dangerous lands", "mountain"),
        (Requirement.HAS_ACCESS | Requirement.HAS_KEY, Provides.AT_GOAL,
         "Hero unlocks the gate to the dark realm", "castle"),
        (Requirement.HAS_ACCESS | Requirement.HAS_INFO, Provides.AT_GOAL,
         "Hero follows the secret path to villain's lair", "dungeon"),
    ],

    ProppFunction.STRUGGLE: [
        (Requirement.AT_GOAL | Requirement.HAS_WEAPON, Provides.VILLAIN_WEAK,
         "Hero battles the dragon", "dungeon"),
        (Requirement.AT_GOAL, Provides.VILLAIN_WEAK,
         "Hero confronts the dark wizard", "tower"),
        (Requirement.AT_GOAL | Requirement.HAS_ALLY, Provides.VILLAIN_WEAK,
         "Hero and companion face the beast together", "cave"),
    ],

    ProppFunction.VICTORY: [
        (Requirement.VILLAIN_WEAK | Requirement.HAS_WEAPON, Provides.QUEST_COMPLETE,
         "Hero defeats the villain with the magic sword", "dungeon"),
        (Requirement.VILLAIN_WEAK | Requirement.HAS_INFO, Provides.QUEST_COMPLETE,
         "Hero uses secret knowledge to banish the evil", "tower"),
        (Requirement.VILLAIN_WEAK | Requirement.HAS_ALLY, Provides.QUEST_COMPLETE,
         "Companion sacrifices to ensure victory", "castle"),
    ],

    ProppFunction.RETURN: [
        (Requirement.QUEST_COMPLETE, Provides.NONE,
         "Hero returns home a changed person", "village"),
        (Requirement.QUEST_COMPLETE, Provides.NONE,
         "Hero is crowned and the realm is saved", "castle"),
        (Requirement.QUEST_COMPLETE, Provides.HAS_INFO,
         "Hero returns with wisdom for the next generation", "home"),
    ],
}


@dataclass
class PlotGraph:
    """
    Directed graph of plot nodes.

    Edges represent: "A must happen before B" (A provides what B requires).
    Non-linear: multiple valid topological orderings exist.
    """
    nodes: List[PlotNode] = field(default_factory=list)
    edges: Dict[int, List[int]] = field(default_factory=dict)  # node_id -> [successor_ids]
    reverse_edges: Dict[int, List[int]] = field(default_factory=dict)  # node_id -> [predecessor_ids]

    def add_node(self, node: PlotNode) -> int:
        """Add node and return its ID"""
        node.id = len(self.nodes)
        self.nodes.append(node)
        self.edges[node.id] = []
        self.reverse_edges[node.id] = []
        return node.id

    def add_edge(self, from_id: int, to_id: int):
        """Add edge: from_id must happen before to_id"""
        if to_id not in self.edges[from_id]:
            self.edges[from_id].append(to_id)
        if from_id not in self.reverse_edges[to_id]:
            self.reverse_edges[to_id].append(from_id)

    def get_roots(self) -> List[int]:
        """Get nodes with no predecessors (can start here)"""
        return [i for i, preds in self.reverse_edges.items() if not preds]

    def get_leaves(self) -> List[int]:
        """Get nodes with no successors (endings)"""
        return [i for i, succs in self.edges.items() if not succs]

    def topological_sort(self) -> List[int]:
        """Return one valid ordering (Kahn's algorithm)"""
        in_degree = {i: len(preds) for i, preds in self.reverse_edges.items()}
        queue = [i for i, d in in_degree.items() if d == 0]
        result = []

        while queue:
            # Pick randomly among ready nodes (non-deterministic for variety)
            node = random.choice(queue)
            queue.remove(node)
            result.append(node)

            for succ in self.edges[node]:
                in_degree[succ] -= 1
                if in_degree[succ] == 0:
                    queue.append(succ)

        return result if len(result) == len(self.nodes) else []


class BackwardPlotGenerator:
    """
    Generates plot by working BACKWARD from finale.

    Algorithm:
    1. Choose finale type (VICTORY, RETURN)
    2. Track unsatisfied requirements
    3. Work backward, selecting nodes that PROVIDE requirements
    4. Stop when all requirements satisfied (LACK node placed)
    """

    def __init__(self, seed: int = None):
        self.seed = seed
        if seed is not None:
            random.seed(seed)
        self.graph = PlotGraph()

    def reset(self, seed: int = None):
        """Reset generator"""
        if seed is not None:
            self.seed = seed
            random.seed(seed)
        self.graph = PlotGraph()

    def generate(self, include_return: bool = True) -> bool:
        """
        Generate plot working backward from finale.

        Returns True if valid plot generated.
        """
        self.graph = PlotGraph()

        # Start with finale (RETURN or VICTORY)
        if include_return:
            finale_templates = PLOT_TEMPLATES[ProppFunction.RETURN]
            finale_func = ProppFunction.RETURN
        else:
            finale_templates = PLOT_TEMPLATES[ProppFunction.VICTORY]
            finale_func = ProppFunction.VICTORY

        # Choose finale variant
        req, prov, desc, loc = random.choice(finale_templates)
        finale = PlotNode(
            function=finale_func,
            requires=req,
            provides=prov,
            description=desc,
            location_hint=loc
        )
        finale_id = self.graph.add_node(finale)

        # Track what we need to satisfy
        unsatisfied = finale.requires
        pending_nodes = [(finale_id, finale.requires)]

        # Work backward
        used_functions = {finale_func}
        iterations = 0
        max_iterations = 20

        while unsatisfied and iterations < max_iterations:
            iterations += 1

            # Find a function that provides something we need
            best_func = None
            best_template = None
            best_provides = 0

            # Shuffle function order for variety
            functions = list(ProppFunction)
            random.shuffle(functions)

            for func in functions:
                if func in used_functions and func not in [ProppFunction.ACQUISITION, ProppFunction.DONOR_TEST]:
                    # Allow duplicates only for certain functions
                    continue

                for req, prov, desc, loc in PLOT_TEMPLATES[func]:
                    # Check if this provides anything we need
                    provides_needed = prov & unsatisfied
                    if provides_needed:
                        # Prefer functions that provide more of what we need
                        if provides_needed > best_provides:
                            best_provides = provides_needed
                            best_func = func
                            best_template = (req, prov, desc, loc)

            if best_func is None:
                # No function provides what we need - try to relax
                break

            # Create the node
            req, prov, desc, loc = best_template
            new_node = PlotNode(
                function=best_func,
                requires=req,
                provides=prov,
                description=desc,
                location_hint=loc
            )
            new_id = self.graph.add_node(new_node)
            used_functions.add(best_func)

            # Connect new node to nodes that need what it provides
            for node_id, node_reqs in pending_nodes:
                if prov & node_reqs:
                    self.graph.add_edge(new_id, node_id)

            # Connect existing nodes that provide what new node requires
            for node_id, _ in pending_nodes:
                existing_node = self.graph.nodes[node_id]
                if existing_node.provides & req:
                    self.graph.add_edge(node_id, new_id)

            # Update unsatisfied (remove what this provides, add what it requires)
            unsatisfied = (unsatisfied & ~prov) | req
            pending_nodes.append((new_id, req))

        # Check if we have a valid plot (LACK at the beginning)
        roots = self.graph.get_roots()
        has_lack = any(self.graph.nodes[r].function == ProppFunction.LACK for r in roots)

        return has_lack and len(self.graph.nodes) >= 4

    def get_plot_summary(self) -> str:
        """Get human-readable plot summary"""
        lines = ["=== Plot Structure ===", ""]

        # Topological order
        order = self.graph.topological_sort()
        if not order:
            return "Invalid plot (cycle detected)"

        for i, node_id in enumerate(order):
            node = self.graph.nodes[node_id]
            lines.append(f"{i+1}. [{PROPP_NAMES[node.function]}] {node.description}")
            lines.append(f"   Location: {node.location_hint}")

            # Show requirements
            reqs = []
            for r in Requirement:
                if r != Requirement.NONE and node.requires & r:
                    reqs.append(r.name)
            if reqs:
                lines.append(f"   Requires: {', '.join(reqs)}")

            # Show provides
            provs = []
            for p in Provides:
                if p != Provides.NONE and node.provides & p:
                    provs.append(p.name)
            if provs:
                lines.append(f"   Provides: {', '.join(provs)}")

            lines.append("")

        return '\n'.join(lines)

    def get_location_requirements(self) -> Dict[str, List[str]]:
        """Get which locations are needed for this plot"""
        locations = {}
        for node in self.graph.nodes:
            loc = node.location_hint
            if loc not in locations:
                locations[loc] = []
            locations[loc].append(PROPP_NAMES[node.function])
        return locations

    def verify_completability(self) -> Tuple[bool, str]:
        """
        Verify plot is completable.

        Returns (is_valid, error_message).
        """
        # Check for cycles
        order = self.graph.topological_sort()
        if not order:
            return False, "Plot contains cycles"

        # Simulate playing through
        state = 0  # Current requirements met

        for node_id in order:
            node = self.graph.nodes[node_id]

            # Check if requirements met
            if (node.requires & state) != node.requires:
                missing = node.requires & ~state
                missing_names = [r.name for r in Requirement if r != Requirement.NONE and missing & r]
                return False, f"Node {node_id} ({PROPP_NAMES[node.function]}) requires: {missing_names}"

            # Update state
            state |= node.provides

        return True, "Plot is completable"


# =============================================================================
# Demo
# =============================================================================

def demo():
    """Demo backward plot generation"""
    print("=== Backward Plot Generator Demo ===\n")

    gen = BackwardPlotGenerator(seed=42)

    print("Generating plot (3 attempts)...\n")

    for attempt in range(3):
        gen.reset(seed=42 + attempt)
        if gen.generate():
            print(f"Attempt {attempt + 1}: SUCCESS\n")
            print(gen.get_plot_summary())

            # Verify
            valid, msg = gen.verify_completability()
            print(f"Verification: {msg}\n")

            # Show required locations
            print("Required locations:")
            for loc, funcs in gen.get_location_requirements().items():
                print(f"  {loc}: {', '.join(funcs)}")
            print()

            # Show graph structure
            print("Graph edges (A -> B means A before B):")
            for from_id, to_ids in gen.graph.edges.items():
                if to_ids:
                    from_name = PROPP_NAMES[gen.graph.nodes[from_id].function]
                    for to_id in to_ids:
                        to_name = PROPP_NAMES[gen.graph.nodes[to_id].function]
                        print(f"  {from_name} -> {to_name}")
            break
        else:
            print(f"Attempt {attempt + 1}: Failed to generate valid plot")


if __name__ == "__main__":
    demo()
