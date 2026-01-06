# Emergent Adventure: Vision Document

**Date:** 2026-01-06
**Version:** 0.1
**Status:** Design Phase

---

## Executive Summary

A procedural narrative text adventure engine for ZX Spectrum (48K/128K) featuring:
- Bitwise WFC for geography generation
- Backward plot generation using Propp functions
- Living NPCs with ForthoLisp behavior trees
- Self-healing plot system (DRAMA_MANAGER)
- Emergent storytelling through NPC interactions

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                   "EMERGENT ADVENTURE"                          │
│         Procedural Narrative Engine for ZX Spectrum             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐       │
│  │  GEOGRAPHY    │  │    PLOT       │  │     NPC       │       │
│  │  Bitwise WFC  │  │  Backward     │  │  ForthoLisp   │       │
│  │  Regions +    │  │  generation   │  │  Behavior     │       │
│  │  Locations    │  │  + Anchors    │  │  Trees        │       │
│  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘       │
│          │                  │                  │                │
│          └──────────────────┼──────────────────┘                │
│                             │                                   │
│                    ┌────────▼────────┐                          │
│                    │  DRAMA_MANAGER  │                          │
│                    │  Self-healing   │                          │
│                    │  plot           │                          │
│                    └────────┬────────┘                          │
│                             │                                   │
│                    ┌────────▼────────┐                          │
│                    │   INTERFACE     │                          │
│                    │  Parser + Text  │                          │
│                    │  + Prop. font   │                          │
│                    └─────────────────┘                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Subsystems

### GENESIS: Geography Generator

**Technology:** Bitwise Wave Function Collapse (16-bit masks)

```
16 Location Types:
┌────┬─────────────┬──────────────────────────────┐
│ ID │ Type        │ Allowed Neighbors (mask)     │
├────┼─────────────┼──────────────────────────────┤
│ 0  │ FOREST      │ 0b0000000000001111           │
│ 1  │ CLEARING    │ 0b0000000000001111           │
│ 2  │ RIVER       │ 0b0000000000110110           │
│ 3  │ ROAD        │ 0b0000111100001001           │
│ 4  │ MOUNTAIN    │ 0b0000000000110001           │
│ 5  │ CAVE        │ 0b0000000000010001           │
│ 6  │ VILLAGE     │ 0b0000000000001011           │
│ 7  │ CASTLE      │ 0b0000000000001000           │
│ 8  │ SWAMP       │ 0b0000000000000111           │
│ 9  │ RUINS       │ 0b0000000000111111           │
│ 10 │ TOWER       │ 0b0000000000001001           │
│ 11 │ LAKE        │ 0b0000000001000110           │
│ 12 │ BRIDGE      │ 0b0000000000001100           │
│ 13 │ TAVERN      │ 0b0000000001001010           │
│ 14 │ TEMPLE      │ 0b0000000000110001           │
│ 15 │ DUNGEON     │ 0b0000000000100001           │
└────┴─────────────┴──────────────────────────────┘
```

**Key Operations:**
- Collapse: Single AND operation per neighbor
- Entropy: Popcount lookup table (256 bytes)
- Propagation: Stack-based flood fill

### DIRECTOR: Plot Generator

**Technology:** Backward generation using Propp functions

