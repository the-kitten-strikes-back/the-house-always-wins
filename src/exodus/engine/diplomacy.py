from __future__ import annotations

from itertools import combinations

from exodus.domain.entities import Alliance
from exodus.domain.state import SimulationState
from exodus.engine.base import SimulationSystem


class DiplomacySystem(SimulationSystem):
    def update(self, state: SimulationState) -> None:
        factions = []
        for galaxy in state.galaxies:
            for system in galaxy.star_systems:
                for planet in system.planets:
                    factions.extend(planet.factions)

        for left, right in combinations(factions, 2):
            affinity = (left.diplomacy + right.diplomacy) / 2
            trust = left.relations.get(right.name, affinity)
            trust = min(1.0, trust + 0.03)
            left.relations[right.name] = trust
            right.relations[left.name] = trust

            if trust >= 0.8 and not _allied(state, left.name, right.name):
                state.alliances.append(Alliance(members=(left.name, right.name), trust=trust))
                state.record(f"{left.name} and {right.name} formed an alliance.")


def _allied(state: SimulationState, left: str, right: str) -> bool:
    member_pair = {left, right}
    return any(set(alliance.members) == member_pair for alliance in state.alliances)

