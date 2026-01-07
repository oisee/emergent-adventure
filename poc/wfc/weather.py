"""
Weather, Climate, Seasons, and Time of Day System

Comprehensive atmospheric system for emergent storytelling:
- Weather types with combinations (thunderstorm = rain + lightning)
- Climate zones based on latitude
- Seasonal cycles affecting weather probabilities
- Time of day with lighting and mood effects
- Weather-mood interactions for narrative tone
"""

from dataclasses import dataclass, field
from enum import IntEnum, auto
from typing import Dict, List, Set, Tuple, Optional, Any
import random
import math


# =============================================================================
# TIME OF DAY
# =============================================================================

class TimeOfDay(IntEnum):
    """Times of day with associated lighting"""
    DAWN = 0        # First light
    MORNING = 1     # Early day
    NOON = 2        # Midday
    AFTERNOON = 3   # Late day
    DUSK = 4        # Twilight
    EVENING = 5     # Early night
    NIGHT = 6       # Deep night
    MIDNIGHT = 7    # Darkest hour


TIME_OF_DAY_INFO = {
    TimeOfDay.DAWN: {
        "name": "Dawn",
        "icon": "🌅",
        "light_level": 0.4,
        "color": "#FFB347",  # Soft orange
        "mood_modifier": "hopeful",
        "description": "The first rays of light paint the sky",
    },
    TimeOfDay.MORNING: {
        "name": "Morning",
        "icon": "🌄",
        "light_level": 0.7,
        "color": "#87CEEB",  # Sky blue
        "mood_modifier": "fresh",
        "description": "The world awakens with renewed energy",
    },
    TimeOfDay.NOON: {
        "name": "Noon",
        "icon": "☀️",
        "light_level": 1.0,
        "color": "#FFD700",  # Bright gold
        "mood_modifier": "vibrant",
        "description": "The sun stands at its zenith",
    },
    TimeOfDay.AFTERNOON: {
        "name": "Afternoon",
        "icon": "🌤️",
        "light_level": 0.85,
        "color": "#F0E68C",  # Khaki
        "mood_modifier": "warm",
        "description": "Golden light stretches across the land",
    },
    TimeOfDay.DUSK: {
        "name": "Dusk",
        "icon": "🌇",
        "light_level": 0.35,
        "color": "#FF6B6B",  # Coral red
        "mood_modifier": "melancholic",
        "description": "The sun sinks below the horizon",
    },
    TimeOfDay.EVENING: {
        "name": "Evening",
        "icon": "🌆",
        "light_level": 0.2,
        "color": "#4B0082",  # Indigo
        "mood_modifier": "mysterious",
        "description": "Stars begin to emerge in the darkening sky",
    },
    TimeOfDay.NIGHT: {
        "name": "Night",
        "icon": "🌙",
        "light_level": 0.1,
        "color": "#191970",  # Midnight blue
        "mood_modifier": "ominous",
        "description": "Darkness blankets the world",
    },
    TimeOfDay.MIDNIGHT: {
        "name": "Midnight",
        "icon": "🌑",
        "light_level": 0.05,
        "color": "#0D0D1A",  # Near black
        "mood_modifier": "eerie",
        "description": "The witching hour, when shadows reign",
    },
}


# =============================================================================
# SEASONS
# =============================================================================

class Season(IntEnum):
    """Four seasons"""
    SPRING = 0
    SUMMER = 1
    AUTUMN = 2
    WINTER = 3


