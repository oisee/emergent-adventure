# WFC Mask Width Analysis for Plot Generation

**Date:** 2026-01-06
**Status:** Design Analysis
**Question:** Should we use wider WFC masks (32/64-bit) for plot to accommodate full Propp (31 functions) and more roles?

---

## Current Design Summary

```
GEOGRAPHY WFC:  16-bit masks → 16 tile types
PLOT WFC:       24-bit hierarchical → 8 functions × 8 requirements × 8 provides
ROLE WFC:       8-bit masks → 8 archetypes
```

---

## The Core Question

Propp defines **31 functions** and **7 dramatis personae**. Our current design uses only **8 function types**. Are we losing essential narrative expressivity?

---

## Deep Analysis: Plot Generation is NOT Geography Generation

### Key Insight #1: Different Constraint Topologies

```
GEOGRAPHY WFC:
┌───┬───┬───┬───┐
│ ? │ ? │ ? │ ? │     Each cell constrains 4 neighbors
├───┼───┼───┼───┤     Truly parallel collapse possible
│ ? │ ? │ ? │ ? │     Order of collapse matters little
├───┼───┼───┼───┤     Local constraints only
│ ? │ ? │ ? │ ? │
└───┴───┴───┴───┘

PLOT WFC:
┌───┐   ┌───┐   ┌───┐   ┌───┐
│ S │──►│ ? │──►│ ? │──►│ F │   Linear chain (mostly)
└───┘   └───┘   └───┘   └───┘
  │       │       │       │
  └───────┴───────┴───────┘     GLOBAL constraints (causality!)

S = Start, F = Finale
```

**Plot has GLOBAL constraints that geography doesn't:**
- Event A must happen BEFORE event B (temporal ordering)
- Hero must HAVE sword before USING sword (state tracking)
- Villain must be ALIVE before being KILLED (logical necessity)

**Conclusion:** Pure WFC is less suitable for plot than for geography. Backward requirement solving handles causality naturally.

### Key Insight #2: Propp Functions Have Hierarchy

Not all 31 Propp functions are equal. They form groups:

```
PREPARATORY SECTION (Functions 1-7):
  α (absentation), β (interdiction), γ (violation),
  δ (reconnaissance), ε (delivery), ζ (trickery), η (complicity)

  → These SET UP the story but aren't mandatory
  → POC can SKIP these or use generic "INTRODUCTION" node

COMPLICATION (Functions 8-11):
  A (villainy) or a (lack), B (mediation), C (counteraction), ↑ (departure)

  → ESSENTIAL: Every story needs a problem and a start
  → Our LACK and DEPARTURE cover this

DONOR SEQUENCE (Functions 12-14):
  D (donor testing), E (hero's reaction), F (receipt of agent)

  → ESSENTIAL for fantasy: getting the magic item
  → Our DONOR_TEST and ACQUISITION cover this

STRUGGLE (Functions 15-19):
  G (guidance), H (struggle), I (branding), J (victory), K (liquidation)

  → ESSENTIAL: The climax
  → Our GUIDANCE, STRUGGLE, VICTORY cover this

RETURN (Functions 20-31):
  ↓ (return), Pr (pursuit), Rs (rescue), O (arrival), L (claims),
  M (task), N (solution), Q (recognition), Ex (exposure),
  T (transfiguration), U (punishment), W (wedding)

  → OPTIONAL elaboration - many stories skip most of these
  → Our RETURN is sufficient for POC
```

**Conclusion:** 8 functions cover the ESSENTIAL narrative skeleton. Full 31 is elaboration.

### Key Insight #3: Z80 Bit Operation Costs

```
OPERATION           8-BIT    16-BIT   32-BIT   64-BIT
─────────────────────────────────────────────────────
AND                 4 cyc    8 cyc    16 cyc   32 cyc
OR                  4 cyc    8 cyc    16 cyc   32 cyc
Popcount (LUT)      8 cyc    16 cyc   32 cyc   64 cyc
Compare             4 cyc    8 cyc    16 cyc   32 cyc
Memory per mask     1 byte   2 bytes  4 bytes  8 bytes
─────────────────────────────────────────────────────
Constraint table    256 B    64 KB    16 MB    TOO BIG
(N×N/8 bytes)
```

