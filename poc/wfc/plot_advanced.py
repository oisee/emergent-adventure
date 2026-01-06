"""
Advanced Plot Generator

Features:
- 16 Propp functions (expanded from 8)
- Multi-branch plots with mergers
- Exclusive/alternative endings
- Genre/setting system with themed vocabulary
- Palette generation
"""

from dataclasses import dataclass, field
from typing import List, Set, Tuple, Dict, Optional
from enum import IntEnum, IntFlag, auto
import random


# =============================================================================
# Expanded Propp Functions (16)
# =============================================================================

class ProppFunc(IntEnum):
    """16 Propp narrative functions"""
    # ACT I - Setup
    EQUILIBRIUM = 0      # Initial peaceful state
    LACK = 1             # Something missing/wrong
    INTERDICTION = 2     # "Don't do X" warning
    VIOLATION = 3        # Hero breaks rule

    # ACT II - Adventure
    DEPARTURE = 4        # Hero sets out
    DONOR_TEST = 5       # Prove worthiness
    ACQUISITION = 6      # Get magic item/ally
    GUIDANCE = 7         # Travel/navigate

    # ACT III - Confrontation
    STRUGGLE = 8         # Battle/conflict
    BRANDING = 9         # Hero marked/changed
    VICTORY = 10         # Defeat antagonist
    PURSUIT = 11         # Chase/escape sequence

    # ACT IV - Resolution
    RESCUE = 12          # Save someone
    RECOGNITION = 13     # Hero's identity revealed
    PUNISHMENT = 14      # Villain punished
    RETURN = 15          # Come home changed


PROPP_NAMES = {f: f.name for f in ProppFunc}


class Requirement(IntFlag):
    """What a plot node needs (16-bit)"""
    NONE = 0
    HERO_EXISTS = 1 << 0
    HAS_WEAPON = 1 << 1
    HAS_KEY = 1 << 2
    HAS_INFO = 1 << 3
    HAS_ALLY = 1 << 4
    HAS_ACCESS = 1 << 5
    VILLAIN_WEAK = 1 << 6
    AT_GOAL = 1 << 7
    QUEST_COMPLETE = 1 << 8
    VILLAIN_DEAD = 1 << 9
    RESCUED_SOMEONE = 1 << 10
    HERO_MARKED = 1 << 11
    RULE_BROKEN = 1 << 12
    PURSUED = 1 << 13
    RECOGNIZED = 1 << 14
    PUNISHED_VILLAIN = 1 << 15


class Provides(IntFlag):
    """What a plot node gives (16-bit)"""
    NONE = 0
    HERO_EXISTS = 1 << 0
    HAS_WEAPON = 1 << 1
    HAS_KEY = 1 << 2
    HAS_INFO = 1 << 3
    HAS_ALLY = 1 << 4
    HAS_ACCESS = 1 << 5
    VILLAIN_WEAK = 1 << 6
    AT_GOAL = 1 << 7
    QUEST_COMPLETE = 1 << 8
    VILLAIN_DEAD = 1 << 9
    RESCUED_SOMEONE = 1 << 10
    HERO_MARKED = 1 << 11
    RULE_BROKEN = 1 << 12
    PURSUED = 1 << 13
    RECOGNIZED = 1 << 14
    PUNISHED_VILLAIN = 1 << 15


# =============================================================================
# Plot Twist Types
# =============================================================================

class TwistType(IntEnum):
    """Types of plot twists"""
    NONE = 0
    ALLY_BETRAYAL = 1       # Ally was enemy all along
    VILLAIN_SYMPATHETIC = 2  # Villain had good reasons
    HERO_ORIGIN = 3         # Hero's true identity revealed
    FALSE_VICTORY = 4       # Defeated wrong enemy / decoy
    HIDDEN_VILLAIN = 5      # Real villain was hidden
    PROPHECY_TWIST = 6      # Prophecy meant something else
    DEAD_ALIVE = 7          # Someone thought dead returns
    MEMORY_FALSE = 8        # Hero's memories were lies
    TIME_LOOP = 9           # Events are repeating
    DREAM_REAL = 10         # "Dream" was real / reality was dream


# =============================================================================
# Genre/Setting System
# =============================================================================

@dataclass
class Genre:
    """Genre/setting definition with themed content"""
    name: str
    description: str

    # Color palette (hex colors)
    palette: Dict[str, str] = field(default_factory=dict)

    # Vocabulary replacements
    vocab: Dict[str, str] = field(default_factory=dict)

    # Weighted tile preferences (tile_type -> weight)
    tile_weights: Dict[str, float] = field(default_factory=dict)

    # Available endings
    endings: List[str] = field(default_factory=list)

    # Mood modifiers
    mood: str = "neutral"  # hopeful, dark, mysterious, epic