SEASON_INFO = {
    Season.SPRING: {
        "name": "Spring",
        "icon": "🌸",
        "color": "#98FB98",  # Pale green
        "temperature_modifier": 0.0,  # Baseline
        "precipitation_modifier": 1.2,  # Rainy
        "mood": "hopeful",
        "description": "New life blooms across the land",
        "weather_weights": {
            "clear": 0.3, "cloudy": 0.2, "rain": 0.25,
            "fog": 0.1, "wind": 0.1, "storm": 0.05
        },
    },
    Season.SUMMER: {
        "name": "Summer",
        "icon": "☀️",
        "color": "#FFD700",  # Gold
        "temperature_modifier": 0.4,  # Hot
        "precipitation_modifier": 0.6,  # Dry
        "mood": "vibrant",
        "description": "Long days of warmth and light",
        "weather_weights": {
            "clear": 0.5, "heat": 0.2, "drought": 0.1,
            "storm": 0.1, "cloudy": 0.1
        },
    },
    Season.AUTUMN: {
        "name": "Autumn",
        "icon": "🍂",
        "color": "#D2691E",  # Chocolate
        "temperature_modifier": -0.1,
        "precipitation_modifier": 1.0,
        "mood": "melancholic",
        "description": "Leaves turn gold as the world prepares for rest",
        "weather_weights": {
            "cloudy": 0.25, "rain": 0.2, "fog": 0.15,
            "wind": 0.2, "clear": 0.15, "storm": 0.05
        },
    },
    Season.WINTER: {
        "name": "Winter",
        "icon": "❄️",
        "color": "#B0E0E6",  # Powder blue
        "temperature_modifier": -0.5,  # Cold
        "precipitation_modifier": 0.8,
        "mood": "stark",
        "description": "The world sleeps beneath a blanket of cold",
        "weather_weights": {
            "snow": 0.3, "clear": 0.2, "cloudy": 0.2,
            "blizzard": 0.1, "fog": 0.1, "frost": 0.1
        },
    },
}


# =============================================================================
# CLIMATE ZONES
# =============================================================================

class ClimateZone(IntEnum):
    """Climate zones based on latitude"""
    TROPICAL = 0      # 0-23 degrees
    SUBTROPICAL = 1   # 23-35 degrees
    TEMPERATE = 2     # 35-55 degrees
    CONTINENTAL = 3   # 55-66 degrees
    SUBARCTIC = 4     # 66-75 degrees
    ARCTIC = 5        # 75-90 degrees


CLIMATE_INFO = {
    ClimateZone.TROPICAL: {
        "name": "Tropical",
        "icon": "🌴",
        "latitude_range": (0, 23),
        "base_temperature": 0.8,  # Hot
        "humidity": 0.9,
        "seasonal_variation": 0.1,  # Little variation
        "description": "Hot and humid year-round",
        "weather_modifiers": {
            "rain": 1.5, "storm": 1.3, "heat": 1.4,
            "snow": 0.0, "frost": 0.0, "blizzard": 0.0
        },
    },
    ClimateZone.SUBTROPICAL: {
        "name": "Subtropical",
        "icon": "🏝️",
        "latitude_range": (23, 35),
        "base_temperature": 0.6,
        "humidity": 0.6,
        "seasonal_variation": 0.3,
        "description": "Warm with mild winters",
        "weather_modifiers": {
            "heat": 1.2, "drought": 1.3, "rain": 0.9,
            "snow": 0.2, "frost": 0.3
        },
    },
    ClimateZone.TEMPERATE: {
        "name": "Temperate",
        "icon": "🌳",
        "latitude_range": (35, 55),
        "base_temperature": 0.3,
        "humidity": 0.5,
        "seasonal_variation": 0.5,  # Full seasons
        "description": "Four distinct seasons",
        "weather_modifiers": {
            # Baseline - no strong modifiers
        },
    },
    ClimateZone.CONTINENTAL: {
        "name": "Continental",
        "icon": "🏔️",
        "latitude_range": (55, 66),
        "base_temperature": 0.1,
        "humidity": 0.4,
        "seasonal_variation": 0.7,  # Extreme variation
        "description": "Hot summers, harsh winters",
        "weather_modifiers": {
            "snow": 1.3, "frost": 1.4, "blizzard": 1.2,
            "heat": 0.8
        },
    },
    ClimateZone.SUBARCTIC: {
        "name": "Subarctic",
        "icon": "🌲",
        "latitude_range": (66, 75),
        "base_temperature": -0.2,
        "humidity": 0.3,
        "seasonal_variation": 0.6,
        "description": "Long winters, brief summers",
        "weather_modifiers": {
            "snow": 1.5, "frost": 1.6, "blizzard": 1.4,
            "heat": 0.3, "drought": 0.5
        },
    },
    ClimateZone.ARCTIC: {
        "name": "Arctic",
        "icon": "🧊",
        "latitude_range": (75, 90),
        "base_temperature": -0.5,
        "humidity": 0.2,
        "seasonal_variation": 0.3,
        "description": "Frozen realm of eternal winter",
        "weather_modifiers": {
            "snow": 2.0, "frost": 2.0, "blizzard": 1.8,
            "heat": 0.0, "drought": 0.0, "rain": 0.3, "storm": 0.5
        },
    },
}


