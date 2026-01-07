"""
Text Adventure Engine

Allows exploration of generated worlds.
Simple command parser and game state management.
Supports advanced plots with twists and false endings.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional, Callable
from enum import Enum, auto
import random
import textwrap

from .integration import WorldGenerator, PlotType
from .geography import TileType, TILE_CHARS, PASSABLE_TILES
from .plot import ProppFunction, PROPP_NAMES, PlotNode, Requirement, Provides
from .plot_advanced import (
    ProppFunc, TwistType, GENRES,
    PROPP_NAMES as ADV_PROPP_NAMES
)
from .core import find_path
from .landscape import LandscapeRenderer


class GameState(Enum):
    """Current state of the game"""
    EXPLORING = auto()
    IN_EVENT = auto()
    VICTORY = auto()
    GAME_OVER = auto()


# Location descriptions
TILE_DESCRIPTIONS = {
    TileType.FOREST: [
        "You are in a dense forest. Tall trees surround you on all sides.",
        "Ancient oaks tower above. Shafts of light pierce the canopy.",
        "The forest is thick here. You hear birds singing in the branches.",
    ],
    TileType.CLEARING: [
        "You stand in an open clearing. Grass sways gently in the breeze.",
        "A peaceful meadow stretches before you.",
        "Wildflowers dot this sunny clearing.",
    ],
    TileType.RIVER: [
        "A swift river blocks your path. The water runs deep and cold.",
        "You stand at the river's edge. The current is strong.",
    ],
    TileType.ROAD: [
        "A dusty road stretches before you, worn by countless travelers.",
        "The well-trodden path continues in both directions.",
        "Wheel ruts mark this old trade road.",
    ],
    TileType.MOUNTAIN: [
        "Steep rocky cliffs rise before you. The way is impassable.",
        "Jagged peaks tower overhead. No path leads through.",
    ],
    TileType.CAVE: [
        "A dark cave mouth yawns before you. Cold air flows from within.",
        "You stand at the entrance to a cavern. Darkness awaits.",
    ],
    TileType.VILLAGE: [
        "A small village lies before you. Smoke rises from chimneys.",
        "Cottages cluster around a central well. Villagers go about their day.",
    ],
    TileType.CASTLE: [
        "A great castle looms ahead, its towers reaching toward the sky.",
        "Massive stone walls surround the fortress. Banners flutter above.",
    ],
    TileType.SWAMP: [
        "Murky water and twisted trees mark this treacherous swamp.",
        "The ground squelches underfoot. The air smells of decay.",
    ],
    TileType.RUINS: [
        "Ancient ruins crumble around you. Who built this place?",
        "Broken columns and fallen stones speak of past glory.",
    ],
    TileType.TOWER: [
        "A tall tower rises from the landscape, its purpose unknown.",
        "The wizard's tower stands silent, windows dark.",
    ],
    TileType.LAKE: [
        "A vast lake spreads before you, its surface mirror-smooth.",
        "Crystal waters reflect the sky. The lake is too deep to cross.",
    ],
    TileType.BRIDGE: [
        "An old stone bridge spans the water here.",
        "A wooden bridge creaks under your weight but holds firm.",
    ],
    TileType.TAVERN: [
        "A welcoming tavern stands here. Sounds of merriment drift out.",
        "The inn's sign creaks in the wind. A warm glow comes from within.",
    ],
    TileType.TEMPLE: [
        "An ancient temple rises before you, carved with mysterious symbols.",
        "Stone steps lead up to the temple entrance. Peace fills the air.",
    ],
    TileType.DUNGEON: [
        "Iron gates guard the entrance to a dark dungeon.",
        "Stone steps descend into darkness. A chill wind rises from below.",
    ],
}


@dataclass
class GameEngine:
    """
    Text adventure game engine.

    Manages game state, player movement, and plot progression.
    Supports advanced plots with twists and false endings.
    """

    # World
    world_gen: WorldGenerator = None

    # Player state
    player_x: int = 0
    player_y: int = 0
    visited: Set[Tuple[int, int]] = field(default_factory=set)
    inventory: List[str] = field(default_factory=list)

    # Plot state
    completed_events: Set[int] = field(default_factory=set)
    current_event: Optional[int] = None
    plot_state: int = 0  # Bitmask of completed requirements

    # Advanced plot state
    twist_revealed: bool = False
    false_endings_seen: int = 0
    in_false_ending: bool = False

    # Game state
    state: GameState = GameState.EXPLORING
    turn_count: int = 0

    # Output buffer
    output_buffer: List[str] = field(default_factory=list)

    # Landscape renderer
    landscape: LandscapeRenderer = field(default_factory=lambda: LandscapeRenderer(50, 12))
    facing: str = 'N'  # Current facing direction

    # Plot type for display
    plot_type: PlotType = PlotType.SIMPLE
    genre_name: str = ""

    def initialize(self, seed: int = None, width: int = 16, height: int = 12,
                   plot_type: PlotType = PlotType.SIMPLE,
                   genre: str = None) -> bool:
        """Initialize game with generated world"""
        if seed is None:
            seed = random.randint(0, 999999)

        self.world_gen = WorldGenerator(width=width, height=height, seed=seed)
        self.plot_type = plot_type
        self.genre_name = genre or ""

        if not self.world_gen.generate(plot_type=plot_type, genre=genre):
            return False

        # Find starting position (LACK event location or first passable)
        start_pos = self._find_start_position()
        if start_pos:
            self.player_x, self.player_y = start_pos
        else:
            return False

        self.visited = {(self.player_x, self.player_y)}
        self.inventory = []
        self.completed_events = set()
        self.current_event = None
        self.plot_state = 0
        self.state = GameState.EXPLORING
        self.turn_count = 0
        self.output_buffer = []

        # Reset advanced plot state
        self.twist_revealed = False
        self.false_endings_seen = 0
        self.in_false_ending = False

        return True

    def _find_start_position(self) -> Optional[Tuple[int, int]]:
        """Find starting position (prefer LACK/EQUILIBRIUM event location)"""
        # Get nodes from either simple or advanced plot
        nodes = self.world_gen.world.get_plot_nodes()

        # Look for LACK or EQUILIBRIUM event (story beginning)
        for node in nodes:
            func = node.function
            # Check both simple and advanced function types
            is_start = (func == ProppFunction.LACK if isinstance(func, ProppFunction)
                       else func in (ProppFunc.LACK, ProppFunc.EQUILIBRIUM))
            if is_start:
                pos = self.world_gen.world.node_locations.get(node.id)
                if pos:
                    return pos

        # Fallback: find any passable tile
        grid = self.world_gen.geo_gen.wfc.to_tile_grid()
        for y in range(len(grid)):
            for x in range(len(grid[0])):
                if TileType(grid[y][x]) in PASSABLE_TILES:
                    return (x, y)

        return None

    def output(self, text: str):
        """Add text to output buffer"""
        self.output_buffer.append(text)

    def get_output(self) -> str:
        """Get and clear output buffer"""
        result = '\n'.join(self.output_buffer)
        self.output_buffer = []
        return result

    def get_tile(self, x: int, y: int) -> Optional[TileType]:
        """Get tile type at position"""
        grid = self.world_gen.geo_gen.wfc.to_tile_grid()
        if 0 <= y < len(grid) and 0 <= x < len(grid[0]):
            return TileType(grid[y][x])
        return None

    def can_move_to(self, x: int, y: int) -> bool:
        """Check if player can move to position"""
        tile = self.get_tile(x, y)
        return tile is not None and tile in PASSABLE_TILES

    def describe_location(self):
        """Describe current location"""
        tile = self.get_tile(self.player_x, self.player_y)
        if tile is None:
            self.output("You are nowhere.")
            return

        # Get description
        descriptions = TILE_DESCRIPTIONS.get(tile, ["You are somewhere."])
        desc = random.choice(descriptions)
        self.output(desc)

        # Check for plot events here
        event = self._get_event_at_position(self.player_x, self.player_y)
        if event and event.id not in self.completed_events:
            self.output("")
            self.output(f"*** {event.description} ***")

        # Show exits
        exits = self._get_exits()
        if exits:
            self.output(f"\nExits: {', '.join(exits)}")

        # First visit?
        if (self.player_x, self.player_y) not in self.visited:
            self.visited.add((self.player_x, self.player_y))

    def _get_exits(self) -> List[str]:
        """Get available exit directions"""
        exits = []
        directions = [
            ('north', 0, -1),
            ('east', 1, 0),
            ('south', 0, 1),
            ('west', -1, 0),
        ]

        for name, dx, dy in directions:
            nx, ny = self.player_x + dx, self.player_y + dy
            if self.can_move_to(nx, ny):
                exits.append(name)

        return exits

    def _get_event_at_position(self, x: int, y: int) -> Optional[object]:
        """Get plot event at position (works with both simple and advanced plots)"""
        nodes = self.world_gen.world.get_plot_nodes()
        node_map = {n.id: n for n in nodes}

        for node_id, pos in self.world_gen.world.node_locations.items():
            if pos == (x, y):
                return node_map.get(node_id)
        return None

    def move(self, direction: str) -> bool:
        """Move player in direction"""
        dx, dy = 0, 0

        if direction in ('n', 'north'):
            dy = -1
            self.facing = 'N'
        elif direction in ('s', 'south'):
            dy = 1
            self.facing = 'S'
        elif direction in ('e', 'east'):
            dx = 1
            self.facing = 'E'
        elif direction in ('w', 'west'):
            dx = -1
            self.facing = 'W'
        else:
            self.output(f"Unknown direction: {direction}")
            return False

        nx, ny = self.player_x + dx, self.player_y + dy

        if not self.can_move_to(nx, ny):
            tile = self.get_tile(nx, ny)
            if tile == TileType.RIVER:
                self.output("The river is too deep to cross here.")
            elif tile == TileType.MOUNTAIN:
                self.output("The mountain is too steep to climb.")
            elif tile == TileType.LAKE:
                self.output("You cannot swim across the lake.")
            elif tile == TileType.SWAMP:
                self.output("The swamp is too dangerous to enter.")
            else:
                self.output("You cannot go that way.")
            return False

        self.player_x, self.player_y = nx, ny
        self.turn_count += 1
        self.describe_location()
        return True

    def do_event(self) -> bool:
        """Interact with event at current location"""
        event = self._get_event_at_position(self.player_x, self.player_y)

        if event is None:
            self.output("There is nothing special here.")
            return False

        if event.id in self.completed_events:
            self.output("You have already done what needed to be done here.")
            return False

        # Check requirements (be lenient for advanced plots)
        req = event.requires
        if req and (req & self.plot_state) != req:
            self.output("You are not yet ready for this challenge.")
            # Hint at what's needed
            missing = req & ~self.plot_state
            hints = []
            if missing & Requirement.HAS_WEAPON:
                hints.append("a weapon")
            if missing & Requirement.HAS_KEY:
                hints.append("a key")
            if missing & Requirement.HAS_INFO:
                hints.append("knowledge")
            if missing & Requirement.HAS_ALLY:
                hints.append("an ally")
            if missing & Requirement.VILLAIN_WEAK:
                hints.append("to know the enemy's weakness")
            if missing & Requirement.AT_GOAL:
                hints.append("to reach your destination")
            if hints:
                self.output(f"You feel you need: {', '.join(hints)}")
            return False

        # Complete the event
        self.completed_events.add(event.id)
        self.plot_state |= event.provides

        # Describe completion
        self._describe_event_completion(event)

        # Handle twist reveals
        if hasattr(event, 'twist_type') and event.twist_type and event.twist_type != TwistType.NONE:
            self._handle_twist_reveal(event)

        # Handle false endings
        if hasattr(event, 'is_false_ending') and event.is_false_ending:
            self._handle_false_ending(event)
            return True  # Don't check for victory yet

        # Check for victory (simple plot or final true victory)
        func = event.function
        is_victory = (func == ProppFunction.VICTORY if isinstance(func, ProppFunction)
                     else func == ProppFunc.VICTORY)
        is_return = (func == ProppFunction.RETURN if isinstance(func, ProppFunction)
                    else func == ProppFunc.RETURN)

        if is_victory or (hasattr(event, 'is_ending') and event.is_ending):
            if not self.in_false_ending:
                self.output("\n*** VICTORY! Your quest is complete! ***")
                self.state = GameState.VICTORY
        elif is_return and hasattr(event, 'is_ending') and event.is_ending:
            self.output("\n*** THE END - Your epic journey is complete! ***")
            self.state = GameState.VICTORY

        return True

    def _handle_twist_reveal(self, event):
        """Handle a plot twist being revealed"""
        self.twist_revealed = True

        self.output("")
        self.output("=" * 40)
        self.output("*** PLOT TWIST! ***")
        self.output("=" * 40)

        if hasattr(event, 'twist_reveals') and event.twist_reveals:
            self.output(event.twist_reveals)

        # Show what's been invalidated
        if hasattr(event, 'recontextualizes'):
            for node_id, context in event.recontextualizes.items():
                self.output(f"  - {context}")

        self.output("")
        self.output("The truth changes everything...")
        self.output("")

    def _handle_false_ending(self, event):
        """Handle a false ending"""
        self.false_endings_seen += 1
        self.in_false_ending = True

        self.output("")
        self.output("=" * 40)
        self.output("*** YOU THINK YOU'VE WON... ***")
        self.output("=" * 40)
        self.output("")

        if hasattr(event, 'false_ending_reveal') and event.false_ending_reveal:
            self.output("But wait...")
            self.output(event.false_ending_reveal)
            self.output("")
            self.output("The quest continues!")
            self.in_false_ending = False  # Ready for next chapter

    def _describe_event_completion(self, event):
        """Describe completing a plot event (handles both simple and advanced functions)"""
        self.output("")

        # Use the event's description directly if available
        if hasattr(event, 'description') and event.description:
            self.output(event.description)

        # Get function for comparison
        func = event.function

        # Check function type (simple ProppFunction or advanced ProppFunc)
        is_simple = isinstance(func, ProppFunction)

        # Map function names for comparison
        func_name = func.name if hasattr(func, 'name') else str(func)

        # Handle inventory for acquisition events
        if func_name in ('ACQUISITION', 'DONOR_TEST'):
            provides = event.provides
            if provides & Provides.HAS_WEAPON:
                self.output("You receive a mighty weapon!")
                if "magic sword" not in self.inventory:
                    self.inventory.append("magic sword")
            elif provides & Provides.HAS_KEY:
                self.output("You obtain a mysterious key!")
                if "ancient key" not in self.inventory:
                    self.inventory.append("ancient key")
            elif provides & Provides.HAS_ALLY:
                self.output("A loyal companion joins your quest!")
                if "loyal companion" not in self.inventory:
                    self.inventory.append("loyal companion")
            elif provides & Provides.HAS_INFO:
                self.output("Ancient wisdom is revealed to you!")

        # Additional flavor for specific functions
        if func_name == 'EQUILIBRIUM':
            self.output("Peace reigns... for now.")
        elif func_name == 'LACK':
            self.output("Your journey begins!")
        elif func_name == 'INTERDICTION':
            self.output("A warning has been given...")
        elif func_name == 'VIOLATION':
            self.output("Rules are meant to be broken.")
        elif func_name == 'DEPARTURE':
            self.output("The road ahead is long, but your heart is determined.")
        elif func_name == 'GUIDANCE':
            self.output("The path to your goal becomes clear.")
        elif func_name == 'STRUGGLE':
            self.output("Battle is joined!")
        elif func_name == 'BRANDING':
            self.output("You bear the mark of your deeds.")
        elif func_name == 'PURSUIT':
            self.output("They're after you!")
        elif func_name == 'RESCUE':
            self.output("Someone is saved from peril!")
        elif func_name == 'RECOGNITION':
            self.output("The truth is revealed!")
        elif func_name == 'PUNISHMENT':
            self.output("Justice is served.")
        elif func_name in ('VICTORY', 'RETURN'):
            if not (hasattr(event, 'is_false_ending') and event.is_false_ending):
                self.output("Peace returns to the land.")

        self.output("")

    def show_inventory(self):
        """Show player inventory"""
        if not self.inventory:
            self.output("You are carrying nothing.")
        else:
            self.output("You are carrying:")
            for item in self.inventory:
                self.output(f"  - {item}")

    def show_map(self):
        """Show ASCII map with player position"""
        grid = self.world_gen.geo_gen.wfc.to_tile_grid()
        height = len(grid)
        width = len(grid[0]) if height > 0 else 0

        self.output("Map (* = you, @ = quest location, ? = unvisited):")
        self.output("")

        for y in range(height):
            line = ""
            for x in range(width):
                if (x, y) == (self.player_x, self.player_y):
                    line += "*"
                elif (x, y) in self.world_gen.world.node_locations.values():
                    # Quest location
                    event = self._get_event_at_position(x, y)
                    if event and event.id in self.completed_events:
                        line += "+"  # Completed
                    else:
                        line += "@"  # Active
                elif (x, y) not in self.visited:
                    tile = self.get_tile(x, y)
                    if tile in PASSABLE_TILES:
                        line += "?"
                    else:
                        line += TILE_CHARS.get(tile, ' ')
                else:
                    tile = TileType(grid[y][x])
                    line += TILE_CHARS.get(tile, '?')
            self.output(line)

    def show_quest(self):
        """Show quest progress (handles both simple and advanced plots)"""
        self.output("Quest Progress:")
        if self.genre_name:
            self.output(f"Genre: {self.genre_name}")
        if self.plot_type != PlotType.SIMPLE:
            self.output(f"Type: {self.plot_type.name}")
        self.output("-" * 30)

        # Get order from appropriate plot
        if self.world_gen.world.advanced_plot:
            order = self.world_gen.world.advanced_plot.topological_sort()
            propp_names = ADV_PROPP_NAMES
        else:
            order = self.world_gen.world.plot.topological_sort()
            propp_names = PROPP_NAMES

        nodes = self.world_gen.world.get_plot_nodes()
        node_map = {n.id: n for n in nodes}

        for node_id in order:
            node = node_map.get(node_id)
            if node is None:
                continue

            status = "[X]" if node_id in self.completed_events else "[ ]"
            func_name = propp_names.get(node.function, str(node.function))
            desc = node.description[:40] if node.description else "..."

            # Add markers for special nodes
            markers = ""
            if hasattr(node, 'is_twist') and node.is_twist:
                markers += " [TWIST]"
            elif hasattr(node, 'twist_type') and node.twist_type and node.twist_type != TwistType.NONE:
                markers += " [TWIST]"
            if hasattr(node, 'is_false_ending') and node.is_false_ending:
                markers += " [FALSE END]"
            if hasattr(node, 'is_ending') and node.is_ending:
                markers += " [END]"

            self.output(f"{status} {func_name}: {desc}...{markers}")

    def show_landscape(self):
        """Show Lords of Midnight-style landscape view"""
        grid = self.world_gen.geo_gen.wfc.to_tile_grid()
        tile = self.get_tile(self.player_x, self.player_y)
        location_name = tile.name if tile else "Unknown"

        view = self.landscape.render(
            grid,
            self.player_x, self.player_y,
            self.facing,
            location_name
        )
        self.output(view)

    def turn_left(self):
        """Turn 90 degrees left"""
        dirs = ['N', 'W', 'S', 'E']
        idx = dirs.index(self.facing) if self.facing in dirs else 0
        self.facing = dirs[(idx + 1) % 4]
        self.output(f"You turn to face {self.facing}.")
        self.show_landscape()

    def turn_right(self):
        """Turn 90 degrees right"""
        dirs = ['N', 'E', 'S', 'W']
        idx = dirs.index(self.facing) if self.facing in dirs else 0
        self.facing = dirs[(idx + 1) % 4]
        self.output(f"You turn to face {self.facing}.")
        self.show_landscape()

    def show_help(self):
        """Show help"""
        self.output("""
