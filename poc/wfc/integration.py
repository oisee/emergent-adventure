"""
Plot-Geography Integration

Connects plot structure to physical world:
1. Generate plot (backward from finale)
2. Extract location requirements
3. Generate geography with plot anchors
4. Verify reachability (non-linear paths OK)
5. Full completability check
"""

from dataclasses import dataclass, field
from typing import List, Set, Tuple, Dict, Optional
import random

from .core import check_reachability, find_path
from .geography import (
    GeographyGenerator, TileType, TILE_CHARS, PASSABLE_TILES
)
from .plot import (
    BackwardPlotGenerator, PlotGraph, PlotNode,
    ProppFunction, PROPP_NAMES, Requirement, Provides
)


# Map location hints to suitable tile types
LOCATION_TO_TILES = {
    "village": [TileType.VILLAGE],
    "home": [TileType.VILLAGE, TileType.TAVERN],
    "road": [TileType.ROAD, TileType.BRIDGE],
    "cave": [TileType.CAVE],
    "dungeon": [TileType.DUNGEON, TileType.CAVE],
    "tower": [TileType.TOWER],
    "castle": [TileType.CASTLE],
    "ruins": [TileType.RUINS],
    "temple": [TileType.TEMPLE],
    "tavern": [TileType.TAVERN],
    "forest": [TileType.FOREST],
    "mountain": [TileType.MOUNTAIN, TileType.CAVE],
    "clearing": [TileType.CLEARING],
}


@dataclass
class WorldState:
    """Complete generated world state"""
    # Generation results
    plot: PlotGraph = None
    geography: GeographyGenerator = None

    # Mapping plot -> geography
    node_locations: Dict[int, Tuple[int, int]] = field(default_factory=dict)

    # Statistics
    plot_seed: int = 0
    geo_seed: int = 0
    attempts: int = 0

    def is_valid(self) -> bool:
        return self.plot is not None and self.geography is not None


