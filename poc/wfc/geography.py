"""
Geography Generator using Bitwise WFC

16 tile types with Z80-friendly constraint masks.
Designed for non-linear reachability (multiple valid paths allowed).
"""

from dataclasses import dataclass, field
from typing import List, Set, Tuple, Dict, Optional
from enum import IntEnum
import random

from .core import (
    BitwiseWFC, WFCCell, popcount,
    find_connected_components, check_reachability, find_path
)


class TileType(IntEnum):
    """16 geography tile types"""
    FOREST = 0
    CLEARING = 1
    RIVER = 2
    ROAD = 3
    MOUNTAIN = 4
    CAVE = 5
    VILLAGE = 6
    CASTLE = 7
    SWAMP = 8
    RUINS = 9
    TOWER = 10
    LAKE = 11
    BRIDGE = 12
    TAVERN = 13
    TEMPLE = 14
    DUNGEON = 15


# Tile display characters (ASCII visualization)
TILE_CHARS = {
    TileType.FOREST: 'T',    # Trees
    TileType.CLEARING: '.',  # Open
    TileType.RIVER: '~',     # Water
    TileType.ROAD: '=',      # Path
    TileType.MOUNTAIN: '^',  # Peaks
    TileType.CAVE: 'O',      # Opening
    TileType.VILLAGE: 'V',   # Village
    TileType.CASTLE: 'C',    # Castle
    TileType.SWAMP: '%',     # Swamp
    TileType.RUINS: 'R',     # Ruins
    TileType.TOWER: 'I',     # Tower
    TileType.LAKE: 'L',      # Lake
    TileType.BRIDGE: '#',    # Bridge
    TileType.TAVERN: 't',    # Tavern
    TileType.TEMPLE: '+',    # Temple
    TileType.DUNGEON: 'D',   # Dungeon
}


# Passable tiles for reachability (hero can walk through)
PASSABLE_TILES = {
    TileType.FOREST,
    TileType.CLEARING,
    TileType.ROAD,
    TileType.CAVE,
    TileType.VILLAGE,
    TileType.CASTLE,
    TileType.RUINS,
    TileType.TOWER,
    TileType.BRIDGE,
    TileType.TAVERN,
    TileType.TEMPLE,
    TileType.DUNGEON,
}

# Impassable tiles (water, mountains, swamp)
IMPASSABLE_TILES = {
    TileType.RIVER,
    TileType.MOUNTAIN,
    TileType.SWAMP,
    TileType.LAKE,
}