**Structure (24-bit hierarchical):**
```
┌──────────────────────────────────────────────────────────────┐
│                    PLOT NODE (24 bits)                       │
├──────────────┬──────────────┬────────────────────────────────┤
│ BYTE 0       │ BYTE 1       │ BYTE 2                         │
│ FUNC_TYPE    │ REQUIREMENT  │ PROVIDES                       │
│ (Propp)      │ (what needed)│ (what gives)                   │
├──────────────┼──────────────┼────────────────────────────────┤
│ 0: LACK      │ bit 0: HERO  │ bit 0: HAS_WEAPON              │
│ 1: DEPARTURE │ bit 1: WEAPON│ bit 1: HAS_KEY                 │
│ 2: DONOR_TEST│ bit 2: KEY   │ bit 2: HAS_INFO                │
│ 3: ACQUISITION│bit 3: INFO  │ bit 3: ALLY_JOINED             │
│ 4: GUIDANCE  │ bit 4: ALLY  │ bit 4: DOOR_OPEN               │
│ 5: STRUGGLE  │ bit 5: ACCESS│ bit 5: VILLAIN_WEAK            │
│ 6: VICTORY   │ bit 6: VULN  │ bit 6: VILLAIN_DEAD            │
│ 7: RETURN    │ bit 7: BOSS  │ bit 7: QUEST_COMPLETE          │
└──────────────┴──────────────┴────────────────────────────────┘
```

**Algorithm:**
1. Set finale node (VICTORY, TRAGEDY, REVELATION)
2. Track required conditions
3. Work backward, selecting Propp functions that provide requirements
4. Stop when all requirements satisfied

### SOUL: NPC AI Engine

**Technology:** ForthoLisp behavior trees + Markov chains

**NPC Structure (32 bytes):**
```
NPC_STRUCT:
├── PHYSICS (4 bytes)
│   ├── location:        1 byte
│   ├── destination:     1 byte
│   ├── state:           1 byte
│   └── health:          1 byte
├── COMMAND QUEUE (14 bytes)
│   ├── queue_head:      1 byte
│   ├── queue_tail:      1 byte
│   └── queue_data:      12 bytes (4×3)
├── PERSONALITY (8 bytes)
│   ├── behavior_ptr:    2 bytes
│   ├── triggers_ptr:    2 bytes
│   ├── personality:     2 bytes
│   └── relations:       2 bytes
└── MEMORY (6 bytes)
    ├── last_seen_obj:   1 byte
    ├── last_seen_npc:   1 byte
    ├── current_goal:    1 byte
    ├── inventory:       2 bytes
    └── flags:           1 byte
```

**Behavior Tree Execution:**
```
NPC_TICK:
  1. CHECK_INTERRUPTS  → danger? combat mode
  2. EXECUTE_QUEUE     → player commands
  3. CHECK_TRIGGERS    → IF-THEN rules
  4. MARKOV_SAMPLE     → personality-based default
```

### DRAMA_MANAGER: Self-Healing Plot

**Strategies:**
1. **Sticky MacGuffins:** Plot items cannot be destroyed
2. **Role Migration:** Dead NPC's role transfers to backup
3. **Fate Injection:** Critical NPCs survive until destiny fulfilled

