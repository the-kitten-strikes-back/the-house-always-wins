from __future__ import annotations

from exodus.domain.state import SimulationState
from exodus.engine.base import SimulationSystem


class TechnologySystem(SimulationSystem):
    def update(self, state: SimulationState) -> None:
        for galaxy in state.galaxies:
            for system in galaxy.star_systems:
                for planet in system.planets:
                    for faction in planet.factions:
                        innovation_pressure = faction.economy + faction.stability + (faction.population / 20_000_000)
                        if innovation_pressure > faction.technology.level + 0.9:
                            faction.technology.level += 1
                            breakthrough = f"Tier-{faction.technology.level} development"
                            faction.technology.breakthroughs.append(breakthrough)
                            state.record(f"{faction.name} unlocked {breakthrough}.")

