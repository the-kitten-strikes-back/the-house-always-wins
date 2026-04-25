from __future__ import annotations

from exodus.domain.state import SimulationState
from exodus.engine.base import SimulationSystem


class TechnologySystem(SimulationSystem):
    def update(self, state: SimulationState) -> None:
        for faction in state.iter_factions():
            knowledge_pressure = (
                faction.economy * 0.2
                + faction.stability * 0.12
                + faction.industrial_capacity * 0.15
                + faction.energy_security * 0.12
                + faction.population / 40_000_000
            )
            faction.technology.research_points += knowledge_pressure

            focus_gain = 0.28 + faction.technology.level * 0.02
            faction.technology.fields[faction.research_focus] += focus_gain
            secondary_field = "computing" if faction.research_focus != "computing" else "materials"
            faction.technology.fields[secondary_field] += 0.18
            faction.technology.fields["energy"] += 0.05

            completed_fields = sum(
                1 for value in faction.technology.fields.values() if value >= max(0.6, faction.technology.level * 0.75)
            )
            if completed_fields >= 2 and faction.technology.research_points >= faction.technology.level * 1.05:
                faction.technology.level += 1
                doctrine = f"{faction.research_focus.title()} Doctrine {faction.technology.level}"
                breakthrough = f"Tier-{faction.technology.level} {faction.research_focus.title()} Breakthrough"
                faction.technology.doctrines.append(doctrine)
                faction.technology.breakthroughs.append(breakthrough)
                faction.technology.research_points = max(0.0, faction.technology.research_points - faction.technology.level)
                faction.economy = _bounded(faction.economy + 0.02)
                faction.military_power = _bounded(
                    faction.military_power + (0.03 if faction.research_focus == "warfare" else 0.01)
                )
                state.record(f"{faction.name} unlocked {breakthrough} and adopted {doctrine}.")


def _bounded(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 2)