# Pre-defined genres
GENRES = {
    "fantasy": Genre(
        name="Fantasy",
        description="Classic sword and sorcery",
        palette={
            "primary": "#4A6741",    # Forest green
            "secondary": "#8B4513",  # Saddle brown
            "accent": "#FFD700",     # Gold
            "danger": "#8B0000",     # Dark red
            "water": "#4169E1",      # Royal blue
            "magic": "#9932CC",      # Purple
        },
        vocab={
            "weapon": "enchanted sword",
            "enemy": "dark lord",
            "ally": "wise wizard",
            "goal": "ancient kingdom",
            "item": "magic amulet",
            "place": "mystical realm",
        },
        tile_weights={"CASTLE": 1.5, "FOREST": 1.2, "DUNGEON": 1.3},
        endings=["VICTORY", "RETURN", "RECOGNITION"],
        mood="epic",
    ),

    "solarpunk": Genre(
        name="Solarpunk",
        description="Optimistic eco-future",
        palette={
            "primary": "#228B22",    # Forest green
            "secondary": "#87CEEB",  # Sky blue
            "accent": "#FFD700",     # Solar gold
            "danger": "#FF6347",     # Tomato
            "water": "#00CED1",      # Turquoise
            "magic": "#98FB98",      # Pale green
        },
        vocab={
            "weapon": "solar lance",
            "enemy": "corporate overseer",
            "ally": "community elder",
            "goal": "renewable sanctuary",
            "item": "seed archive",
            "place": "garden city",
        },
        tile_weights={"VILLAGE": 1.5, "CLEARING": 1.3, "TEMPLE": 1.2},
        endings=["RESCUE", "RECOGNITION", "RETURN"],
        mood="hopeful",
    ),

    "hopepunk": Genre(
        name="Hopepunk",
        description="Radical hope and kindness as resistance",
        palette={
            "primary": "#DDA0DD",    # Plum
            "secondary": "#F0E68C",  # Khaki
            "accent": "#FF69B4",     # Hot pink
            "danger": "#696969",     # Dim gray
            "water": "#ADD8E6",      # Light blue
            "magic": "#FFB6C1",      # Light pink
        },
        vocab={
            "weapon": "words of truth",
            "enemy": "forces of despair",
            "ally": "kind stranger",
            "goal": "community in need",
            "item": "book of stories",
            "place": "gathering hall",
        },
        tile_weights={"TAVERN": 1.5, "VILLAGE": 1.4, "BRIDGE": 1.3},
        endings=["RESCUE", "RETURN", "RECOGNITION"],
        mood="hopeful",
    ),

    "dark_fantasy": Genre(
        name="Dark Fantasy",
        description="Grim and perilous world",
        palette={
            "primary": "#2F4F4F",    # Dark slate
            "secondary": "#8B0000",  # Dark red
            "accent": "#C0C0C0",     # Silver
            "danger": "#000000",     # Black
            "water": "#191970",      # Midnight blue
            "magic": "#4B0082",      # Indigo
        },
        vocab={
            "weapon": "cursed blade",
            "enemy": "elder horror",
            "ally": "damned soul",
            "goal": "forbidden citadel",
            "item": "blood artifact",
            "place": "blighted land",
        },
        tile_weights={"DUNGEON": 1.5, "RUINS": 1.4, "SWAMP": 1.3},
        endings=["VICTORY", "BRANDING", "PUNISHMENT"],
        mood="dark",
    ),

    "mystery": Genre(
        name="Mystery",
        description="Secrets and investigation",
        palette={
            "primary": "#708090",    # Slate gray
            "secondary": "#F5F5DC",  # Beige
            "accent": "#B8860B",     # Dark goldenrod
            "danger": "#800000",     # Maroon
            "water": "#5F9EA0",      # Cadet blue
            "magic": "#DDA0DD",      # Plum
        },
        vocab={
            "weapon": "sharp wit",
            "enemy": "hidden mastermind",
            "ally": "informant",
            "goal": "truth",
            "item": "crucial evidence",
            "place": "secret archive",
        },
        tile_weights={"TOWER": 1.4, "RUINS": 1.3, "TAVERN": 1.2},
        endings=["RECOGNITION", "PUNISHMENT", "RETURN"],
        mood="mysterious",
    ),
}


def mix_genres(*genre_names: str, weights: List[float] = None) -> Genre:
    """Mix multiple genres together"""
    if weights is None:
        weights = [1.0] * len(genre_names)

    total = sum(weights)
    weights = [w / total for w in weights]

    genres = [GENRES[name] for name in genre_names if name in GENRES]
    if not genres:
        return GENRES["fantasy"]

    # Mix palettes
    mixed_palette = {}
    for key in genres[0].palette.keys():
        colors = [g.palette.get(key, "#808080") for g in genres]
        # Simple average of hex colors
        r = int(sum(int(c[1:3], 16) * w for c, w in zip(colors, weights)))
        g = int(sum(int(c[3:5], 16) * w for c, w in zip(colors, weights)))
        b = int(sum(int(c[5:7], 16) * w for c, w in zip(colors, weights)))
        mixed_palette[key] = f"#{min(r,255):02x}{min(g,255):02x}{min(b,255):02x}"

    # Mix vocab (weighted random selection)
    mixed_vocab = {}
    for key in genres[0].vocab.keys():
        options = [(g.vocab.get(key, ""), w) for g, w in zip(genres, weights)]
        mixed_vocab[key] = random.choices([o[0] for o in options], [o[1] for o in options])[0]

    # Mix tile weights
    mixed_tiles = {}
    for g, w in zip(genres, weights):
        for tile, tw in g.tile_weights.items():
            mixed_tiles[tile] = mixed_tiles.get(tile, 1.0) + (tw - 1.0) * w

    # Combine endings
    all_endings = set()
    for g in genres:
        all_endings.update(g.endings)

    # Determine mood (majority vote)
    moods = [g.mood for g in genres]
    mood = max(set(moods), key=moods.count)

    return Genre(
        name=" + ".join(genre_names),
        description="Mixed genre",
        palette=mixed_palette,
        vocab=mixed_vocab,
        tile_weights=mixed_tiles,
        endings=list(all_endings),
        mood=mood,
    )


# =============================================================================
# Advanced Plot Node
# =============================================================================

@dataclass
class PlotNode:
    """Plot node with branching support"""
    id: int
    function: ProppFunc
    requires: int
    provides: int

    # Content
    description: str = ""
    location_hint: str = ""

    # Branching
    branch_id: int = 0          # Which story branch (0 = main)
    is_merge_point: bool = False  # Multiple branches converge here
    is_branch_point: bool = False # Story splits here
    exclusive_with: Set[int] = field(default_factory=set)  # Mutually exclusive nodes

    # For endings
    is_ending: bool = False
    ending_type: str = ""       # "victory", "tragedy", "bittersweet", etc.

    # False endings and twists
    is_false_ending: bool = False     # Looks like ending but isn't
    false_ending_reveal: str = ""     # What reveals it's false
    twist_type: TwistType = TwistType.NONE
    twist_reveals: str = ""           # What the twist reveals
    invalidates: Set[int] = field(default_factory=set)  # Nodes this twist invalidates
    recontextualizes: Dict[int, str] = field(default_factory=dict)  # node_id -> new meaning


