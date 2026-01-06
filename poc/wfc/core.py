"""
Core Bitwise WFC Engine

Designed to be Z80-portable:
- All operations use bitwise AND/OR only
- No floating point
- Popcount via lookup table
- Stack-based propagation
"""

from dataclasses import dataclass, field
from typing import List, Set, Tuple, Optional, Dict
from enum import IntEnum
import random


class WFCState(IntEnum):
    """Cell states during generation"""
    UNCOLLAPSED = 0
    COLLAPSED = 1
    CONTRADICTION = 2


@dataclass
class WFCCell:
    """Single cell in WFC grid"""
    possibilities: int  # Bitmask of possible tiles
    collapsed_to: int = -1  # Tile ID after collapse, -1 if not collapsed

    @property
    def is_collapsed(self) -> bool:
        return self.collapsed_to >= 0

    @property
    def is_contradiction(self) -> bool:
        return self.possibilities == 0 and not self.is_collapsed


# Popcount lookup table (256 entries for 8-bit, can extend for wider)
POPCOUNT_LUT = [bin(i).count('1') for i in range(256)]

def popcount(mask: int, bits: int = 32) -> int:
    """Count set bits in mask (Z80-friendly via LUT)"""
    count = 0
    for _ in range(bits // 8):
        count += POPCOUNT_LUT[mask & 0xFF]
        mask >>= 8
    return count


def lowest_bit(mask: int) -> int:
    """Get position of lowest set bit"""
    if mask == 0:
        return -1
    pos = 0
    while (mask & 1) == 0:
        mask >>= 1
        pos += 1
    return pos


def random_set_bit(mask: int, bits: int = 32) -> int:
    """Choose random set bit from mask"""
    count = popcount(mask, bits)
    if count == 0:
        return -1
    target = random.randint(0, count - 1)
    pos = 0
    for i in range(bits):
        if mask & (1 << i):
            if pos == target:
                return i
            pos += 1
    return -1


@dataclass
class BitwiseWFC:
    """
    Generic Bitwise WFC Engine

    Works with any number of tile types (up to mask width).
    Constraints defined as bitmasks of allowed neighbors.
    """

    width: int
    height: int
    num_tiles: int
    mask_bits: int = 32  # Width of bitmask (8, 16, 32, 64)

    # Constraints: tile_id -> mask of allowed neighbors for each direction
    # Direction order: N, E, S, W
    constraints_n: Dict[int, int] = field(default_factory=dict)
    constraints_e: Dict[int, int] = field(default_factory=dict)
    constraints_s: Dict[int, int] = field(default_factory=dict)
    constraints_w: Dict[int, int] = field(default_factory=dict)

    # Grid of cells
    grid: List[List[WFCCell]] = field(default_factory=list)

    # Propagation stack (Z80: fixed-size array)
    prop_stack: List[Tuple[int, int]] = field(default_factory=list)

    # Statistics
    iterations: int = 0
    backtracks: int = 0

    def __post_init__(self):
        """Initialize grid with all possibilities"""
        self.reset()

    def reset(self):
        """Reset grid to initial state (all possibilities open)"""
        all_possible = (1 << self.num_tiles) - 1
        self.grid = [
            [WFCCell(possibilities=all_possible) for _ in range(self.width)]
            for _ in range(self.height)
        ]
        self.prop_stack = []
        self.iterations = 0
        self.backtracks = 0

    def set_symmetric_constraint(self, tile_a: int, tile_b: int):
        """Set that tile_a and tile_b can be neighbors in any direction"""
        for constraints in [self.constraints_n, self.constraints_e,
                           self.constraints_s, self.constraints_w]:
            constraints.setdefault(tile_a, 0)
            constraints.setdefault(tile_b, 0)
            constraints[tile_a] |= (1 << tile_b)
            constraints[tile_b] |= (1 << tile_a)

    def set_directional_constraint(self, tile_from: int, tile_to: int,
                                    direction: str):
        """
        Set that tile_to can be in direction from tile_from
        direction: 'N', 'E', 'S', 'W'
        """
        constraints_map = {
            'N': (self.constraints_n, self.constraints_s),
            'E': (self.constraints_e, self.constraints_w),
            'S': (self.constraints_s, self.constraints_n),
            'W': (self.constraints_w, self.constraints_e),
        }
        forward, backward = constraints_map[direction]
        forward.setdefault(tile_from, 0)
        backward.setdefault(tile_to, 0)
        forward[tile_from] |= (1 << tile_to)
        backward[tile_to] |= (1 << tile_from)

    def get_allowed_neighbors(self, possibilities: int, direction: str) -> int:
        """
        Get mask of tiles that can be neighbors of any tile in possibilities.
        This is the UNION of all allowed neighbors.
        """
        constraints = {
            'N': self.constraints_n,
            'E': self.constraints_e,
            'S': self.constraints_s,
            'W': self.constraints_w,
        }[direction]

        allowed = 0
        for tile_id in range(self.num_tiles):
            if possibilities & (1 << tile_id):
                allowed |= constraints.get(tile_id, 0)
        return allowed

    def get_entropy(self, x: int, y: int) -> int:
        """Get entropy (number of possibilities) for cell"""
        cell = self.grid[y][x]
        if cell.is_collapsed:
            return 0
        return popcount(cell.possibilities, self.mask_bits)

    def find_min_entropy_cell(self) -> Optional[Tuple[int, int]]:
        """Find uncollapsed cell with minimum entropy (>1)"""
        min_entropy = self.num_tiles + 1
        candidates = []

        for y in range(self.height):
            for x in range(self.width):
                cell = self.grid[y][x]
                if cell.is_collapsed or cell.is_contradiction:
                    continue
                entropy = popcount(cell.possibilities, self.mask_bits)
                if entropy == 1:
                    # Auto-collapse cells with single possibility
                    return (x, y)
                if entropy < min_entropy:
                    min_entropy = entropy
                    candidates = [(x, y)]
                elif entropy == min_entropy:
                    candidates.append((x, y))

        if not candidates:
            return None
        return random.choice(candidates)

    def collapse(self, x: int, y: int, tile_id: Optional[int] = None) -> bool:
        """
        Collapse cell to single tile.
        Returns False if contradiction.
        """
        cell = self.grid[y][x]

        if tile_id is None:
            # Choose random tile from possibilities
            tile_id = random_set_bit(cell.possibilities, self.mask_bits)

        if tile_id < 0 or not (cell.possibilities & (1 << tile_id)):
            return False

        cell.possibilities = 1 << tile_id
        cell.collapsed_to = tile_id

        # Add to propagation stack
        self.prop_stack.append((x, y))
        return True

    def propagate(self) -> bool:
        """
        Propagate constraints from collapsed cells.
        Returns False if contradiction detected.
        """
        directions = [
            ('N', 0, -1),
            ('E', 1, 0),
            ('S', 0, 1),
            ('W', -1, 0),
        ]

        while self.prop_stack:
            x, y = self.prop_stack.pop()
            cell = self.grid[y][x]

            for dir_name, dx, dy in directions:
                nx, ny = x + dx, y + dy
                if not (0 <= nx < self.width and 0 <= ny < self.height):
                    continue

                neighbor = self.grid[ny][nx]
                if neighbor.is_collapsed:
                    continue

                # Get allowed tiles for this direction
                allowed = self.get_allowed_neighbors(cell.possibilities, dir_name)

                # Constrain neighbor: new = old AND allowed
                old_poss = neighbor.possibilities
                new_poss = old_poss & allowed

                if new_poss == 0:
                    # Contradiction!
                    return False

                if new_poss != old_poss:
                    neighbor.possibilities = new_poss
                    # Check if auto-collapsed
                    if popcount(new_poss, self.mask_bits) == 1:
                        neighbor.collapsed_to = lowest_bit(new_poss)
                    # Add to stack for further propagation
                    self.prop_stack.append((nx, ny))

        return True

    def is_complete(self) -> bool:
        """Check if all cells are collapsed"""
        for row in self.grid:
            for cell in row:
                if not cell.is_collapsed:
                    return False
        return True

    def has_contradiction(self) -> bool:
        """Check if any cell has no possibilities"""
        for row in self.grid:
            for cell in row:
                if cell.is_contradiction:
                    return True
        return False

    def generate(self, max_iterations: int = 10000) -> bool:
        """
        Run WFC generation.
        Returns True if successful, False if contradiction.
        """
        for _ in range(max_iterations):
            self.iterations += 1

            # Find cell to collapse
            cell_pos = self.find_min_entropy_cell()
            if cell_pos is None:
                # All collapsed or contradiction
                return self.is_complete()

            x, y = cell_pos

            # Collapse it
            if not self.collapse(x, y):
                return False

            # Propagate constraints
            if not self.propagate():
                return False

            if self.is_complete():
                return True

        return False

    def to_tile_grid(self) -> List[List[int]]:
        """Convert to simple grid of tile IDs"""
        return [
            [cell.collapsed_to for cell in row]
            for row in self.grid
        ]

    def visualize(self, tile_chars: Dict[int, str]) -> str:
        """Create ASCII visualization"""
        lines = []
        for row in self.grid:
            line = ""
            for cell in row:
                if cell.is_collapsed:
                    line += tile_chars.get(cell.collapsed_to, '?')
                elif cell.is_contradiction:
                    line += 'X'
                else:
                    entropy = popcount(cell.possibilities, self.mask_bits)
                    if entropy <= 9:
                        line += str(entropy)
                    else:
                        line += '+'
            lines.append(line)
        return '\n'.join(lines)


# =============================================================================
# Reachability Tester
# =============================================================================

def find_connected_components(grid: List[List[int]],
                               passable: Set[int]) -> List[Set[Tuple[int, int]]]:
    """
    Find all connected components of passable tiles.
    Uses BFS - Z80 friendly with fixed stack.
    """
    height = len(grid)
    width = len(grid[0]) if height > 0 else 0

    visited = set()
    components = []

    for start_y in range(height):
        for start_x in range(width):
            if (start_x, start_y) in visited:
                continue
            if grid[start_y][start_x] not in passable:
                continue

            # BFS from this cell
            component = set()
            queue = [(start_x, start_y)]

            while queue:
                x, y = queue.pop(0)
                if (x, y) in visited:
                    continue
                if grid[y][x] not in passable:
                    continue

                visited.add((x, y))
                component.add((x, y))

                # Add neighbors
                for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        if (nx, ny) not in visited:
                            queue.append((nx, ny))

            if component:
                components.append(component)

    return components


def check_reachability(grid: List[List[int]],
                       start: Tuple[int, int],
                       targets: List[Tuple[int, int]],
                       passable: Set[int]) -> Tuple[bool, Set[Tuple[int, int]]]:
    """
    Check if all targets are reachable from start.

    Returns:
        (all_reachable, set of unreachable targets)
    """
    height = len(grid)
    width = len(grid[0]) if height > 0 else 0

    # BFS from start
    visited = set()
    queue = [start]

    while queue:
        x, y = queue.pop(0)
        if (x, y) in visited:
            continue
        if not (0 <= x < width and 0 <= y < height):
            continue
        if grid[y][x] not in passable:
            continue

        visited.add((x, y))

        for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if (nx, ny) not in visited:
                queue.append((nx, ny))

    # Check which targets were reached
    unreachable = set()
    for target in targets:
        if target not in visited:
            unreachable.add(target)

    return len(unreachable) == 0, unreachable


def find_path(grid: List[List[int]],
              start: Tuple[int, int],
              goal: Tuple[int, int],
              passable: Set[int]) -> Optional[List[Tuple[int, int]]]:
    """
    Find shortest path from start to goal using BFS.
    Returns path as list of (x, y) or None if unreachable.
    """
    height = len(grid)
    width = len(grid[0]) if height > 0 else 0

    if start == goal:
        return [start]

    visited = {start: None}  # cell -> came_from
    queue = [start]

    while queue:
        x, y = queue.pop(0)

        for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
            nx, ny = x + dx, y + dy

            if not (0 <= nx < width and 0 <= ny < height):
                continue
            if (nx, ny) in visited:
                continue
            if grid[ny][nx] not in passable:
                continue

            visited[(nx, ny)] = (x, y)

            if (nx, ny) == goal:
                # Reconstruct path
                path = [(nx, ny)]
                current = (x, y)
                while current is not None:
                    path.append(current)
                    current = visited[current]
                return list(reversed(path))

            queue.append((nx, ny))

    return None


# =============================================================================
# Test
# =============================================================================

if __name__ == "__main__":
    # Quick test
    wfc = BitwiseWFC(width=8, height=8, num_tiles=4)

    # Define simple constraints: all tiles can neighbor each other
    for i in range(4):
        for j in range(4):
            wfc.set_symmetric_constraint(i, j)

    success = wfc.generate()
    print(f"Generation {'succeeded' if success else 'failed'}")
    print(f"Iterations: {wfc.iterations}")

    tile_chars = {0: '.', 1: '#', 2: '~', 3: '*'}
    print(wfc.visualize(tile_chars))
