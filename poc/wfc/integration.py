"""
Plot-Geography Integration

Connects plot structure to physical world:
1. Generate plot (backward from finale, with optional twists/false endings)
2. Extract location requirements
3. Generate geography with plot anchors
4. Verify reachability (non-linear paths OK)
5. Full completability check
"""

from dataclasses import dataclass, field
from typing import List, Set, Tuple, Dict, Optional
from enum import Enum, auto
import random

from .core import check_reachability, find_path
from .geography import (
    GeographyGenerator, TileType, TILE_CHARS, PASSABLE_TILES
)
from .plot import (
    BackwardPlotGenerator, PlotGraph, PlotNode,
    ProppFunction, PROPP_NAMES, Requirement, Provides
)
from .plot_advanced import (
    AdvancedPlotGenerator, MultiPlot, PlotNode as AdvPlotNode,
    ProppFunc, TwistType, GENRES, Genre, mix_genres,
    PROPP_NAMES as ADV_PROPP_NAMES
)
from .plot_fractal import (
    FractalPlotGenerator, FractalPlot, FractalPlotNode,
    NarrativeLevel, EndingMode, ENDING_MODES, LEVEL_NAMES
)
from .npc.integration.plot_roles import PlotRoleIntegrator
from .npc.archetypes.fractal_roles import ActantRole, FractalRoleSystem
from .weather import (
    WeatherState, WeatherGenerator, WeatherType, Season, ClimateZone,
    TimeOfDay, AtmosphericPhenomenon, create_weather_for_genre,
    WEATHER_INFO, SEASON_INFO, TIME_OF_DAY_INFO, CLIMATE_INFO
)


class PlotType(Enum):
    """Type of plot to generate"""
    SIMPLE = auto()          # Basic linear plot
    BRANCHING = auto()       # Multiple branches
    WITH_TWIST = auto()      # Contains plot twist
    WITH_FALSE_ENDING = auto()  # Has false ending(s)
    EPIC = auto()            # Full 3-act with twist + false ending
    FRACTAL = auto()         # Nested fractal plot with sub-plots


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
    plot: PlotGraph = None           # Simple plot (legacy)
    advanced_plot: MultiPlot = None  # Advanced plot with twists
    fractal_plot: FractalPlot = None # Fractal nested plot
    geography: GeographyGenerator = None

    # Mapping plot -> geography
    node_locations: Dict[int, Tuple[int, int]] = field(default_factory=dict)

    # Plot metadata
    plot_type: PlotType = PlotType.SIMPLE
    genre: Genre = None
    has_twist: bool = False
    has_false_ending: bool = False
    twist_type: TwistType = None

    # Fractal plot metadata
    narrative_level: NarrativeLevel = NarrativeLevel.MACRO
    ending_mode: EndingMode = None
    fractal_depth: int = 2

    # NPC/Cast system
    cast_system: PlotRoleIntegrator = None

    # Weather/Atmosphere
    weather: WeatherState = None
    weather_generator: WeatherGenerator = None

    # Statistics
    plot_seed: int = 0
    geo_seed: int = 0
    attempts: int = 0

    def is_valid(self) -> bool:
        has_plot = (self.plot is not None or
                    self.advanced_plot is not None or
                    self.fractal_plot is not None)
        return has_plot and self.geography is not None

    def get_plot_nodes(self) -> List:
        """Get plot nodes from simple, advanced, or fractal plot"""
        if self.fractal_plot:
            # Return flattened nodes from fractal plot
            return self._flatten_fractal_nodes()
        elif self.advanced_plot:
            return self.advanced_plot.nodes
        elif self.plot:
            return self.plot.nodes
        return []

    def _flatten_fractal_nodes(self) -> List:
        """Flatten fractal plot nodes for compatibility"""
        if not self.fractal_plot:
            return []
        result = []
        for node in self.fractal_plot.nodes:
            result.extend(node.get_all_nodes_flat())
        return result

    def get_plot_edges(self) -> Dict:
        """Get plot edges"""
        if self.fractal_plot:
            return self.fractal_plot.edges
        elif self.advanced_plot:
            return self.advanced_plot.edges
        elif self.plot:
            return self.plot.edges
        return {}

    def to_dict(self) -> Dict:
        """Export complete world state to dictionary"""
        data = {
            "metadata": {
                "plot_type": self.plot_type.name if self.plot_type else "UNKNOWN",
                "plot_seed": self.plot_seed,
                "geo_seed": self.geo_seed,
                "attempts": self.attempts,
            }
        }

        # Genre
        if self.genre:
            data["genre"] = {
                "name": self.genre.name,
                "description": self.genre.description,
                "mood": self.genre.mood,
                "palette": self.genre.palette,
                "vocab": self.genre.vocab,
            }

        # Plot
        if self.fractal_plot:
            data["plot"] = self.fractal_plot.to_dict()
            data["metadata"]["narrative_level"] = self.narrative_level.name
            data["metadata"]["fractal_depth"] = self.fractal_depth
            if self.ending_mode:
                data["metadata"]["ending_mode"] = self.ending_mode.name

        # Cast
        if self.cast_system:
            cast_data = {
                "npcs": {},
                "role_transitions": []
            }
            for npc_name, fractal_role in self.cast_system.role_system.npc_roles.items():
                cast_data["npcs"][npc_name] = {
                    "macro_role": fractal_role.macro_role.name if fractal_role.macro_role else None,
                    "meso_role": fractal_role.meso_role.name if fractal_role.meso_role else None,
                    "micro_role": fractal_role.micro_role.name if fractal_role.micro_role else None,
                    "transitions": [
                        {
                            "from": t.from_role.name,
                            "to": t.to_role.name,
                            "trigger": t.trigger,
                            "level": t.at_level.name if hasattr(t, 'at_level') and t.at_level else None
                        }
                        for t in fractal_role.transitions
                    ]
                }
            data["cast"] = cast_data

        # Weather
        if self.weather:
            data["weather"] = self.weather.to_dict()

        # Node locations
        if self.node_locations:
            data["node_locations"] = {
                str(k): list(v) for k, v in self.node_locations.items()
            }

        return data

    def to_json(self, indent: int = 2) -> str:
        """Export complete world state to JSON"""
        import json
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


