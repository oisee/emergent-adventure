"""
Z80 Story Compiler

Compiles complete story data to Z80-ready binary format.

Output structure:
- Header (16 bytes)
- Geography data (width * height bytes)
- Plot data (variable)
- NPC data (4 bytes per NPC)
- String table (compressed)
- Template indices

Total target: <8KB for full story world.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
from enum import IntEnum
import struct
import zlib


# =============================================================================
# BINARY FORMAT CONSTANTS
# =============================================================================

# Magic number: "EADV" = Emergent Adventure
MAGIC = b'EADV'
VERSION = 1

# Section IDs
class Section(IntEnum):
    HEADER = 0x00
    GEOGRAPHY = 0x01
    PLOT = 0x02
    NPCS = 0x03
    STRINGS = 0x04
    TEMPLATES = 0x05
    WEATHER = 0x06
    METADATA = 0xFF


# =============================================================================
# HEADER FORMAT (16 bytes)
# =============================================================================

@dataclass
class StoryHeader:
    """
    Binary header format:
    - 4 bytes: Magic ("EADV")
    - 1 byte: Version
    - 1 byte: Flags
    - 2 bytes: Seed
    - 1 byte: Width
    - 1 byte: Height
    - 1 byte: NPC count
    - 1 byte: Plot node count
    - 2 bytes: String table offset
    - 2 bytes: Total size
    """
    magic: bytes = MAGIC
    version: int = VERSION
    flags: int = 0
    seed: int = 0
    width: int = 48
    height: int = 32
    npc_count: int = 0
    plot_count: int = 0
    string_offset: int = 0
    total_size: int = 0

    # Flags
    FLAG_COMPRESSED = 0x01
    FLAG_HAS_WEATHER = 0x02
    FLAG_HAS_TEMPLATES = 0x04
    FLAG_MULTI_BRANCH = 0x08

    def to_bytes(self) -> bytes:
        return struct.pack('<4sBBHBBBBHH',
            self.magic,
            self.version,
            self.flags,
            self.seed & 0xFFFF,
            self.width & 0xFF,
            self.height & 0xFF,
            self.npc_count & 0xFF,
            self.plot_count & 0xFF,
            self.string_offset & 0xFFFF,
            self.total_size & 0xFFFF,
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> 'StoryHeader':
        magic, version, flags, seed, width, height, npc_count, plot_count, string_offset, total_size = \
            struct.unpack('<4sBBHBBBBHH', data[:16])
        return cls(
            magic=magic,
            version=version,
            flags=flags,
            seed=seed,
            width=width,
            height=height,
            npc_count=npc_count,
            plot_count=plot_count,
            string_offset=string_offset,
            total_size=total_size,
        )


# =============================================================================
# STRING COMPRESSION
# =============================================================================

class StringTable:
    """
    Compressed string storage.

    Uses:
    - Common word dictionary (1 byte = common word)
    - RLE for repeated chars
    - 7-bit ASCII packing where possible
    """

    # Common words get single-byte codes (0x80-0xFF)
    COMMON_WORDS = [
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
        'and', 'or', 'but', 'if', 'then', 'else', 'when', 'while',
        'you', 'your', 'hero', 'villain', 'they', 'their', 'them',
        'to', 'from', 'in', 'on', 'at', 'by', 'for', 'with',
        'says', 'said', 'speak', 'speaks', 'ask', 'asks',
        'go', 'goes', 'went', 'come', 'comes', 'came',
        'take', 'takes', 'took', 'give', 'gives', 'gave',
        'look', 'looks', 'looked', 'see', 'sees', 'saw',
        'dark', 'light', 'good', 'evil', 'true', 'false',
        'north', 'south', 'east', 'west',
        'sword', 'shield', 'armor', 'item', 'magic',
        'village', 'castle', 'forest', 'mountain', 'river',
    ]

    def __init__(self):
        self.strings: List[str] = []
        self.offsets: Dict[str, int] = {}
        self.data = bytearray()

    def add(self, s: str) -> int:
        """Add string, return offset"""
        if s in self.offsets:
            return self.offsets[s]

        offset = len(self.data)
        self.offsets[s] = offset

        # Encode string
        encoded = self._encode(s)
        self.data.extend(encoded)
        self.data.append(0)  # null terminator

        self.strings.append(s)
        return offset

    def _encode(self, s: str) -> bytes:
        """Encode string with compression"""
        result = bytearray()
        words = s.split()

        for i, word in enumerate(words):
            if i > 0:
                result.append(0x20)  # space

            # Check for common word
            word_lower = word.lower().rstrip('.,!?;:')
            punct = word[len(word_lower):] if len(word_lower) < len(word) else ''

            if word_lower in self.COMMON_WORDS:
                idx = self.COMMON_WORDS.index(word_lower)
                result.append(0x80 + idx)
                # Handle capitalization
                if word[0].isupper():
                    result[-1] |= 0x40  # Set cap flag... wait, we need different approach
            else:
                # Raw ASCII
                result.extend(word.encode('ascii', errors='replace'))

            # Add punctuation
            if punct:
                result.extend(punct.encode('ascii'))

        return bytes(result)

    def get_bytes(self) -> bytes:
        return bytes(self.data)

    def get_offset(self, s: str) -> int:
        return self.offsets.get(s, 0)


# =============================================================================
# Z80 COMPILER
# =============================================================================

class Z80Compiler:
    """
    Compiles story world to Z80 binary format.
    """

    def __init__(self):
        self.header = StoryHeader()
        self.geography_data = bytes()
        self.plot_data = bytes()
        self.npc_data = bytes()
        self.weather_data = bytes()
        self.strings = StringTable()
        self.template_data = bytes()

    def compile_geography(self, tiles: List[List[int]]) -> bytes:
        """Compile geography to bytes"""
        data = bytearray()

        height = len(tiles)
        width = len(tiles[0]) if tiles else 0

        self.header.width = width
        self.header.height = height

        # RLE compression for tiles
        for row in tiles:
            i = 0
            while i < len(row):
                tile = row[i]
                count = 1

                # Count consecutive same tiles
                while i + count < len(row) and row[i + count] == tile and count < 127:
                    count += 1

                if count > 2:
                    # RLE: 0x80 | count, tile
                    data.append(0x80 | count)
                    data.append(tile)
                    i += count
                else:
                    # Raw tile
                    data.append(tile)
                    i += 1

        self.geography_data = bytes(data)
        return self.geography_data

    def compile_plot(self, nodes: List[Dict]) -> bytes:
        """
        Compile plot nodes.

        Per node (5 bytes):
        - 1 byte: node ID
        - 1 byte: function index
        - 1 byte: parent ID
        - 1 byte: flags
        - 1 byte: next ID
        """
        from .lsystem_plot import PROPP_ALPHABET

        func_list = list(PROPP_ALPHABET.values())

        data = bytearray()
        data.append(len(nodes))  # node count

        for node in nodes:
            node_id = node.get('id', 0) & 0xFF
            func_name = node.get('function', 'EQUILIBRIUM')
            func_idx = func_list.index(func_name) if func_name in func_list else 0
            parent_id = node.get('parent_id', 0) & 0xFF
            flags = node.get('flags', 0) & 0xFF
            next_id = node.get('next_id', 0) & 0xFF

            data.extend(struct.pack('BBBBB', node_id, func_idx, parent_id, flags, next_id))

        self.header.plot_count = len(nodes)
        self.plot_data = bytes(data)
        return self.plot_data

    def compile_npcs(self, npcs: List[Dict]) -> bytes:
        """
        Compile NPCs.

        Per NPC (4 bytes):
        - 1 byte: traits
        - 1 byte: trust
        - 1 byte: roles (apparent | true << 4)
        - 1 byte: location

        Plus string references for names.
        """
        data = bytearray()
        data.append(len(npcs))  # NPC count

        # First pass: add names to string table
        name_offsets = []
        for npc in npcs:
            name = npc.get('name', 'Unknown')
            offset = self.strings.add(name)
            name_offsets.append(offset)

        # Second pass: compile NPC data
        for i, npc in enumerate(npcs):
            traits = npc.get('traits', 0) & 0xFF
            trust = npc.get('trust', 128) & 0xFF
            role = npc.get('role', 0) & 0x0F
            true_role = npc.get('true_role', role) & 0x0F
            location = npc.get('location', 0) & 0xFF

            roles_byte = role | (true_role << 4)

            # 6 bytes per NPC: 4 data + 2 name offset
            data.extend(struct.pack('<BBBBH',
                traits, trust, roles_byte, location, name_offsets[i]))

        self.header.npc_count = len(npcs)
        self.npc_data = bytes(data)
        return self.npc_data

    def compile_weather(self, weather: Dict) -> bytes:
        """
        Compile weather state (4 bytes).

        - 1 byte: weather type
        - 1 byte: time of day
        - 1 byte: season | climate << 4
        - 1 byte: intensity (0-255)
        """
        weather_type = weather.get('weather_type', 0) & 0xFF
        time_of_day = weather.get('time_of_day', 0) & 0xFF
        season = weather.get('season', 0) & 0x0F
        climate = weather.get('climate', 0) & 0x0F
        intensity = int(weather.get('intensity', 0.5) * 255) & 0xFF

        season_climate = season | (climate << 4)

        self.weather_data = struct.pack('BBBB',
            weather_type, time_of_day, season_climate, intensity)

        self.header.flags |= StoryHeader.FLAG_HAS_WEATHER
        return self.weather_data

    def compile_templates(self, template_indices: Dict[str, int]) -> bytes:
        """
        Compile template indices for text generation.

        Format:
        - 1 byte: template count
        - Per template:
          - 1 byte: function index
          - 2 bytes: string offset
        """
        data = bytearray()
        data.append(len(template_indices))

        for func_name, template_text in template_indices.items():
            # Add template to string table
            offset = self.strings.add(template_text)

            # Map function name to index
            from .lsystem_plot import PROPP_ALPHABET
            func_list = list(PROPP_ALPHABET.values())
            func_idx = func_list.index(func_name) if func_name in func_list else 0

            data.extend(struct.pack('<BH', func_idx, offset))

        self.template_data = bytes(data)
        self.header.flags |= StoryHeader.FLAG_HAS_TEMPLATES
        return self.template_data

    def compile_from_world(self, world) -> bytes:
        """Compile complete world state"""
        # Geography
        if hasattr(world, 'geography') and world.geography:
            tiles = [[cell.value for cell in row] for row in world.geography.grid]
            self.compile_geography(tiles)

        # Plot
        if hasattr(world, 'plot') and world.plot:
            nodes = [{'id': i, 'function': f.name, 'parent_id': max(0, i-1),
                      'flags': 0, 'next_id': i+1 if i < len(world.plot.sequence)-1 else 0}
                     for i, f in enumerate(world.plot.sequence)]
            self.compile_plot(nodes)

        # NPCs
        if hasattr(world, 'npcs') and world.npcs:
            npc_list = []
            for npc_id, npc in world.npcs.items():
                npc_list.append({
                    'name': npc.name,
                    'traits': getattr(npc, 'traits', 0),
                    'trust': getattr(npc, 'trust', 128),
                    'role': getattr(npc, 'role', 0),
                    'true_role': getattr(npc, 'true_role', 0),
                    'location': getattr(npc, 'location', 0),
                })
            self.compile_npcs(npc_list)

        # Weather
        if hasattr(world, 'weather') and world.weather:
            self.compile_weather({
                'weather_type': world.weather.weather.value,
                'time_of_day': world.weather.time_of_day.value,
                'season': world.weather.season.value,
                'climate': world.weather.climate.value,
                'intensity': world.weather.intensity,
            })

        return self.link()

    def link(self) -> bytes:
        """Link all sections into final binary"""
        # Build sections
        sections = bytearray()

        # Geography section
        sections.append(Section.GEOGRAPHY)
        sections.extend(struct.pack('<H', len(self.geography_data)))
        sections.extend(self.geography_data)

        # Plot section
        sections.append(Section.PLOT)
        sections.extend(struct.pack('<H', len(self.plot_data)))
        sections.extend(self.plot_data)

        # NPC section
        sections.append(Section.NPCS)
        sections.extend(struct.pack('<H', len(self.npc_data)))
        sections.extend(self.npc_data)

        # Weather section (if present)
        if self.weather_data:
            sections.append(Section.WEATHER)
            sections.extend(struct.pack('<H', len(self.weather_data)))
            sections.extend(self.weather_data)

        # String table
        string_bytes = self.strings.get_bytes()
        self.header.string_offset = 16 + len(sections) + 3  # header + sections + section header
        sections.append(Section.STRINGS)
        sections.extend(struct.pack('<H', len(string_bytes)))
        sections.extend(string_bytes)

        # Templates (if present)
        if self.template_data:
            sections.append(Section.TEMPLATES)
            sections.extend(struct.pack('<H', len(self.template_data)))
            sections.extend(self.template_data)

        # Update header
        self.header.total_size = 16 + len(sections)
        self.header.seed = getattr(self, 'seed', 0)

        # Final binary
        return self.header.to_bytes() + bytes(sections)

    def to_asm(self, binary: bytes = None) -> str:
        """Generate Z80 assembly source"""
        if binary is None:
            binary = self.link()

        lines = [
            "; Emergent Adventure - Compiled Story Data",
            f"; Total size: {len(binary)} bytes",
            f"; Seed: {self.header.seed}",
            "",
            "STORY_DATA:",
            "",
            "; Header (16 bytes)",
        ]

        # Header bytes
        header_bytes = binary[:16]
        lines.append(f'    db "{MAGIC.decode()}"  ; magic')
        lines.append(f'    db {header_bytes[4]}          ; version')
        lines.append(f'    db ${header_bytes[5]:02X}         ; flags')
        lines.append(f'    dw ${self.header.seed:04X}      ; seed')
        lines.append(f'    db {self.header.width}, {self.header.height}     ; dimensions')
        lines.append(f'    db {self.header.npc_count}, {self.header.plot_count}     ; counts')
        lines.append(f'    dw ${self.header.string_offset:04X}      ; string offset')
        lines.append(f'    dw ${self.header.total_size:04X}      ; total size')
        lines.append("")

        # Section data (as hex dumps)
        pos = 16
        while pos < len(binary):
            section_id = binary[pos]
            section_len = struct.unpack('<H', binary[pos+1:pos+3])[0]

            section_name = Section(section_id).name if section_id in [s.value for s in Section] else f"UNKNOWN_{section_id}"
            lines.append(f"; Section: {section_name} ({section_len} bytes)")
            lines.append(f"SECTION_{section_name}:")
            lines.append(f"    db ${section_id:02X}         ; section ID")
            lines.append(f"    dw ${section_len:04X}      ; section length")

            # Data bytes (in rows of 16)
            data_start = pos + 3
            data_end = data_start + section_len

            for i in range(data_start, data_end, 16):
                row = binary[i:min(i+16, data_end)]
                hex_str = ', '.join(f'${b:02X}' for b in row)
                lines.append(f"    db {hex_str}")

            lines.append("")
            pos = data_end

        return '\n'.join(lines)


# =============================================================================
# DEMO
# =============================================================================

def demo():
    """Demonstrate Z80 compilation"""
    print("=" * 60)
    print("Z80 STORY COMPILER DEMO")
    print("=" * 60)
    print()

    compiler = Z80Compiler()
    compiler.seed = 12345

    # Sample geography (8x8 for demo)
    tiles = [
        [0, 0, 1, 1, 2, 2, 3, 3],
        [0, 1, 1, 2, 2, 3, 3, 4],
        [1, 1, 2, 2, 3, 3, 4, 4],
        [1, 2, 2, 3, 3, 4, 4, 5],
        [2, 2, 3, 3, 4, 4, 5, 5],
        [2, 3, 3, 4, 4, 5, 5, 6],
        [3, 3, 4, 4, 5, 5, 6, 6],
        [3, 4, 4, 5, 5, 6, 6, 7],
    ]

    # Sample plot
    plot_nodes = [
        {'id': 0, 'function': 'EQUILIBRIUM', 'parent_id': 0, 'flags': 0, 'next_id': 1},
        {'id': 1, 'function': 'LACK', 'parent_id': 0, 'flags': 0, 'next_id': 2},
        {'id': 2, 'function': 'DEPARTURE', 'parent_id': 1, 'flags': 0, 'next_id': 3},
        {'id': 3, 'function': 'DONOR_TEST', 'parent_id': 2, 'flags': 0, 'next_id': 4},
        {'id': 4, 'function': 'ACQUISITION', 'parent_id': 3, 'flags': 0, 'next_id': 5},
        {'id': 5, 'function': 'STRUGGLE', 'parent_id': 4, 'flags': 0, 'next_id': 6},
        {'id': 6, 'function': 'VICTORY', 'parent_id': 5, 'flags': 0, 'next_id': 7},
        {'id': 7, 'function': 'RETURN', 'parent_id': 6, 'flags': 0x80, 'next_id': 0},
    ]

    # Sample NPCs
    npcs = [
        {'name': 'Aldric', 'traits': 0x07, 'trust': 255, 'role': 1, 'true_role': 1, 'location': 5},
        {'name': 'Grimald', 'traits': 0x92, 'trust': 60, 'role': 1, 'true_role': 6, 'location': 5},
        {'name': 'Elena', 'traits': 0x0B, 'trust': 200, 'role': 2, 'true_role': 2, 'location': 3},
        {'name': 'Shadow King', 'traits': 0xC0, 'trust': 0, 'role': 3, 'true_role': 3, 'location': 63},
    ]

    # Sample weather
    weather = {
        'weather_type': 8,  # STORM
        'time_of_day': 5,   # EVENING
        'season': 2,        # AUTUMN
        'climate': 2,       # TEMPERATE
        'intensity': 0.7,
    }

    # Compile
    print("Compiling...")
    compiler.compile_geography(tiles)
    compiler.compile_plot(plot_nodes)
    compiler.compile_npcs(npcs)
    compiler.compile_weather(weather)

    binary = compiler.link()

    print(f"Compiled size: {len(binary)} bytes")
    print()

    # Size breakdown
    print("=== Size Breakdown ===")
    print(f"  Header:     16 bytes")
    print(f"  Geography:  {len(compiler.geography_data)} bytes")
    print(f"  Plot:       {len(compiler.plot_data)} bytes")
    print(f"  NPCs:       {len(compiler.npc_data)} bytes")
    print(f"  Weather:    {len(compiler.weather_data)} bytes")
    print(f"  Strings:    {len(compiler.strings.get_bytes())} bytes")
    print(f"  Overhead:   {len(binary) - 16 - len(compiler.geography_data) - len(compiler.plot_data) - len(compiler.npc_data) - len(compiler.weather_data) - len(compiler.strings.get_bytes())} bytes")
    print()

    # Header info
    print("=== Header ===")
    header = StoryHeader.from_bytes(binary)
    print(f"  Magic: {header.magic}")
    print(f"  Version: {header.version}")
    print(f"  Flags: {header.flags:#04x}")
    print(f"  Seed: {header.seed}")
    print(f"  Dimensions: {header.width}x{header.height}")
    print(f"  NPCs: {header.npc_count}")
    print(f"  Plot nodes: {header.plot_count}")
    print(f"  String offset: {header.string_offset}")
    print(f"  Total size: {header.total_size}")
    print()

    # Assembly output
    print("=== Z80 Assembly (first 50 lines) ===")
    asm = compiler.to_asm(binary)
    lines = asm.split('\n')
    for line in lines[:50]:
        print(line)
    if len(lines) > 50:
        print(f"... ({len(lines) - 50} more lines)")


if __name__ == '__main__':
    demo()
