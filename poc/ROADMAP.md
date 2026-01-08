# Emergent Adventure - Roadmap & Vision

## Vision

**Goal:** Procedural narrative text adventure engine that generates complete, coherent story worlds from a 2-byte seed. Target: Z80/ZX Spectrum compatibility (<8KB total).

**Core Philosophy:**
- Emergence over scripting — drama happens from rule interactions, not authored events
- Deterministic generation — same seed = same world, always
- Minimal footprint — every byte counts
- Fractal structure — stories contain stories contain stories

---

## Completed

### Core Systems
- [x] **WFC Geography** (`wfc/wfc.py`) — Wave Function Collapse map generation
- [x] **L-System Plot** (`wfc/lsystem_plot.py`) — Grammar-based narrative expansion
- [x] **Social Physics** (`wfc/social_physics.py`) — Emergent NPC behavior (4 bytes/NPC)
- [x] **Weather System** (`wfc/weather.py`) — Climate, seasons, atmospheric phenomena
- [x] **Advanced Plot** (`wfc/plot_advanced.py`) — Multi-branch plots, twists, false endings

### NPC Mind System
- [x] **ForthLisp VM** (`wfc/npc/forthlisp/`) — Stack-based scripting language
  - [x] Lexer — Tokenization
  - [x] Parser — S-expression AST
  - [x] VM — Bytecode execution with NPC hooks
- [x] **Mind Components** (`wfc/npc/mind/`)
  - [x] Beliefs — Key-value with confidence
  - [x] Desires — Priority queue goals
  - [x] Personality — Big Five + archetypes
  - [x] Memory — Episodic with decay
  - [x] Relationships — Trust/fear/loyalty

### Rendering & Export
- [x] **CFG Renderer** (`wfc/cfg_renderer.py`) — Propp functions → prose
- [x] **Z80 Compiler** (`wfc/z80_compiler.py`) — Binary export format
- [x] **Visualizer** (`visualizer.py`) — Streamlit interactive UI

### Documentation
- [x] **README.md** — Architecture overview
- [x] **Inline docstrings** — All modules documented

---

## In Progress / Pending

### Integration Tasks
- [ ] **L-System ↔ Social Physics bridge**
  - When L-System generates `'T'` (TWIST), trigger `reveal_hidden_role()` in Social Physics
  - Connect plot beats to NPC situation triggers
  - Example: `RECOGNITION` Propp function → `Situation.TRUTH_REVEALED`

- [ ] **NPC ↔ Engine integration**
  - Add NPC commands to `engine.py`: `talk`, `suggest`, `convince`, `persuade`, `command`
  - NPC placement on geography (spawn points from WFC)
  - Autonomous NPC actions each turn

### Missing Components
- [ ] **Save/Load system**
  - Serialize WorldState to binary
  - Resume from save (deterministic replay possible)
  - Save slots (multiple worlds)

- [ ] **CFG ↔ ForthLisp integration**
  - NPC dialogue generated from CFG templates
  - ForthLisp scripts can invoke CFG renderer
  - Dynamic text based on NPC beliefs/mood

- [ ] **Sound/Music hooks**
  - Mood → music track mapping
  - Weather → ambient sound
  - Z80 beeper patterns for events

---

## Future / Wishlist

### Short Term
- [ ] **Multi-language support**
  - Template localization (EN, RU, etc.)
  - String table per language
  - Genre-appropriate vocabulary per language

- [ ] **Quest system**
  - Generated from L-System QUEST nodes
  - Objectives tied to geography locations
  - NPC involvement (fetch quests, escort, etc.)

- [ ] **Inventory system**
  - Items from ACQUISITION Propp function
  - Item effects on NPC interactions
  - Z80: 1 byte per item slot

### Medium Term
- [ ] **Combat system**
  - Simple stat-based resolution
  - NPC traits affect combat (BRAVE, COWARD)
  - Tied to STRUGGLE Propp function