def get_climate_from_latitude(latitude: float) -> ClimateZone:
    """Determine climate zone from latitude (0-90)"""
    latitude = abs(latitude)  # Northern/Southern hemisphere same
    for zone, info in CLIMATE_INFO.items():
        low, high = info["latitude_range"]
        if low <= latitude < high:
            return zone
    return ClimateZone.ARCTIC


# =============================================================================
# WEATHER TYPES
# =============================================================================

class WeatherType(IntEnum):
    """Base weather types"""
    CLEAR = 0
    CLOUDY = 1
    OVERCAST = 2
    FOG = 3
    MIST = 4
    RAIN = 5
    DRIZZLE = 6
    DOWNPOUR = 7
    STORM = 8
    THUNDERSTORM = 9
    SNOW = 10
    SLEET = 11
    HAIL = 12
    BLIZZARD = 13
    FROST = 14
    HEAT = 15
    DROUGHT = 16
    WIND = 17
    GALE = 18
    HURRICANE = 19


# Weather combinations - when multiple conditions combine
WEATHER_COMBINATIONS = {
    # (base, modifier) -> combined
    (WeatherType.RAIN, WeatherType.WIND): WeatherType.STORM,
    (WeatherType.STORM, WeatherType.WIND): WeatherType.THUNDERSTORM,
    (WeatherType.SNOW, WeatherType.WIND): WeatherType.BLIZZARD,
    (WeatherType.RAIN, WeatherType.FROST): WeatherType.SLEET,
    (WeatherType.CLOUDY, WeatherType.WIND): WeatherType.OVERCAST,
    (WeatherType.CLEAR, WeatherType.FROST): WeatherType.FROST,
    (WeatherType.CLEAR, WeatherType.HEAT): WeatherType.HEAT,
    (WeatherType.HEAT, WeatherType.WIND): WeatherType.DROUGHT,
    (WeatherType.WIND, WeatherType.GALE): WeatherType.HURRICANE,
}


