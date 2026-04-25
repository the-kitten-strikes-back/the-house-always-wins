from __future__ import annotations

from exodus.domain.entities import Faction, TechnologyTree
from exodus.domain.state import SimulationState
from exodus.engine.base import SimulationSystem


class ExpansionSystem(SimulationSystem):
    def update(self, state: SimulationState) -> None:
        planets = list(state.iter_planets())
        if not planets:
            return

        for source in planets:
            if not source.factions:
                continue
            targets = [planet for planet in planets if not planet.factions and planet is not source]
            if not targets:
                return

            for faction in list(source.factions):
                expansion_capacity = (
                    faction.logistics
                    + faction.technology.fields["propulsion"] * 0.08
                    + faction.energy_security
                    + faction.economy
                )
                if faction.population < 4_000_000 or expansion_capacity < 2.4:
                    continue

                best_target = max(
                    targets,
                    key=lambda planet: planet.habitability + planet.resources / 150 + planet.strategic_value * 0.3,
                )
                colony = _build_colony(faction, best_target.name)
                species = state.get_species(faction.species_name)
                if species is not None and not any(existing.name == species.name for existing in best_target.species):
                    best_target.species.append(species)
                best_target.factions.append(colony)
                faction.population = int(faction.population * 0.9)
                faction.stability = _bounded(faction.stability - 0.04)
                best_target.infrastructure = _bounded(best_target.infrastructure + 0.08)
                state.record(f"{faction.name} founded {colony.name} on {best_target.name}.")
                targets.remove(best_target)


def _build_colony(parent: Faction, target_world: str) -> Faction:
    return Faction(
        name=f"{parent.name} Colony",
        species_name=parent.species_name,
        homeworld=target_world,
        ideology=parent.ideology,
        population=max(500_000, int(parent.population * 0.12)),
        stability=max(0.3, round(parent.stability - 0.08, 2)),
        military_power=max(0.2, round(parent.military_power - 0.06, 2)),
        diplomacy=max(0.2, round(parent.diplomacy - 0.02, 2)),
        economy=max(0.2, round(parent.economy - 0.1, 2)),
        cohesion=max(0.25, round(parent.cohesion - 0.05, 2)),
        morale=max(0.25, round(parent.morale - 0.04, 2)),
        industrial_capacity=max(0.18, round(parent.industrial_capacity - 0.08, 2)),
        logistics=max(0.22, round(parent.logistics - 0.1, 2)),
        espionage=max(0.1, round(parent.espionage - 0.03, 2)),
        food_security=max(0.15, round(parent.food_security - 0.08, 2)),
        energy_security=max(0.15, round(parent.energy_security - 0.08, 2)),
        research_focus=parent.research_focus,
        technology=TechnologyTree(
            level=parent.technology.level,
            research_points=parent.technology.research_points * 0.25,
            fields={field: value * 0.7 for field, value in parent.technology.fields.items()},
            doctrines=list(parent.technology.doctrines),
            breakthroughs=list(parent.technology.breakthroughs),
        ),
        relations=dict(parent.relations),
    )


def _bounded(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 2)