- [ ] **Dialogue trees**
  - Generated from NPC beliefs + CFG
  - Player choices affect trust/relationships
  - ForthLisp conditions for dialogue branches

- [ ] **Time system**
  - Day/night cycle affects events
  - NPC schedules (location changes)
  - Seasonal events

### Long Term
- [ ] **Actual Z80 port**
  - Assembly implementation of core systems
  - ZX Spectrum Next target (expanded memory)
  - Classic 48K version (compressed)

- [ ] **Multiplayer seeds**
  - Share seed = share world
  - Competitive scoring (treasure found, quests completed)
  - Async play comparison

- [ ] **Mod system**
  - Custom grammars (L-System rules)
  - Custom NPC archetypes
  - Custom CFG templates

---

## Technical Debt

- [ ] Fix pronoun handling in CFG renderer (edge cases)
- [ ] Optimize string table compression
- [ ] Add unit tests for all modules
- [ ] Benchmark memory usage
- [ ] Profile Z80 compiler output size

---

## Architecture Notes

### Data Flow
```
┌─────────┐
│  Seed   │ (2 bytes)
└────┬────┘
     │
     ▼
┌─────────────────────────────────────────────┐
│              GENERATION PHASE               │
├─────────────┬─────────────┬─────────────────┤
│  L-System   │    WFC      │  Social Physics │
│  (Plot)     │  (Map)      │  (NPCs)         │
└──────┬──────┴──────┬──────┴────────┬────────┘
       │             │               │
       ▼             ▼               ▼
┌─────────────────────────────────────────────┐
│              WORLD STATE                    │
│  - Plot nodes (5 bytes each)                │
│  - Geography (1 byte/tile)                  │
│  - NPCs (4 bytes each)                      │
│  - Weather (4 bytes)                        │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│              RUNTIME PHASE                  │
├─────────────┬─────────────┬─────────────────┤
│  Engine     │  ForthLisp  │  CFG Renderer   │
│  (Commands) │  (NPC AI)   │  (Text Output)  │
└─────────────┴─────────────┴─────────────────┘
```

### Memory Budget (Z80 Target)
```
Component        Typical    Max
─────────────────────────────────
Header           16         16
Geography        1536       2048    (48x32 to 64x32)
Plot             120        200     (24-40 nodes)
NPCs             48         96      (8-16 NPCs × 6 bytes)
Weather          4          4
Strings          256        512
Templates        128        256
─────────────────────────────────
TOTAL            ~2KB       ~3KB

Remaining for code: 5-6KB (in 8KB target)
```

### Key Design Decisions

1. **Why L-Systems for plot?**
   - Deterministic from seed
   - Fractal (self-similar at all scales)
   - Compact (rules ~100 bytes, expand to 100+ nodes)
   - Genre-modifiable weights

2. **Why Social Physics?**
   - Emergent > scripted (unpredictable drama)
   - Trait flags = 1 byte (8 personality dimensions)
   - Rules are data (can add/modify without code changes)
   - Dwarf Fortress proven this works

3. **Why ForthLisp?**
   - Stack-based = minimal overhead
   - Homoiconic = code is data
   - Fits Z80 architecture (no heap needed)
   - Can compile to actual Z80 asm

4. **Why CFG for text?**
   - Templates are compact
   - Slot-filling is fast
   - Mood modifiers are simple word replacement
   - Genre variants share structure

---

## References & Inspiration

- **Dwarf Fortress** — Emergent stories from simulation
- **Caves of Qud** — Procedural history and mythology
- **AI Dungeon** — Dynamic narrative (but we're deterministic)
- **The Hobbit (1982)** — Z80 text adventure with NPC AI
- **Propp's Morphology** — Folktale structure theory
- **L-Systems** — Lindenmayer's biological modeling
- **WFC** — Gumin's Wave Function Collapse

---

## Contact & Contributing

Repository: https://github.com/oisee/emergent-adventure

For questions, issues, or contributions, open a GitHub issue.