# =============================================================================
# Twist Templates
# =============================================================================

TWIST_TEMPLATES = {
    TwistType.ALLY_BETRAYAL: [
        ("The {ally} reveals their true allegiance to the {enemy}!",
         "Your trusted companion was a spy all along.",
         {"HAS_ALLY": False}),  # Invalidates ally
        ("\"Did you really think I was helping you?\" laughs the {ally}.",
         "Every piece of advice was a trap.",
         {"HAS_ALLY": False, "HAS_INFO": False}),
    ],

    TwistType.VILLAIN_SYMPATHETIC: [
        ("The {enemy} shows you the truth - they were protecting the world.",
         "The real threat was what you were trying to unleash.",
         {}),
        ("\"I did what I had to,\" the {enemy} whispers, dying.",
         "Their sacrifice saved countless lives you never knew about.",
         {}),
    ],

    TwistType.HERO_ORIGIN: [
        ("You ARE the lost heir of the {place}!",
         "The birthmark proves everything.",
         {}),
        ("The prophecy spoke of YOU all along.",
         "You are both the hero and the villain's child.",
         {}),
    ],

    TwistType.FALSE_VICTORY: [
        ("That wasn't the real {enemy}... just a puppet!",
         "The true master still lurks in shadows.",
         {"VILLAIN_DEAD": False, "QUEST_COMPLETE": False}),
        ("As the dust settles, you realize - this was only the beginning.",
         "The {enemy} you killed was merely a servant.",
         {"VILLAIN_DEAD": False}),
    ],

    TwistType.HIDDEN_VILLAIN: [
        ("The {ally} removes their mask - it was THEM all along!",
         "Every helpful act was manipulation.",
         {"HAS_ALLY": False}),
        ("The true {enemy} emerges from the shadows of the {place}.",
         "You've been fighting the wrong battle.",
         {}),
    ],

    TwistType.PROPHECY_TWIST: [
        ("'Defeat the darkness' meant... become it?!",
         "The prophecy's true meaning is terrifying.",
         {}),
        ("You finally understand - you were meant to FAIL.",
         "Your failure was the true victory.",
         {}),
    ],

    TwistType.DEAD_ALIVE: [
        ("The {ally} you mourned stands before you, alive!",
         "Their 'death' was an elaborate ruse.",
         {"HAS_ALLY": True}),
        ("The {enemy} rises once more! They cannot truly die.",
         "Immortality was their secret all along.",
         {"VILLAIN_DEAD": False}),
    ],

    TwistType.MEMORY_FALSE: [
        ("These memories... they're not real. They were IMPLANTED.",
         "Your entire quest was built on lies.",
         {"HAS_INFO": False}),
        ("You never had a home. The {place} never existed.",
         "Someone created you to believe a false past.",
         {}),
    ],

    TwistType.TIME_LOOP: [
        ("Wait... you've done this before. Many times.",
         "This cycle has repeated endlessly.",
         {}),
        ("The old sage's warning makes sense now - you're trapped in time.",
         "Breaking the loop is the true quest.",
         {}),
    ],

    TwistType.DREAM_REAL: [
        ("The 'nightmare realm' was reality. This... this is the dream.",
         "Everything you thought you saved was illusion.",
         {}),
        ("You wake up. But which world is real?",
         "Both realities exist. You must choose.",
         {}),
    ],
}


FALSE_ENDING_TEMPLATES = [
    # (description, reveal_trigger, what_continues)
    ("Peace returns to the land. Your quest is complete... or is it?",
     "A distant rumble. The {enemy}'s true fortress awakens.",
     ProppFunc.LACK),

    ("You return home a hero. The {place} celebrates...",
     "But the {item} in your pack begins to glow ominously.",
     ProppFunc.DEPARTURE),

    ("The {enemy} falls. Victory! The crowd cheers!",
     "\"Fool,\" echoes a voice. \"I am ETERNAL.\"",
     ProppFunc.STRUGGLE),

    ("At last, the {ally} is saved. Together you escape.",
     "The {ally}'s eyes flash red for just a moment...",
     ProppFunc.INTERDICTION),

    ("The curse is lifted. The kingdom rejoices!",
     "Three days later, the crops begin to wither again.",
     ProppFunc.LACK),
]


@dataclass
class PlotBranch:
    """A story branch/thread"""
    id: int
    name: str
    nodes: List[int] = field(default_factory=list)  # Node IDs
    parent_branch: int = -1     # -1 = root
    merge_into: int = -1        # -1 = doesn't merge
    is_optional: bool = False


@dataclass
class MultiPlot:
    """Multi-branch plot structure"""
    nodes: List[PlotNode] = field(default_factory=list)
    branches: List[PlotBranch] = field(default_factory=list)
    edges: Dict[int, List[int]] = field(default_factory=dict)
    genre: Genre = None

    # Ending nodes
    endings: List[int] = field(default_factory=list)

    def add_node(self, node: PlotNode) -> int:
        node.id = len(self.nodes)
        self.nodes.append(node)
        self.edges[node.id] = []
        return node.id

    def add_edge(self, from_id: int, to_id: int):
        if to_id not in self.edges[from_id]:
            self.edges[from_id].append(to_id)

    def get_all_paths(self) -> List[List[int]]:
        """Get all possible paths through the plot"""
        paths = []

        def dfs(node_id: int, path: List[int], visited: Set[int]):
            if node_id in visited:
                return

            new_path = path + [node_id]
            new_visited = visited | {node_id}

            # Check for exclusive nodes
            node = self.nodes[node_id]
            for excl in node.exclusive_with:
                if excl in visited:
                    return  # Can't reach this node

            if node.is_ending:
                paths.append(new_path)
                return

            successors = self.edges.get(node_id, [])
            if not successors:
                paths.append(new_path)
            else:
                for succ in successors:
                    dfs(succ, new_path, new_visited)

        # Find root nodes
        all_targets = set()
        for succs in self.edges.values():
            all_targets.update(succs)
        roots = [i for i in range(len(self.nodes)) if i not in all_targets]

        for root in roots:
            dfs(root, [], set())

        return paths


