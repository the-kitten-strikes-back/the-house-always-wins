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
    habitability: float
    resources: int
    species: list["Species"] = field(default_factory=list)
    factions: list["Faction"] = field(default_factory=list)


@dataclass(slots=True)
class Species:
    name: str
    intelligence: float
    aggression: float
    adaptability: float


@dataclass(slots=True)
class TechnologyTree:
    level: int = 1
    breakthroughs: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Faction:
    name: str
    species_name: str
    population: int
    stability: float
    military_power: float
    diplomacy: float
    economy: float
    technology: TechnologyTree = field(default_factory=TechnologyTree)
    relations: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class Conflict:
    attacker: str
    defender: str
    intensity: float
    turn_started: int
    resolved: bool = False


@dataclass(slots=True)
class Alliance:
    members: tuple[str, str]
    trust: float