```
REPAIR_STRATEGIES:
┌─────────────────────────────────────────────────────────────────┐
│  ISSUE              STRATEGY 1        STRATEGY 2    FALLBACK   │
├─────────────────────────────────────────────────────────────────┤
│  Unreachable        Add bridge/       Teleport      Regenerate │
│  location           tunnel            scroll        region     │
│  NPC dead           Role migration    Spawn ghost   Add diary  │
│  Item locked        Move item         Add key       On corpse  │
│  Quest broken       Insert helper     Lower diff    Skip node  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Generation Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    GENERATION PIPELINE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PHASE 1          PHASE 2          PHASE 3          PHASE 4    │
│  ┌─────────┐     ┌─────────┐      ┌─────────┐      ┌─────────┐ │
│  │GEOGRAPHY│ ──► │  PLOT   │ ──►  │  ROLES  │ ──►  │ HEALING │ │
│  │   WFC   │     │   WFC   │      │   WFC   │      │  CHECK  │ │
│  │ 16-bit  │     │ 24-bit  │      │ 8-bit   │      │         │ │
│  └─────────┘     └─────────┘      └─────────┘      └─────────┘ │
│       │               │                │                │      │
│       ▼               ▼                ▼                ▼      │
│  ┌─────────┐     ┌─────────┐      ┌─────────┐      ┌─────────┐ │
│  │ Matrix  │     │  Graph  │      │   NPC   │      │ Repair  │ │
│  │ → Graph │     │  Nodes  │      │ Assign  │      │   or    │ │
│  │         │     │         │      │         │      │ Regen   │ │
│  └─────────┘     └─────────┘      └─────────┘      └─────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Development Phases

### Phase 0: Python POC (~11 weeks)
- 0.1 Core Bitwise WFC (2 weeks)
- 0.2 Geography WFC (2 weeks)
- 0.3 Plot WFC (3 weeks)
- 0.4 Role WFC (2 weeks)
- 0.5 Healing System (2 weeks)

### Phase 1: Integrated MVP (~8 weeks)
- 1.0 Full Pipeline (3 weeks)
- 1.1 Playable Text Prototype (3 weeks)
- 1.2 LLM Testing Harness (2 weeks)

### Phase 2: Z80 Porting (~12 weeks)
- 2.0 Data Structures (2 weeks)
- 2.1 WFC Core (4 weeks)
- 2.2 Plot Generator (3 weeks)
- 2.3 Healing System (3 weeks)

### Phase 3: Integration (~6 weeks)
- 3.0 Full Generator (4 weeks)
- 3.1 Testing & Tuning (2 weeks)

**Total: ~37 weeks (~9 months)**

---

## Memory Budget (Z80)

```
┌─────────────────────────────────────────────────────────────────┐
│                    MEMORY ALLOCATION (48K)                      │
├─────────────────────────────────────────────────────────────────┤
│  GENERATION (temporary):           576 bytes                   │
│  WORLD STATE (permanent):          384 bytes                   │
│  STATIC DATA:                      288 bytes                   │
│  ──────────────────────────────────────────                    │
│  TOTAL: ~1.2 KB for generation system                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

| Subsystem       | Decision                         | Rationale                |
|-----------------|----------------------------------|--------------------------|
| WFC             | Bitwise masks                    | 16 cycles per propagate  |
| World Structure | Regions → Locations (hierarchical)| Pathfinding O(1)        |
| Plot            | Backward generation + PLOT_NODES | Guarantees completability|
| NPC behavior    | ForthoLisp trees                 | Generatable + compact    |
| NPC execution   | Tokenized VM                     | No text parsing          |
| Emergent + Plot | DRAMA_MANAGER                    | Self-healing plot        |
| Font            | Column mask tables               | 42-57 chars/line         |
| Memory          | 48K base, 128K full              | Banks for content        |

---

## Integration with Storygen Framework

```
STORYGEN + EMERGENT ADVENTURE:

Framework Element      →    Game Implementation
────────────────────────────────────────────────────
Backward generation    →    PLOT_NODES from finale
Propp functions        →    Anchor event types
PipDecks Archetypes    →    NPC personalities
Hero's Journey         →    Quest structure
Storyteller Tactics    →    Drama triggers
Fractality             →    Nested quests
```

---

## Testing Strategy

### LLM Test Harness
- Automated playthrough with GPT-3.5/4
- Supervisor agent with god-view
- Boredom/frustration metrics
- Seed mining for interesting worlds

### Metrics
- Completability: 100% required
- Success rate: >95% generation
- Average gen time: <30s on 3.5MHz
- Memory usage: <2KB during generation

---

## Risks and Mitigations

| Risk                 | Probability | Mitigation                    |
|----------------------|-------------|-------------------------------|
| WFC doesn't converge | Medium      | Backtracking, seed selection  |
| Plot too boring      | High        | More Propp primitives         |
| NPCs act stupid      | Medium      | Tune behavior trees           |
| Memory overflow      | High        | Aggressive optimization, banks|
| Too slow             | Medium      | Precomputation, caching       |

---

## Next Steps

1. **Immediate:** Start POC-0.1 (Core Bitwise WFC in Python)
2. **Week 2:** Validate on 16x16 grids
3. **Week 4:** Integrate with plot generation
4. **Week 8:** First playable prototype

---

*Document generated from brainstorming session 2026-01-06*
