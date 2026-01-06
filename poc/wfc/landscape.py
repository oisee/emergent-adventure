"""
Lords of Midnight-style Landscape Renderer

First-person horizon view with silhouettes of terrain features.
Inspired by Mike Singleton's 1984 ZX Spectrum classic.
"""

from typing import List, Tuple, Optional
from .geography import TileType

# ASCII art sprites for each terrain type (3 distance levels: far, mid, near)
# Each sprite is a list of lines (bottom to top)

SPRITES = {
    TileType.MOUNTAIN: {
        'far': [
            "   /\\   ",
            "  /  \\  ",
        ],
        'mid': [
            "    /\\    ",
            "   /  \\   ",
            "  /    \\  ",
            " /      \\ ",
        ],
        'near': [
            "      /\\      ",
            "     /  \\     ",
            "    /    \\    ",
            "   /      \\   ",
            "  /   /\\   \\  ",
            " /   /  \\   \\ ",
        ],
    },
    TileType.FOREST: {
        'far': [
            "   *   ",
            "  ***  ",
            "   |   ",
        ],
        'mid': [
            "    *    ",
            "   ***   ",
            "  *****  ",
            "    |    ",
        ],
        'near': [
            "      *      ",
            "     ***     ",
            "    *****    ",
            "   *******   ",
            "      |      ",
            "      |      ",
        ],
    },
    TileType.TOWER: {
        'far': [
            "  [ ]  ",
            "  | |  ",
        ],
        'mid': [
            "   [=]   ",
            "   | |   ",
            "   | |   ",
            "   |_|   ",
        ],
        'near': [
            "     [===]     ",
            "     |   |     ",
            "     |   |     ",
            "     | o |     ",
            "     |   |     ",
            "     |___|     ",
        ],
    },
    TileType.CASTLE: {
        'far': [
            " [=n=] ",
            "  | |  ",
        ],
        'mid': [
            "  [=n=n=]  ",
            "  |     |  ",
            "  |  o  |  ",
            "  |_____|  ",
        ],
        'near': [
            "   n=======n   ",
            "   |       |   ",
            "   | o   o |   ",
            "   |   ^   |   ",
            "   |  | |  |   ",
            "   |__|_|__|   ",
        ],
    },
    TileType.VILLAGE: {
        'far': [
            "  /\\   ",
            " /  \\  ",
        ],
        'mid': [
            "   /\\  /\\ ",
            "  /__\\/__\\",
        ],
        'near': [
            "    /\\    /\\    ",
            "   /  \\  /  \\   ",
            "  / oo \\/  o \\  ",
            " /______\\____\\ ",
        ],
    },
    TileType.TEMPLE: {
        'far': [
            "  /=\\  ",
            "  | |  ",
        ],
        'mid': [
            "   _/\\_   ",
            "  | ++ |  ",
            "  |    |  ",
            "  |____|  ",
        ],
        'near': [
            "      _/\\_      ",
            "    /|    |\\    ",
            "   / | ++ | \\   ",
            "  |  |    |  |  ",
            "  |  | oo |  |  ",
            "  |__|____|__|  ",
        ],
    },
    TileType.RUINS: {
        'far': [
            "  n  n ",
            "  |  | ",
        ],
        'mid': [
            "  n   ' n  ",
            "  |  '  |  ",
            " _|_   _|_ ",
        ],
        'near': [
            "   n    '   n   ",
            "   |   ' '  |   ",
            "   | '      |   ",
            "  _|    '  _|_  ",
            " /__'   __/___\\ ",
        ],
    },
    TileType.CAVE: {
        'far': [
            " (   ) ",
            "  \\_/  ",
        ],
        'mid': [
            "  (     )  ",
            "   \\   /   ",
            "    \\_/    ",
        ],
        'near': [
            "    (       )    ",
            "   /         \\   ",
            "  |   \\   /   |  ",
            "   \\   \\_/   /   ",
            "    \\_______/    ",
        ],
    },
    TileType.RIVER: {
        'far': [
            " ~~~~~ ",
        ],
        'mid': [
            " ~~~~~~~~~ ",
            "  ~~~~~~~  ",
        ],
        'near': [
            "  ~~~~~~~~~~~~  ",
            " ~~~~~~~~~~~~~~  ",
            "  ~~~~~~~~~~~~  ",
        ],
    },
    TileType.LAKE: {
        'far': [
            " ~~~~~ ",
        ],
        'mid': [
            " ~~~~~~~~~ ",
            " ~~~~~~~~~ ",
        ],
        'near': [
            " ~~~~~~~~~~~~~~ ",
            " ~~~~~~~~~~~~~~ ",
            " ~~~~~~~~~~~~~~ ",
        ],
    },
    TileType.BRIDGE: {
        'far': [
            " ===== ",
        ],
        'mid': [
            " |=====| ",
            " |     | ",
        ],
        'near': [
            "  |=========|  ",
            "  |         |  ",
            " /|         |\\ ",
        ],
    },
    TileType.ROAD: {
        'far': [
            "  ...  ",
        ],
        'mid': [
            "  .....  ",
            "  .....  ",
        ],
        'near': [
            "   .........   ",
            "   .........   ",
            "   .........   ",
        ],
    },
    TileType.CLEARING: {
        'far': [
            "  . .  ",
        ],
        'mid': [
            "  . , .  ",
            "  , . ,  ",
        ],
        'near': [
            "   . , . , .   ",
            "   , . , . ,   ",
            "   . , . , .   ",
        ],
    },
    TileType.SWAMP: {
        'far': [
            " %~~~% ",
        ],
        'mid': [
            " %~~%~~% ",
            "  %~~~%  ",
        ],
        'near': [
            "  %~~%~~~%~~%  ",
            " ~~%~~~%~~~%~~ ",
            "  %~~~%~~~%~~  ",
        ],
    },
    TileType.TAVERN: {
        'far': [
            "  /T\\  ",
            "  |_|  ",
        ],
        'mid': [
            "   /T\\   ",
            "  |   |  ",
            "  |_o_|  ",
        ],
        'near': [
            "     _/T\\_     ",
            "    |     |    ",
            "    | o o |    ",
            "    |  _  |    ",
            "    |_|_|_|    ",
        ],
    },
    TileType.DUNGEON: {
        'far': [
            "  [X]  ",
            "  |||  ",
        ],
        'mid': [
            "   [X]   ",
            "  \\|||/  ",
            "   |||   ",
        ],
        'near': [
            "     [XXX]     ",
            "    \\|||||/    ",
            "     |||||     ",
            "    _|||||_    ",
            "   /_______\\   ",
        ],
    },
}