class WorldGenerator:
    """
    Generates complete game world:
    - Plot structure (backward from finale)
    - Geography (WFC with plot anchors)
    - Verified completability
    """

    def __init__(self, width: int = 16, height: int = 12, seed: int = None):
        self.width = width
        self.height = height
        self.base_seed = seed if seed is not None else random.randint(0, 999999)

        self.plot_gen = BackwardPlotGenerator()
        self.geo_gen = GeographyGenerator(width, height)

        self.world = WorldState()

    def generate(self, max_plot_attempts: int = 10,
                 max_geo_attempts: int = 20) -> bool:
        """
        Generate complete world.

        Returns True if successful.
        """
        self.world = WorldState()

        # Phase 1: Generate plot
        for plot_attempt in range(max_plot_attempts):
            plot_seed = self.base_seed + plot_attempt * 1000
            self.plot_gen.reset(plot_seed)

            if self.plot_gen.generate():
                self.world.plot = self.plot_gen.graph
                self.world.plot_seed = plot_seed
                break

        if self.world.plot is None:
            return False

        # Phase 2: Extract location requirements
        required_locations = self._extract_locations()

        # Phase 3: Generate geography with anchors
        for geo_attempt in range(max_geo_attempts):
            geo_seed = self.base_seed + geo_attempt
            self.geo_gen.reset(geo_seed)

            # Place anchors for plot locations
            if self._place_plot_anchors(required_locations):
                # Run WFC
                if self.geo_gen.generate():
                    # Verify reachability
                    if self._verify_reachability():
                        self.world.geography = self.geo_gen
                        self.world.geo_seed = geo_seed
                        self.world.attempts = geo_attempt + 1
                        return True

        return False

    def _extract_locations(self) -> Dict[int, str]:
        """Extract location hints from plot nodes"""
        locations = {}
        for node in self.world.plot.nodes:
            if node.location_hint:
                locations[node.id] = node.location_hint
        return locations

    def _place_plot_anchors(self, required_locations: Dict[int, str]) -> bool:
        """
        Place plot location anchors on geography.

        Strategy: Spread anchors across the map with some randomization.
        """
        num_locations = len(required_locations)
        if num_locations == 0:
            return True

        # Create placement zones (divide map into regions)
        # For simplicity, spread locations across the map
        positions = self._generate_spread_positions(num_locations)

        # Assign positions to nodes
        location_list = list(required_locations.items())
        random.shuffle(location_list)

        self.world.node_locations = {}

        for i, (node_id, loc_hint) in enumerate(location_list):
            if i >= len(positions):
                break

            x, y = positions[i]

            # Choose appropriate tile type
            tile_types = LOCATION_TO_TILES.get(loc_hint, [TileType.CLEARING])
            tile_type = random.choice(tile_types)

            # Place anchor
            name = f"plot_{node_id}"
            if not self.geo_gen.place_anchor(x, y, tile_type, name):
                # Try adjacent positions if anchor fails
                placed = False
                for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        if self.geo_gen.place_anchor(nx, ny, tile_type, name):
                            x, y = nx, ny
                            placed = True
                            break
                if not placed:
                    return False

            self.world.node_locations[node_id] = (x, y)

        return True

    def _generate_spread_positions(self, count: int) -> List[Tuple[int, int]]:
        """Generate spread-out positions across map"""
        positions = []

        # Use grid-based spreading with jitter
        cols = max(2, int(count ** 0.5) + 1)
        rows = (count + cols - 1) // cols

        cell_w = self.width // cols
        cell_h = self.height // rows

        for i in range(count):
            row = i // cols
            col = i % cols

            # Center of cell with random jitter
            base_x = col * cell_w + cell_w // 2
            base_y = row * cell_h + cell_h // 2

            # Add jitter
            jitter_x = random.randint(-cell_w // 3, cell_w // 3)
            jitter_y = random.randint(-cell_h // 3, cell_h // 3)

            x = max(1, min(self.width - 2, base_x + jitter_x))
            y = max(1, min(self.height - 2, base_y + jitter_y))

            positions.append((x, y))

        return positions

    def _verify_reachability(self) -> bool:
        """
        Verify all plot locations are mutually reachable.

        Non-linear: any path is valid, order doesn't matter.
        """
        if len(self.world.node_locations) < 2:
            return True

        grid = self.geo_gen.wfc.to_tile_grid()
        passable = {t.value for t in PASSABLE_TILES}

        positions = list(self.world.node_locations.values())
        start = positions[0]

        all_reachable, unreachable = check_reachability(
            grid, start, positions[1:], passable
        )

        return all_reachable

    def verify_completability(self) -> Tuple[bool, str]:
        """
        Full completability check:
        1. Plot is valid (no cycles, requirements satisfied)
        2. Geography is connected
        3. All plot locations reachable
        """
        if not self.world.is_valid():
            return False, "World not generated"

        # Check plot completability
        plot_valid, plot_msg = self.plot_gen.verify_completability()
        if not plot_valid:
            return False, f"Plot: {plot_msg}"

        # Check geography connectivity
        regions = self.geo_gen.get_connected_regions()
        if len(regions) == 0:
            return False, "No passable regions"

        # Find which region contains plot locations
        main_region = None
        for region in regions:
            positions_in_region = sum(
                1 for pos in self.world.node_locations.values()
                if pos in region
            )
            if positions_in_region > 0:
                if main_region is None or len(region) > len(main_region):
                    main_region = region

        # Check all plot locations are in same region
        for node_id, pos in self.world.node_locations.items():
            if pos not in main_region:
                node = self.world.plot.nodes[node_id]
                return False, f"Plot location '{node.location_hint}' unreachable"

        return True, "World is completable"

    def get_summary(self) -> str:
        """Get human-readable world summary"""
        lines = ["=" * 50, "GENERATED WORLD", "=" * 50, ""]

        if not self.world.is_valid():
            return "World generation failed"

        # Plot summary
        lines.append("PLOT STRUCTURE:")
        lines.append("-" * 30)
        order = self.world.plot.topological_sort()
        for i, node_id in enumerate(order):
            node = self.world.plot.nodes[node_id]
            pos = self.world.node_locations.get(node_id, "?")
            lines.append(f"{i+1}. [{PROPP_NAMES[node.function]}] @ {pos}")
            lines.append(f"   {node.description}")
        lines.append("")

        # Geography
        lines.append("GEOGRAPHY:")
        lines.append("-" * 30)
        lines.append(self.geo_gen.visualize())
        lines.append("")

        # Key locations
        lines.append("PLOT LOCATIONS:")
        for node_id, pos in self.world.node_locations.items():
            node = self.world.plot.nodes[node_id]
            lines.append(f"  {PROPP_NAMES[node.function]}: {pos} ({node.location_hint})")
        lines.append("")

        # Stats
        lines.append(f"Seeds: plot={self.world.plot_seed}, geo={self.world.geo_seed}")
        lines.append(f"Generation attempts: {self.world.attempts}")

        # Verify
        valid, msg = self.verify_completability()
        lines.append(f"Completability: {msg}")

        return '\n'.join(lines)

    def get_playable_order(self) -> List[Tuple[int, PlotNode, Tuple[int, int]]]:
        """
        Get plot nodes in a valid play order with their locations.

        Returns list of (node_id, node, position).
        """
        if not self.world.is_valid():
            return []

        order = self.world.plot.topological_sort()
        result = []

        for node_id in order:
            node = self.world.plot.nodes[node_id]
            pos = self.world.node_locations.get(node_id)
            result.append((node_id, node, pos))

        return result


# =============================================================================
# Demo
# =============================================================================

def demo():
    """Demo complete world generation"""
    print("=== World Generator Demo ===\n")

    gen = WorldGenerator(width=20, height=12, seed=42)

    print("Generating world...")
    success = gen.generate()

    if success:
        print("SUCCESS!\n")
        print(gen.get_summary())

        # Show paths between plot points
        print("\nPATH LENGTHS BETWEEN PLOT POINTS:")
        playable = gen.get_playable_order()
        for i in range(len(playable) - 1):
            from_id, from_node, from_pos = playable[i]
            to_id, to_node, to_pos = playable[i + 1]

            if from_pos and to_pos:
                path = gen.geo_gen.find_path_between(
                    f"plot_{from_id}", f"plot_{to_id}"
                )
                if path:
                    print(f"  {PROPP_NAMES[from_node.function]} -> {PROPP_NAMES[to_node.function]}: {len(path)} steps")
                else:
                    print(f"  {PROPP_NAMES[from_node.function]} -> {PROPP_NAMES[to_node.function]}: NO PATH")
    else:
        print("World generation FAILED")


if __name__ == "__main__":
    demo()