Commands:
  north/n, south/s, east/e, west/w - Move in direction
  left/right - Turn to face direction
  look/l - Look around (text)
  view/v - Landscape view (Lords of Midnight style)
  do/interact - Interact with quest event
  inventory/i - Show inventory
  map/m - Show map
  quest/q - Show quest progress
  help/h - Show this help
  quit - End game
        """.strip())

    def process_command(self, command: str) -> bool:
        """
        Process player command.

        Returns False if game should end.
        """
        command = command.strip().lower()

        if not command:
            return True

        # Movement
        if command in ('n', 'north'):
            self.move('north')
        elif command in ('s', 'south'):
            self.move('south')
        elif command in ('e', 'east'):
            self.move('east')
        elif command in ('w', 'west'):
            self.move('west')

        # Turning
        elif command in ('left', 'turn left', 'tl'):
            self.turn_left()
        elif command in ('right', 'turn right', 'tr'):
            self.turn_right()

        # Actions
        elif command in ('l', 'look'):
            self.describe_location()
        elif command in ('v', 'view', 'landscape'):
            self.show_landscape()
        elif command in ('do', 'interact', 'action'):
            self.do_event()
        elif command in ('i', 'inventory', 'inv'):
            self.show_inventory()
        elif command in ('m', 'map'):
            self.show_map()
        elif command in ('q', 'quest', 'journal'):
            self.show_quest()
        elif command in ('h', 'help', '?'):
            self.show_help()
        elif command in ('quit', 'exit', 'bye'):
            self.output("Farewell, adventurer!")
            return False

        # Unknown
        else:
            self.output(f"I don't understand '{command}'. Type 'help' for commands.")

        return True


def play_text_adventure(seed: int = None,
                        plot_type: PlotType = PlotType.SIMPLE,
                        genre: str = None):
    """Play text adventure in terminal"""
    print("=" * 60)
    print("EMERGENT ADVENTURE")
    print("A Procedurally Generated Text Adventure")
    print("=" * 60)

    # Show game settings
    if plot_type != PlotType.SIMPLE:
        print(f"Plot Type: {plot_type.name}")
    if genre:
        print(f"Genre: {genre}")
    print()

    engine = GameEngine()

    print("Generating world...")
    if not engine.initialize(seed=seed, width=16, height=12,
                            plot_type=plot_type, genre=genre):
        print("Failed to generate world!")
        return

    print(f"World generated! (seed: {engine.world_gen.world.geo_seed})")

    # Show plot metadata
    world = engine.world_gen.world
    if world.has_twist:
        twist_name = world.twist_type.name if world.twist_type else "UNKNOWN"
        print(f"This story contains a {twist_name} twist!")
    if world.has_false_ending:
        print("Beware of false victories...")

    print()
    print("Type 'help' for commands.")
    print("-" * 40)
    print()

    # Initial description
    engine.describe_location()
    print(engine.get_output())

    # Game loop
    while engine.state not in (GameState.VICTORY, GameState.GAME_OVER):
        try:
            command = input("\n> ").strip()
            if not engine.process_command(command):
                break
            output = engine.get_output()
            if output:
                print(output)
        except (EOFError, KeyboardInterrupt):
            print("\nFarewell!")
            break

    # Game over stats
    print()
    print("=" * 60)
    print(f"Game Over - Turns: {engine.turn_count}")
    print(f"Locations visited: {len(engine.visited)}")

    nodes = engine.world_gen.world.get_plot_nodes()
    print(f"Events completed: {len(engine.completed_events)}/{len(nodes)}")

    if engine.twist_revealed:
        print("Twist revealed: Yes!")
    if engine.false_endings_seen > 0:
        print(f"False endings encountered: {engine.false_endings_seen}")

    print("=" * 60)


if __name__ == "__main__":
    import sys

    # Parse arguments: seed [plot_type] [genre]
    seed = None
    plot_type = PlotType.SIMPLE
    genre = None

    args = sys.argv[1:]

    # Check for help
    if args and args[0] in ('-h', '--help', 'help'):
        print("Usage: python -m wfc.engine [seed] [plot_type] [genre]")
        print()
        print("Plot types: simple, branching, twist, false, epic")
        print("Genres: fantasy, solarpunk, hopepunk, dark_fantasy, mystery")
        print()
        print("Examples:")
        print("  python -m wfc.engine 42")
        print("  python -m wfc.engine 42 twist fantasy")
        print("  python -m wfc.engine 42 epic dark_fantasy")
        sys.exit(0)

    if args:
        try:
            seed = int(args[0])
        except ValueError:
            pass

    if len(args) > 1:
        type_map = {
            'simple': PlotType.SIMPLE,
            'branching': PlotType.BRANCHING,
            'twist': PlotType.WITH_TWIST,
            'false': PlotType.WITH_FALSE_ENDING,
            'epic': PlotType.EPIC
        }
        plot_type = type_map.get(args[1].lower(), PlotType.SIMPLE)

    if len(args) > 2:
        genre = args[2].lower()

    play_text_adventure(seed=seed, plot_type=plot_type, genre=genre)
