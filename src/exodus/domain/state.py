from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator

from .entities import Alliance, Conflict, Faction, Galaxy, Planet, Species


@dataclass(slots=True)
class SimulationState:
    turn: int = 0
    galaxies: list[Galaxy] = field(default_factory=list)
    conflicts: list[Conflict] = field(default_factory=list)
    alliances: list[Alliance] = field(default_factory=list)
    event_log: list[str] = field(default_factory=list)

    def record(self, message: str) -> None:
        self.event_log.append(f"Turn {self.turn}: {message}")

    def iter_planets(self) -> Iterator[Planet]:
        for galaxy in self.galaxies:
            for system in galaxy.star_systems:
                for planet in system.planets:
                    yield planet

    def iter_factions(self) -> Iterator[Faction]:
        for planet in self.iter_planets():
            yield from planet.factions

    def get_faction(self, name: str) -> Faction | None:
        for faction in self.iter_factions():
            if faction.name == name:
                return faction
        return None

    def get_species(self, name: str) -> Species | None:
        for planet in self.iter_planets():
            for species in planet.species:
                if species.name == name:
                    return species
        return None
