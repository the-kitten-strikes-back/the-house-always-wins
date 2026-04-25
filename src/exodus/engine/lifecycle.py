from __future__ import annotations

from exodus.domain.entities import Faction, TechnologyTree
from exodus.domain.state import SimulationState
from exodus.engine.base import SimulationSystem


class LifecycleSystem(SimulationSystem):
    def update(self, state: SimulationState) -> None:
        for planet in state.iter_planets():
            self._emerge_new_factions(state, planet.factions, planet.name)
            self._collapse_unstable_factions(state, planet.factions, planet.name)

    def _emerge_new_factions(self, state: SimulationState, factions: list[Faction], planet_name: str) -> None:
        for faction in list(factions):
            schism_pressure = (1 - faction.cohesion) + (1 - faction.stability) + (1 - faction.morale)
            if faction.population > 8_000_000 and schism_pressure < 0.95 and faction.technology.level >= 2:
                splinter_name = f"{faction.name} Frontier"
                if any(existing.name == splinter_name for existing in factions):
                    continue
                factions.append(
                    Faction(
                        name=splinter_name,
                        species_name=faction.species_name,
                        homeworld=planet_name,
                        ideology=faction.ideology,
                        population=int(faction.population * 0.18),
                        stability=0.62,
                        military_power=max(0.2, faction.military_power - 0.08),
                        diplomacy=faction.diplomacy,
                        economy=max(0.3, faction.economy - 0.04),
                        cohesion=max(0.28, faction.cohesion - 0.12),
                        morale=max(0.34, faction.morale - 0.08),
                        industrial_capacity=max(0.22, faction.industrial_capacity - 0.06),
                        logistics=max(0.24, faction.logistics - 0.05),
                        espionage=max(0.16, faction.espionage - 0.02),
                        food_security=max(0.2, faction.food_security - 0.05),
                        energy_security=max(0.2, faction.energy_security - 0.04),
                        research_focus=faction.research_focus,
                        technology=TechnologyTree(
                            level=faction.technology.level,
                            research_points=faction.technology.research_points * 0.35,
                            fields=dict(faction.technology.fields),
                            doctrines=list(faction.technology.doctrines),
                            breakthroughs=list(faction.technology.breakthroughs),
                        ),
                    )
                )
                faction.population = int(faction.population * 0.82)
                faction.cohesion = max(0.0, round(faction.cohesion - 0.08, 2))
                state.record(f"{splinter_name} emerged on {planet_name}.")

    def _collapse_unstable_factions(self, state: SimulationState, factions: list[Faction], planet_name: str) -> None:
        collapsed = [
            faction
            for faction in factions
            if faction.stability < 0.18 or faction.population < 350_000 or faction.food_security < 0.08
        ]
        for faction in collapsed:
            factions.remove(faction)
            state.record(f"{faction.name} collapsed on {planet_name}.")