**32-bit masks:**
- 32 function types possible
- Operations ~4x slower than 8-bit
- Constraint table: 32×32×4 = 4KB (manageable)

**64-bit masks:**
- 64 function types possible
- Operations ~8x slower
- Constraint table: 64×64×8 = 32KB (problematic on 48K)

**Conclusion:** 32-bit is the practical maximum for Z80. 16-bit is comfortable.

---

## Alternative Architectures

### Option A: Current Design (8-bit function, 8-bit req, 8-bit provides)

```
TOTAL: 24 bits per node

PROS:
+ Simple requirement tracking
+ Fast operations (3 × 8-bit)
+ Small constraint tables
+ Validates core mechanic

CONS:
- Only 8 function types
- Limited role variety
- May produce repetitive stories
```

### Option B: Wider Functions (16-bit function, 8-bit req, 8-bit provides)

```
TOTAL: 32 bits per node

PROS:
+ 16 function types (covers half of Propp)
+ Still fast on Z80 (16-bit native)
+ Richer narrative variety

CONS:
- Larger constraint table (512 bytes)
- More complex testing
- May be overkill for POC
```

### Option C: Full Propp (32-bit function mask, 16-bit req, 16-bit provides)

```
TOTAL: 64 bits per node

PROS:
+ 32 function types (full Propp + extensions)
+ 16 requirement/provide bits (rich state)
+ Maximum expressivity

CONS:
- Slow operations (emulated 32-bit)
- Large constraint tables (4KB+)
- Complex debugging
- Definitely overkill for POC
```

### Option D: Hybrid - Backward Solve + WFC Filling

```
STRUCTURE:
1. Backward solve: Creates MANDATORY nodes (8 types)
2. WFC filling: Inserts OPTIONAL nodes between them (16+ types)

Example:
  [LACK]──────────[DONOR_TEST]──────────[STRUGGLE]──────────[VICTORY]
          │                     │                    │
          ▼                     ▼                    ▼
     WFC inserts:          WFC inserts:         WFC inserts:
     - JOURNEY             - HELPER_APPEARS     - PURSUIT
     - RECONNAISSANCE      - PREPARATION        - RESCUE

PROS:
+ Guaranteed completability (mandatory nodes)
+ Rich variety (WFC filling)
+ Separates concerns cleanly

CONS:
- Two systems to implement
- More complex control flow
```

---

## Recommendation for POC

### Phase 1 (POC): Minimal Viable Plot

**Use Option A (8-bit functions)**

```
FUNCTION_TYPES (8):
  0: LACK           - Something missing/wrong
  1: DEPARTURE      - Hero sets out
  2: DONOR_TEST     - Prove worthiness
  3: ACQUISITION    - Get magic item/info
  4: GUIDANCE       - Travel to goal
  5: STRUGGLE       - Fight villain
  6: VICTORY        - Defeat villain
  7: RETURN         - Come home changed

REQUIREMENT_BITS (8):
  0: HERO_EXISTS    - Story has protagonist
  1: HAS_WEAPON     - Combat capability
  2: HAS_KEY        - Access item
  3: HAS_INFO       - Knowledge gained
  4: HAS_ALLY       - Helper joined
  5: HAS_ACCESS     - Can reach location
  6: VILLAIN_WEAK   - Vulnerability known
  7: AT_GOAL        - Reached destination

PROVIDES_BITS (8):
  0: HERO_EXISTS
  1: HAS_WEAPON
  2: HAS_KEY
  3: HAS_INFO
  4: ALLY_JOINED
  5: DOOR_OPEN
  6: VILLAIN_DEAD
  7: QUEST_COMPLETE
```

**Rationale:**
1. Validates backward generation mechanic
2. Produces recognizable story structure
3. Fast development cycle
4. Easy to test and debug
5. Can always expand later

### Phase 2 (Full Version): Extended Propp

**Use Option D (Hybrid)**