WEATHER_INFO = {
    WeatherType.CLEAR: {
        "name": "Clear",
        "icon": "☀️",
        "intensity": 0.0,
        "visibility": 1.0,
        "mood": "hopeful",
        "color": "#87CEEB",
        "description": "Crystal clear skies",
        "effects": [],
    },
    WeatherType.CLOUDY: {
        "name": "Cloudy",
        "icon": "☁️",
        "intensity": 0.2,
        "visibility": 0.9,
        "mood": "neutral",
        "color": "#B0C4DE",
        "description": "Clouds drift lazily overhead",
        "effects": ["reduced_sunlight"],
    },
    WeatherType.OVERCAST: {
        "name": "Overcast",
        "icon": "🌥️",
        "intensity": 0.3,
        "visibility": 0.8,
        "mood": "somber",
        "color": "#708090",
        "description": "A heavy blanket of gray",
        "effects": ["reduced_sunlight", "oppressive"],
    },
    WeatherType.FOG: {
        "name": "Fog",
        "icon": "🌫️",
        "intensity": 0.4,
        "visibility": 0.3,
        "mood": "mysterious",
        "color": "#D3D3D3",
        "description": "Thick fog obscures all",
        "effects": ["low_visibility", "mysterious", "disorienting"],
    },
    WeatherType.MIST: {
        "name": "Mist",
        "icon": "🌁",
        "intensity": 0.2,
        "visibility": 0.6,
        "mood": "dreamy",
        "color": "#E0E0E0",
        "description": "A gentle mist hangs in the air",
        "effects": ["reduced_visibility", "ethereal"],
    },
    WeatherType.RAIN: {
        "name": "Rain",
        "icon": "🌧️",
        "intensity": 0.5,
        "visibility": 0.7,
        "mood": "melancholic",
        "color": "#4682B4",
        "description": "Rain patters steadily down",
        "effects": ["wet", "reduced_visibility", "ambient_sound"],
    },
    WeatherType.DRIZZLE: {
        "name": "Drizzle",
        "icon": "🌦️",
        "intensity": 0.3,
        "visibility": 0.85,
        "mood": "contemplative",
        "color": "#87CEEB",
        "description": "A light drizzle mists the air",
        "effects": ["damp", "gentle"],
    },
    WeatherType.DOWNPOUR: {
        "name": "Downpour",
        "icon": "⛈️",
        "intensity": 0.8,
        "visibility": 0.4,
        "mood": "oppressive",
        "color": "#2F4F4F",
        "description": "Sheets of rain pound the earth",
        "effects": ["soaked", "low_visibility", "loud", "flooding"],
    },
    WeatherType.STORM: {
        "name": "Storm",
        "icon": "🌧️💨",
        "intensity": 0.7,
        "visibility": 0.5,
        "mood": "turbulent",
        "color": "#4A5568",
        "description": "Wind and rain lash the land",
        "effects": ["wet", "windy", "dangerous"],
    },
    WeatherType.THUNDERSTORM: {
        "name": "Thunderstorm",
        "icon": "⛈️⚡",
        "intensity": 0.9,
        "visibility": 0.3,
        "mood": "dramatic",
        "color": "#1A1A2E",
        "description": "Thunder roars and lightning splits the sky",
        "effects": ["wet", "windy", "dangerous", "lightning", "dramatic"],
    },
    WeatherType.SNOW: {
        "name": "Snow",
        "icon": "🌨️",
        "intensity": 0.5,
        "visibility": 0.6,
        "mood": "serene",
        "color": "#F0F8FF",
        "description": "Snowflakes dance through the air",
        "effects": ["cold", "reduced_visibility", "quiet", "beautiful"],
    },
    WeatherType.SLEET: {
        "name": "Sleet",
        "icon": "🌨️💧",
        "intensity": 0.6,
        "visibility": 0.5,
        "mood": "harsh",
        "color": "#B0C4DE",
        "description": "Icy rain stings exposed skin",
        "effects": ["cold", "wet", "slippery", "unpleasant"],
    },
    WeatherType.HAIL: {
        "name": "Hail",
        "icon": "🌨️⚪",
        "intensity": 0.8,
        "visibility": 0.5,
        "mood": "violent",
        "color": "#E0E0E0",
        "description": "Ice pellets hammer down from above",
        "effects": ["dangerous", "damaging", "loud", "painful"],
    },
    WeatherType.BLIZZARD: {
        "name": "Blizzard",
        "icon": "❄️💨",
        "intensity": 1.0,
        "visibility": 0.1,
        "mood": "perilous",
        "color": "#F5F5F5",
        "description": "A wall of white, screaming wind and snow",
        "effects": ["freezing", "zero_visibility", "deadly", "disorienting"],
    },
    WeatherType.FROST: {
        "name": "Frost",
        "icon": "❄️",
        "intensity": 0.3,
        "visibility": 0.95,
        "mood": "crisp",
        "color": "#E0FFFF",
        "description": "A delicate layer of ice crystals",
        "effects": ["cold", "slippery", "beautiful", "fragile"],
    },
    WeatherType.HEAT: {
        "name": "Heat Wave",
        "icon": "🔥",
        "intensity": 0.7,
        "visibility": 0.8,
        "mood": "oppressive",
        "color": "#FF6347",
        "description": "Oppressive heat shimmers in the air",
        "effects": ["hot", "exhausting", "dehydrating", "haze"],
    },
    WeatherType.DROUGHT: {
        "name": "Drought",
        "icon": "🏜️",
        "intensity": 0.6,
        "visibility": 0.9,
        "mood": "desperate",
        "color": "#DEB887",
        "description": "The land cracks and thirsts",
        "effects": ["parched", "dying_vegetation", "water_scarcity"],
    },
    WeatherType.WIND: {
        "name": "Windy",
        "icon": "💨",
        "intensity": 0.4,
        "visibility": 0.9,
        "mood": "restless",
        "color": "#B0E0E6",
        "description": "Strong winds sweep across the land",
        "effects": ["windy", "noise", "movement"],
    },
    WeatherType.GALE: {
        "name": "Gale",
        "icon": "💨💨",
        "intensity": 0.8,
        "visibility": 0.7,
        "mood": "wild",
        "color": "#778899",
        "description": "Howling winds threaten to knock you down",
        "effects": ["very_windy", "dangerous", "loud", "debris"],
    },
    WeatherType.HURRICANE: {
        "name": "Hurricane",
        "icon": "🌀",
        "intensity": 1.0,
        "visibility": 0.2,
        "mood": "apocalyptic",
        "color": "#2F4F4F",
        "description": "Nature's fury unleashed",
        "effects": ["deadly", "destructive", "flooding", "zero_visibility"],
    },
}