class WorldGenerator:
    """
    Generates complete game world:
    - Plot structure (backward from finale, with twists/false endings)
    - Geography (WFC with plot anchors)
    - Verified completability
    """

    def __init__(self, width: int = 16, height: int = 12, seed: int = None):
        self.width = width
        self.height = height
        self.base_seed = seed if seed is not None else random.randint(0, 999999)

        # Legacy simple plot generator
        self.plot_gen = BackwardPlotGenerator()
        # Advanced plot generator
        self.adv_plot_gen = AdvancedPlotGenerator()
        # Fractal plot generator
        self.fractal_plot_gen: Optional[FractalPlotGenerator] = None
        self.geo_gen = GeographyGenerator(width, height)

        self.world = WorldState()

    def generate(self, max_plot_attempts: int = 10,
                 max_geo_attempts: int = 20,
                 plot_type: PlotType = PlotType.SIMPLE,
                 genre = None,  # str or Genre object
                 twist_type: TwistType = None,
                 # Fractal plot options
                 narrative_level: NarrativeLevel = NarrativeLevel.MACRO,
                 fractal_depth: int = 2,
                 ending_mode: EndingMode = None,
                 branching: bool = True,
                 level_complexity: Dict[NarrativeLevel, Tuple[int, int]] = None,
                 add_twist: bool = False,
                 add_false_ending: bool = False) -> bool:
        """
        Generate complete world.

        Args:
            max_plot_attempts: Max attempts for plot generation
            max_geo_attempts: Max attempts for geography generation
            plot_type: Type of plot to generate (SIMPLE, BRANCHING, WITH_TWIST, FRACTAL, etc.)
            genre: Genre name string or Genre object (for mixed genres)
            twist_type: Specific twist type (or None for random)
            narrative_level: For FRACTAL - starting level (MACRO, MESO, etc.)
            fractal_depth: For FRACTAL - decomposition depth
            ending_mode: For FRACTAL - emotional ending mode
            branching: For FRACTAL - allow branching paths
            level_complexity: For FRACTAL - override node counts per level
                              Dict mapping NarrativeLevel -> (min, max)
            add_twist: For FRACTAL - add plot twist
            add_false_ending: For FRACTAL - add false ending

        Returns True if successful.
        """
        self.world = WorldState()
        self.world.plot_type = plot_type

        # Set genre if specified - handle both string names and Genre objects
        if genre:
            if isinstance(genre, str) and genre in GENRES:
                self.world.genre = GENRES[genre]
            elif isinstance(genre, Genre):
                self.world.genre = genre

        # Phase 1: Generate plot based on type
        if plot_type == PlotType.SIMPLE:
            success = self._generate_simple_plot(max_plot_attempts)
        elif plot_type == PlotType.FRACTAL:
            success = self._generate_fractal_plot(
                max_plot_attempts, narrative_level, fractal_depth,
                ending_mode, branching, level_complexity,
                add_twist, add_false_ending
            )
        else:
            success = self._generate_advanced_plot(max_plot_attempts, plot_type, twist_type)

        if not success:
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

    def _generate_simple_plot(self, max_attempts: int) -> bool:
        """Generate simple linear plot using legacy generator"""
        for plot_attempt in range(max_attempts):
            plot_seed = self.base_seed + plot_attempt * 1000
            self.plot_gen.reset(plot_seed)

            if self.plot_gen.generate():
                self.world.plot = self.plot_gen.graph
                self.world.plot_seed = plot_seed
                return True
        return False

    def _generate_advanced_plot(self, max_attempts: int,
                                plot_type: PlotType,
                                twist_type: TwistType = None) -> bool:
        """Generate advanced plot with twists/false endings"""
        for plot_attempt in range(max_attempts):
            plot_seed = self.base_seed + plot_attempt * 1000
            self.adv_plot_gen.reset(plot_seed)

            # Set genre if available
            if self.world.genre:
                self.adv_plot_gen.genre = self.world.genre

            success = False

            if plot_type == PlotType.BRANCHING:
                success = self.adv_plot_gen.generate_branching(
                    main_length=6, num_branches=2, branch_length=3
                )

            elif plot_type == PlotType.WITH_TWIST:
                success = self.adv_plot_gen.generate_with_twist(
                    length=8, twist_type=twist_type
                )
                if success:
                    self.world.has_twist = True
                    self.world.twist_type = twist_type or self.adv_plot_gen.plot.twist_type

            elif plot_type == PlotType.WITH_FALSE_ENDING:
                success = self.adv_plot_gen.generate_with_false_ending(
                    length=10, num_false_endings=1
                )
                if success:
                    self.world.has_false_ending = True

            elif plot_type == PlotType.EPIC:
                success = self.adv_plot_gen.generate_epic(
                    acts=3, nodes_per_act=4, twists=1, false_endings=1
                )
                if success:
                    self.world.has_twist = True
                    self.world.has_false_ending = True
                    if self.adv_plot_gen.plot.twist_type:
                        self.world.twist_type = self.adv_plot_gen.plot.twist_type

            else:
                # Default to linear
                success = self.adv_plot_gen.generate_linear(length=6)

            if success:
                self.world.advanced_plot = self.adv_plot_gen.plot
                self.world.plot_seed = plot_seed
                return True

        return False

    def _generate_fractal_plot(self, max_attempts: int,
                               narrative_level: NarrativeLevel,
                               depth: int,
                               ending_mode: EndingMode,
                               branching: bool,
                               level_complexity: Dict[NarrativeLevel, Tuple[int, int]] = None,
                               add_twist: bool = False,
                               add_false_ending: bool = False) -> bool:
        """Generate fractal nested plot structure"""
        for plot_attempt in range(max_attempts):
            plot_seed = self.base_seed + plot_attempt * 1000

            # Create fractal generator
            genre = self.world.genre or GENRES.get('fantasy')
            self.fractal_plot_gen = FractalPlotGenerator(
                genre=genre,
                seed=plot_seed,
                branching_chance=0.4 if branching else 0.0,
                level_complexity=level_complexity
            )

            # Generate fractal plot
            success = self.fractal_plot_gen.generate(
                target_level=narrative_level,
                depth=depth,
                finale=ProppFunc.VICTORY,
                branching=branching,
                ending_mode=ending_mode,
                add_twist=add_twist,
                add_false_ending=add_false_ending
            )

            if success:
                self.world.fractal_plot = self.fractal_plot_gen.plot
                self.world.plot_seed = plot_seed
                self.world.narrative_level = narrative_level
                self.world.fractal_depth = depth
                self.world.ending_mode = self.fractal_plot_gen.plot.ending_mode

                # Generate cast and assign roles
                self._generate_cast()

                # Generate weather
                self._generate_weather()

                return True

        return False

    def _generate_cast(self):
        """Generate NPC cast and assign roles based on plot structure"""
        if not self.world.fractal_plot:
            return

        # Create cast system
        cast = PlotRoleIntegrator()

        # Generate archetype-based NPCs
        npc_archetypes = [
            ("Elder Sage", ActantRole.MENTOR),
            ("Dark Knight", ActantRole.OPPONENT),
            ("Loyal Companion", ActantRole.HELPER),
            ("Mysterious Stranger", ActantRole.TRICKSTER),
            ("Village Elder", ActantRole.SENDER),
            ("The Prisoner", ActantRole.RECEIVER),
            ("Gate Guardian", ActantRole.THRESHOLD_GUARDIAN),
            ("Shadow Lord", ActantRole.SHADOW),
        ]

        # Register NPCs
        for name, role in npc_archetypes:
            cast.register_npc(name, role)

        # Create roster for assignment
        npc_roster = {name: role for name, role in npc_archetypes}

        # Assign roles to plot
        cast.assign_plot_roles(self.world.fractal_plot, npc_roster=npc_roster)

        # Add some role transitions based on plot features
        if self.world.fractal_plot.nodes:
            # Check if there's a twist - add betrayal transition
            has_twist = any(
                n.twist_type and n.twist_type.value > 0
                for n in self._get_all_fractal_nodes()
            )
            if has_twist:
                cast.role_system.add_transition(
                    "Dark Knight",
                    from_role=ActantRole.HELPER,
                    to_role=ActantRole.SHADOW,
                    trigger="twist_revealed"
                )
                cast.role_system.add_transition(
                    "Mysterious Stranger",
                    from_role=ActantRole.TRICKSTER,
                    to_role=ActantRole.MENTOR,
                    trigger="true_identity"
                )

        self.world.cast_system = cast

    def _generate_weather(self):
        """Generate weather state based on genre and world settings"""
        # Determine latitude from genre mood (rough approximation)
        latitude = 45.0  # Default temperate

        if self.world.genre:
            mood = self.world.genre.mood
            # Dark genres -> higher latitudes (colder, harsher)
            # Tropical genres -> lower latitudes
            if mood == "dark":
                latitude = random.uniform(50, 65)
            elif mood == "hopeful":
                latitude = random.uniform(35, 50)
            elif mood == "epic":
                latitude = random.uniform(40, 55)

        # Create weather generator
        self.world.weather_generator = WeatherGenerator(
            seed=self.base_seed,
            latitude=latitude,
            season=None  # Random season
        )

        # Generate initial weather, optionally biased by genre
        genre_name = None
        if self.world.genre:
            # Try to match genre name to weather preferences
            for g_name in ['dark_fantasy', 'cozy', 'iyashikei', 'mystery',
                          'solarpunk', 'hopepunk', 'fantasy', 'luminous']:
                if g_name in self.world.genre.name.lower():
                    genre_name = g_name
                    break

        if genre_name:
            self.world.weather = create_weather_for_genre(
                genre_name,
                seed=self.base_seed,
                latitude=latitude
            )
        else:
            self.world.weather = self.world.weather_generator.generate_initial()

    def _get_all_fractal_nodes(self):
        """Get all nodes from fractal plot including nested ones"""
        nodes = []
        def collect(plot):
            for node in plot.nodes:
                nodes.append(node)
                if node.has_sub_plot():
                    collect(node.sub_plot)
        if self.world.fractal_plot:
            collect(self.world.fractal_plot)
        return nodes

    def _extract_locations(self) -> Dict[int, str]:
        """Extract location hints from plot nodes (works with both simple and advanced)"""
        locations = {}
        nodes = self.world.get_plot_nodes()
        for node in nodes:
            if hasattr(node, 'location_hint') and node.location_hint:
                locations[node.id] = node.location_hint
            elif hasattr(node, 'location') and node.location:
                locations[node.id] = node.location
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

        # Check plot completability (use appropriate generator)
        if self.world.fractal_plot:
            # Fractal plots are valid if they have nodes
            plot_valid = len(self.world.fractal_plot.nodes) > 0
            plot_msg = "OK" if plot_valid else "Empty fractal plot"
        elif self.world.advanced_plot:
            plot_valid, plot_msg = self.adv_plot_gen.verify_completability()
        else:
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

        if main_region is None:
            return True, "World is completable (no plot locations)"

        # Check all plot locations are in same region
        nodes = self.world.get_plot_nodes()
        node_map = {n.id: n for n in nodes}
        for node_id, pos in self.world.node_locations.items():
            if pos not in main_region:
                node = node_map.get(node_id)
                loc_hint = getattr(node, 'location_hint', None) or getattr(node, 'location', 'unknown')
                return False, f"Plot location '{loc_hint}' unreachable"

        return True, "World is completable"

    def get_summary(self) -> str:
        """Get human-readable world summary"""
        lines = ["=" * 50, "GENERATED WORLD", "=" * 50, ""]

        if not self.world.is_valid():
            return "World generation failed"

        # Plot type and genre info
        lines.append(f"Plot Type: {self.world.plot_type.name}")
        if self.world.genre:
            lines.append(f"Genre: {self.world.genre.name}")
        if self.world.has_twist:
            twist_name = self.world.twist_type.name if self.world.twist_type else "UNKNOWN"
            lines.append(f"Twist: {twist_name}")
        if self.world.has_false_ending:
            lines.append("Has False Ending: Yes")
        lines.append("")

        # Plot summary - handle simple, advanced, and fractal
        lines.append("PLOT STRUCTURE:")
        lines.append("-" * 30)

        # Handle fractal plot separately
        if self.world.fractal_plot:
            if self.fractal_plot_gen:
                lines.append(self.fractal_plot_gen.get_summary())
            else:
                lines.append(f"Fractal Plot: {self.world.fractal_plot.get_total_node_count()} nodes")
                lines.append(f"Max Depth: {self.world.fractal_plot.get_max_depth()}")
                if self.world.ending_mode:
                    ending_info = ENDING_MODES.get(self.world.ending_mode, {})
                    lines.append(f"Ending: {ending_info.get('name', '?')} ({ending_info.get('greek', '')})")
        else:
            nodes = self.world.get_plot_nodes()
            node_map = {n.id: n for n in nodes}

            # Get topological order
            if self.world.advanced_plot:
                order = self.world.advanced_plot.topological_sort()
                propp_names = ADV_PROPP_NAMES
            elif self.world.plot:
                order = self.world.plot.topological_sort()
                propp_names = PROPP_NAMES
            else:
                order = []
                propp_names = PROPP_NAMES

            for i, node_id in enumerate(order):
                node = node_map.get(node_id)
                if node is None:
                    continue
                pos = self.world.node_locations.get(node_id, "?")
                func_name = propp_names.get(node.function, str(node.function))
                lines.append(f"{i+1}. [{func_name}] @ {pos}")
                lines.append(f"   {node.description}")

                # Show twist/false ending markers
                if hasattr(node, 'is_twist') and node.is_twist:
                    lines.append(f"   ** TWIST POINT **")
                if hasattr(node, 'is_false_ending') and node.is_false_ending:
                    lines.append(f"   ** FALSE ENDING **")
        lines.append("")

        # Geography
        lines.append("GEOGRAPHY:")
        lines.append("-" * 30)
        lines.append(self.geo_gen.visualize())
        lines.append("")

        # Key locations
        lines.append("PLOT LOCATIONS:")
        if self.world.node_locations:
            all_nodes = self.world.get_plot_nodes()
            all_node_map = {n.id: n for n in all_nodes}
            for node_id, pos in self.world.node_locations.items():
                node = all_node_map.get(node_id)
                if node is None:
                    lines.append(f"  Node {node_id}: {pos}")
                else:
                    func_name = ADV_PROPP_NAMES.get(node.function, str(node.function))
                    loc_hint = getattr(node, 'location_hint', None) or getattr(node, 'location', 'unknown')
                    lines.append(f"  {func_name}: {pos} ({loc_hint})")
        lines.append("")

        # Stats
        lines.append(f"Seeds: plot={self.world.plot_seed}, geo={self.world.geo_seed}")
        lines.append(f"Generation attempts: {self.world.attempts}")

        # Verify
        valid, msg = self.verify_completability()
        lines.append(f"Completability: {msg}")

        return '\n'.join(lines)

    def get_playable_order(self) -> List[Tuple[int, object, Tuple[int, int]]]:
        """
        Get plot nodes in a valid play order with their locations.

        Returns list of (node_id, node, position).
        Works with both simple and advanced plots.
        """
        if not self.world.is_valid():
            return []

        # Get order from appropriate plot
        if self.world.advanced_plot:
            order = self.world.advanced_plot.topological_sort()
            nodes = self.world.advanced_plot.nodes
        else:
            order = self.world.plot.topological_sort()
            nodes = self.world.plot.nodes

        node_map = {n.id: n for n in nodes}
        result = []

        for node_id in order:
            node = node_map.get(node_id)
            if node:
                pos = self.world.node_locations.get(node_id)
                result.append((node_id, node, pos))

        return result

    def get_twist_nodes(self) -> List[Tuple[int, object]]:
        """Get nodes that are twist points"""
        if not self.world.advanced_plot:
            return []
        return [(n.id, n) for n in self.world.advanced_plot.nodes
                if hasattr(n, 'is_twist') and n.is_twist]

    def get_false_ending_nodes(self) -> List[Tuple[int, object]]:
        """Get nodes that are false endings"""
        if not self.world.advanced_plot:
            return []
        return [(n.id, n) for n in self.world.advanced_plot.nodes
                if hasattr(n, 'is_false_ending') and n.is_false_ending]


