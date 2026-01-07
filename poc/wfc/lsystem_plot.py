"""
L-System Plot Generator

Generates fractal narrative structures from a seed using Lindenmayer systems.
2 bytes seed → 100+ nodes deterministically.

The grammar rules encode narrative DNA:
- Uppercase = narrative containers (expand further)
- Lowercase = atomic Propp functions (terminal symbols)

This is Z80-friendly: rules fit in ~100 bytes, expansion is deterministic.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Set
from enum import IntEnum
import struct


# =============================================================================
# PROPP FUNCTION ALPHABET
# =============================================================================

# Terminal symbols (lowercase) = atomic story beats
# These map to ProppFunc from plot_fractal.py
PROPP_ALPHABET = {
    # Act I - Setup
    'e': 'EQUILIBRIUM',      # Initial state
    'l': 'LACK',             # Something missing/wrong
    'i': 'INTERDICTION',     # Warning given
    'v': 'VIOLATION',        # Warning ignored

    # Act II - Adventure
    'd': 'DEPARTURE',        # Hero leaves
    't': 'DONOR_TEST',       # Trial/test
    'a': 'ACQUISITION',      # Gain helper/item
    'g': 'GUIDANCE',         # Direction given

    # Act III - Confrontation
    's': 'STRUGGLE',         # Battle/conflict
    'b': 'BRANDING',         # Hero marked
    'w': 'VICTORY',          # Hero wins
    'p': 'PURSUIT',          # Chase sequence

    # Act IV - Resolution
    'r': 'RESCUE',           # Save someone
    'n': 'RECOGNITION',      # True identity revealed
    'u': 'PUNISHMENT',       # Villain punished
    'h': 'RETURN',           # Hero returns home
}

# Non-terminal symbols (uppercase) = expandable containers
CONTAINER_SYMBOLS = {
    'S': 'SAGA',             # Multi-arc epic
    'A': 'ARC',              # Major story arc
    'C': 'CHAPTER',          # Chapter/subplot
    'Q': 'QUEST',            # Scene cluster
    'B': 'BEAT',             # Single beat (rarely used)

    # Special modifiers
    'T': 'TWIST',            # Plot twist insertion point
    'F': 'FALSE_END',        # False ending
    'X': 'BRANCH',           # Branching point
}


# =============================================================================
# GRAMMAR RULES (The Narrative DNA)
# =============================================================================

# Each rule: symbol -> list of possible expansions
# Weights can be added for probabilistic selection

GRAMMAR_RULES: Dict[str, List[Tuple[str, float]]] = {
    # SAGA expands to arc patterns
    'S': [
        ('ACE', 1.0),              # Setup-Conflict-End (3-act)
        ('AACE', 0.7),             # 4-arc saga
        ('ATCE', 0.5),             # With twist in middle
        ('AXCE', 0.3),             # With branching
    ],

    # ARC expands to chapter patterns
    'A': [
        ('CQC', 1.0),              # Chapter-Quest-Chapter
        ('QCQ', 0.8),              # Quest-Chapter-Quest
        ('CCQ', 0.6),              # Heavy chapters
        ('CTCQ', 0.4),             # With twist
    ],

    # CHAPTER expands to quest/scene patterns
    'C': [
        ('QQ', 1.0),               # Two quests
        ('QQQ', 0.5),              # Three quests
        ('dga', 0.8),              # Departure-Guidance-Acquisition
        ('lds', 0.6),              # Lack-Departure-Struggle
    ],

    # QUEST expands to beat patterns
    'Q': [
        ('dgt', 1.0),              # Departure-Guidance-Test
        ('tas', 0.8),              # Test-Acquire-Struggle
        ('ivd', 0.6),              # Interdiction-Violation-Departure
        ('sw', 0.7),               # Struggle-Victory
        ('gta', 0.5),              # Guidance-Test-Acquisition
    ],

    # TWIST - special expansion
    'T': [
        ('nX', 1.0),               # Recognition + Branch
        ('bs', 0.8),               # Branding-Struggle (betrayal moment)
        ('pn', 0.6),               # Pursuit-Recognition
    ],

    # FALSE_END - looks like ending but continues
    'F': [
        ('wC', 1.0),               # Victory... then more!
        ('hQ', 0.8),               # Return... but wait!
        ('rA', 0.5),               # Rescue... new arc!
    ],

    # BRANCH - creates parallel paths
    'X': [
        ('Q|Q', 1.0),              # Two quest branches
        ('C|C', 0.5),              # Two chapter branches
        ('sw|rn', 0.7),            # Struggle/Victory OR Rescue/Recognition
    ],

    # ENDING patterns (special rule 'E')
    'E': [
        ('swh', 1.0),              # Struggle-Victory-Return
        ('rnuh', 0.8),             # Recognition-Punishment-Return
        ('swrh', 0.6),             # Full resolution
        ('wFh', 0.3),              # Victory-FalseEnd-Return
    ],
}


# =============================================================================
# GENRE RULE MODIFIERS
# =============================================================================

# Each genre biases certain rules
GENRE_RULE_WEIGHTS = {
    'fantasy': {
        'Q': [('dgt', 1.5), ('tas', 1.2), ('sw', 1.0)],
    },
    'mystery': {
        'Q': [('ivd', 1.5), ('gta', 1.3)],
        'T': [('nX', 1.5), ('pn', 1.2)],
    },
    'solarpunk': {
        'Q': [('gta', 1.5), ('dgt', 1.0)],
        'E': [('rnuh', 0.3), ('swrh', 1.5)],  # Less punishment
    },
    'dark_fantasy': {
        'T': [('bs', 1.5)],  # More betrayals
        'E': [('swh', 0.5), ('wFh', 1.5)],  # More false endings
    },
    'isekai': {
        'A': [('CQC', 1.5), ('CTCQ', 1.2)],  # More structured
        'Q': [('dgt', 1.5), ('tas', 1.3)],   # Classic hero journey
    },
    'cozy': {
        'Q': [('gta', 1.5), ('dgt', 0.8)],
        'E': [('swh', 1.5), ('rnuh', 1.3)],  # Happy endings
        'T': [('nX', 0.5)],  # Fewer twists
    },
}


# =============================================================================
# L-SYSTEM EXPANDER
# =============================================================================

class LSystemExpander:
    """
    Expands L-system grammar into plot structure.

    Deterministic: same seed always produces same result.
    Compact: rules fit in ~100 bytes.
    """

    def __init__(self, seed: int = 0, genre: str = None, max_depth: int = 6):
        self.seed = seed
        self.genre = genre
        self.max_depth = max_depth
        self.rng_state = seed

        # Build effective rules with genre modifiers
        self.rules = self._build_rules()

    def _lcg_random(self) -> float:
        """Linear Congruential Generator - Z80 compatible"""
        # Classic LCG: state = (a * state + c) mod m
        # These constants work well and fit in 16-bit math
        self.rng_state = (self.rng_state * 1103515245 + 12345) & 0x7FFFFFFF
        return (self.rng_state >> 16) / 32768.0

    def _seed_for_symbol(self, symbol: str, depth: int, position: int):
        """Create deterministic sub-seed for each expansion"""
        self.rng_state = (self.seed + ord(symbol) * 256 + depth * 65536 + position) & 0x7FFFFFFF

    def _build_rules(self) -> Dict[str, List[Tuple[str, float]]]:
        """Build rules with genre modifications"""
        rules = {k: list(v) for k, v in GRAMMAR_RULES.items()}

        if self.genre and self.genre in GENRE_RULE_WEIGHTS:
            mods = GENRE_RULE_WEIGHTS[self.genre]
            for symbol, mod_rules in mods.items():
                if symbol in rules:
                    # Modify weights
                    for pattern, weight_mod in mod_rules:
                        for i, (rule_pattern, weight) in enumerate(rules[symbol]):
                            if rule_pattern == pattern:
                                rules[symbol][i] = (pattern, weight * weight_mod)

        return rules

    def _select_rule(self, symbol: str) -> str:
        """Select expansion rule using weighted random"""
        if symbol not in self.rules:
            return symbol  # Terminal or unknown

        options = self.rules[symbol]
        total_weight = sum(w for _, w in options)

        r = self._lcg_random() * total_weight
        cumulative = 0.0

        for pattern, weight in options:
            cumulative += weight
            if r <= cumulative:
                return pattern

        return options[0][0]  # Fallback

    def expand(self, start: str = 'S') -> str:
        """
        Expand from start symbol to full string.

        Returns string of terminals (lowercase Propp functions)
        with special markers for branches (|) and structure.
        """
        return self._expand_recursive(start, 0, 0)

    def _expand_recursive(self, symbols: str, depth: int, position: int) -> str:
        """Recursively expand symbols"""
        if depth > self.max_depth:
            # Convert remaining non-terminals to simple patterns
            return self._force_terminal(symbols)

        result = []
        pos = 0

        for i, char in enumerate(symbols):
            if char == '|':
                # Branch marker - keep it
                result.append('|')
            elif char.isupper():
                # Non-terminal - expand
                self._seed_for_symbol(char, depth, position + pos)
                expansion = self._select_rule(char)
                expanded = self._expand_recursive(expansion, depth + 1, position + pos)
                result.append(expanded)
                pos += len(expanded)
            else:
                # Terminal - keep it
                result.append(char)
                pos += 1

        return ''.join(result)

    def _force_terminal(self, symbols: str) -> str:
        """Force non-terminals to become terminals"""
        result = []
        for char in symbols:
            if char.isupper():
                # Map to default terminal pattern
                defaults = {
                    'S': 'sw', 'A': 'ds', 'C': 'gt', 'Q': 'ta',
                    'T': 'n', 'F': 'w', 'X': 's', 'E': 'wh', 'B': 't'
                }
                result.append(defaults.get(char, 't'))
            else:
                result.append(char)
        return ''.join(result)

    def to_propp_sequence(self, expanded: str = None) -> List[str]:
        """Convert expanded string to Propp function sequence"""
        if expanded is None:
            expanded = self.expand()

        sequence = []
        branches = expanded.split('|')

        if len(branches) == 1:
            # Linear
            for char in expanded:
                if char in PROPP_ALPHABET:
                    sequence.append(PROPP_ALPHABET[char])
        else:
            # Has branches - return nested structure
            for branch in branches:
                branch_seq = []
                for char in branch:
                    if char in PROPP_ALPHABET:
                        branch_seq.append(PROPP_ALPHABET[char])
                if branch_seq:
                    sequence.append(branch_seq)

        return sequence

    def get_structure_info(self, expanded: str = None) -> Dict:
        """Analyze the expanded structure"""
        if expanded is None:
            expanded = self.expand()

        return {
            'raw': expanded,
            'length': len([c for c in expanded if c.islower()]),
            'branches': expanded.count('|'),
            'has_twist': 'n' in expanded and expanded.index('n') < len(expanded) * 0.8,
            'acts': self._count_acts(expanded),
        }

    def _count_acts(self, expanded: str) -> int:
        """Estimate number of acts from structure"""
        # Rough heuristic: count major transitions
        transitions = 0
        last_type = None
        for char in expanded:
            if char in 'eliv':  # Setup
                current = 'setup'
            elif char in 'dgta':  # Adventure
                current = 'adventure'
            elif char in 'sbwp':  # Confrontation
                current = 'confrontation'
            elif char in 'rnuh':  # Resolution
                current = 'resolution'
            else:
                continue

            if last_type and current != last_type:
                transitions += 1
            last_type = current

        return max(1, transitions // 2)


# =============================================================================
# PLOT NODE GENERATOR (from L-System expansion)
# =============================================================================

@dataclass
class LSystemPlotNode:
    """Minimal plot node - Z80 friendly (5 bytes per node)"""
    id: int                    # 1 byte
    function: str              # stored as index (1 byte)
    parent_id: int = 0         # 1 byte
    flags: int = 0             # 1 byte (is_ending, is_twist, etc.)
    next_id: int = 0           # 1 byte (or 2 for branches)

    # Flags
    FLAG_ENDING = 0x80
    FLAG_TWIST = 0x40
    FLAG_BRANCH = 0x20
    FLAG_FALSE_END = 0x10

    def to_bytes(self) -> bytes:
        """Pack to 5 bytes for Z80"""
        func_index = list(PROPP_ALPHABET.values()).index(self.function) if self.function in PROPP_ALPHABET.values() else 0
        return struct.pack('BBBBB',
            self.id & 0xFF,
            func_index & 0xFF,
            self.parent_id & 0xFF,
            self.flags & 0xFF,
            self.next_id & 0xFF
        )


class LSystemPlotGenerator:
    """
    Generates plot structure from L-system expansion.

    Pipeline:
    1. Seed → L-System expansion → string
    2. String → Node graph
    3. Node graph → JSON or Z80 bytes
    """

    def __init__(self, seed: int = 0, genre: str = None):
        self.seed = seed
        self.genre = genre
        self.expander = LSystemExpander(seed, genre)
        self.nodes: List[LSystemPlotNode] = []

    def generate(self) -> List[LSystemPlotNode]:
        """Generate plot nodes from L-system"""
        expanded = self.expander.expand()
        sequence = self.expander.to_propp_sequence(expanded)
        info = self.expander.get_structure_info(expanded)

        self.nodes = []
        node_id = 0

        # Handle branches
        if any(isinstance(item, list) for item in sequence):
            # Has branches
            for branch_idx, item in enumerate(sequence):
                if isinstance(item, list):
                    # Branch point
                    for func in item:
                        node = LSystemPlotNode(
                            id=node_id,
                            function=func,
                            parent_id=max(0, node_id - 1),
                            flags=LSystemPlotNode.FLAG_BRANCH if branch_idx > 0 else 0,
                            next_id=node_id + 1
                        )
                        self.nodes.append(node)
                        node_id += 1
                else:
                    # Single function
                    node = LSystemPlotNode(
                        id=node_id,
                        function=item,
                        parent_id=max(0, node_id - 1),
                        next_id=node_id + 1
                    )
                    self.nodes.append(node)
                    node_id += 1
        else:
            # Linear sequence
            for i, func in enumerate(sequence):
                flags = 0
                if i == len(sequence) - 1:
                    flags |= LSystemPlotNode.FLAG_ENDING
                if func == 'RECOGNITION' and i < len(sequence) * 0.8:
                    flags |= LSystemPlotNode.FLAG_TWIST

                node = LSystemPlotNode(
                    id=node_id,
                    function=func,
                    parent_id=max(0, node_id - 1),
                    flags=flags,
                    next_id=node_id + 1 if i < len(sequence) - 1 else 0
                )
                self.nodes.append(node)
                node_id += 1

        return self.nodes

    def to_bytes(self) -> bytes:
        """Export all nodes as Z80-ready bytes"""
        if not self.nodes:
            self.generate()

        # Header: node_count (1 byte) + seed (2 bytes)
        header = struct.pack('<BH', len(self.nodes), self.seed & 0xFFFF)

        # Node data
        node_data = b''.join(node.to_bytes() for node in self.nodes)

        return header + node_data

    def to_asm(self) -> str:
        """Export as Z80 assembly data"""
        if not self.nodes:
            self.generate()

        lines = [
            "; L-System Generated Plot",
            f"; Seed: {self.seed}",
            f"; Genre: {self.genre or 'default'}",
            f"; Nodes: {len(self.nodes)}",
            "",
            "PLOT_DATA:",
            f"    db {len(self.nodes)}      ; node count",
            f"    dw {self.seed & 0xFFFF}   ; seed",
            "",
        ]

        for node in self.nodes:
            func_idx = list(PROPP_ALPHABET.values()).index(node.function) if node.function in PROPP_ALPHABET.values() else 0
            lines.append(f"    ; Node {node.id}: {node.function}")
            lines.append(f"    db {node.id}, {func_idx}, {node.parent_id}, {node.flags}, {node.next_id}")

        return '\n'.join(lines)

    def to_dict(self) -> Dict:
        """Export as dictionary (for JSON)"""
        if not self.nodes:
            self.generate()

        expanded = self.expander.expand()
        info = self.expander.get_structure_info(expanded)

        return {
            'seed': self.seed,
            'genre': self.genre,
            'expansion': expanded,
            'info': info,
            'nodes': [
                {
                    'id': n.id,
                    'function': n.function,
                    'parent_id': n.parent_id,
                    'flags': n.flags,
                    'next_id': n.next_id,
                    'is_ending': bool(n.flags & LSystemPlotNode.FLAG_ENDING),
                    'is_twist': bool(n.flags & LSystemPlotNode.FLAG_TWIST),
                }
                for n in self.nodes
            ],
            'byte_size': len(self.to_bytes()),
        }


# =============================================================================
# DEMO / TEST
# =============================================================================

def demo():
    """Demonstrate L-system plot generation"""
    print("=" * 60)
    print("L-SYSTEM PLOT GENERATOR DEMO")
    print("=" * 60)
    print()

    # Test different seeds and genres
    tests = [
        (12345, 'fantasy'),
        (12345, 'mystery'),
        (12345, 'dark_fantasy'),
        (99999, 'solarpunk'),
        (42, 'isekai'),
    ]

    for seed, genre in tests:
        print(f"Seed: {seed}, Genre: {genre}")
        print("-" * 40)

        gen = LSystemPlotGenerator(seed=seed, genre=genre)
        nodes = gen.generate()

        expanded = gen.expander.expand()
        info = gen.expander.get_structure_info(expanded)

        print(f"  Expansion: {expanded[:50]}{'...' if len(expanded) > 50 else ''}")
        print(f"  Nodes: {len(nodes)}")
        print(f"  Acts: {info['acts']}")
        print(f"  Branches: {info['branches']}")
        print(f"  Has twist: {info['has_twist']}")
        print(f"  Byte size: {len(gen.to_bytes())} bytes")
        print()

        # Show first few nodes
        print("  First 5 nodes:")
        for node in nodes[:5]:
            flags_str = []
            if node.flags & LSystemPlotNode.FLAG_ENDING:
                flags_str.append('END')
            if node.flags & LSystemPlotNode.FLAG_TWIST:
                flags_str.append('TWIST')
            print(f"    [{node.id}] {node.function} {' '.join(flags_str)}")
        print()

    # Show Z80 assembly output
    print("=" * 60)
    print("Z80 ASSEMBLY OUTPUT (seed=42, isekai)")
    print("=" * 60)
    gen = LSystemPlotGenerator(seed=42, genre='isekai')
    gen.generate()
    print(gen.to_asm())


if __name__ == '__main__':
    demo()
