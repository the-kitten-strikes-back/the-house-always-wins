from __future__ import annotations

from itertools import combinations

from exodus.domain.entities import Conflict
from exodus.domain.state import SimulationState
from exodus.engine.base import SimulationSystem


class WarfareSystem(SimulationSystem):
    def update(self, state: SimulationState) -> None:
        factions = []
        for galaxy in state.galaxies:
            for system in galaxy.star_systems:
                for planet in system.planets:
                    factions.extend(planet.factions)

        for left, right in combinations(factions, 2):
            hostility = 1 - ((left.relations.get(right.name, 0.5) + right.relations.get(left.name, 0.5)) / 2)
            pressure = ((left.military_power + right.military_power) / 2) * hostility
            if pressure > 0.38 and not _active_conflict(state, left.name, right.name):
                state.conflicts.append(
                    Conflict(attacker=left.name, defender=right.name, intensity=pressure, turn_started=state.turn)
                )
                state.record(f"War erupted between {left.name} and {right.name}.")

        for conflict in state.conflicts:
            if conflict.resolved:
                continue
            if state.turn - conflict.turn_started >= 2:
                conflict.resolved = True
                state.record(f"The conflict between {conflict.attacker} and {conflict.defender} subsided.")


def _active_conflict(state: SimulationState, left: str, right: str) -> bool:
    member_pair = {left, right}
    return any(
        not conflict.resolved and {conflict.attacker, conflict.defender} == member_pair for conflict in state.conflicts
    )