# =============================================================================
# Demo
# =============================================================================

def demo():
    """Demo complete world generation with different plot types"""
    import sys

    # Parse command line args
    plot_type = PlotType.SIMPLE
    genre = None
    seed = 42

    if len(sys.argv) > 1:
        type_map = {
            'simple': PlotType.SIMPLE,
            'branching': PlotType.BRANCHING,
            'twist': PlotType.WITH_TWIST,
            'false': PlotType.WITH_FALSE_ENDING,
            'epic': PlotType.EPIC
        }
        plot_type = type_map.get(sys.argv[1].lower(), PlotType.SIMPLE)

    if len(sys.argv) > 2:
        genre = sys.argv[2].lower()

    if len(sys.argv) > 3:
        seed = int(sys.argv[3])

    print(f"=== World Generator Demo ===")
    print(f"Plot type: {plot_type.name}")
    print(f"Genre: {genre or 'default'}")
    print(f"Seed: {seed}")
    print()

    gen = WorldGenerator(width=20, height=12, seed=seed)

    print("Generating world...")
    success = gen.generate(plot_type=plot_type, genre=genre)

    if success:
        print("SUCCESS!\n")
        print(gen.get_summary())

        # Show paths between plot points
        print("\nPATH LENGTHS BETWEEN PLOT POINTS:")
        playable = gen.get_playable_order()

        # Choose propp names based on plot type
        propp_names = ADV_PROPP_NAMES if gen.world.advanced_plot else PROPP_NAMES

        for i in range(len(playable) - 1):
            from_id, from_node, from_pos = playable[i]
            to_id, to_node, to_pos = playable[i + 1]

            if from_pos and to_pos:
                path = gen.geo_gen.find_path_between(
                    f"plot_{from_id}", f"plot_{to_id}"
                )
                from_name = propp_names.get(from_node.function, str(from_node.function))
                to_name = propp_names.get(to_node.function, str(to_node.function))
                if path:
                    print(f"  {from_name} -> {to_name}: {len(path)} steps")
                else:
                    print(f"  {from_name} -> {to_name}: NO PATH")

        # Show twist/false ending info
        twist_nodes = gen.get_twist_nodes()
        if twist_nodes:
            print(f"\nTWIST POINTS:")
            for node_id, node in twist_nodes:
                print(f"  Node {node_id}: {node.description}")

        false_endings = gen.get_false_ending_nodes()
        if false_endings:
            print(f"\nFALSE ENDINGS:")
            for node_id, node in false_endings:
                print(f"  Node {node_id}: {node.description}")
    else:
        print("World generation FAILED")


def demo_all():
    """Demo all plot types"""
    print("=" * 60)
    print("DEMONSTRATING ALL PLOT TYPES")
    print("=" * 60)

    for plot_type in PlotType:
        print(f"\n{'='*60}")
        print(f"PLOT TYPE: {plot_type.name}")
        print("=" * 60)

        gen = WorldGenerator(width=16, height=10, seed=42)
        success = gen.generate(plot_type=plot_type, genre='fantasy')

        if success:
            print(f"Generated: {len(gen.world.get_plot_nodes())} nodes")
            print(f"Twist: {gen.world.has_twist}")
            print(f"False ending: {gen.world.has_false_ending}")
            valid, msg = gen.verify_completability()
            print(f"Valid: {valid} - {msg}")
        else:
            print("FAILED")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'all':
        demo_all()
    else:
        demo()