# =============================================================================
# Plot Templates (Expanded)
# =============================================================================

PLOT_TEMPLATES = {
    ProppFunc.EQUILIBRIUM: [
        (Requirement.NONE, Provides.HERO_EXISTS,
         "Peace reigns in the {place}", "village"),
        (Requirement.NONE, Provides.HERO_EXISTS,
         "Life continues as it always has", "home"),
    ],

    ProppFunc.LACK: [
        (Requirement.HERO_EXISTS, Provides.NONE,
         "The {enemy} threatens everything", "village"),
        (Requirement.HERO_EXISTS, Provides.NONE,
         "A precious {item} is stolen", "castle"),
        (Requirement.HERO_EXISTS, Provides.NONE,
         "The {ally} goes missing", "clearing"),
    ],

    ProppFunc.INTERDICTION: [
        (Requirement.HERO_EXISTS, Provides.NONE,
         "\"Never venture to the {place}!\"", "village"),
        (Requirement.HERO_EXISTS, Provides.NONE,
         "\"Do not trust the {enemy}!\"", "tavern"),
    ],

    ProppFunc.VIOLATION: [
        (Requirement.HERO_EXISTS, Provides.RULE_BROKEN,
         "The hero defies the warning", "forest"),
        (Requirement.HERO_EXISTS, Provides.RULE_BROKEN | Provides.HAS_INFO,
         "Curiosity overcomes caution", "ruins"),
    ],

    ProppFunc.DEPARTURE: [
        (Requirement.HERO_EXISTS, Provides.HAS_ACCESS,
         "The hero sets forth", "road"),
        (Requirement.HERO_EXISTS | Requirement.RULE_BROKEN, Provides.HAS_ACCESS,
         "No choice but to leave", "clearing"),
    ],

    ProppFunc.DONOR_TEST: [
        (Requirement.HAS_ACCESS, Provides.NONE,
         "A {ally} tests the hero's worth", "temple"),
        (Requirement.HAS_ACCESS, Provides.VILLAIN_WEAK,
         "Ancient spirits reveal secrets", "ruins"),
    ],

    ProppFunc.ACQUISITION: [
        (Requirement.HAS_ACCESS, Provides.HAS_WEAPON,
         "The hero receives a {weapon}", "cave"),
        (Requirement.HAS_ACCESS, Provides.HAS_KEY,
         "A mysterious key is found", "tower"),
        (Requirement.HAS_ACCESS, Provides.HAS_ALLY,
         "A {ally} joins the quest", "tavern"),
        (Requirement.HAS_ACCESS, Provides.HAS_INFO,
         "Secret knowledge is gained", "temple"),
    ],

    ProppFunc.GUIDANCE: [
        (Requirement.HAS_ACCESS, Provides.AT_GOAL,
         "The path to the {goal} becomes clear", "mountain"),
        (Requirement.HAS_ACCESS | Requirement.HAS_KEY, Provides.AT_GOAL,
         "The locked way opens", "castle"),
    ],

    ProppFunc.STRUGGLE: [
        (Requirement.AT_GOAL | Requirement.HAS_WEAPON, Provides.VILLAIN_WEAK,
         "Battle with the {enemy}!", "dungeon"),
        (Requirement.AT_GOAL | Requirement.HAS_ALLY, Provides.VILLAIN_WEAK,
         "Together against the darkness", "cave"),
    ],

    ProppFunc.BRANDING: [
        (Requirement.VILLAIN_WEAK, Provides.HERO_MARKED,
         "The hero is forever changed", "dungeon"),
        (Requirement.HAS_WEAPON, Provides.HERO_MARKED,
         "The {weapon} leaves its mark", "ruins"),
    ],

    ProppFunc.VICTORY: [
        (Requirement.VILLAIN_WEAK | Requirement.HAS_WEAPON, Provides.VILLAIN_DEAD | Provides.QUEST_COMPLETE,
         "The {enemy} falls!", "dungeon"),
        (Requirement.VILLAIN_WEAK | Requirement.HAS_INFO, Provides.VILLAIN_DEAD | Provides.QUEST_COMPLETE,
         "Knowledge defeats evil", "tower"),
    ],

    ProppFunc.PURSUIT: [
        (Requirement.VILLAIN_WEAK, Provides.PURSUED,
         "The {enemy}'s minions give chase", "forest"),
        (Requirement.QUEST_COMPLETE, Provides.PURSUED,
         "Dark forces seek revenge", "road"),
    ],

    ProppFunc.RESCUE: [
        (Requirement.AT_GOAL, Provides.RESCUED_SOMEONE | Provides.QUEST_COMPLETE,
         "The captive is freed!", "dungeon"),
        (Requirement.HAS_ALLY | Requirement.AT_GOAL, Provides.RESCUED_SOMEONE,
         "Together they escape", "cave"),
    ],

    ProppFunc.RECOGNITION: [
        (Requirement.QUEST_COMPLETE, Provides.RECOGNIZED,
         "The hero's true nature is revealed", "castle"),
        (Requirement.HERO_MARKED, Provides.RECOGNIZED,
         "The mark tells the story", "village"),
    ],

    ProppFunc.PUNISHMENT: [
        (Requirement.VILLAIN_DEAD, Provides.PUNISHED_VILLAIN,
         "Justice is served", "castle"),
        (Requirement.RECOGNIZED, Provides.PUNISHED_VILLAIN,
         "The conspirators face judgment", "village"),
    ],

    ProppFunc.RETURN: [
        (Requirement.QUEST_COMPLETE, Provides.NONE,
         "Home at last, forever changed", "village"),
        (Requirement.RECOGNIZED, Provides.NONE,
         "A new chapter begins", "home"),
        (Requirement.RESCUED_SOMEONE, Provides.NONE,
         "Together, a new life awaits", "village"),
    ],
}


