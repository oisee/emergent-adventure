"""
Fractal Plot System

Implements nested narrative structure based on storygen-book:
- MEGA: World-spanning (rare)
- MACRO: Main story quest (e.g., "Defeat Dark Lord")
- MESO: Subplot/chapter (e.g., "Acquire Magic Sword")
- MICRO: Scene (e.g., "Convince Blacksmith")
- NANO: Beat/action (e.g., "Prove trustworthiness")

Each plot point can contain a sub-plot, creating fractal structure.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set
from enum import IntEnum, auto
import random

from .plot_advanced import (
    ProppFunc, Requirement, Provides, PlotNode as BasePlotNode,
    MultiPlot, TwistType, Genre, GENRES, PLOT_TEMPLATES,
    PROPP_NAMES as ADV_PROPP_NAMES
)


class NarrativeLevel(IntEnum):
    """Fractal narrative levels"""
    NANO = 0      # Single action/dialogue beat
    MICRO = 1     # Single scene/encounter
    MESO = 2      # Subplot/chapter
    MACRO = 3     # Main story arc
    MEGA = 4      # World-spanning epic (rare)


class EndingMode(IntEnum):
    """
    Модусы финала - эмоциональное состояние в конце нарратива.
    Based on Greek concepts of narrative resolution.
    """
    CATHARSIS = 0       # Κάθαρσις - очищение через страдание (Brothers, Shadow of Colossus)
    EUDAIMONIA = 1      # Εὐδαιμονία - процветание, смысл найден (Disco Elysium, Stardew)
    NOSTALGIA = 2       # Νόστος+Ἄλγος - светлая печаль (Journey, Spiritfarer)
    THAUMA = 3          # Θαῦμα - удивление, расширение мира (Outer Wilds, SOMA)
    CLOSURE = 4         # Closure - гештальт закрыт (ZORK, Portal, Obra Dinn)
    METAMORPHOSIS = 5   # Μεταμόρφωσις - необратимое изменение (Elden Ring, Undertale)
    APORIA = 6          # Ἀπορία - продуктивная неопределённость (Dark Souls, Twin Peaks)
    ATARAXIA = 7        # Ἀταραξία - безмятежность, принятие (Flower, ABZÛ)
    ELPIS = 8           # Ἐλπίς - надежда, to be continued (Mass Effect 2)
    ANAMNESIS = 9       # Ἀνάμνησις - переосмысление прошлого (Braid, Her Story)
    KENOSIS = 10        # Κένωσις - опустошение, отпускание (Celeste, Gris)
    EKSTASIS = 11       # Ἔκστασις - трансцендентность (Rez Infinite, Tetris Effect)


# Ending mode metadata
ENDING_MODES = {
    EndingMode.CATHARSIS: {
        "name": "Catharsis",
        "greek": "Κάθαρσις",
        "emotion": "purification through suffering",
        "color": "#8B0000",  # dark red
        "compatible_finales": [ProppFunc.VICTORY, ProppFunc.RESCUE, ProppFunc.PUNISHMENT],
    },
    EndingMode.EUDAIMONIA: {
        "name": "Eudaimonia",
        "greek": "Εὐδαιμονία",
        "emotion": "flourishing, meaning found",
        "color": "#FFD700",  # gold
        "compatible_finales": [ProppFunc.VICTORY, ProppFunc.RECOGNITION, ProppFunc.RETURN],
    },
    EndingMode.NOSTALGIA: {
        "name": "Nostalgia",
        "greek": "Νόστος+Ἄλγος",
        "emotion": "bittersweet longing",
        "color": "#DDA0DD",  # plum
        "compatible_finales": [ProppFunc.RETURN, ProppFunc.RECOGNITION],
    },
    EndingMode.THAUMA: {
        "name": "Thauma",
        "greek": "Θαῦμα",
        "emotion": "wonder, world expanded",
        "color": "#4169E1",  # royal blue
        "compatible_finales": [ProppFunc.RECOGNITION, ProppFunc.ACQUISITION],
    },
    EndingMode.CLOSURE: {
        "name": "Closure",
        "greek": "Closure",
        "emotion": "gestalt complete",
        "color": "#228B22",  # forest green
        "compatible_finales": [ProppFunc.VICTORY, ProppFunc.RETURN, ProppFunc.PUNISHMENT],
    },
    EndingMode.METAMORPHOSIS: {
        "name": "Metamorphosis",
        "greek": "Μεταμόρφωσις",
        "emotion": "irreversible transformation",
        "color": "#9932CC",  # dark orchid
        "compatible_finales": [ProppFunc.BRANDING, ProppFunc.VICTORY, ProppFunc.RECOGNITION],
    },
    EndingMode.APORIA: {
        "name": "Aporia",
        "greek": "Ἀπορία",
        "emotion": "productive uncertainty",
        "color": "#696969",  # dim gray
        "compatible_finales": [ProppFunc.RECOGNITION, ProppFunc.GUIDANCE],
    },
    EndingMode.ATARAXIA: {
        "name": "Ataraxia",
        "greek": "Ἀταραξία",
        "emotion": "serene acceptance",
        "color": "#87CEEB",  # sky blue
        "compatible_finales": [ProppFunc.RETURN, ProppFunc.RECOGNITION],
    },
    EndingMode.ELPIS: {
        "name": "Elpis",
        "greek": "Ἐλπίς",
        "emotion": "hope, anticipation",
        "color": "#FFA500",  # orange
        "compatible_finales": [ProppFunc.DEPARTURE, ProppFunc.GUIDANCE, ProppFunc.PURSUIT],
    },
    EndingMode.ANAMNESIS: {
        "name": "Anamnesis",
        "greek": "Ἀνάμνησις",
        "emotion": "recontextualization of past",
        "color": "#BA55D3",  # medium orchid
        "compatible_finales": [ProppFunc.RECOGNITION, ProppFunc.RETURN],
    },
    EndingMode.KENOSIS: {
        "name": "Kenosis",
        "greek": "Κένωσις",
        "emotion": "emptying, letting go",
        "color": "#B0C4DE",  # light steel blue
        "compatible_finales": [ProppFunc.RESCUE, ProppFunc.RETURN],
    },
    EndingMode.EKSTASIS: {
        "name": "Ekstasis",
        "greek": "Ἔκστασις",
        "emotion": "transcendence",
        "color": "#FF69B4",  # hot pink
        "compatible_finales": [ProppFunc.VICTORY, ProppFunc.RECOGNITION, ProppFunc.BRANDING],
    },
}


# How many sub-nodes each level typically contains
LEVEL_COMPLEXITY = {
    NarrativeLevel.MEGA: (3, 5),   # 3-5 MACRO arcs
    NarrativeLevel.MACRO: (4, 8),  # 4-8 MESO subplots
    NarrativeLevel.MESO: (2, 5),   # 2-5 MICRO scenes
    NarrativeLevel.MICRO: (1, 3),  # 1-3 NANO beats
    NarrativeLevel.NANO: (0, 0),   # No sub-levels
}

# Level names for display
LEVEL_NAMES = {
    NarrativeLevel.NANO: "Beat",
    NarrativeLevel.MICRO: "Scene",
    NarrativeLevel.MESO: "Chapter",
    NarrativeLevel.MACRO: "Arc",
    NarrativeLevel.MEGA: "Saga",
}


@dataclass
class FractalPlotNode:
    """
    A plot node that can contain a nested sub-plot.

    Example:
    - MACRO "Defeat Dark Lord"
      - MESO "Acquire Magic Sword"
        - MICRO "Find the Blacksmith"
        - MICRO "Prove Worthiness"
        - MICRO "Receive the Blade"
      - MESO "Gather Allies"
        - MICRO "Recruit the Mage"
        - MICRO "Free the Prisoner"
    """
    id: int
    function: ProppFunc
    requires: int = 0
    provides: int = 0

    # Content
    description: str = ""
    location_hint: str = ""

    # Fractal structure
    level: NarrativeLevel = NarrativeLevel.MICRO
    sub_plot: Optional['FractalPlot'] = None  # Nested plot
    parent_id: Optional[int] = None  # Parent node in higher level

    # State tracking
    is_expanded: bool = False  # For UI - show sub-plot?
    is_active: bool = False    # Currently in this subplot?
    is_completed: bool = False

    # Twist/ending markers (from advanced plot)
    is_ending: bool = False
    is_false_ending: bool = False
    twist_type: TwistType = TwistType.NONE

    # Ending mode - emotional state at resolution
    ending_mode: Optional[EndingMode] = None

    def has_sub_plot(self) -> bool:
        return self.sub_plot is not None and len(self.sub_plot.nodes) > 0

    def to_dict(self) -> dict:
        """Convert node to dictionary for JSON export"""
        result = {
            "id": self.id,
            "function": self.function.name,
            "level": LEVEL_NAMES.get(self.level, str(self.level)),
            "level_value": int(self.level),
            "description": self.description,
            "location_hint": self.location_hint,
        }

        # Add optional fields
        if self.is_ending:
            result["is_ending"] = True
        if self.is_false_ending:
            result["is_false_ending"] = True
        if self.twist_type and self.twist_type != TwistType.NONE:
            result["twist_type"] = self.twist_type.name
        if self.ending_mode:
            mode_info = ENDING_MODES.get(self.ending_mode, {})
            result["ending_mode"] = {
                "name": mode_info.get("name"),
                "greek": mode_info.get("greek"),
                "emotion": mode_info.get("emotion"),
            }

        # Recursively add sub-plot
        if self.has_sub_plot():
            result["sub_plot"] = self.sub_plot.to_dict()

        return result

    def get_depth(self) -> int:
        """Get maximum depth of nested sub-plots"""
        if not self.has_sub_plot():
            return 0
        return 1 + max((n.get_depth() for n in self.sub_plot.nodes), default=0)

    def get_all_nodes_flat(self) -> List['FractalPlotNode']:
        """Get all nodes including nested ones as flat list"""
        result = [self]
        if self.has_sub_plot():
            for node in self.sub_plot.nodes:
                result.extend(node.get_all_nodes_flat())
        return result


@dataclass
class FractalPlot:
    """
    A plot that can contain fractal sub-structure.
    """
    nodes: List[FractalPlotNode] = field(default_factory=list)
    edges: Dict[int, List[int]] = field(default_factory=dict)
    level: NarrativeLevel = NarrativeLevel.MACRO
    genre: Genre = None

    # Metadata
    title: str = ""
    summary: str = ""

    # Ending mode for the overall plot
    ending_mode: EndingMode = EndingMode.CLOSURE

    # Current state
    current_node_id: int = 0
    current_level: NarrativeLevel = NarrativeLevel.MICRO

    def add_node(self, node: FractalPlotNode) -> int:
        node.id = len(self.nodes)
        self.nodes.append(node)
        self.edges[node.id] = []
        return node.id

    def add_edge(self, from_id: int, to_id: int):
        if from_id in self.edges and to_id not in self.edges[from_id]:
            self.edges[from_id].append(to_id)

    def get_node(self, node_id: int) -> Optional[FractalPlotNode]:
        if 0 <= node_id < len(self.nodes):
            return self.nodes[node_id]
        return None

    def topological_sort(self) -> List[int]:
        """Return nodes in topological order"""
        in_degree = {i: 0 for i in range(len(self.nodes))}
        for from_id, to_list in self.edges.items():
            for to_id in to_list:
                in_degree[to_id] = in_degree.get(to_id, 0) + 1

        queue = [i for i in range(len(self.nodes)) if in_degree[i] == 0]
        result = []

        while queue:
            node_id = queue.pop(0)
            result.append(node_id)
            for successor in self.edges.get(node_id, []):
                in_degree[successor] -= 1
                if in_degree[successor] == 0:
                    queue.append(successor)

        return result if len(result) == len(self.nodes) else []

    def get_total_node_count(self) -> int:
        """Get total nodes including all nested sub-plots"""
        count = len(self.nodes)
        for node in self.nodes:
            if node.has_sub_plot():
                count += node.sub_plot.get_total_node_count()
        return count

    def get_max_depth(self) -> int:
        """Get maximum nesting depth"""
        if not self.nodes:
            return 0
        return max((n.get_depth() for n in self.nodes), default=0) + 1

    def to_dict(self) -> dict:
        """Convert plot to dictionary for JSON export"""
        # Ending mode info
        ending_info = ENDING_MODES.get(self.ending_mode, {})

        result = {
            "type": "fractal_plot",
            "level": LEVEL_NAMES.get(self.level, str(self.level)),
            "level_value": int(self.level),
            "title": self.title,
            "summary": self.summary,
            "ending_mode": {
                "name": ending_info.get("name"),
                "greek": ending_info.get("greek"),
                "emotion": ending_info.get("emotion"),
            } if self.ending_mode else None,
            "stats": {
                "total_nodes": self.get_total_node_count(),
                "max_depth": self.get_max_depth(),
                "top_level_nodes": len(self.nodes),
            },
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": {str(k): v for k, v in self.edges.items()},
        }

        if self.genre:
            result["genre"] = self.genre.name

        return result

    def to_json(self, indent: int = 2) -> str:
        """Export plot to JSON string"""
        import json
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


# =============================================================================
# Sub-plot templates for decomposition
# =============================================================================

# How to decompose high-level goals into sub-goals
DECOMPOSITION_TEMPLATES = {
    # MACRO -> MESO decomposition
    ProppFunc.VICTORY: [
        # Victory decomposes into: prepare, confront, overcome
        [ProppFunc.ACQUISITION, ProppFunc.GUIDANCE, ProppFunc.STRUGGLE],
        [ProppFunc.DONOR_TEST, ProppFunc.BRANDING, ProppFunc.STRUGGLE],
    ],
    ProppFunc.RESCUE: [
        # Rescue decomposes into: locate, infiltrate, extract
        [ProppFunc.GUIDANCE, ProppFunc.STRUGGLE, ProppFunc.PURSUIT],
        [ProppFunc.ACQUISITION, ProppFunc.GUIDANCE, ProppFunc.RESCUE],
    ],
    ProppFunc.ACQUISITION: [
        # Get item decomposes into: find source, prove worth, receive
        [ProppFunc.GUIDANCE, ProppFunc.DONOR_TEST, ProppFunc.ACQUISITION],
        [ProppFunc.DEPARTURE, ProppFunc.STRUGGLE, ProppFunc.ACQUISITION],
    ],
    ProppFunc.RECOGNITION: [
        # Recognition decomposes into: gather evidence, confront, reveal
        [ProppFunc.ACQUISITION, ProppFunc.GUIDANCE, ProppFunc.RECOGNITION],
    ],

    # MESO -> MICRO decomposition (simpler)
    ProppFunc.DONOR_TEST: [
        [ProppFunc.INTERDICTION, ProppFunc.VIOLATION, ProppFunc.DONOR_TEST],
    ],
    ProppFunc.GUIDANCE: [
        [ProppFunc.DEPARTURE, ProppFunc.GUIDANCE],
    ],
    ProppFunc.STRUGGLE: [
        [ProppFunc.PURSUIT, ProppFunc.STRUGGLE],
        [ProppFunc.BRANDING, ProppFunc.STRUGGLE],
    ],
}

# Scene descriptions for MICRO level
MICRO_SCENE_TEMPLATES = {
    ProppFunc.DEPARTURE: [
        "The hero leaves the safety of home",
        "Setting out on the dangerous path",
        "Crossing the threshold into adventure",
    ],
    ProppFunc.DONOR_TEST: [
        "A mysterious figure poses a challenge",
        "The hero must prove their worth",
        "A test of character and skill",
    ],
    ProppFunc.ACQUISITION: [
        "The reward is bestowed upon the hero",
        "A powerful ally joins the cause",
        "The key item is finally obtained",
    ],
    ProppFunc.GUIDANCE: [
        "The path forward becomes clear",
        "Following the signs to the destination",
        "The journey continues",
    ],
    ProppFunc.STRUGGLE: [
        "Combat erupts!",
        "A fierce confrontation",
        "The hero faces opposition",
    ],
    ProppFunc.PURSUIT: [
        "The chase is on!",
        "Escaping from danger",
        "Running for survival",
    ],
    ProppFunc.RESCUE: [
        "The captive is freed!",
        "Breaking the chains",
        "Salvation at last",
    ],
    ProppFunc.RECOGNITION: [
        "The truth is revealed",
        "Identity confirmed",
        "All becomes clear",
    ],
    ProppFunc.VICTORY: [
        "Triumph over evil!",
        "The enemy falls",
        "Victory is achieved",
    ],
}


class FractalPlotGenerator:
    """
    Generates fractal plots with nested sub-structure.
    Supports branching narratives with multiple paths.
    """

    def __init__(self, genre: Genre = None, seed: int = None,
                 branching_chance: float = 0.3,
                 level_complexity: Dict[NarrativeLevel, Tuple[int, int]] = None):
        """
        Initialize fractal plot generator.

        Args:
            genre: Genre for vocabulary and theming
            seed: Random seed for reproducibility
            branching_chance: Probability of branching at decision points (0.0-1.0)
            level_complexity: Override for node counts per level.
                              Dict mapping NarrativeLevel -> (min_nodes, max_nodes)
                              Example: {NarrativeLevel.MACRO: (5, 10), NarrativeLevel.MESO: (3, 6)}
        """
        self.genre = genre or GENRES["fantasy"]
        self.seed = seed
        self.branching_chance = branching_chance  # Chance to branch at decision points
        # Merge custom complexity with defaults
        self.level_complexity = dict(LEVEL_COMPLEXITY)
        if level_complexity:
            self.level_complexity.update(level_complexity)
        if seed is not None:
            random.seed(seed)
        self.plot = FractalPlot(genre=self.genre)
        self.next_id = 0

    def reset(self, seed: int = None):
        if seed is not None:
            self.seed = seed
            random.seed(seed)
        self.plot = FractalPlot(genre=self.genre, level=NarrativeLevel.MACRO)
        self.next_id = 0

    def _apply_genre_vocab(self, text: str) -> str:
        """Replace {placeholders} with genre-specific vocabulary"""
        result = text
        for key, value in self.genre.vocab.items():
            result = result.replace(f"{{{key}}}", value)
        return result

    def set_level_complexity(self, level: NarrativeLevel, min_nodes: int, max_nodes: int):
        """Set complexity (node count range) for a specific narrative level."""
        self.level_complexity[level] = (min_nodes, max_nodes)

    def get_level_complexity(self, level: NarrativeLevel) -> Tuple[int, int]:
        """Get complexity range for a level."""
        return self.level_complexity.get(level, (1, 3))

    def generate(self,
                 target_level: NarrativeLevel = NarrativeLevel.MACRO,
                 depth: int = 2,
                 finale: ProppFunc = ProppFunc.VICTORY,
                 branching: bool = True,
                 ending_mode: EndingMode = None,
                 complexity_override: Dict[NarrativeLevel, Tuple[int, int]] = None,
                 add_twist: bool = False,
                 twist_type: TwistType = None,
                 add_false_ending: bool = False) -> bool:
        """
        Generate a fractal plot.

        Args:
            target_level: The top level of the plot
            depth: How many levels to decompose
            finale: The ultimate goal
            branching: Whether to allow branching paths
            ending_mode: Emotional ending mode (catharsis, eudaimonia, etc.)
            complexity_override: One-time override for level complexity
                                 (doesn't change generator's default settings)
            add_twist: Whether to add a plot twist
            twist_type: Specific twist type (or None for random)
            add_false_ending: Whether to add a false ending
        """
        # Apply one-time complexity override
        original_complexity = self.level_complexity.copy()
        if complexity_override:
            self.level_complexity.update(complexity_override)
        self.reset(self.seed)
        self.plot.level = target_level
        self.allow_branching = branching
        self.add_twist = add_twist
        self.twist_type = twist_type
        self.add_false_ending = add_false_ending
        self.twist_inserted = False
        self.false_ending_inserted = False

        # Set or derive ending mode
        if ending_mode is None:
            # Pick random ending mode compatible with finale
            compatible = [
                mode for mode, data in ENDING_MODES.items()
                if finale in data["compatible_finales"]
            ]
            ending_mode = random.choice(compatible) if compatible else EndingMode.CLOSURE

        self.plot.ending_mode = ending_mode
        self.ending_mode = ending_mode

        try:
            # Build top-level plot with potential branching
            if not self._build_level_with_branches(target_level, finale, depth):
                return False

            # Mark the final node with ending mode
            if self.plot.nodes:
                self.plot.nodes[0].ending_mode = ending_mode

            # Post-process: add twists and false endings
            if add_twist and not self.twist_inserted:
                self._insert_twist_post(twist_type)
            if add_false_ending and not self.false_ending_inserted:
                self._insert_false_ending_post()

            return len(self.plot.nodes) > 0
        finally:
            # Restore original complexity if we used an override
            if complexity_override:
                self.level_complexity = original_complexity

    def _insert_twist_post(self, twist_type: TwistType = None):
        """Insert a plot twist into an existing plot structure"""
        if not self.plot.nodes:
            return

        # Choose twist type
        if twist_type is None:
            twist_type = random.choice([
                TwistType.ALLY_BETRAYAL, TwistType.VILLAIN_SYMPATHETIC,
                TwistType.HERO_ORIGIN, TwistType.HIDDEN_VILLAIN,
                TwistType.PROPHECY_TWIST, TwistType.DEAD_ALIVE
            ])

        # Find a good node for the twist (mid-point of the plot)
        all_nodes = []
        def collect_nodes(p: FractalPlot, level_depth: int = 0):
            for node in p.nodes:
                all_nodes.append((node, level_depth))
                if node.has_sub_plot():
                    collect_nodes(node.sub_plot, level_depth + 1)

        collect_nodes(self.plot)

        if len(all_nodes) < 3:
            return

        # Place twist around 40-60% of the way through
        twist_idx = len(all_nodes) * random.randint(40, 60) // 100
        twist_node, _ = all_nodes[twist_idx]

        twist_node.twist_type = twist_type
        twist_node.description = f"[TWIST: {twist_type.name}] " + twist_node.description
        self.twist_inserted = True

    def _insert_false_ending_post(self):
        """Insert a false ending into an existing plot structure"""
        if not self.plot.nodes:
            return

        # Collect all nodes
        all_nodes = []
        def collect_nodes(p: FractalPlot):
            for node in p.nodes:
                all_nodes.append(node)
                if node.has_sub_plot():
                    collect_nodes(node.sub_plot)

        collect_nodes(self.plot)

        if len(all_nodes) < 4:
            return

        # Place false ending around 70-85% of the way through
        false_ending_idx = len(all_nodes) * random.randint(70, 85) // 100
        false_ending_node = all_nodes[false_ending_idx]

        false_ending_node.is_false_ending = True
        false_ending_node.description = "[FALSE ENDING] " + false_ending_node.description
        self.false_ending_inserted = True

    def _build_level_with_branches(self, level: NarrativeLevel,
                                    goal: ProppFunc,
                                    remaining_depth: int,
                                    parent_id: int = None) -> bool:
        """Build a plot level that may include branching paths"""

        # Get templates for this goal
        templates = PLOT_TEMPLATES.get(goal, [])
        if not templates:
            return False

        req, prov, desc, loc = random.choice(templates)

        # Create the goal node
        goal_node = FractalPlotNode(
            id=self.next_id,
            function=goal,
            requires=req,
            provides=prov,
            description=self._apply_genre_vocab(desc),
            location_hint=loc,
            level=level,
            parent_id=parent_id,
            is_ending=(level == self.plot.level),
        )
        self.next_id += 1
        node_id = self.plot.add_node(goal_node)

        # Build preceding nodes with potential branching
        if remaining_depth > 0 and level > NarrativeLevel.NANO:
            sub_level = NarrativeLevel(level - 1)

            # Get decomposition templates
            decomp = DECOMPOSITION_TEMPLATES.get(goal, [])
            if decomp:
                sub_funcs = list(random.choice(decomp))
            else:
                sub_funcs = self._default_decomposition(goal, sub_level)

            # Apply level complexity to determine node count
            min_nodes, max_nodes = self.get_level_complexity(sub_level)
            target_count = random.randint(min_nodes, max_nodes) if max_nodes > 0 else len(sub_funcs)

            # Adjust sub_funcs to match target complexity
            if target_count > 0:
                sub_funcs = self._adjust_node_count(sub_funcs, target_count, sub_level)

            if sub_funcs and len(sub_funcs) >= 2:
                # Check for branching opportunity
                should_branch = (
                    self.allow_branching and
                    random.random() < self.branching_chance and
                    len(sub_funcs) >= 2
                )

                if should_branch:
                    # Create branching sub-plot
                    sub_plot = FractalPlot(
                        level=sub_level,
                        genre=self.genre,
                        title=f"Branching sub-plot for: {goal.name}",
                    )
                    goal_node.sub_plot = sub_plot

                    # Create a starting node
                    start_node = self._create_sub_node(sub_funcs[0], sub_level, remaining_depth - 1)
                    if start_node:
                        start_id = sub_plot.add_node(start_node)

                        # Create 2 branches from the start
                        branch_funcs = sub_funcs[1:] if len(sub_funcs) > 1 else [ProppFunc.STRUGGLE, ProppFunc.GUIDANCE]
                        branch_ids = []

                        for i, branch_func in enumerate(branch_funcs[:2]):
                            branch_node = self._create_sub_node(branch_func, sub_level, remaining_depth - 1)
                            if branch_node:
                                bid = sub_plot.add_node(branch_node)
                                branch_ids.append(bid)
                                sub_plot.add_edge(start_id, bid)

                        # Both branches can converge to the goal (or have separate endings)
                        if random.random() < 0.5 and branch_ids:
                            # Converging branches - create a convergence point
                            converge_node = self._create_sub_node(
                                ProppFunc.RECOGNITION, sub_level, 0
                            )
                            if converge_node:
                                cid = sub_plot.add_node(converge_node)
                                for bid in branch_ids:
                                    sub_plot.add_edge(bid, cid)
                else:
                    # Linear sub-plot (existing behavior)
                    sub_plot = FractalPlot(
                        level=sub_level,
                        genre=self.genre,
                        title=f"Sub-plot for: {goal.name}",
                    )
                    goal_node.sub_plot = sub_plot

                    prev_sub_id = None
                    for sub_func in sub_funcs:
                        sub_node = self._create_sub_node(sub_func, sub_level, remaining_depth - 1)
                        if sub_node:
                            sub_id = sub_plot.add_node(sub_node)
                            if prev_sub_id is not None:
                                sub_plot.add_edge(prev_sub_id, sub_id)
                            prev_sub_id = sub_id

        return True

    def _build_level(self, level: NarrativeLevel,
                     goal: ProppFunc,
                     remaining_depth: int,
                     parent_id: int = None) -> bool:
        """Build a single level of the plot"""

        # Get templates for this goal
        templates = PLOT_TEMPLATES.get(goal, [])
        if not templates:
            return False

        req, prov, desc, loc = random.choice(templates)

        # Create the goal node
        goal_node = FractalPlotNode(
            id=self.next_id,
            function=goal,
            requires=req,
            provides=prov,
            description=self._apply_genre_vocab(desc),
            location_hint=loc,
            level=level,
            parent_id=parent_id,
            is_ending=(level == self.plot.level),  # Top-level goal is ending
        )
        self.next_id += 1
        node_id = self.plot.add_node(goal_node)

        # Decompose if we have depth remaining
        if remaining_depth > 0 and level > NarrativeLevel.NANO:
            sub_level = NarrativeLevel(level - 1)

            # Get decomposition template
            decomp = DECOMPOSITION_TEMPLATES.get(goal, [])
            if decomp:
                sub_funcs = random.choice(decomp)
            else:
                # Default decomposition
                sub_funcs = self._default_decomposition(goal, sub_level)

            if sub_funcs:
                # Create sub-plot
                sub_plot = FractalPlot(
                    level=sub_level,
                    genre=self.genre,
                    title=f"Sub-plot for: {goal.name}",
                )
                goal_node.sub_plot = sub_plot

                # Build sub-nodes
                prev_sub_id = None
                for sub_func in sub_funcs:
                    sub_node = self._create_sub_node(sub_func, sub_level, remaining_depth - 1)
                    if sub_node:
                        sub_id = sub_plot.add_node(sub_node)
                        if prev_sub_id is not None:
                            sub_plot.add_edge(prev_sub_id, sub_id)
                        prev_sub_id = sub_id

        return True

    def _create_sub_node(self, func: ProppFunc, level: NarrativeLevel,
                         remaining_depth: int) -> Optional[FractalPlotNode]:
        """Create a sub-node with potential further nesting"""

        # Get description
        if level <= NarrativeLevel.MICRO:
            templates = MICRO_SCENE_TEMPLATES.get(func, [f"{func.name} scene"])
            desc = random.choice(templates)
        else:
            templates = PLOT_TEMPLATES.get(func, [])
            if templates:
                _, _, desc, loc = random.choice(templates)
                desc = self._apply_genre_vocab(desc)
            else:
                desc = f"{func.name}"

        # Get location
        templates = PLOT_TEMPLATES.get(func, [])
        if templates:
            _, _, _, loc = random.choice(templates)
        else:
            loc = "clearing"

        node = FractalPlotNode(
            id=self.next_id,
            function=func,
            description=desc,
            location_hint=loc,
            level=level,
        )
        self.next_id += 1

        # Further decomposition - use level_complexity settings
        if remaining_depth > 0 and level > NarrativeLevel.NANO:
            sub_level = NarrativeLevel(level - 1)
            decomp = DECOMPOSITION_TEMPLATES.get(func, [])

            # Higher chance to decompose when we have depth remaining
            decompose_chance = 0.9 if remaining_depth > 1 else 0.7

            if decomp and random.random() < decompose_chance:
                sub_funcs = list(random.choice(decomp))

                # Apply level complexity to get target node count
                min_nodes, max_nodes = self.get_level_complexity(sub_level)
                if max_nodes > 0:
                    target_count = random.randint(min_nodes, max_nodes)
                    sub_funcs = self._adjust_node_count(sub_funcs, target_count, sub_level)

                sub_plot = FractalPlot(level=sub_level, genre=self.genre)
                node.sub_plot = sub_plot

                prev_id = None
                for sf in sub_funcs:  # No artificial limit - use complexity settings
                    sub_node = self._create_sub_node(sf, sub_level, remaining_depth - 1)
                    if sub_node:
                        sid = sub_plot.add_node(sub_node)
                        if prev_id is not None:
                            sub_plot.add_edge(prev_id, sid)
                        prev_id = sid

        return node

    def _adjust_node_count(self, funcs: List[ProppFunc], target_count: int,
                           level: NarrativeLevel) -> List[ProppFunc]:
        """Adjust the number of functions to match target complexity."""
        if not funcs:
            return funcs

        current_count = len(funcs)

        if current_count == target_count:
            return funcs

        elif current_count < target_count:
            # Need to add more nodes - duplicate or add common functions
            result = list(funcs)
            extra_funcs = [
                ProppFunc.GUIDANCE, ProppFunc.STRUGGLE, ProppFunc.DONOR_TEST,
                ProppFunc.ACQUISITION, ProppFunc.PURSUIT, ProppFunc.DEPARTURE,
            ]
            while len(result) < target_count:
                # Add extra functions, preferring ones not already in the list
                available = [f for f in extra_funcs if f not in result]
                if available:
                    result.insert(-1, random.choice(available))  # Insert before last
                else:
                    result.insert(-1, random.choice(extra_funcs))
            return result

        else:
            # Need to reduce nodes - keep first and last, trim middle
            if target_count <= 1:
                return [funcs[-1]]  # Just keep the goal
            elif target_count == 2:
                return [funcs[0], funcs[-1]]  # Keep start and end
            else:
                # Keep first, last, and randomly sample middle
                middle = funcs[1:-1]
                keep_middle = target_count - 2
                if len(middle) <= keep_middle:
                    return funcs[:target_count]
                sampled = random.sample(middle, keep_middle)
                return [funcs[0]] + sampled + [funcs[-1]]

    def _default_decomposition(self, goal: ProppFunc,
                               level: NarrativeLevel) -> List[ProppFunc]:
        """Generate default decomposition for a goal"""
        # Simple decomposition based on goal type
        if goal in (ProppFunc.VICTORY, ProppFunc.STRUGGLE):
            return [ProppFunc.GUIDANCE, ProppFunc.STRUGGLE]
        elif goal in (ProppFunc.ACQUISITION, ProppFunc.RESCUE):
            return [ProppFunc.DEPARTURE, ProppFunc.ACQUISITION]
        elif goal == ProppFunc.RECOGNITION:
            return [ProppFunc.GUIDANCE, ProppFunc.RECOGNITION]
        else:
            return [ProppFunc.DEPARTURE, goal]

    def get_summary(self) -> str:
        """Get human-readable summary of fractal plot"""
        ending_info = ENDING_MODES.get(self.plot.ending_mode, {})
        lines = [
            f"=== Fractal Plot: {LEVEL_NAMES[self.plot.level]} ===",
            f"Genre: {self.genre.name}",
            f"Ending Mode: {ending_info.get('name', '?')} ({ending_info.get('greek', '')})",
            f"  → {ending_info.get('emotion', '')}",
            f"Total nodes: {self.plot.get_total_node_count()}",
            f"Max depth: {self.plot.get_max_depth()}",
            "",
        ]

        def print_node(node: FractalPlotNode, indent: int = 0):
            prefix = "  " * indent
            level_name = LEVEL_NAMES[node.level]
            lines.append(f"{prefix}[{level_name}] {node.function.name}: {node.description[:40]}...")

            if node.has_sub_plot():
                for sub_node in node.sub_plot.nodes:
                    print_node(sub_node, indent + 1)

        for node in self.plot.nodes:
            print_node(node)

        return '\n'.join(lines)


# =============================================================================
# Demo
# =============================================================================

def demo():
    """Demo fractal plot generation"""
    print("=" * 60)
    print("FRACTAL PLOT GENERATOR DEMO")
    print("=" * 60)

    gen = FractalPlotGenerator(GENRES["fantasy"], seed=42)

    print("\n1. MACRO plot with depth 2:")
    print("-" * 40)
    gen.generate(NarrativeLevel.MACRO, depth=2, finale=ProppFunc.VICTORY)
    print(gen.get_summary())

    print("\n\n2. MACRO plot with depth 3 (RESCUE):")
    print("-" * 40)
    gen.reset(123)
    gen.generate(NarrativeLevel.MACRO, depth=3, finale=ProppFunc.RESCUE)
    print(gen.get_summary())


if __name__ == "__main__":
    demo()