# Direction names
DIRECTIONS = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
DIRECTION_OFFSETS = {
    'N': (0, -1), 'NE': (1, -1), 'E': (1, 0), 'SE': (1, 1),
    'S': (0, 1), 'SW': (-1, 1), 'W': (-1, 0), 'NW': (-1, -1),
}


class LandscapeRenderer:
    """
    Renders Lords of Midnight-style first-person landscape view.
    """

    def __init__(self, width: int = 60, height: int = 15):
        self.width = width
        self.height = height

    def get_visible_tiles(self, grid: List[List[int]],
                          x: int, y: int,
                          direction: str) -> List[Tuple[TileType, str]]:
        """
        Get tiles visible from position looking in direction.
        Returns list of (tile_type, distance) tuples.
        distance is 'near', 'mid', or 'far'
        """
        dx, dy = DIRECTION_OFFSETS.get(direction, (0, -1))

        height = len(grid)
        width = len(grid[0]) if height > 0 else 0

        visible = []

        # Look ahead in 3 distance bands
        for dist, dist_name in [(1, 'near'), (2, 'mid'), (3, 'far')]:
            nx = x + dx * dist
            ny = y + dy * dist

            if 0 <= nx < width and 0 <= ny < height:
                tile = TileType(grid[ny][nx])
                visible.append((tile, dist_name))

            # Also check sides at each distance
            if dist <= 2:
                # Perpendicular offsets
                if dx == 0:
                    perp = [(1, 0), (-1, 0)]
                elif dy == 0:
                    perp = [(0, 1), (0, -1)]
                else:
                    perp = [(-dy, dx), (dy, -dx)]

                for px, py in perp:
                    sx = nx + px
                    sy = ny + py
                    if 0 <= sx < width and 0 <= sy < height:
                        tile = TileType(grid[sy][sx])
                        # Side tiles appear one distance band further
                        side_dist = 'far' if dist_name == 'mid' else 'mid' if dist_name == 'near' else 'far'
                        visible.append((tile, side_dist))

        return visible

    def render(self, grid: List[List[int]],
               x: int, y: int,
               direction: str = 'N',
               location_name: str = None) -> str:
        """
        Render landscape view from position looking in direction.
        """
        lines = []

        # Sky
        lines.append("=" * self.width)
        lines.append(" " * self.width)

        # Get visible tiles
        visible = self.get_visible_tiles(grid, x, y, direction)

        # Create canvas
        canvas = [[' ' for _ in range(self.width)] for _ in range(self.height - 4)]

        # Horizon line
        horizon_y = 2
        for i in range(self.width):
            canvas[horizon_y][i] = '-'

        # Draw sprites (far to near, so near overwrites far)
        for tile, distance in reversed(visible):
            sprite_data = SPRITES.get(tile, {}).get(distance, [])
            if not sprite_data:
                continue

            # Position sprite
            if distance == 'far':
                start_y = horizon_y - len(sprite_data)
                center_x = self.width // 2
                scale = 0.7
            elif distance == 'mid':
                start_y = horizon_y - len(sprite_data) + 1
                center_x = self.width // 2
                scale = 0.85
            else:  # near
                start_y = horizon_y - len(sprite_data) + 2
                center_x = self.width // 2
                scale = 1.0

            # Add some horizontal offset for variety
            offset = hash(str(tile) + distance) % 7 - 3
            center_x += offset

            # Draw sprite
            for i, line in enumerate(reversed(sprite_data)):
                y_pos = start_y + i
                if 0 <= y_pos < len(canvas):
                    x_start = center_x - len(line) // 2
                    for j, char in enumerate(line):
                        x_pos = x_start + j
                        if 0 <= x_pos < self.width and char != ' ':
                            canvas[y_pos][x_pos] = char

        # Ground texture
        current_tile = TileType(grid[y][x]) if 0 <= y < len(grid) and 0 <= x < len(grid[0]) else TileType.CLEARING
        ground_char = {
            TileType.FOREST: '"',
            TileType.ROAD: '.',
            TileType.CLEARING: ',',
            TileType.SWAMP: '%',
            TileType.RIVER: '~',
            TileType.BRIDGE: '=',
        }.get(current_tile, ',')

        for y_pos in range(horizon_y + 1, len(canvas)):
            for x_pos in range(self.width):
                if canvas[y_pos][x_pos] == ' ':
                    canvas[y_pos][x_pos] = ground_char

        # Convert canvas to lines
        for row in canvas:
            lines.append(''.join(row))

        # Status line
        lines.append("=" * self.width)

        # Direction indicator
        dir_display = f"Looking {direction}"
        if location_name:
            dir_display += f" | {location_name}"
        lines.append(dir_display.center(self.width))

        return '\n'.join(lines)

    def render_compass(self, direction: str) -> str:
        """Render a simple compass"""
        dirs = ['N', 'E', 'S', 'W']
        compass = """
    N
  W + E
    S
        """.strip()

        # Highlight current direction
        result = compass
        for d in dirs:
            if d == direction or (len(direction) == 2 and d in direction):
                result = result.replace(d, f'[{d}]')

        return result


def demo():
    """Demo the landscape renderer"""
    from .geography import GeographyGenerator

    print("=== Lords of Midnight-style Landscape Demo ===\n")

    # Generate world
    gen = GeographyGenerator(width=16, height=12, seed=42)
    gen.generate()

    grid = gen.wfc.to_tile_grid()
    renderer = LandscapeRenderer(width=50, height=12)

    # Find a good starting position
    x, y = 8, 6

    # Show views in all cardinal directions
    for direction in ['N', 'E', 'S', 'W']:
        print(f"\n--- Looking {direction} from ({x}, {y}) ---\n")
        view = renderer.render(grid, x, y, direction)
        print(view)
        print()


if __name__ == "__main__":
    demo()