# =============================================================================
# Advanced Plot Generator
# =============================================================================

class AdvancedPlotGenerator:
    """
    Generates complex multi-branch plots.

    Features:
    - Multiple story threads
    - Branch and merge points
    - Exclusive endings
    - Genre-themed descriptions
    """

    def __init__(self, genre: Genre = None, seed: int = None):
        self.genre = genre or GENRES["fantasy"]
        self.seed = seed
        if seed is not None:
            random.seed(seed)
        self.plot = MultiPlot(genre=self.genre)

    def reset(self, seed: int = None):
        if seed is not None:
            self.seed = seed
            random.seed(seed)
        self.plot = MultiPlot(genre=self.genre)

    def _apply_genre_vocab(self, text: str) -> str:
        """Replace {placeholders} with genre-specific vocabulary"""
        result = text
        for key, value in self.genre.vocab.items():
            result = result.replace(f"{{{key}}}", value)
        return result

    def generate_linear(self, length: int = 6) -> bool:
        """Generate a simple linear plot"""
        self.reset()

        # Choose ending based on genre
        ending_func = ProppFunc[random.choice(self.genre.endings)]

        # Build backward from ending
        return self._build_backward(ending_func, length)

    def generate_branching(self,
                          main_length: int = 6,
                          num_branches: int = 2,
                          branch_length: int = 3) -> bool:
        """
        Generate plot with branches that can merge or lead to exclusive endings.
        """
        self.reset()

        # Generate main plot
        if not self._build_backward(ProppFunc.VICTORY, main_length):
            return False

        main_branch = PlotBranch(id=0, name="Main Quest",
                                 nodes=[n.id for n in self.plot.nodes])
        self.plot.branches.append(main_branch)

        # Find good branch points (nodes with HAS_ACCESS)
        branch_points = [
            n.id for n in self.plot.nodes
            if n.provides & Provides.HAS_ACCESS and not n.is_ending
        ]

        if not branch_points:
            return True  # Linear plot is fine

        # Add side branches
        for i in range(min(num_branches, len(branch_points))):
            branch_point = random.choice(branch_points)
            branch_points.remove(branch_point)

            # Create side quest
            side_branch = self._create_side_branch(
                branch_point,
                branch_length,
                branch_id=i + 1
            )

            if side_branch:
                self.plot.branches.append(side_branch)

        return True

    def generate_multi_ending(self,
                             length: int = 8,
                             num_endings: int = 3) -> bool:
        """
        Generate plot with multiple possible endings (some exclusive).
        """
        self.reset()

        # Build toward a branch point
        midpoint = length // 2

        # Build first half (shared)
        if not self._build_backward(ProppFunc.GUIDANCE, midpoint):
            return False

        # Mark last node as branch point
        if self.plot.nodes:
            self.plot.nodes[-1].is_branch_point = True

        # Build multiple endings
        available_endings = list(self.genre.endings)
        random.shuffle(available_endings)

        ending_nodes = []
        for i in range(min(num_endings, len(available_endings))):
            ending_type = available_endings[i]
            ending_func = ProppFunc[ending_type]

            # Build path to this ending
            end_node = self._build_ending_branch(ending_func, length - midpoint, i)
            if end_node:
                ending_nodes.append(end_node)

        # Mark exclusive endings
        if len(ending_nodes) >= 2:
            for i, node_id in enumerate(ending_nodes):
                self.plot.nodes[node_id].exclusive_with = set(
                    ending_nodes[:i] + ending_nodes[i+1:]
                )

        return len(ending_nodes) > 0

    def _build_backward(self, finale_func: ProppFunc, target_length: int) -> bool:
        """Build plot backward from finale"""
        # Create finale
        templates = PLOT_TEMPLATES.get(finale_func, [])
        if not templates:
            return False

        req, prov, desc, loc = random.choice(templates)
        finale = PlotNode(
            id=-1,  # Will be assigned
            function=finale_func,
            requires=req,
            provides=prov,
            description=self._apply_genre_vocab(desc),
            location_hint=loc,
            is_ending=True,
            ending_type=finale_func.name,
        )
        finale_id = self.plot.add_node(finale)
        self.plot.endings.append(finale_id)

        # Track requirements
        unsatisfied = finale.requires
        pending = [(finale_id, finale.requires)]
        used_funcs = {finale_func}

        iterations = 0
        while unsatisfied and iterations < target_length * 2:
            iterations += 1

            # Find function that provides what we need
            best = self._find_providing_function(unsatisfied, used_funcs)
            if not best:
                break

            func, template = best
            req, prov, desc, loc = template

            new_node = PlotNode(
                id=-1,
                function=func,
                requires=req,
                provides=prov,
                description=self._apply_genre_vocab(desc),
                location_hint=loc,
            )
            new_id = self.plot.add_node(new_node)

            # Connect
            for node_id, node_req in pending:
                if prov & node_req:
                    self.plot.add_edge(new_id, node_id)

            # Check if existing nodes provide what new node needs
            for node_id, _ in pending:
                existing = self.plot.nodes[node_id]
                if existing.provides & req:
                    self.plot.add_edge(node_id, new_id)

            # Update tracking
            unsatisfied = (unsatisfied & ~prov) | req
            pending.append((new_id, req))
            used_funcs.add(func)

            if len(self.plot.nodes) >= target_length:
                break

        return len(self.plot.nodes) >= 3

    def _find_providing_function(self,
                                 needs: int,
                                 used: Set[ProppFunc]) -> Optional[Tuple[ProppFunc, tuple]]:
        """Find a function that provides something we need"""
        candidates = []

        funcs = list(ProppFunc)
        random.shuffle(funcs)

        for func in funcs:
            # Allow some repetition
            if func in used and func not in [ProppFunc.ACQUISITION, ProppFunc.DONOR_TEST]:
                continue

            for template in PLOT_TEMPLATES.get(func, []):
                req, prov, desc, loc = template
                provides_needed = prov & needs
                if provides_needed:
                    # Score by how much it provides
                    score = bin(provides_needed).count('1')
                    candidates.append((score, func, template))

        if not candidates:
            return None

        # Pick best (or random among good ones)
        candidates.sort(key=lambda x: -x[0])
        top_score = candidates[0][0]
        top_candidates = [c for c in candidates if c[0] == top_score]

        _, func, template = random.choice(top_candidates)
        return func, template

    def _create_side_branch(self,
                           branch_point: int,
                           length: int,
                           branch_id: int) -> Optional[PlotBranch]:
        """Create a side quest branch"""
        # Choose a side quest goal
        side_goals = [ProppFunc.RESCUE, ProppFunc.ACQUISITION, ProppFunc.RECOGNITION]
        goal = random.choice(side_goals)

        templates = PLOT_TEMPLATES.get(goal, [])
        if not templates:
            return None

        req, prov, desc, loc = random.choice(templates)

        # Create ending node for side quest
        end_node = PlotNode(
            id=-1,
            function=goal,
            requires=req | Requirement.HAS_ACCESS,
            provides=prov,
            description=self._apply_genre_vocab(desc),
            location_hint=loc,
            branch_id=branch_id,
        )
        end_id = self.plot.add_node(end_node)

        # Connect to branch point
        self.plot.add_edge(branch_point, end_id)

        # Mark branch point
        self.plot.nodes[branch_point].is_branch_point = True

        branch = PlotBranch(
            id=branch_id,
            name=f"Side Quest: {goal.name}",
            nodes=[end_id],
            parent_branch=0,
            is_optional=True,
        )

        return branch

    def _build_ending_branch(self,
                            ending_func: ProppFunc,
                            length: int,
                            branch_id: int) -> Optional[int]:
        """Build a branch leading to specific ending"""
        templates = PLOT_TEMPLATES.get(ending_func, [])
        if not templates:
            return None

        req, prov, desc, loc = random.choice(templates)

        end_node = PlotNode(
            id=-1,
            function=ending_func,
            requires=req,
            provides=prov,
            description=self._apply_genre_vocab(desc),
            location_hint=loc,
            branch_id=branch_id,
            is_ending=True,
            ending_type=ending_func.name,
        )
        end_id = self.plot.add_node(end_node)
        self.plot.endings.append(end_id)

        # Connect from existing nodes that could lead here
        for node in self.plot.nodes[:-1]:
            if node.provides & req:
                self.plot.add_edge(node.id, end_id)

        return end_id

    def generate_with_twist(self,
                           length: int = 8,
                           twist_type: TwistType = None) -> bool:
        """
        Generate plot with a plot twist.

        The twist recontextualizes earlier events.
        """
        self.reset()

        # Build normal plot first
        if not self._build_backward(ProppFunc.VICTORY, length - 2):
            return False

        # Choose twist type
        if twist_type is None:
            twist_type = random.choice([t for t in TwistType if t != TwistType.NONE])

        templates = TWIST_TEMPLATES.get(twist_type, [])
        if not templates:
            return False

        twist_desc, reveal, invalidations = random.choice(templates)
        twist_desc = self._apply_genre_vocab(twist_desc)
        reveal = self._apply_genre_vocab(reveal)

        # Find a good place for the twist (after midpoint)
        midpoint = len(self.plot.nodes) // 2
        twist_position = random.randint(midpoint, len(self.plot.nodes) - 1)

        # Create twist node
        twist_node = PlotNode(
            id=-1,
            function=ProppFunc.RECOGNITION,  # Twists are revelations
            requires=Requirement.AT_GOAL,
            provides=Provides.RECOGNIZED,
            description=twist_desc,
            location_hint="ruins",  # Twists often in mysterious places
            twist_type=twist_type,
            twist_reveals=reveal,
        )

        # Find nodes to invalidate based on twist type
        if twist_type == TwistType.ALLY_BETRAYAL:
            for node in self.plot.nodes:
                if node.provides & Provides.HAS_ALLY:
                    twist_node.invalidates.add(node.id)
                    twist_node.recontextualizes[node.id] = "The ally was deceiving you"

        elif twist_type == TwistType.FALSE_VICTORY:
            for node in self.plot.nodes:
                if node.function == ProppFunc.VICTORY:
                    twist_node.invalidates.add(node.id)
                    twist_node.recontextualizes[node.id] = "This victory was hollow"

        elif twist_type == TwistType.HIDDEN_VILLAIN:
            for node in self.plot.nodes:
                if node.provides & Provides.HAS_ALLY:
                    twist_node.recontextualizes[node.id] = "They were watching you all along"

        twist_id = self.plot.add_node(twist_node)

        # Connect twist to the story
        if twist_position < len(self.plot.nodes) - 1:
            self.plot.add_edge(twist_position, twist_id)

        # Add continuation after twist (new goal)
        continuation = PlotNode(
            id=-1,
            function=ProppFunc.STRUGGLE,
            requires=Requirement.RECOGNIZED,
            provides=Provides.VILLAIN_WEAK,
            description=self._apply_genre_vocab("Now you face the TRUE {enemy}!"),
            location_hint="dungeon",
        )
        cont_id = self.plot.add_node(continuation)
        self.plot.add_edge(twist_id, cont_id)

        # Add real ending
        final = PlotNode(
            id=-1,
            function=ProppFunc.VICTORY,
            requires=Requirement.VILLAIN_WEAK | Requirement.RECOGNIZED,
            provides=Provides.QUEST_COMPLETE | Provides.VILLAIN_DEAD,
            description=self._apply_genre_vocab("At last, the TRUE {enemy} is defeated!"),
            location_hint="dungeon",
            is_ending=True,
            ending_type="TRUE_VICTORY",
        )
        final_id = self.plot.add_node(final)
        self.plot.add_edge(cont_id, final_id)
        self.plot.endings.append(final_id)

        return True

    def generate_with_false_ending(self,
                                   length: int = 10,
                                   num_false_endings: int = 1) -> bool:
        """
        Generate plot with false ending(s).

        Player thinks they've won, but the story continues.
        """
        self.reset()

        for i in range(num_false_endings):
            # Build to false ending
            segment_length = length // (num_false_endings + 1)

            if i == 0:
                if not self._build_backward(ProppFunc.VICTORY, segment_length):
                    return False
            else:
                # Continue from previous reveal
                if not self._continue_from_reveal(segment_length):
                    continue

            # Mark last victory as false ending
            for node in reversed(self.plot.nodes):
                if node.function == ProppFunc.VICTORY and not node.is_false_ending:
                    node.is_false_ending = True
                    node.is_ending = False  # Not a real ending!

                    # Choose reveal
                    template = random.choice(FALSE_ENDING_TEMPLATES)
                    false_desc, reveal, next_func = template

                    node.description = self._apply_genre_vocab(false_desc)
                    node.false_ending_reveal = self._apply_genre_vocab(reveal)

                    # Add reveal node
                    reveal_node = PlotNode(
                        id=-1,
                        function=next_func,
                        requires=Requirement.QUEST_COMPLETE,
                        provides=Provides.NONE,
                        description=node.false_ending_reveal,
                        location_hint=node.location_hint,
                    )
                    reveal_id = self.plot.add_node(reveal_node)
                    self.plot.add_edge(node.id, reveal_id)
                    break

        # Add real ending
        final = PlotNode(
            id=-1,
            function=ProppFunc.VICTORY,
            requires=Requirement.VILLAIN_WEAK | Requirement.HAS_WEAPON,
            provides=Provides.QUEST_COMPLETE | Provides.VILLAIN_DEAD,
            description=self._apply_genre_vocab("This time, the {enemy} falls FOR REAL!"),
            location_hint="dungeon",
            is_ending=True,
            ending_type="FINAL_VICTORY",
        )
        final_id = self.plot.add_node(final)

        # Connect from last non-ending node
        for node in reversed(self.plot.nodes[:-1]):
            if not node.is_ending:
                self.plot.add_edge(node.id, final_id)
                break

        self.plot.endings.append(final_id)

        return True

    def _continue_from_reveal(self, length: int) -> bool:
        """Continue plot after a false ending reveal"""
        # Find last reveal node
        last_reveal = None
        for node in reversed(self.plot.nodes):
            if node.false_ending_reveal or node.function == ProppFunc.LACK:
                last_reveal = node
                break

        if not last_reveal:
            return False

        # Build new segment
        for _ in range(length):
            # Find function that can follow
            func = random.choice([
                ProppFunc.DEPARTURE, ProppFunc.ACQUISITION,
                ProppFunc.DONOR_TEST, ProppFunc.GUIDANCE,
                ProppFunc.STRUGGLE
            ])

            templates = PLOT_TEMPLATES.get(func, [])
            if not templates:
                continue

            req, prov, desc, loc = random.choice(templates)

            new_node = PlotNode(
                id=-1,
                function=func,
                requires=req,
                provides=prov,
                description=self._apply_genre_vocab(desc),
                location_hint=loc,
            )
            new_id = self.plot.add_node(new_node)
            self.plot.add_edge(last_reveal.id, new_id)
            last_reveal = new_node

        return True

    def generate_epic(self,
                     acts: int = 3,
                     nodes_per_act: int = 4,
                     twists: int = 1,
                     false_endings: int = 1) -> bool:
        """
        Generate epic multi-act plot with twists and false endings.

        Structure:
        - Act 1: Setup and departure
        - Act 2: Trials, false victory, twist
        - Act 3: True confrontation and resolution
        """
        self.reset()

        total_nodes = 0

        # ACT 1: Setup
        act1_funcs = [ProppFunc.EQUILIBRIUM, ProppFunc.LACK,
                      ProppFunc.INTERDICTION, ProppFunc.DEPARTURE]

        for func in act1_funcs[:nodes_per_act]:
            templates = PLOT_TEMPLATES.get(func, [])
            if templates:
                req, prov, desc, loc = random.choice(templates)
                node = PlotNode(
                    id=-1, function=func, requires=req, provides=prov,
                    description=self._apply_genre_vocab(desc),
                    location_hint=loc,
                )
                node_id = self.plot.add_node(node)
                if total_nodes > 0:
                    self.plot.add_edge(total_nodes - 1, node_id)
                total_nodes += 1

        # ACT 2: Trials and false victory
        act2_funcs = [ProppFunc.DONOR_TEST, ProppFunc.ACQUISITION,
                      ProppFunc.GUIDANCE, ProppFunc.STRUGGLE, ProppFunc.VICTORY]

        for func in act2_funcs[:nodes_per_act + 1]:
            templates = PLOT_TEMPLATES.get(func, [])
            if templates:
                req, prov, desc, loc = random.choice(templates)
                node = PlotNode(
                    id=-1, function=func, requires=req, provides=prov,
                    description=self._apply_genre_vocab(desc),
                    location_hint=loc,
                )

                # Make victory a false ending
                if func == ProppFunc.VICTORY and false_endings > 0:
                    template = random.choice(FALSE_ENDING_TEMPLATES)
                    false_desc, reveal, _ = template
                    node.description = self._apply_genre_vocab(false_desc)
                    node.is_false_ending = True
                    node.false_ending_reveal = self._apply_genre_vocab(reveal)
                    false_endings -= 1

                node_id = self.plot.add_node(node)
                if total_nodes > 0:
                    self.plot.add_edge(total_nodes - 1, node_id)
                total_nodes += 1

        # Add twist after false victory
        if twists > 0:
            twist_type = random.choice([
                TwistType.ALLY_BETRAYAL, TwistType.FALSE_VICTORY,
                TwistType.HIDDEN_VILLAIN, TwistType.VILLAIN_SYMPATHETIC
            ])
            templates = TWIST_TEMPLATES.get(twist_type, [])
            if templates:
                twist_desc, reveal, _ = random.choice(templates)
                twist = PlotNode(
                    id=-1, function=ProppFunc.RECOGNITION,
                    requires=Requirement.QUEST_COMPLETE,
                    provides=Provides.RECOGNIZED,
                    description=self._apply_genre_vocab(twist_desc),
                    location_hint="ruins",
                    twist_type=twist_type,
                    twist_reveals=self._apply_genre_vocab(reveal),
                )
                twist_id = self.plot.add_node(twist)
                self.plot.add_edge(total_nodes - 1, twist_id)
                total_nodes += 1

        # ACT 3: True confrontation
        act3_funcs = [ProppFunc.PURSUIT, ProppFunc.BRANDING,
                      ProppFunc.STRUGGLE, ProppFunc.VICTORY, ProppFunc.RETURN]

        for func in act3_funcs[:nodes_per_act + 1]:
            templates = PLOT_TEMPLATES.get(func, [])
            if templates:
                req, prov, desc, loc = random.choice(templates)

                # Modify for "true" versions
                if func == ProppFunc.VICTORY:
                    desc = "The TRUE {enemy} is finally defeated!"
                elif func == ProppFunc.RETURN:
                    desc = "At long last, the hero returns - truly victorious."

                node = PlotNode(
                    id=-1, function=func, requires=req, provides=prov,
                    description=self._apply_genre_vocab(desc),
                    location_hint=loc,
                    is_ending=(func == ProppFunc.RETURN),
                    ending_type="EPIC_VICTORY" if func == ProppFunc.RETURN else "",
                )
                node_id = self.plot.add_node(node)
                if total_nodes > 0:
                    self.plot.add_edge(total_nodes - 1, node_id)
                total_nodes += 1

                if func == ProppFunc.RETURN:
                    self.plot.endings.append(node_id)

        return total_nodes >= acts * nodes_per_act

    def get_summary(self) -> str:
        """Get human-readable plot summary"""
        # Count special nodes
        twists = [n for n in self.plot.nodes if n.twist_type != TwistType.NONE]
        false_ends = [n for n in self.plot.nodes if n.is_false_ending]

        lines = [
            f"=== {self.genre.name} Plot ===",
            f"Mood: {self.genre.mood}",
            f"Nodes: {len(self.plot.nodes)}",
            f"Branches: {len(self.plot.branches)}",
            f"Endings: {len(self.plot.endings)}",
            f"Twists: {len(twists)}",
            f"False Endings: {len(false_ends)}",
            "",
            "Story Structure:",
            "-" * 40,
        ]

        # Show all paths
        paths = self.plot.get_all_paths()
        for i, path in enumerate(paths[:5]):  # Limit to 5 paths
            lines.append(f"\nPath {i+1}:")
            for node_id in path:
                node = self.plot.nodes[node_id]
                markers = []
                if node.is_ending:
                    markers.append("END")
                if node.is_false_ending:
                    markers.append("FALSE END!")
                if node.is_branch_point:
                    markers.append("BRANCH")
                if node.twist_type != TwistType.NONE:
                    markers.append(f"TWIST:{node.twist_type.name}")

                marker_str = f" [{', '.join(markers)}]" if markers else ""
                lines.append(f"  {node.function.name}: {node.description[:45]}...{marker_str}")

                # Show twist reveal
                if node.twist_reveals:
                    lines.append(f"    ↳ Reveals: {node.twist_reveals[:40]}...")

                # Show false ending reveal
                if node.false_ending_reveal:
                    lines.append(f"    ↳ But then: {node.false_ending_reveal[:40]}...")

        if len(paths) > 5:
            lines.append(f"\n... and {len(paths) - 5} more paths")

        return '\n'.join(lines)