def create_geography_constraints() -> Dict[str, Dict[int, int]]:
    """
    Create constraint masks for 16 tile types.

    Design principles:
    - Natural transitions (forest->clearing, road->village)
    - Logical barriers (mountains block, rivers need bridges)
    - Interesting geography (ruins in remote areas)
    """

    # Start with empty constraints
    n = {}  # North neighbors
    e = {}  # East neighbors
    s = {}  # South neighbors
    w = {}  # West neighbors

    # Initialize all tiles with no neighbors
    for t in TileType:
        n[t] = 0
        e[t] = 0
        s[t] = 0
        w[t] = 0

    def symmetric(a: TileType, b: TileType):
        """a and b can be neighbors in any direction"""
        mask_a = 1 << a
        mask_b = 1 << b
        for d in [n, e, s, w]:
            d[a] |= mask_b
            d[b] |= mask_a

    def self_neighbor(t: TileType):
        """t can neighbor itself"""
        symmetric(t, t)

    # === NATURAL TERRAIN ===

    # Forest: neighbors forest, clearing, road, mountain edge, ruins
    self_neighbor(TileType.FOREST)
    symmetric(TileType.FOREST, TileType.CLEARING)
    symmetric(TileType.FOREST, TileType.ROAD)
    symmetric(TileType.FOREST, TileType.MOUNTAIN)
    symmetric(TileType.FOREST, TileType.RUINS)
    symmetric(TileType.FOREST, TileType.SWAMP)

    # Clearing: open area, neighbors most things
    self_neighbor(TileType.CLEARING)
    symmetric(TileType.CLEARING, TileType.ROAD)
    symmetric(TileType.CLEARING, TileType.VILLAGE)
    symmetric(TileType.CLEARING, TileType.RUINS)
    symmetric(TileType.CLEARING, TileType.RIVER)
    symmetric(TileType.CLEARING, TileType.LAKE)

    # River: flows, needs bridges to cross
    self_neighbor(TileType.RIVER)
    symmetric(TileType.RIVER, TileType.BRIDGE)
    symmetric(TileType.RIVER, TileType.LAKE)
    symmetric(TileType.RIVER, TileType.SWAMP)
    symmetric(TileType.RIVER, TileType.FOREST)

    # Road: connects civilized areas
    self_neighbor(TileType.ROAD)
    symmetric(TileType.ROAD, TileType.VILLAGE)
    symmetric(TileType.ROAD, TileType.CASTLE)
    symmetric(TileType.ROAD, TileType.BRIDGE)
    symmetric(TileType.ROAD, TileType.TAVERN)
    symmetric(TileType.ROAD, TileType.TEMPLE)
    symmetric(TileType.ROAD, TileType.TOWER)

    # Mountain: natural barrier
    self_neighbor(TileType.MOUNTAIN)
    symmetric(TileType.MOUNTAIN, TileType.CAVE)
    symmetric(TileType.MOUNTAIN, TileType.TEMPLE)  # Mountain temple

    # Cave: in mountains or forest
    symmetric(TileType.CAVE, TileType.FOREST)
    symmetric(TileType.CAVE, TileType.DUNGEON)

    # === CIVILIZED AREAS ===

    # Village: connected by roads
    symmetric(TileType.VILLAGE, TileType.TAVERN)
    symmetric(TileType.VILLAGE, TileType.CLEARING)

    # Castle: at end of roads, near tower
    symmetric(TileType.CASTLE, TileType.TOWER)
    symmetric(TileType.CASTLE, TileType.CLEARING)

    # Tower: guards areas
    symmetric(TileType.TOWER, TileType.CLEARING)
    symmetric(TileType.TOWER, TileType.MOUNTAIN)

    # Tavern: on roads, near villages
    symmetric(TileType.TAVERN, TileType.CLEARING)

    # Temple: remote, sacred
    symmetric(TileType.TEMPLE, TileType.CLEARING)
    symmetric(TileType.TEMPLE, TileType.RUINS)

    # === SPECIAL AREAS ===

    # Swamp: dangerous, borders forest
    self_neighbor(TileType.SWAMP)
    symmetric(TileType.SWAMP, TileType.RUINS)  # Ancient ruins in swamp

    # Ruins: anywhere remote
    self_neighbor(TileType.RUINS)
    symmetric(TileType.RUINS, TileType.DUNGEON)

    # Lake: water body
    self_neighbor(TileType.LAKE)

    # Bridge: over water, connects roads
    symmetric(TileType.BRIDGE, TileType.CLEARING)

    # Dungeon: underground
    symmetric(TileType.DUNGEON, TileType.RUINS)
    symmetric(TileType.DUNGEON, TileType.MOUNTAIN)

    return {'N': n, 'E': e, 'S': s, 'W': w}


