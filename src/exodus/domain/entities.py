from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Galaxy:
    name: str
    star_systems: list["StarSystem"] = field(default_factory=list)


@dataclass(slots=True)
class StarSystem:
    name: str
    planets: list["Planet"] = field(default_factory=list)


@dataclass(slots=True)
class Planet:
    name: str
    biome: str
    climate_band: str
    habitability: float
    resources: int
    carrying_capacity: int
    infrastructure: float
    stability_modifier: float
    strategic_value: float
    species: list["Species"] = field(default_factory=list)
    factions: list["Faction"] = field(default_factory=list)


@dataclass(slots=True)
class Species:
    name: str
    intelligence: float
    aggression: float
    adaptability: float
    curiosity: float
    resilience: float
    collectivism: float
    preferred_biomes: tuple[str, ...]


@dataclass(slots=True)
class TechnologyTree:
    level: int = 1
    research_points: float = 0.0
    fields: dict[str, float] = field(
        default_factory=lambda: {
            "propulsion": 0.0,
            "warfare": 0.0,
            "biology": 0.0,
            "computing": 0.0,
            "materials": 0.0,
            "energy": 0.0,
        }
    )
    doctrines: list[str] = field(default_factory=list)
    breakthroughs: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Faction:
    name: str
    species_name: str
    homeworld: str
    ideology: str
    population: int
    stability: float
    military_power: float
    diplomacy: float
    economy: float
    cohesion: float
    morale: float
    industrial_capacity: float
    logistics: float
    espionage: float
    food_security: float
    energy_security: float
    research_focus: str
    technology: TechnologyTree = field(default_factory=TechnologyTree)
    relations: dict[str, float] = field(default_factory=dict)

    def strategic_posture(self) -> float:
        return round((self.military_power * 0.4) + (self.espionage * 0.2) + (self.logistics * 0.2) + (1 - self.diplomacy) * 0.2, 2)


@dataclass(slots=True)
class Conflict:
    attacker: str
    defender: str
    theatre: str
    intensity: float
    turn_started: int
    turn_resolved: int | None = None
    casualties: int = 0
    devastation: float = 0.0
    resolved: bool = False


@dataclass(slots=True)
class Alliance:
    members: tuple[str, str]
    trust: float
    purpose: str