# =============================================================================
# Demo
# =============================================================================

def demo():
    """Demo advanced plot generation"""
    print("=" * 60)
    print("ADVANCED PLOT GENERATOR DEMO")
    print("=" * 60)

    # Test plot with twist
    print("\n1. PLOT WITH TWIST (Dark Fantasy + Ally Betrayal):")
    print("-" * 50)
    gen = AdvancedPlotGenerator(GENRES["dark_fantasy"], seed=42)
    gen.generate_with_twist(length=8, twist_type=TwistType.ALLY_BETRAYAL)
    print(gen.get_summary())

    # Test false ending
    print("\n\n2. PLOT WITH FALSE ENDING (Fantasy):")
    print("-" * 50)
    gen = AdvancedPlotGenerator(GENRES["fantasy"], seed=123)
    gen.generate_with_false_ending(length=10, num_false_endings=1)
    print(gen.get_summary())

    # Test epic multi-act
    print("\n\n3. EPIC 3-ACT PLOT (Mystery + Twist + False Ending):")
    print("-" * 50)
    gen = AdvancedPlotGenerator(GENRES["mystery"], seed=456)
    gen.generate_epic(acts=3, nodes_per_act=4, twists=1, false_endings=1)
    print(gen.get_summary())

    # Test mixed genre epic
    print("\n\n4. MIXED GENRE EPIC (Solarpunk + Hopepunk):")
    print("-" * 50)
    mixed = mix_genres("solarpunk", "hopepunk", weights=[0.6, 0.4])
    gen = AdvancedPlotGenerator(mixed, seed=789)
    gen.generate_epic(acts=3, nodes_per_act=3, twists=1, false_endings=1)
    print(gen.get_summary())

    # Show twist types
    print("\n\n5. AVAILABLE TWIST TYPES:")
    print("-" * 50)
    for twist in TwistType:
        if twist != TwistType.NONE:
            templates = TWIST_TEMPLATES.get(twist, [])
            if templates:
                example = templates[0][0][:50]
                print(f"  {twist.name}: \"{example}...\"")


if __name__ == "__main__":
    demo()
