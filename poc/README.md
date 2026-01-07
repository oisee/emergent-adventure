# Emergent Adventure

Procedural narrative text adventure engine with Z80-compatible generation.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         GENERATION                               │
├───────────────┬──────────────────┬──────────────────────────────┤
│   L-System    │  Social Physics  │       WFC Geography          │
│  Plot Engine  │   NPC Engine     │        Generator             │
│               │                  │                              │
│  Seed → Plot  │  Traits → Drama  │  Constraints → Map           │
│  (100 bytes)  │   (4 bytes/NPC)  │    (1 byte/tile)             │
└───────┬───────┴────────┬─────────┴──────────────┬───────────────┘
        │                │                        │
        ▼                ▼                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                      INTEGRATION LAYER                          │
│                                                                 │
│  WorldState = Geography + Plot + NPCs + Weather + Time          │
│  StoryGenerator orchestrates all systems                        │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                        RENDERING                                │
├─────────────────┬───────────────────┬───────────────────────────┤
│  CFG Text       │   ForthLisp VM    │     Visualizer            │
│  Renderer       │   (NPC Scripts)   │     (Streamlit)           │
│                 │                   │                           │
│  Template →     │   Bytecode →      │   Graph + Map + Cast      │
│  Natural Text   │   NPC Response    │   Interactive UI          │
└─────────────────┴───────────────────┴───────────────────────────┘
```

## Core Systems

### 1. L-System Plot Generator (`wfc/lsystem_plot.py`)

Generates fractal narrative structures from a 2-byte seed.

```python
# Grammar-based expansion
S → ACE (3-act structure) | AACE (4-arc saga) | ATCE (with twist)
A → CQC | QCQ | CCQ    # Arcs contain chapters
C → QQ | dga | lds     # Chapters contain quests/beats
Q → dgt | tas | sw     # Quests are Propp function sequences

# Propp function alphabet (terminals)
e=EQUILIBRIUM  l=LACK       i=INTERDICTION  v=VIOLATION
d=DEPARTURE    t=DONOR_TEST a=ACQUISITION   g=GUIDANCE
s=STRUGGLE     b=BRANDING   w=VICTORY       p=PURSUIT
r=RESCUE       n=RECOGNITION u=PUNISHMENT   h=RETURN
```

**Usage:**
```python
from wfc.lsystem_plot import LSystemPlotGenerator

gen = LSystemPlotGenerator(seed=12345, genre='dark_fantasy')
nodes = gen.generate()
print(gen.to_asm())  # Z80 assembly output
```

**Output:** ~100 bytes → 20+ plot nodes deterministically.

### 2. Social Physics NPC Engine (`wfc/social_physics.py`)

Emergent NPC behavior through trait interactions (Dwarf Fortress style).

```python
# NPC structure (4 bytes)
class NPC:
    traits: Trait      # 1 byte (8 flags)
    trust: int         # 1 byte (0-255)
    role: Role         # 4 bits apparent + 4 bits true
    location: int      # 1 byte

# Trait flags
HONEST=0x01  LOYAL=0x02  BRAVE=0x04  KIND=0x08
GREEDY=0x10  COWARD=0x20 VENGEFUL=0x40 AMBITIOUS=0x80

# Emergent drama rules
IF GREEDY + TREASURE_FOUND + trust<80 → ATTEMPT_STEAL
IF VENGEFUL + high_grudge → PLOT_REVENGE
IF HONEST + TRUTH_REVEALED → REVEAL_TRUE_SELF
```

**Usage:**
```python
from wfc.social_physics import SocialPhysicsEngine, Situation

engine = SocialPhysicsEngine(seed=42)
engine.create_npc(1, "Grimbold", role=Role.HELPER, hidden_role=Role.HIDDEN_VILLAIN)
reactions = engine.trigger_situation(Situation.TREASURE_FOUND)
# → [("Grimbold", "ATTEMPT_STEAL")]
```

### 3. ForthLisp NPC Mind (`wfc/npc/`)

Stack-based scripting language for NPC beliefs, desires, and relationships.

```forthlisp
; NPC behavior script
(belief "hero-is-trustworthy" 0.8)
(desire "protect-village" 0.9)

hero trust@ 0.5 > if
    "I'll help you" say
else
    "Prove yourself first" say
then

"helped-me" remembered? if
    hero trust@ 0.2 + hero trust!
