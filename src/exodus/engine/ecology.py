from __future__ import annotations

from exodus.domain.state import SimulationState
from exodus.engine.base import SimulationSystem


class EcologySystem(SimulationSystem):
    def update(self, state: SimulationState) -> None:
        for planet in state.iter_planets():
            population_load = sum(faction.population for faction in planet.factions)
            strain = population_load / max(planet.carrying_capacity, 1)
            development = sum(faction.industrial_capacity for faction in planet.factions) * 0.03

            planet.habitability = _bounded(planet.habitability - max(0.0, strain - 0.95) * 0.02 + 0.004)
            planet.resources = max(10, min(100, int(planet.resources - development + 1)))
            planet.stability_modifier = round(
                max(-0.25, min(0.25, planet.stability_modifier - max(0.0, strain - 1.0) * 0.03 + 0.004)),
                2,
            )

            if strain > 1.15:
                state.record(f"{planet.name} is under ecological strain; load={strain:.2f}.")


def _bounded(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 2)
