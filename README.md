# Emergent Adventure

Procedural narrative text adventure engine for ZX Spectrum-style games.

## Features

- **Bitwise WFC Geography** - 16-bit Wave Function Collapse for terrain generation
- **Backward Plot Generation** - Propp functions with requirement/provides system
- **Guaranteed Completability** - All generated worlds are winnable
- **Lords of Midnight Visualization** - First-person landscape ASCII renderer
- **Text Adventure Engine** - Playable exploration with quest progression

## Quick Start

```bash
cd poc

# Terminal game
python -m wfc.engine 42

# Streamlit visualizer + game
pip install streamlit
streamlit run visualizer.py
```

## Architecture

```
poc/wfc/
├── core.py          # Bitwise WFC engine (16-bit masks, popcount LUT)
├── geography.py     # 16-tile terrain generator with constraints
├── plot.py          # Backward Propp plot generator (8 functions)
├── integration.py   # Plot-geography binding + verification
├── engine.py        # Text adventure engine + command parser
├── landscape.py     # Lords of Midnight-style renderer
└── test_harness.py  # Batch testing (100% success rate)
```

## Generation Pipeline

```
1. PLOT (backward)     →  2. GEOGRAPHY (WFC)  →  3. VERIFY
   [VICTORY]                 Place anchors         Reachability
   ↓ requires                Run collapse          Completability
   [STRUGGLE]                Propagate
   ↓ requires
   [ACQUISITION]
   ↓ requires
   [DEPARTURE]
   ↓ requires
   [LACK]
```

## Game Commands

```
Movement:  n/s/e/w, north/south/east/west
Turning:   left, right
View:      look (text), view (landscape), map
Actions:   do/interact, inventory, quest
System:    help, quit
```

## Technical Details

### WFC Engine
- 16-bit constraint masks per tile type
- Popcount via 256-byte lookup table
- Stack-based propagation (Z80-friendly)
- ~19ms average generation time

### Plot System
- 8 Propp functions (LACK → RETURN)
- 8-bit requirement/provides bitmasks
- DAG structure with topological ordering
- Non-linear paths allowed

### Test Results
```
Success rate:     100%
Completability:   100%
Avg generation:   19ms
Avg plot nodes:   6.5
```

## Inspired By

- **The Hobbit** (1982) - Melbourne House NPC system
- **Lords of Midnight** (1984) - Mike Singleton's landscaping
- **Vladimir Propp** - Morphology of the Folktale
- **Wave Function Collapse** - Maxim Gumin

## License

MIT
