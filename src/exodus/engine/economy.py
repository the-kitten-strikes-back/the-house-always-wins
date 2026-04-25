from __future__ import annotations

from exodus.domain.state import SimulationState
from exodus.engine.base import SimulationSystem


class EconomySystem(SimulationSystem):
    def update(self, state: SimulationState) -> None:
        for planet in state.iter_planets():
            total_population = sum(faction.population for faction in planet.factions) or 1
            capacity_ratio = total_population / max(planet.carrying_capacity, 1)
            resource_pressure = max(0.0, capacity_ratio - 0.9)

            planet.infrastructure = min(1.0, planet.infrastructure + 0.002 * max(1, len(planet.factions)))

            for faction in planet.factions:
                prosperity = (
                    faction.economy * 0.35
                    + faction.industrial_capacity * 0.22
                    + planet.infrastructure * 0.14
                    + faction.energy_security * 0.14
                    + faction.food_security * 0.15
                )
                growth_factor = prosperity - resource_pressure * 0.6 + (planet.habitability - 0.5) * 0.18
                growth = int(faction.population * growth_factor * 0.018)
                faction.population = max(100_000, faction.population + growth)

                faction.economy = _bounded(faction.economy + planet.resources / 1500 - resource_pressure * 0.08)
                faction.industrial_capacity = _bounded(
                    faction.industrial_capacity + planet.infrastructure * 0.02 - resource_pressure * 0.04
                )
                faction.food_security = _bounded(
                    faction.food_security + planet.habitability * 0.03 - resource_pressure * 0.08
                )
                faction.energy_security = _bounded(
                    faction.energy_security + planet.resources / 1800 + faction.technology.fields["energy"] * 0.01
                )
                faction.stability = _bounded(
                    faction.stability
                    + planet.stability_modifier * 0.08
                    + prosperity * 0.015
                    - resource_pressure * 0.1
                )
                faction.morale = _bounded(faction.morale + prosperity * 0.01 - resource_pressure * 0.06)

                state.record(
                    f"{faction.name} changed by {growth:+,} population on {planet.name}; "
                    f"prosperity={prosperity:.2f}, pressure={resource_pressure:.2f}."
                )


def _bounded(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 2)