# =============================================================================
# ATMOSPHERIC PHENOMENA (rare/special)
# =============================================================================

class AtmosphericPhenomenon(IntEnum):
    """Rare atmospheric events"""
    NONE = 0
    AURORA = 1          # Northern/Southern lights
    RAINBOW = 2         # After rain
    DOUBLE_RAINBOW = 3  # Rare beauty
    SUNDOG = 4          # Ice crystal halo
    MOONBOW = 5         # Lunar rainbow
    SHOOTING_STARS = 6  # Meteor shower
    ECLIPSE_SOLAR = 7   # Day turns to night
    ECLIPSE_LUNAR = 8   # Blood moon
    RING_AROUND_MOON = 9  # Weather sign
    CREPUSCULAR_RAYS = 10  # God rays through clouds
    FIRE_SKY = 11       # Intense sunset/sunrise
    GREEN_FLASH = 12    # Rare sunset phenomenon
    MAMMATUS_CLOUDS = 13  # Ominous bubble clouds
    LENTICULAR_CLOUDS = 14  # UFO-like clouds
    BIOLUMINESCENCE = 15  # Glowing water/plants (night)


PHENOMENON_INFO = {
    AtmosphericPhenomenon.NONE: {
        "name": "None",
        "icon": "",
        "rarity": 1.0,
        "description": "",
    },
    AtmosphericPhenomenon.AURORA: {
        "name": "Aurora",
        "icon": "🌌",
        "rarity": 0.05,
        "required_time": [TimeOfDay.NIGHT, TimeOfDay.MIDNIGHT],
        "required_climate": [ClimateZone.SUBARCTIC, ClimateZone.ARCTIC],
        "mood": "magical",
        "description": "Dancing lights ripple across the sky in ethereal greens and purples",
    },
    AtmosphericPhenomenon.RAINBOW: {
        "name": "Rainbow",
        "icon": "🌈",
        "rarity": 0.15,
        "required_weather_after": [WeatherType.RAIN, WeatherType.DRIZZLE, WeatherType.STORM],
        "mood": "hopeful",
        "description": "A brilliant arc of color spans the sky",
    },
    AtmosphericPhenomenon.DOUBLE_RAINBOW: {
        "name": "Double Rainbow",
        "icon": "🌈🌈",
        "rarity": 0.03,
        "required_weather_after": [WeatherType.RAIN, WeatherType.STORM],
        "mood": "wondrous",
        "description": "Two magnificent arcs shimmer in the clearing sky",
    },
    AtmosphericPhenomenon.SHOOTING_STARS: {
        "name": "Shooting Stars",
        "icon": "✨",
        "rarity": 0.08,
        "required_time": [TimeOfDay.NIGHT, TimeOfDay.MIDNIGHT],
        "required_weather": [WeatherType.CLEAR],
        "mood": "magical",
        "description": "Stars streak across the velvet sky",
    },
    AtmosphericPhenomenon.ECLIPSE_SOLAR: {
        "name": "Solar Eclipse",
        "icon": "🌑☀️",
        "rarity": 0.01,
        "required_time": [TimeOfDay.NOON, TimeOfDay.MORNING, TimeOfDay.AFTERNOON],
        "mood": "ominous",
        "description": "The moon swallows the sun, and day becomes night",
    },
    AtmosphericPhenomenon.ECLIPSE_LUNAR: {
        "name": "Blood Moon",
        "icon": "🌕🔴",
        "rarity": 0.02,
        "required_time": [TimeOfDay.NIGHT, TimeOfDay.MIDNIGHT],
        "mood": "dark",
        "description": "The moon turns blood red in Earth's shadow",
    },
    AtmosphericPhenomenon.CREPUSCULAR_RAYS: {
        "name": "God Rays",
        "icon": "☀️✨",
        "rarity": 0.12,
        "required_time": [TimeOfDay.DAWN, TimeOfDay.DUSK],
        "required_weather": [WeatherType.CLOUDY, WeatherType.OVERCAST],
        "mood": "divine",
        "description": "Shafts of golden light pierce through the clouds",
    },
    AtmosphericPhenomenon.FIRE_SKY: {
        "name": "Fire Sky",
        "icon": "🔥🌅",
        "rarity": 0.1,
        "required_time": [TimeOfDay.DAWN, TimeOfDay.DUSK],
        "mood": "dramatic",
        "description": "The entire sky burns with crimson and gold",
    },
    AtmosphericPhenomenon.MAMMATUS_CLOUDS: {
        "name": "Mammatus Clouds",
        "icon": "☁️⚠️",
        "rarity": 0.04,
        "required_weather": [WeatherType.STORM, WeatherType.THUNDERSTORM],
        "mood": "ominous",
        "description": "Bulbous, ominous clouds hang heavy with portent",
    },
    AtmosphericPhenomenon.BIOLUMINESCENCE: {
        "name": "Bioluminescence",
        "icon": "✨💧",
        "rarity": 0.06,
        "required_time": [TimeOfDay.NIGHT, TimeOfDay.MIDNIGHT],
        "required_climate": [ClimateZone.TROPICAL, ClimateZone.SUBTROPICAL],
        "mood": "magical",
        "description": "The water and plants glow with ethereal blue-green light",
    },
}


