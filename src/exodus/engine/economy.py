from __future__ import annotations

from exodus.domain.state import SimulationState
from exodus.engine.base import SimulationSystem


class EconomySystem(SimulationSystem):
    def update(self, state: SimulationState) -> None:
        for galaxy in state.galaxies:
            for system in galaxy.star_systems:
                for planet in system.planets:
                    for faction in planet.factions:
                        growth = int(planet.resources * faction.economy * 120)
                        faction.population += growth
                        faction.stability = min(1.0, faction.stability + 0.01)
                        state.record(f"{faction.name} grew by {growth} citizens on {planet.name}.")