```
MANDATORY_FUNCTIONS (8): Same as POC

OPTIONAL_FUNCTIONS (16 additional):
  8:  INTERDICTION     - "Don't go there"
  9:  VIOLATION        - Hero disobeys
  10: RECONNAISSANCE   - Villain scouts
  11: TRICKERY         - Deception attempt
  12: MEDIATION        - Call to action
  13: COUNTERACTION    - Hero accepts call
  14: BRANDING         - Hero marked
  15: PURSUIT          - Chase sequence
  16: RESCUE           - Saved by helper
  17: FALSE_HERO       - Imposter appears
  18: DIFFICULT_TASK   - Final test
  19: SOLUTION         - Task completed
  20: RECOGNITION      - Hero revealed
  21: EXPOSURE         - Villain/false hero exposed
  22: TRANSFIGURATION  - Hero transformed
  23: PUNISHMENT       - Villain punished

WFC CONSTRAINT TABLE (24×24×3 = 1728 bytes):
  - Which optional functions can follow which
  - Stored in separate 128K bank
```

---

## Role Assignment Analysis

### Current Design: 8 Archetypes

```
ARCHETYPES (from PipDecks):
  0: HERO        - Protagonist
  1: SHADOW      - Antagonist
  2: SAGE        - Mentor/Donor
  3: CAREGIVER   - Helper
  4: EVERYMAN    - Ordinary folk
  5: OUTLAW      - Trickster
  6: EXPLORER    - Guide
  7: MAGICIAN    - Transformer
```

### Propp's Dramatis Personae (7):

```
  1: HERO        - Seeks something
  2: VILLAIN     - Opposes hero
  3: DONOR       - Provides magical agent
  4: HELPER      - Assists hero
  5: PRINCESS    - Sought-for person (reward)
  6: DISPATCHER  - Sends hero on quest
  7: FALSE_HERO  - Takes credit falsely
```

### Mapping

```
ROLE (Propp)    →  ARCHETYPE (PipDecks)   →  BEHAVIORS
─────────────────────────────────────────────────────────
HERO            →  HERO, EXPLORER         →  Brave, seeking
VILLAIN         →  SHADOW                 →  Opposing, cruel
DONOR           →  SAGE, MAGICIAN         →  Testing, giving
HELPER          →  CAREGIVER              →  Supporting
PRINCESS        →  (any, context-dependent)→  Passive or active
DISPATCHER      →  SAGE, EVERYMAN         →  Info-giving
FALSE_HERO      →  OUTLAW, SHADOW         →  Deceptive
```

**Conclusion:** 8 archetypes map well to 7 Propp roles. No expansion needed for POC.

---

## Final Recommendation

### For POC (Immediate)

```
FOCUS ON WHAT WE HAVE:

1. Geography WFC: 16-bit masks (16 tile types)
   - Sufficient for interesting maps
   - Fast and well-understood

2. Plot Generation: 8-bit backward solve
   - 8 Propp functions (essential skeleton)
   - 8-bit requirement/provide masks
   - NO WFC for plot - backward solve is better

3. Role Assignment: 8-bit masks
   - 8 archetypes sufficient
   - Direct mapping to Propp roles

TOTAL SYSTEM: Uses only 8-bit and 16-bit operations
              Maximum Z80 efficiency
              Validates core hypothesis
```

### For Full Version (Later)

```
EXPAND AFTER POC VALIDATES:

1. Optional Functions: Add 16 more via WFC filling
2. Richer Requirements: Expand to 16-bit masks
3. More Archetypes: Add shadow versions (16 total)
4. Nested Quests: Apply same system fractally

This can be done incrementally without redesigning core.
```

---

## Decision Matrix

| Aspect | POC (Now) | Full Version (Later) |
|--------|-----------|---------------------|
| Function types | 8 (essential) | 24 (full Propp) |
| Requirement bits | 8 | 16 |
| Provide bits | 8 | 16 |
| Plot generation | Backward solve | Hybrid (solve + WFC fill) |
| Role types | 8 | 16 |
| Memory per node | 3 bytes | 6 bytes |
| Constraint table | 64 bytes | 2KB |
| Z80 speed | Optimal | Acceptable |

---

## Action Items

1. **Proceed with 8-bit plot functions for POC**
   - Implement backward solver with 8 function types
   - Validate completability mechanics
   - Test with LLM player

2. **Document extension path**
   - Design 24-function expanded set
   - Define WFC constraints for optional functions
   - Plan bank allocation for 128K version

3. **Defer wider masks until POC proves concept**
   - If 8 functions produce boring stories → expand
   - If 8 functions work well → ship minimal version first

---

*"Perfection is achieved not when there is nothing more to add, but when there is nothing left to take away." — Antoine de Saint-Exupéry*

**For POC: Less is more. Validate core mechanics first.**