# =============================================================================
# WEATHER STATE
# =============================================================================

@dataclass
class WeatherState:
    """Complete atmospheric state"""
    # Core weather
    weather: WeatherType = WeatherType.CLEAR
    intensity: float = 0.5  # 0.0-1.0, how strong

    # Time
    time_of_day: TimeOfDay = TimeOfDay.NOON

    # Season and climate
    season: Season = Season.SUMMER
    climate: ClimateZone = ClimateZone.TEMPERATE
    latitude: float = 45.0  # degrees

    # Temperature (-1.0 frozen to 1.0 scorching)
    temperature: float = 0.3

    # Wind
    wind_speed: float = 0.2  # 0.0-1.0
    wind_direction: str = "N"  # N, NE, E, SE, S, SW, W, NW

    # Special phenomena
    phenomenon: AtmosphericPhenomenon = AtmosphericPhenomenon.NONE

    # Derived mood (computed from all factors)
    mood: str = "neutral"

    # Duration tracking
    hours_since_change: int = 0

    def get_effective_visibility(self) -> float:
        """Calculate visibility from weather and time"""
        weather_vis = WEATHER_INFO[self.weather]["visibility"]
        time_light = TIME_OF_DAY_INFO[self.time_of_day]["light_level"]
        return weather_vis * (0.3 + 0.7 * time_light)

    def get_effective_temperature(self) -> float:
        """Calculate temperature from climate, season, time, weather"""
        base = CLIMATE_INFO[self.climate]["base_temperature"]
        seasonal = SEASON_INFO[self.season]["temperature_modifier"]

        # Time of day modifier
        time_mod = 0.0
        if self.time_of_day in [TimeOfDay.NOON, TimeOfDay.AFTERNOON]:
            time_mod = 0.15
        elif self.time_of_day in [TimeOfDay.NIGHT, TimeOfDay.MIDNIGHT]:
            time_mod = -0.15

        # Weather modifier
        weather_mod = 0.0
        if self.weather == WeatherType.HEAT:
            weather_mod = 0.3
        elif self.weather in [WeatherType.SNOW, WeatherType.BLIZZARD, WeatherType.FROST]:
            weather_mod = -0.3
        elif self.weather == WeatherType.RAIN:
            weather_mod = -0.1

        return max(-1.0, min(1.0, base + seasonal + time_mod + weather_mod))

    def get_description(self) -> str:
        """Generate atmospheric description"""
        weather_desc = WEATHER_INFO[self.weather]["description"]
        time_desc = TIME_OF_DAY_INFO[self.time_of_day]["description"]

        parts = [time_desc, weather_desc]

        if self.phenomenon != AtmosphericPhenomenon.NONE:
            phenom_info = PHENOMENON_INFO.get(self.phenomenon, {})
            if phenom_info.get("description"):
                parts.append(phenom_info["description"])

        return ". ".join(parts) + "."

    def get_mood(self) -> str:
        """Determine overall atmospheric mood"""
        weather_mood = WEATHER_INFO[self.weather].get("mood", "neutral")
        time_mood = TIME_OF_DAY_INFO[self.time_of_day].get("mood_modifier", "neutral")

        # Phenomenon can override
        if self.phenomenon != AtmosphericPhenomenon.NONE:
            phenom_mood = PHENOMENON_INFO.get(self.phenomenon, {}).get("mood")
            if phenom_mood:
                return phenom_mood

        # Combine moods (weather usually dominates)
        if self.intensity > 0.7:
            return weather_mood

        # Blend based on time
        mood_priority = ["apocalyptic", "perilous", "dramatic", "ominous",
                        "magical", "wondrous", "divine", "mysterious",
                        "melancholic", "somber", "restless", "harsh",
                        "hopeful", "serene", "dreamy", "contemplative",
                        "vibrant", "warm", "fresh", "neutral"]

        for mood in mood_priority:
            if mood in [weather_mood, time_mood]:
                return mood

        return "neutral"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "weather": self.weather.name,
            "intensity": self.intensity,
            "time_of_day": self.time_of_day.name,
            "season": self.season.name,
            "climate": self.climate.name,
            "latitude": self.latitude,
            "temperature": self.get_effective_temperature(),
            "wind_speed": self.wind_speed,
            "wind_direction": self.wind_direction,
            "phenomenon": self.phenomenon.name,
            "mood": self.get_mood(),
            "visibility": self.get_effective_visibility(),
            "description": self.get_description(),
        }


