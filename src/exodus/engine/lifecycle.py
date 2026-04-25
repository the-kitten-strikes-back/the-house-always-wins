from __future__ import annotations

from exodus.domain.entities import Faction
from exodus.domain.state import SimulationState
from exodus.engine.base import SimulationSystem


class LifecycleSystem(SimulationSystem):
    def update(self, state: SimulationState) -> None:
        for galaxy in state.galaxies:
            for system in galaxy.star_systems:
                for planet in system.planets:
                    self._emerge_new_factions(state, planet.factions, planet.name)
                    self._collapse_unstable_factions(state, planet.factions, planet.name)

    def _emerge_new_factions(self, state: SimulationState, factions: list[Faction], planet_name: str) -> None:
        for faction in list(factions):
            if faction.population > 13_000_000 and faction.stability > 0.8:
                splinter_name = f"{faction.name} Frontier"
                if any(existing.name == splinter_name for existing in factions):
                    continue
                factions.append(
                    Faction(
                        name=splinter_name,
                        species_name=faction.species_name,
                        population=int(faction.population * 0.18),
                        stability=0.67,
                        military_power=max(0.2, faction.military_power - 0.08),
                        diplomacy=faction.diplomacy,
                        economy=max(0.3, faction.economy - 0.04),
                    )
                )
                faction.population = int(faction.population * 0.82)
                state.record(f"{splinter_name} emerged on {planet_name}.")

    def _collapse_unstable_factions(self, state: SimulationState, factions: list[Faction], planet_name: str) -> None:
        collapsed = [faction for faction in factions if faction.stability < 0.25 or faction.population < 500_000]
        for faction in collapsed:
            factions.remove(faction)
            state.record(f"{faction.name} collapsed on {planet_name}.")

