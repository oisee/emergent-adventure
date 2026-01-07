"""
CFG Text Renderer

Context-Free Grammar based natural language generator.
Transforms plot nodes, NPC actions, and world state into prose.

Pipeline:
1. Template selection (based on context)
2. Slot filling (with variations)
3. Coherence pass (pronouns, flow)

Z80-compatible: Templates stored as indices, expansion at runtime.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any, Set
from enum import IntEnum, auto
import random
import re


# =============================================================================
# GRAMMAR COMPONENTS
# =============================================================================

class Mood(IntEnum):
    """Narrative mood affects word choice"""
    NEUTRAL = 0
    HOPEFUL = 1
    DARK = 2
    TENSE = 3
    MELANCHOLIC = 4
    TRIUMPHANT = 5
    MYSTERIOUS = 6
    COZY = 7


class Tense(IntEnum):
    """Verb tense"""
    PAST = 0      # "walked"
    PRESENT = 1   # "walks"
    FUTURE = 2    # "will walk"


class Person(IntEnum):
    """Narrative person"""
    SECOND = 0    # "You walk..."
    THIRD = 1     # "The hero walks..."


# =============================================================================
# PROPP FUNCTION TEMPLATES
# =============================================================================

# Each Propp function has multiple templates with slots
# Slots: {hero}, {villain}, {location}, {item}, {helper}, {action}

PROPP_TEMPLATES = {
    'EQUILIBRIUM': [
        "Peace reigns in {location}. {hero} goes about {their} daily life.",
        "The sun rises over {location}. All seems well.",
        "{hero} dwells in {location}, unaware of what lies ahead.",
        "Life in {location} follows its quiet rhythm.",
    ],
    'LACK': [
        "But something is missing. {item} has vanished.",
        "A shadow falls over {location}. {tragedy} has occurred.",
        "{hero} feels an emptiness that cannot be named.",
        "The {item} is gone, and with it, hope.",
        "Darkness creeps into {location}. Something must be done.",
    ],
    'INTERDICTION': [
        '"Do not {forbidden_action}," warns {mentor}.',
        '{mentor} speaks gravely: "Beware of {danger}."',
        'The elder\'s words echo: "Never trust {villain}."',
        '"Whatever you do," {mentor} says, "stay away from {danger}."',
    ],
    'VIOLATION': [
        "But {hero} {violates}. The warning goes unheeded.",
        "Against all advice, {hero} {forbidden_action}.",
        "Curiosity overcomes caution. {hero} {violates}.",
        "The temptation proves too great.",
    ],
    'DEPARTURE': [
        "{hero} sets forth from {location}, destiny calling.",
        "With heavy heart, {hero} leaves {location} behind.",
        "The journey begins. {hero} steps into the unknown.",
        "{hero} takes the first step on a long road.",
        "Farewell, {location}. {hero} has a quest to fulfill.",
    ],
    'DONOR_TEST': [
        "A strange {donor} appears, offering a challenge.",
        '"{hero}," the {donor} speaks, "prove your worth."',
        "To earn {item}, {hero} must first {test_action}.",
        "The {donor} tests {hero}'s {virtue}.",
    ],
    'ACQUISITION': [
        "{hero} receives {item} from {donor}.",
        "With {item} in hand, {hero} feels renewed strength.",
        "The {donor} bestows {item} upon {hero}.",
        "{item} is now {hero}'s to wield.",
    ],
    'GUIDANCE': [
        '"{path_hint}," {mentor} advises.',
        '{helper} points the way to {destination}.',
        "A clue emerges: {clue}.",
        "{hero} learns where {villain} can be found.",
    ],
    'STRUGGLE': [
        "{hero} and {villain} clash in {location}!",
        "Steel rings against steel. The battle is joined.",
        "{hero} faces {villain} at last.",
        "The confrontation {hero} feared has come.",
        "No more running. {hero} must fight.",
    ],
    'BRANDING': [
        "{hero} bears a new scar—a mark of {significance}.",
        "The battle leaves its mark upon {hero}.",
        "{hero} is changed, forever marked by {event}.",
        "A wound that will never fully heal.",
    ],
    'VICTORY': [
        "{villain} falls! {hero} stands victorious.",
        "Against all odds, {hero} prevails.",
        "The darkness recedes. {hero} has won.",
        "It is done. {villain} is defeated.",
        "Triumph! The threat is ended.",
    ],
    'PURSUIT': [
        "{villain}'s minions give chase!",
        "{hero} flees, {enemy} close behind.",
        "Escape! But the danger follows.",
        "There is no time to rest. The hunt continues.",
    ],
    'RESCUE': [
        "{hero} frees {victim} from {villain}'s grasp.",
        "{victim} is saved! Relief floods through {hero}.",
        "Against impossible odds, the rescue succeeds.",
        "{hero} carries {victim} to safety.",
    ],
    'RECOGNITION': [
        "The truth is revealed: {revelation}.",
        "All becomes clear. {revelation}.",
        "{hero}'s true nature is finally known.",
        "Masks fall away. {secret} is exposed.",
    ],
    'PUNISHMENT': [
        "{villain} faces justice at last.",
        "For {crimes}, {villain} pays the price.",
        "Retribution comes for {villain}.",
        "The wicked are punished, the balance restored.",
    ],
    'RETURN': [
        "{hero} returns to {home}, changed forever.",
        "Home at last. But {hero} is not the same.",
        "The journey ends where it began.",
        "{location} welcomes its hero home.",
        "Full circle. {hero} has returned.",
    ],
}


# =============================================================================
# MOOD MODIFIERS
# =============================================================================

# Word replacements based on mood
MOOD_VOCABULARY = {
    Mood.DARK: {
        'walks': 'trudges',
        'goes': 'creeps',
        'speaks': 'whispers',
        'sun': 'pale light',
        'rises': 'struggles to rise',
        'peace': 'uneasy stillness',
        'home': 'crumbling refuge',
        'victory': 'bitter triumph',
        'hero': 'weary champion',
    },
    Mood.HOPEFUL: {
        'trudges': 'strides',
        'darkness': 'shadow',
        'falls': 'descends briefly',
        'fear': 'concern',
        'danger': 'challenge',
        'fight': 'stand firm',
        'wicked': 'misguided',
    },
    Mood.TENSE: {
        'walks': 'hurries',
        'speaks': 'hisses',
        'waits': 'lurks',
        'appears': 'emerges suddenly',
        'silence': 'dread silence',
    },
    Mood.MELANCHOLIC: {
        'returns': 'drifts back',
        'victory': 'hollow victory',
        'triumph': 'bittersweet success',
        'home': 'what remains of home',
        'peace': 'weary peace',
    },
    Mood.TRIUMPHANT: {
        'walks': 'marches',
        'speaks': 'proclaims',
        'victory': 'glorious victory',
        'returns': 'returns in glory',
        'hero': 'legendary hero',
    },
    Mood.MYSTERIOUS: {
        'appears': 'materializes',
        'speaks': 'intones',
        'truth': 'hidden truth',
        'path': 'shrouded path',
        'stranger': 'enigmatic figure',
    },
    Mood.COZY: {
        'battle': 'scuffle',
        'danger': 'mild peril',
        'villain': 'troublemaker',
        'darkness': 'gloom',
        'fear': 'worry',
        'trudges': 'ambles',
    },
}


# =============================================================================
# SLOT FILLERS
# =============================================================================

# Default slot values (can be overridden by context)
DEFAULT_SLOTS = {
    'hero': 'the hero',
    'their': 'their',
    'them': 'them',
    'villain': 'the dark lord',
    'location': 'the village',
    'home': 'home',
    'item': 'the artifact',
    'helper': 'a mysterious stranger',
    'mentor': 'the wise elder',
    'donor': 'a strange figure',
    'victim': 'the prisoner',
    'destination': 'the dark tower',
    'forbidden_action': 'enter the forbidden grove',
    'violates': 'enters the forbidden grove',
    'danger': 'the shadow lands',
    'test_action': 'answer three riddles',
    'virtue': 'courage',
    'path_hint': 'Follow the river north',
    'clue': 'the villain hides in the mountains',
    'significance': 'their sacrifice',
    'event': 'the great battle',
    'revelation': 'the helper was the true heir',
    'secret': 'the villain\'s identity',
    'crimes': 'countless atrocities',
    'tragedy': 'a great loss',
    'enemy': 'dark riders',
}

# Genre-specific slot values
GENRE_SLOTS = {
    'fantasy': {
        'villain': 'the Dark Lord',
        'item': 'the enchanted sword',
        'location': 'the peaceful shire',
        'destination': 'the obsidian fortress',
        'mentor': 'the wizard',
    },
    'dark_fantasy': {
        'villain': 'the Lich King',
        'item': 'the cursed blade',
        'location': 'the blighted village',
        'destination': 'the throne of bones',
        'mentor': 'the scarred veteran',
        'danger': 'the abyss',
    },
    'solarpunk': {
        'villain': 'the Corporation',
        'item': 'the seed archive',
        'location': 'the garden commune',
        'destination': 'the dead zone',
        'mentor': 'the elder botanist',
        'tragedy': 'the blight has spread',
    },
    'cozy': {
        'villain': 'the grumpy neighbor',
        'item': 'grandmother\'s recipe book',
        'location': 'the cozy cottage',
        'destination': 'the next village',
        'mentor': 'the kindly baker',
        'danger': 'getting lost',
        'tragedy': 'the cat has gone missing',
    },
    'mystery': {
        'villain': 'the masked figure',
        'item': 'the crucial evidence',
        'location': 'the manor house',
        'destination': 'the hidden room',
        'mentor': 'the retired detective',
        'revelation': 'the butler was the killer',
    },
    'isekai': {
        'villain': 'the Demon King',
        'item': 'the legendary weapon',
        'location': 'the starting village',
        'destination': 'the demon realm',
        'mentor': 'the goddess\'s avatar',
        'hero': 'the summoned hero',
    },
}


# =============================================================================
# NPC ACTION TEMPLATES
# =============================================================================

NPC_ACTION_TEMPLATES = {
    'ATTEMPT_STEAL': [
        '{npc} eyes {item} greedily and reaches for it.',
        'A flash of movement—{npc} snatches at {item}!',
        '{npc}\'s true nature shows. They grab for {item}.',
    ],
    'CLAIM_CREDIT': [
        '"{hero} helped, but I did the real work," {npc} announces.',
        '{npc} steps forward to accept praise meant for {hero}.',
    ],
    'FLEE': [
        '{npc} turns and runs, fear overcoming loyalty.',
        'With a cry of terror, {npc} abandons the fight.',
        '{npc} has vanished. So much for bravery.',
    ],
    'PROTECT_HERO': [
        '{npc} steps between {hero} and danger.',
        '"Not while I stand!" {npc} shields {hero}.',
        '{npc} takes the blow meant for {hero}.',
    ],
    'PLOT_REVENGE': [
        '{npc}\'s eyes narrow. They will not forget this.',
        'Hatred burns in {npc}\'s heart. Vengeance will come.',
    ],
    'REVEAL_TRUE_SELF': [
        '{npc} drops the mask. "{revelation}."',
        'The truth at last: {npc} was {true_role} all along.',
    ],
    'SACRIFICE_SELF': [
        '"Go!" {npc} cries, holding the enemy back.',
        '{npc} makes the ultimate sacrifice.',
    ],
    'SPEAK_TRUTH': [
        '{npc} cannot stay silent. "The truth is, {secret}."',
        'Honesty compels {npc} to speak.',
    ],
    'RECIPROCATE': [
        '{npc} returns the kindness tenfold.',
        '"You helped me once. Now I help you," says {npc}.',
    ],
}


# =============================================================================
# WEATHER DESCRIPTION TEMPLATES
# =============================================================================

WEATHER_TEMPLATES = {
    'CLEAR': [
        "Under a clear sky,",
        "Beneath the open heavens,",
        "The sky stretches blue and endless.",
    ],
    'RAIN': [
        "Rain falls steadily,",
        "The rain drums against everything,",
        "Through the downpour,",
    ],
    'STORM': [
        "Thunder rumbles overhead,",
        "The storm rages around {hero},",
        "Lightning splits the sky,",
    ],
    'FOG': [
        "Fog shrouds everything in mystery,",
        "Through the thick mist,",
        "The world fades into gray,",
    ],
    'SNOW': [
        "Snow falls silently,",
        "The world lies white and still,",
        "Snowflakes dance in the air,",
    ],
    'NIGHT': [
        "Darkness blankets the land,",
        "Under the cover of night,",
        "The stars watch coldly,",
    ],
}


# =============================================================================
# CFG RENDERER CLASS
# =============================================================================

@dataclass
class RenderContext:
    """Context for text rendering"""
    # Characters
    hero_name: str = "the hero"
    hero_pronoun: str = "they"
    hero_possessive: str = "their"
    hero_object: str = "them"

    villain_name: str = "the villain"
    npc_names: Dict[str, str] = field(default_factory=dict)

    # World
    current_location: str = "the village"
    home_location: str = "home"
    destination: str = "the dark tower"

    # Items
    quest_item: str = "the artifact"

    # State
    mood: Mood = Mood.NEUTRAL
    tense: Tense = Tense.PAST
    person: Person = Person.SECOND
    genre: str = "fantasy"

    # For coherence
    last_subject: str = ""
    mentioned_entities: Set[str] = field(default_factory=set)


class CFGRenderer:
    """
    Context-Free Grammar text renderer.

    Transforms game events into natural language prose.
    """

    def __init__(self, seed: int = None, genre: str = "fantasy"):
        self.rng = random.Random(seed)
        self.genre = genre
        self.context = RenderContext(genre=genre)

        # Build slot dictionary for this genre
        self.slots = dict(DEFAULT_SLOTS)
        if genre in GENRE_SLOTS:
            self.slots.update(GENRE_SLOTS[genre])

    def set_context(self, **kwargs):
        """Update render context"""
        for key, value in kwargs.items():
            if hasattr(self.context, key):
                setattr(self.context, key, value)

    def render_propp(self, function: str, extra_slots: Dict[str, str] = None) -> str:
        """Render a Propp function to text"""
        if function not in PROPP_TEMPLATES:
            return f"[Unknown function: {function}]"

        # Select template
        templates = PROPP_TEMPLATES[function]
        template = self.rng.choice(templates)

        # Build slots
        slots = dict(self.slots)
        slots['hero'] = self.context.hero_name
        slots['their'] = self.context.hero_possessive
        slots['them'] = self.context.hero_object
        slots['villain'] = self.context.villain_name
        slots['location'] = self.context.current_location
        slots['home'] = self.context.home_location
        slots['destination'] = self.context.destination
        slots['item'] = self.context.quest_item

        if extra_slots:
            slots.update(extra_slots)

        # Fill template
        text = self._fill_template(template, slots)

        # Apply mood
        text = self._apply_mood(text, self.context.mood)

        # Apply person
        if self.context.person == Person.SECOND:
            text = self._to_second_person(text)

        return text

    def render_npc_action(self, npc_name: str, action: str,
                          extra_slots: Dict[str, str] = None) -> str:
        """Render NPC action to text"""
        if action not in NPC_ACTION_TEMPLATES:
            return f"{npc_name} acts ({action})."

        templates = NPC_ACTION_TEMPLATES[action]
        template = self.rng.choice(templates)

        slots = dict(self.slots)
        slots['npc'] = npc_name
        slots['hero'] = self.context.hero_name

        if extra_slots:
            slots.update(extra_slots)

        text = self._fill_template(template, slots)
        text = self._apply_mood(text, self.context.mood)

        return text

    def render_weather(self, weather_type: str) -> str:
        """Render weather description"""
        weather_key = weather_type.upper()

        # Find matching template category
        for key in WEATHER_TEMPLATES:
            if key in weather_key:
                templates = WEATHER_TEMPLATES[key]
                template = self.rng.choice(templates)
                return self._fill_template(template, self.slots)

        return ""

    def render_scene(self, propp_function: str,
                     weather: str = None,
                     npc_actions: List[Tuple[str, str]] = None,
                     extra_slots: Dict[str, str] = None) -> str:
        """Render a complete scene"""
        parts = []

        # Weather intro (optional)
        if weather:
            weather_text = self.render_weather(weather)
            if weather_text:
                parts.append(weather_text)

        # Main Propp function
        propp_text = self.render_propp(propp_function, extra_slots)
        parts.append(propp_text)

        # NPC reactions
        if npc_actions:
            for npc_name, action in npc_actions:
                action_text = self.render_npc_action(npc_name, action, extra_slots)
                parts.append(action_text)

        return " ".join(parts)

    def render_plot_sequence(self, functions: List[str],
                             weather_sequence: List[str] = None) -> str:
        """Render a sequence of plot functions"""
        paragraphs = []

        for i, func in enumerate(functions):
            weather = weather_sequence[i] if weather_sequence and i < len(weather_sequence) else None
            text = self.render_scene(func, weather=weather)
            paragraphs.append(text)

        return "\n\n".join(paragraphs)

    def _fill_template(self, template: str, slots: Dict[str, str]) -> str:
        """Fill template slots with values"""
        result = template

        for key, value in slots.items():
            result = result.replace(f'{{{key}}}', str(value))

        # Handle unfilled slots
        result = re.sub(r'\{[^}]+\}', '[???]', result)

        return result

    def _apply_mood(self, text: str, mood: Mood) -> str:
        """Apply mood-based word replacements"""
        if mood == Mood.NEUTRAL:
            return text

        vocab = MOOD_VOCABULARY.get(mood, {})

        for original, replacement in vocab.items():
            # Case-insensitive replacement preserving case
            pattern = re.compile(re.escape(original), re.IGNORECASE)
            text = pattern.sub(lambda m: self._match_case(m.group(), replacement), text)

        return text

    def _match_case(self, original: str, replacement: str) -> str:
        """Match replacement case to original"""
        if original.isupper():
            return replacement.upper()
        elif original[0].isupper():
            return replacement.capitalize()
        return replacement

    def _to_second_person(self, text: str) -> str:
        """Convert third person to second person"""
        hero = self.context.hero_name

        # Replace hero references with "you"
        text = text.replace(hero, "you")
        text = text.replace(hero.title(), "You")

        # Fix pronouns
        text = text.replace("their", "your")
        text = text.replace("them", "you")
        text = text.replace("they", "you")
        text = text.replace("Their", "Your")
        text = text.replace("Them", "You")
        text = text.replace("They", "You")

        # Fix verb forms (third person -> second person)
        verb_fixes = [
            (" goes ", " go "), (" goes.", " go."),
            (" sets ", " set "), (" sets.", " set."),
            (" steps ", " step "), (" steps.", " step."),
            (" feels ", " feel "), (" feels.", " feel."),
            (" faces ", " face "), (" faces.", " face."),
            (" prevails", " prevail"), (" stands ", " stand "),
            (" returns", " return"), (" leaves ", " leave "),
            (" takes ", " take "), (" receives ", " receive "),
            (" has ", " have "), ("you has", "you have"),
            ("You goes", "You go"), ("You sets", "You set"),
            ("You steps", "You step"), ("You feels", "You feel"),
            ("You faces", "You face"), ("You stands", "You stand"),
            ("you's", "your"),
        ]

        for old, new in verb_fixes:
            text = text.replace(old, new)

        return text


# =============================================================================
# Z80 TEMPLATE INDICES
# =============================================================================

def build_template_index() -> bytes:
    """
    Build compact template index for Z80.

    Format:
    - 1 byte: function count
    - Per function:
      - 1 byte: function index
      - 1 byte: template count
      - Per template:
        - 2 bytes: string offset
    - String table follows
    """
    data = bytearray()
    strings = bytearray()
    string_offsets = {}

    # Function mapping
    func_names = list(PROPP_TEMPLATES.keys())
    data.append(len(func_names))

    for func_idx, func_name in enumerate(func_names):
        templates = PROPP_TEMPLATES[func_name]
        data.append(func_idx)
        data.append(len(templates))

        for template in templates:
            # Store string offset
            if template not in string_offsets:
                string_offsets[template] = len(strings)
                # Encode template (simplified: just ASCII)
                encoded = template.encode('ascii', errors='replace')
                strings.extend(encoded)
                strings.append(0)  # null terminator

            offset = string_offsets[template]
            data.extend(offset.to_bytes(2, 'little'))

    return bytes(data) + bytes(strings)


# =============================================================================
# DEMO
# =============================================================================

def demo():
    """Demonstrate CFG rendering"""
    print("=" * 60)
    print("CFG TEXT RENDERER DEMO")
    print("=" * 60)
    print()

    # Basic rendering
    renderer = CFGRenderer(seed=42, genre="fantasy")
    renderer.set_context(
        hero_name="Aldric",
        hero_pronoun="he",
        hero_possessive="his",
        villain_name="the Shadow King",
        current_location="Thornwood Village",
        quest_item="the Crystal of Dawn"
    )

    print("=== Basic Propp Function Rendering ===\n")

    functions = ['EQUILIBRIUM', 'LACK', 'DEPARTURE', 'DONOR_TEST',
                 'ACQUISITION', 'STRUGGLE', 'VICTORY', 'RETURN']

    for func in functions:
        text = renderer.render_propp(func)
        print(f"[{func}]")
        print(f"  {text}")
        print()

    # Different moods
    print("=== Mood Variations (STRUGGLE) ===\n")

    for mood in [Mood.NEUTRAL, Mood.DARK, Mood.TRIUMPHANT, Mood.COZY]:
        renderer.context.mood = mood
        text = renderer.render_propp('STRUGGLE')
        print(f"{mood.name}:")
        print(f"  {text}")
        print()

    # Full scene with weather and NPC
    print("=== Full Scene Rendering ===\n")
    renderer.context.mood = Mood.TENSE

    scene = renderer.render_scene(
        propp_function='STRUGGLE',
        weather='STORM',
        npc_actions=[('Grimald', 'PROTECT_HERO')],
        extra_slots={'revelation': 'Grimald was the lost prince'}
    )
    print(scene)
    print()

    # Genre comparison
    print("=== Genre Comparison (DEPARTURE) ===\n")

    for genre in ['fantasy', 'dark_fantasy', 'solarpunk', 'cozy']:
        r = CFGRenderer(seed=42, genre=genre)
        r.context.mood = Mood.NEUTRAL
        text = r.render_propp('DEPARTURE')
        print(f"{genre.upper()}:")
        print(f"  {text}")
        print()

    # Plot sequence
    print("=== Full Plot Sequence ===\n")
    renderer = CFGRenderer(seed=12345, genre="dark_fantasy")
    renderer.set_context(
        hero_name="Kira",
        villain_name="the Lich Queen",
        mood=Mood.DARK
    )

    plot = renderer.render_plot_sequence(
        ['EQUILIBRIUM', 'LACK', 'DEPARTURE', 'STRUGGLE', 'VICTORY', 'RETURN']
    )
    print(plot)
    print()

    # Z80 index size
    print("=== Z80 Template Index ===")
    index = build_template_index()
    print(f"Template index size: {len(index)} bytes")
    print(f"Functions: {len(PROPP_TEMPLATES)}")
    print(f"Total templates: {sum(len(t) for t in PROPP_TEMPLATES.values())}")


if __name__ == '__main__':
    demo()
