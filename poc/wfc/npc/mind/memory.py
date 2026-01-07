"""
Memory System

Episodic memory with:
- Event storage
- Emotional valence
- Temporal decay
- Associative retrieval
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set
from enum import IntEnum, auto


class MemoryType(IntEnum):
    """Types of memories"""
    EVENT = 0         # Something that happened
    FACT = 1          # Learned information
    INTERACTION = 2   # Interaction with someone
    PROMISE = 3       # Made or received promise
    BETRAYAL = 4      # Broken trust
    GIFT = 5          # Received something


@dataclass
class Memory:
    """A single episodic memory"""
    key: str                           # Unique identifier
    content: str                       # What happened
    memory_type: MemoryType = MemoryType.EVENT

    # Participants
    participants: Set[str] = field(default_factory=set)

    # Emotional impact
    emotional_valence: float = 0.0     # -1.0 (bad) to 1.0 (good)
    emotional_intensity: float = 0.5   # How strong the emotion

    # Temporal
    timestamp: int = 0                 # When it happened
    strength: float = 1.0              # Memory strength (decays)
    decay_rate: float = 0.01           # Per tick decay

    # Associations
    tags: Set[str] = field(default_factory=set)  # Keywords for retrieval

    def tick(self):
        """Apply time-based decay"""
        # Emotional memories decay slower
        effective_decay = self.decay_rate * (1.0 - abs(self.emotional_valence) * 0.5)
        self.strength = max(0.0, self.strength - effective_decay)

    def strengthen(self, amount: float = 0.2):
        """Strengthen memory (from recall or repetition)"""
        self.strength = min(1.0, self.strength + amount)

    def is_remembered(self, threshold: float = 0.3) -> bool:
        """Check if memory is still accessible"""
        return self.strength >= threshold

    def involves(self, participant: str) -> bool:
        """Check if memory involves someone"""
        return participant in self.participants


class MemorySystem:
    """
    Manages episodic memories for an NPC.

    Features:
    - Key-based storage
    - Tag-based retrieval
    - Participant-based queries
    - Decay over time
    """

    def __init__(self, max_memories: int = 100):
        self.memories: Dict[str, Memory] = {}
        self.max_memories = max_memories
        self.tick_count: int = 0

    def remember(self, key: str, content: str,
                 memory_type: MemoryType = MemoryType.EVENT,
                 participants: Set[str] = None,
                 emotional_valence: float = 0.0,
                 emotional_intensity: float = 0.5,
                 tags: Set[str] = None,
                 decay_rate: float = 0.01):
        """Store a new memory"""
        # If memory exists, strengthen it
        if key in self.memories:
            self.memories[key].strengthen()
            return

        # Prune if at capacity
        if len(self.memories) >= self.max_memories:
            self._prune_weakest()

        self.memories[key] = Memory(
            key=key,
            content=content,
            memory_type=memory_type,
            participants=participants or set(),
            emotional_valence=emotional_valence,
            emotional_intensity=emotional_intensity,
            timestamp=self.tick_count,
            tags=tags or set(),
            decay_rate=decay_rate,
        )

    def forget(self, key: str):
        """Explicitly forget a memory"""
        if key in self.memories:
            del self.memories[key]

    def recall(self, key: str) -> Optional[Memory]:
        """Recall a specific memory (strengthens it)"""
        if key in self.memories:
            memory = self.memories[key]
            if memory.is_remembered():
                memory.strengthen(0.1)
                return memory
        return None

    def is_remembered(self, key: str) -> bool:
        """Check if something is remembered"""
        if key in self.memories:
            return self.memories[key].is_remembered()
        return False

    def get_value(self, key: str) -> Optional[str]:
        """Get memory content (for VM)"""
        memory = self.recall(key)
        return memory.content if memory else None

    def store(self, key: str, value: Any):
        """Store a simple fact (for VM)"""
        self.remember(
            key=key,
            content=str(value),
            memory_type=MemoryType.FACT,
        )

    def tick(self):
        """Process time-based decay"""
        self.tick_count += 1
        to_forget = []

        for key, memory in self.memories.items():
            memory.tick()
            if not memory.is_remembered(0.1):  # Forget very weak memories
                to_forget.append(key)

        for key in to_forget:
            del self.memories[key]

    def _prune_weakest(self):
        """Remove weakest memories to make space"""
        if not self.memories:
            return

        # Find weakest non-emotional memory
        weakest = min(
            self.memories.values(),
            key=lambda m: m.strength * (1 + abs(m.emotional_valence))
        )
        del self.memories[weakest.key]

    def find_by_participant(self, participant: str) -> List[Memory]:
        """Find memories involving a participant"""
        return [
            m for m in self.memories.values()
            if m.involves(participant) and m.is_remembered()
        ]

    def find_by_tag(self, tag: str) -> List[Memory]:
        """Find memories with a tag"""
        return [
            m for m in self.memories.values()
            if tag in m.tags and m.is_remembered()
        ]

    def find_by_type(self, memory_type: MemoryType) -> List[Memory]:
        """Find memories of a type"""
        return [
            m for m in self.memories.values()
            if m.memory_type == memory_type and m.is_remembered()
        ]

    def find_emotional(self, positive: bool = True) -> List[Memory]:
        """Find emotionally charged memories"""
        threshold = 0.3
        return [
            m for m in self.memories.values()
            if m.is_remembered() and (
                (positive and m.emotional_valence > threshold) or
                (not positive and m.emotional_valence < -threshold)
            )
        ]

    def get_recent(self, count: int = 5) -> List[Memory]:
        """Get most recent memories"""
        remembered = [m for m in self.memories.values() if m.is_remembered()]
        return sorted(remembered, key=lambda m: -m.timestamp)[:count]

    def get_strongest(self, count: int = 5) -> List[Memory]:
        """Get strongest memories"""
        remembered = [m for m in self.memories.values() if m.is_remembered()]
        return sorted(remembered, key=lambda m: -m.strength)[:count]

    def relationship_history(self, target: str) -> List[Memory]:
        """Get history of interactions with a target"""
        relevant = self.find_by_participant(target)
        return sorted(relevant, key=lambda m: m.timestamp)

    def emotional_average(self, target: str) -> float:
        """Get average emotional valence toward a target"""
        memories = self.find_by_participant(target)
        if not memories:
            return 0.0

        total = sum(m.emotional_valence * m.strength for m in memories)
        weight = sum(m.strength for m in memories)

        return total / weight if weight > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            'memories': {
                k: {
                    'content': v.content,
                    'memory_type': v.memory_type.name,
                    'participants': list(v.participants),
                    'emotional_valence': v.emotional_valence,
                    'emotional_intensity': v.emotional_intensity,
                    'timestamp': v.timestamp,
                    'strength': v.strength,
                    'decay_rate': v.decay_rate,
                    'tags': list(v.tags),
                }
                for k, v in self.memories.items()
            },
            'tick_count': self.tick_count,
            'max_memories': self.max_memories,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemorySystem':
        """Deserialize from dictionary"""
        system = cls(max_memories=data.get('max_memories', 100))
        system.tick_count = data.get('tick_count', 0)

        for key, mem_data in data.get('memories', {}).items():
            system.memories[key] = Memory(
                key=key,
                content=mem_data['content'],
                memory_type=MemoryType[mem_data['memory_type']],
                participants=set(mem_data.get('participants', [])),
                emotional_valence=mem_data['emotional_valence'],
                emotional_intensity=mem_data.get('emotional_intensity', 0.5),
                timestamp=mem_data['timestamp'],
                strength=mem_data['strength'],
                decay_rate=mem_data.get('decay_rate', 0.01),
                tags=set(mem_data.get('tags', [])),
            )

        return system