# =============================================================================
# WEATHER GENERATOR
# =============================================================================

class WeatherGenerator:
    """Generates and evolves weather states"""

    def __init__(self, seed: int = None,
                 latitude: float = 45.0,
                 season: Season = None):
        self.rng = random.Random(seed)
        self.latitude = latitude
        self.climate = get_climate_from_latitude(latitude)
        self.season = season if season is not None else self.rng.choice(list(Season))

        self.state = WeatherState(
            climate=self.climate,
            latitude=latitude,
            season=self.season
        )

    def generate_initial(self, time_of_day: TimeOfDay = None) -> WeatherState:
        """Generate initial weather state"""
        if time_of_day is None:
            time_of_day = self.rng.choice(list(TimeOfDay))

        self.state.time_of_day = time_of_day
        self.state.weather = self._pick_weather()
        self.state.intensity = self.rng.uniform(0.3, 0.8)
        self.state.wind_speed = self.rng.uniform(0.0, 0.5)
        self.state.wind_direction = self.rng.choice(
            ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        )
        self.state.mood = self.state.get_mood()

        # Check for phenomenon
        self._maybe_add_phenomenon()

        return self.state

    def _pick_weather(self) -> WeatherType:
        """Pick weather based on season and climate"""
        season_weights = SEASON_INFO[self.season].get("weather_weights", {})
        climate_mods = CLIMATE_INFO[self.climate].get("weather_modifiers", {})

        # Build probability distribution
        weather_probs = {}
        for wtype in WeatherType:
            base_name = wtype.name.lower()

            # Start with season weight or default
            prob = season_weights.get(base_name, 0.1)

            # Apply climate modifier
            mod = climate_mods.get(base_name, 1.0)
            prob *= mod

            weather_probs[wtype] = max(0, prob)

        # Normalize
        total = sum(weather_probs.values())
        if total == 0:
            return WeatherType.CLEAR

        # Pick weighted random
        r = self.rng.random() * total
        cumulative = 0
        for wtype, prob in weather_probs.items():
            cumulative += prob
            if r <= cumulative:
                return wtype

        return WeatherType.CLEAR

    def _maybe_add_phenomenon(self):
        """Potentially add rare atmospheric phenomenon"""
        self.state.phenomenon = AtmosphericPhenomenon.NONE

        for phenom, info in PHENOMENON_INFO.items():
            if phenom == AtmosphericPhenomenon.NONE:
                continue

            # Check requirements
            if "required_time" in info:
                if self.state.time_of_day not in info["required_time"]:
                    continue

            if "required_climate" in info:
                if self.climate not in info["required_climate"]:
                    continue

            if "required_weather" in info:
                if self.state.weather not in info["required_weather"]:
                    continue

            # Roll for it
            if self.rng.random() < info["rarity"]:
                self.state.phenomenon = phenom
                return

    def advance_time(self, hours: int = 1) -> WeatherState:
        """Advance time and potentially change weather"""
        # Advance time of day
        current_idx = self.state.time_of_day.value
        new_idx = (current_idx + (hours // 3)) % len(TimeOfDay)
        self.state.time_of_day = TimeOfDay(new_idx)

        self.state.hours_since_change += hours

        # Weather change probability increases over time
        change_prob = min(0.8, self.state.hours_since_change * 0.05)

        if self.rng.random() < change_prob:
            # Change weather
            old_weather = self.state.weather
            self.state.weather = self._pick_weather()
            self.state.intensity = self.rng.uniform(0.3, 0.8)
            self.state.hours_since_change = 0

            # Check for weather combinations
            for (base, mod), result in WEATHER_COMBINATIONS.items():
                if old_weather == base and self.state.weather == mod:
                    self.state.weather = result
                    self.state.intensity = min(1.0, self.state.intensity + 0.2)
                    break

        # Wind changes more frequently
        if self.rng.random() < 0.3:
            self.state.wind_speed = max(0, min(1.0,
                self.state.wind_speed + self.rng.uniform(-0.2, 0.2)
            ))

        if self.rng.random() < 0.1:
            directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
            idx = directions.index(self.state.wind_direction)
            idx = (idx + self.rng.choice([-1, 1])) % len(directions)
            self.state.wind_direction = directions[idx]

        # Recheck phenomena
        self._maybe_add_phenomenon()

        self.state.mood = self.state.get_mood()

        return self.state

    def set_season(self, season: Season):
        """Change the season"""
        self.season = season
        self.state.season = season

    def advance_season(self) -> Season:
        """Move to next season"""
        new_season = Season((self.season.value + 1) % len(Season))
        self.set_season(new_season)
        return new_season


# =============================================================================
# WEATHER-GENRE INTERACTIONS
# =============================================================================

# How different genres prefer different weather
GENRE_WEATHER_PREFERENCES = {
    "fantasy": {
        WeatherType.CLEAR: 1.0,
        WeatherType.STORM: 1.2,
        WeatherType.FOG: 1.1,
    },
    "dark_fantasy": {
        WeatherType.OVERCAST: 1.3,
        WeatherType.FOG: 1.4,
        WeatherType.STORM: 1.2,
        WeatherType.THUNDERSTORM: 1.3,
        WeatherType.CLEAR: 0.6,
    },
    "solarpunk": {
        WeatherType.CLEAR: 1.5,
        WeatherType.DRIZZLE: 1.2,
        WeatherType.HEAT: 0.8,
        WeatherType.STORM: 0.7,
    },
    "hopepunk": {
        WeatherType.CLEAR: 1.3,
        WeatherType.RAIN: 1.1,  # Rain can be hopeful
        WeatherType.STORM: 0.8,
    },
    "cozy": {
        WeatherType.SNOW: 1.4,
        WeatherType.RAIN: 1.2,  # Cozy inside
        WeatherType.DRIZZLE: 1.3,
        WeatherType.CLEAR: 1.0,
        WeatherType.STORM: 0.6,
    },
    "iyashikei": {
        WeatherType.CLEAR: 1.3,
        WeatherType.DRIZZLE: 1.2,
        WeatherType.MIST: 1.4,
        WeatherType.SNOW: 1.2,
        WeatherType.STORM: 0.4,
    },
    "mystery": {
        WeatherType.FOG: 1.5,
        WeatherType.OVERCAST: 1.3,
        WeatherType.RAIN: 1.2,
        WeatherType.MIST: 1.3,
        WeatherType.CLEAR: 0.7,
    },
    "luminous": {
        WeatherType.CLEAR: 1.5,
        WeatherType.MIST: 1.2,  # Ethereal
        WeatherType.FROST: 1.3,
        WeatherType.STORM: 0.5,
    },
}


def create_weather_for_genre(genre_name: str, seed: int = None,
                             latitude: float = 45.0,
                             season: Season = None) -> WeatherState:
    """Create weather appropriate for a genre"""
    gen = WeatherGenerator(seed=seed, latitude=latitude, season=season)
    state = gen.generate_initial()

    # Apply genre preferences
    prefs = GENRE_WEATHER_PREFERENCES.get(genre_name, {})
    if prefs:
        # Re-roll weather with genre bias
        rng = random.Random(seed)

        best_weather = state.weather
        best_score = prefs.get(state.weather, 1.0)

        for _ in range(3):  # Try a few times
            candidate = gen._pick_weather()
            score = prefs.get(candidate, 1.0) * rng.uniform(0.8, 1.2)
            if score > best_score:
                best_weather = candidate
                best_score = score

        state.weather = best_weather
        state.mood = state.get_mood()

    return state