class GeographyGenerator:
    """
    Geography generator using Bitwise WFC.

    Creates connected worlds with guaranteed reachability
    between key locations (non-linear paths allowed).
    """

    def __init__(self, width: int = 16, height: int = 16, seed: int = None):
        self.width = width
        self.height = height
        self.seed = seed

        if seed is not None:
            random.seed(seed)

        # Create WFC engine
        self.wfc = BitwiseWFC(
            width=width,
            height=height,
            num_tiles=16,
            mask_bits=16
        )

        # Load constraints
        constraints = create_geography_constraints()
        self.wfc.constraints_n = constraints['N']
        self.wfc.constraints_e = constraints['E']
        self.wfc.constraints_s = constraints['S']
        self.wfc.constraints_w = constraints['W']

        # Key locations (set after generation)
        self.key_locations: Dict[str, Tuple[int, int]] = {}

    def reset(self, seed: int = None):
        """Reset generator with new seed"""
        if seed is not None:
            self.seed = seed
            random.seed(seed)
        self.wfc.reset()
        self.key_locations = {}

    def place_anchor(self, x: int, y: int, tile_type: TileType, name: str = None):
        """
        Force a specific tile at location (anchor point).
        Used for placing key story locations.
        """
        if not self.wfc.collapse(x, y, tile_type):
            return False
        if name:
            self.key_locations[name] = (x, y)
        return True

    def generate(self, max_attempts: int = 10) -> bool:
        """
        Generate geography with retries.
        Returns True if successful with connected key locations.
        """
        for attempt in range(max_attempts):
            self.wfc.reset()

            # Re-place anchors if any
            anchors_copy = dict(self.key_locations)
            self.key_locations = {}

            all_placed = True
            for name, (x, y) in anchors_copy.items():
                cell = self.wfc.grid[y][x]
                # Find a valid tile for this anchor
                # (simplified: just pick lowest bit from possibilities)
                if cell.possibilities == 0:
                    all_placed = False
                    break
                tile = cell.possibilities & -cell.possibilities  # isolate lowest bit
                tile_id = (tile - 1).bit_length() - 1 if tile > 1 else 0
                if not self.place_anchor(x, y, tile_id, name):
                    all_placed = False
                    break

            if not all_placed:
                continue

            # Run WFC
            if self.wfc.generate():
                # Check reachability between key locations
                if self._check_key_reachability():
                    return True

            self.wfc.backtracks += 1

        return False

    def _check_key_reachability(self) -> bool:
        """
        Check that all key locations are mutually reachable.
        Non-linear: any path is valid, not just direct.
        """
        if len(self.key_locations) < 2:
            return True

        grid = self.wfc.to_tile_grid()
        passable = {t.value for t in PASSABLE_TILES}

        # Get all key location positions
        positions = list(self.key_locations.values())
        start = positions[0]

        # Check if all others are reachable from start
        all_reachable, unreachable = check_reachability(
            grid, start, positions[1:], passable
        )

        return all_reachable

    def get_connected_regions(self) -> List[Set[Tuple[int, int]]]:
        """Get all connected passable regions"""
        grid = self.wfc.to_tile_grid()
        passable = {t.value for t in PASSABLE_TILES}
        return find_connected_components(grid, passable)

    def find_path_between(self, start_name: str, goal_name: str) -> Optional[List[Tuple[int, int]]]:
        """Find path between two named locations"""
        if start_name not in self.key_locations or goal_name not in self.key_locations:
            return None

        grid = self.wfc.to_tile_grid()
        passable = {t.value for t in PASSABLE_TILES}

        return find_path(
            grid,
            self.key_locations[start_name],
            self.key_locations[goal_name],
            passable
        )

    def visualize(self) -> str:
        """Create ASCII map with key locations marked"""
        base = self.wfc.visualize({t.value: c for t, c in TILE_CHARS.items()})

        # Mark key locations
        lines = base.split('\n')
        for name, (x, y) in self.key_locations.items():
            if 0 <= y < len(lines) and 0 <= x < len(lines[y]):
                line = list(lines[y])
                line[x] = '@'  # Mark key location
                lines[y] = ''.join(line)

        return '\n'.join(lines)

    def get_tile_stats(self) -> Dict[TileType, int]:
        """Count tiles of each type"""
        stats = {t: 0 for t in TileType}
        for row in self.wfc.grid:
            for cell in row:
                if cell.is_collapsed:
                    stats[TileType(cell.collapsed_to)] += 1
        return stats


# =============================================================================
# Demo / Test
# =============================================================================

def demo():
    """Demo geography generation with reachability test"""
    print("=== Geography Generator Demo ===\n")

    # Create generator
    gen = GeographyGenerator(width=20, height=12, seed=42)

    # Place key story locations
    gen.place_anchor(2, 2, TileType.VILLAGE, "home")
    gen.place_anchor(17, 9, TileType.CASTLE, "castle")
    gen.place_anchor(10, 5, TileType.CAVE, "dragon_lair")

    # Generate
    print("Generating world...")
    success = gen.generate(max_attempts=20)

    if success:
        print(f"Success! (iterations: {gen.wfc.iterations}, backtracks: {gen.wfc.backtracks})\n")
        print("Map (@ = key location):")
        print(gen.visualize())
        print()

        # Show key locations
        print("Key locations:")
        for name, pos in gen.key_locations.items():
            print(f"  {name}: {pos}")
        print()

        # Test reachability
        print("Path finding:")
        path = gen.find_path_between("home", "dragon_lair")
        if path:
            print(f"  home -> dragon_lair: {len(path)} steps")
        else:
            print("  home -> dragon_lair: NO PATH!")

        path = gen.find_path_between("dragon_lair", "castle")
        if path:
            print(f"  dragon_lair -> castle: {len(path)} steps")
        else:
            print("  dragon_lair -> castle: NO PATH!")
        print()

        # Connected regions
        regions = gen.get_connected_regions()
        print(f"Connected passable regions: {len(regions)}")
        for i, region in enumerate(regions):
            print(f"  Region {i+1}: {len(region)} cells")
        print()

        # Tile stats
        print("Tile distribution:")
        stats = gen.get_tile_stats()
        for tile, count in sorted(stats.items(), key=lambda x: -x[1]):
            if count > 0:
                print(f"  {tile.name}: {count}")
    else:
        print("Generation failed!")
        print(f"Backtracks: {gen.wfc.backtracks}")


if __name__ == "__main__":
    demo()
