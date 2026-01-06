"""
Text Adventure Engine

Allows exploration of generated worlds.
Simple command parser and game state management.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional, Callable
from enum import Enum, auto
import random
import textwrap

from .integration import WorldGenerator
from .geography import TileType, TILE_CHARS, PASSABLE_TILES
from .plot import ProppFunction, PROPP_NAMES, PlotNode
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

    # Game state
    state: GameState = GameState.EXPLORING
    turn_count: int = 0

    # Output buffer
    output_buffer: List[str] = field(default_factory=list)

    # Landscape renderer
    landscape: LandscapeRenderer = field(default_factory=lambda: LandscapeRenderer(50, 12))
    facing: str = 'N'  # Current facing direction

    def initialize(self, seed: int = None, width: int = 16, height: int = 12) -> bool:
        """Initialize game with generated world"""
        if seed is None:
            seed = random.randint(0, 999999)

        self.world_gen = WorldGenerator(width=width, height=height, seed=seed)

        if not self.world_gen.generate():
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

        return True

    def _find_start_position(self) -> Optional[Tuple[int, int]]:
        """Find starting position (prefer LACK event location)"""
        # Look for LACK event
        for node in self.world_gen.world.plot.nodes:
            if node.function == ProppFunction.LACK:
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

    def _get_event_at_position(self, x: int, y: int) -> Optional[PlotNode]:
        """Get plot event at position"""
        for node_id, pos in self.world_gen.world.node_locations.items():
            if pos == (x, y):
                return self.world_gen.world.plot.nodes[node_id]
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

        # Check requirements
        if (event.requires & self.plot_state) != event.requires:
            self.output("You are not yet ready for this challenge.")
            # Hint at what's needed
            from .plot import Requirement
            missing = event.requires & ~self.plot_state
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

        # Check for victory
        if event.function == ProppFunction.VICTORY:
            self.output("\n*** VICTORY! Your quest is complete! ***")
            self.state = GameState.VICTORY

        return True

    def _describe_event_completion(self, event: PlotNode):
        """Describe completing a plot event"""
        from .plot import Provides

        self.output("")

        if event.function == ProppFunction.LACK:
            self.output("You learn of the threat facing the land.")
            self.output("Your journey begins!")
        elif event.function == ProppFunction.DEPARTURE:
            self.output("You set forth on your quest.")
            self.output("The road ahead is long, but your heart is determined.")
        elif event.function == ProppFunction.DONOR_TEST:
            self.output("You have proven your worth!")
        elif event.function == ProppFunction.ACQUISITION:
            if event.provides & Provides.HAS_WEAPON:
                self.output("You receive a mighty weapon!")
                self.inventory.append("magic sword")
            elif event.provides & Provides.HAS_KEY:
                self.output("You obtain a mysterious key!")
                self.inventory.append("ancient key")
            elif event.provides & Provides.HAS_INFO:
                self.output("Ancient wisdom is revealed to you!")
            elif event.provides & Provides.HAS_ALLY:
                self.output("A loyal companion joins your quest!")
                self.inventory.append("loyal companion")
        elif event.function == ProppFunction.GUIDANCE:
            self.output("The path to your goal becomes clear.")
        elif event.function == ProppFunction.STRUGGLE:
            self.output("Battle is joined! You fight with all your might!")
        elif event.function == ProppFunction.VICTORY:
            self.output("The villain is defeated!")
            self.output("Peace returns to the land.")
        elif event.function == ProppFunction.RETURN:
            self.output("You return home, forever changed by your journey.")

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
        """Show quest progress"""
        self.output("Quest Progress:")
        self.output("-" * 30)

        order = self.world_gen.world.plot.topological_sort()
        for node_id in order:
            node = self.world_gen.world.plot.nodes[node_id]
            status = "[X]" if node_id in self.completed_events else "[ ]"
            self.output(f"{status} {PROPP_NAMES[node.function]}: {node.description[:40]}...")

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


def play_text_adventure(seed: int = None):
    """Play text adventure in terminal"""
    print("=" * 60)
    print("EMERGENT ADVENTURE")
    print("A Procedurally Generated Text Adventure")
    print("=" * 60)
    print()

    engine = GameEngine()

    print("Generating world...")
    if not engine.initialize(seed=seed, width=16, height=12):
        print("Failed to generate world!")
        return

    print(f"World generated! (seed: {engine.world_gen.world.geo_seed})")
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

    print()
    print("=" * 60)
    print(f"Game Over - Turns: {engine.turn_count}")
    print(f"Locations visited: {len(engine.visited)}")
    print(f"Events completed: {len(engine.completed_events)}/{len(engine.world_gen.world.plot.nodes)}")
    print("=" * 60)


if __name__ == "__main__":
    import sys
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else None
    play_text_adventure(seed)