then
```

**Components:**
- `forthlisp/lexer.py` - Tokenizer
- `forthlisp/parser.py` - S-expression parser
- `forthlisp/vm.py` - Stack-based bytecode VM
- `mind/beliefs.py` - Belief system (key, value, confidence, source)
- `mind/desires.py` - Goal priority queue
- `mind/personality.py` - Big Five + archetypes
- `mind/memory.py` - Episodic memory with decay
- `mind/relationships.py` - Trust/fear/loyalty tracking

### 4. Weather System (`wfc/weather.py`)

Atmospheric simulation with mood integration.

```python
# Components
- TimeOfDay: DAWN → MORNING → NOON → ... → MIDNIGHT
- Season: SPRING | SUMMER | AUTUMN | WINTER
- ClimateZone: TROPICAL → ARCTIC (based on latitude)
- WeatherType: 20 types (CLEAR, FOG, THUNDERSTORM, BLIZZARD...)
- AtmosphericPhenomenon: Rare events (AURORA, ECLIPSE, RAINBOW...)

# Genre preferences
dark_fantasy → FOG, OVERCAST, STORM
cozy → SNOW, DRIZZLE, RAIN (inside!)
solarpunk → CLEAR, sunshine
```

### 5. WFC Geography (`wfc/wfc.py`)

Wave Function Collapse for coherent map generation.

```python
# Tile types with adjacency rules
VOID < OCEAN < COAST < PLAINS < FOREST < HILLS < MOUNTAINS

# Genre modifiers affect tile probabilities
dark_fantasy → more SWAMP, RUINS
solarpunk → more PLAINS, FOREST
```

## Integration

The `StoryGenerator` class (`wfc/integration.py`) combines all systems:

```python
from wfc.integration import StoryGenerator

gen = StoryGenerator(
    seed=42,
    width=48, height=32,
    genre="dark_fantasy",
    plot_type=PlotType.MULTI_BRANCH
)
gen.generate()

# Access components
gen.world.geography      # WFC map
gen.world.plot          # Basic plot (8 Propp functions)
gen.world.advanced_plot # Full plot (16 functions, twists)
gen.world.weather       # Current weather state
gen.world.npcs          # NPC mind dictionary
```

## Visualizer

Interactive Streamlit app (`visualizer.py`):

```bash
streamlit run visualizer.py
```

**Features:**
- Seed control with generation
- Genre and PlotType selectors
- WFC map visualization
- Plot structure graph
- Cast panel with NPC stats
- Weather display
- Z80 byte export

## Z80 Compatibility

All systems designed for Z80 assembly output:

| System | Bytes | Structure |
|--------|-------|-----------|
| Plot node | 5 | id, func, parent, flags, next |
| NPC | 4 | traits, trust, roles, location |
| Weather | 4 | type, time, season, climate |
| Map tile | 1 | terrain type (0-15) |

**Example Z80 output:**
```asm
; L-System Generated Plot
; Seed: 12345, Genre: dark_fantasy
PLOT_DATA:
    db 24           ; node count
    dw 12345        ; seed
    ; Node 0: DEPARTURE
    db 0, 4, 0, 0, 1
    ; Node 1: GUIDANCE
    db 1, 7, 0, 0, 2
    ...
```

## File Structure

```
poc/
├── visualizer.py          # Streamlit UI
├── wfc/
│   ├── wfc.py             # Wave Function Collapse
│   ├── engine.py          # Game engine
│   ├── integration.py     # System orchestration
│   ├── lsystem_plot.py    # L-System plot generator
│   ├── social_physics.py  # Emergent NPC behavior
│   ├── weather.py         # Atmospheric system
│   ├── plot_advanced.py   # Multi-branch plots
│   ├── plot_fractal.py    # Fractal narrative
│   └── npc/
│       ├── forthlisp/     # Scripting VM
│       │   ├── lexer.py
│       │   ├── parser.py
│       │   └── vm.py
│       ├── mind/          # NPC psychology
│       │   ├── beliefs.py
│       │   ├── desires.py
│       │   ├── personality.py
│       │   ├── memory.py
│       │   └── relationships.py
│       └── nlp/           # Command processing
│           ├── commands.py
│           └── processing.py
```

## Design Principles

1. **Deterministic** - Same seed always produces same output
2. **Compact** - Minimal bytes per structure (Z80 target)
3. **Emergent** - Complex behavior from simple rules
4. **Modular** - Each system works independently
5. **Genre-aware** - All systems respond to genre parameters

## Running Tests

```bash
# Individual modules
python -m wfc.lsystem_plot
python -m wfc.social_physics
python -m wfc.npc.forthlisp.vm

# Full demo
python -c "from wfc.integration import demo; demo()"
```

## TODO

- [x] CFG text renderer for natural language output (`wfc/cfg_renderer.py`)
- [x] Z80 story compiler (full binary export) (`wfc/z80_compiler.py`)
- [ ] L-System ↔ Social Physics integration (TWIST triggers role reveal)
- [ ] Save/load game state
- [ ] Multi-language support
