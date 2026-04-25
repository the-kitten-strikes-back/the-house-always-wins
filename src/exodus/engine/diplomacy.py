from __future__ import annotations

from itertools import combinations

from exodus.domain.entities import Alliance
from exodus.domain.state import SimulationState
from exodus.engine.base import SimulationSystem


class DiplomacySystem(SimulationSystem):
    def update(self, state: SimulationState) -> None:
        factions = list(state.iter_factions())

        for alliance in list(state.alliances):
            left = state.get_faction(alliance.members[0])
            right = state.get_faction(alliance.members[1])
            if left is None or right is None:
                state.alliances.remove(alliance)
                continue
            alliance_modifier = 0.02 if alliance.purpose == "research" else 0.01
            alliance.trust = _bounded(alliance.trust + alliance_modifier - abs(left.ideology != right.ideology) * 0.01)
            if alliance.trust < 0.42:
                state.alliances.remove(alliance)
                left.relations[right.name] = _bounded(left.relations.get(right.name, 0.5) - 0.12)
                right.relations[left.name] = _bounded(right.relations.get(left.name, 0.5) - 0.12)
                state.record(f"The alliance between {left.name} and {right.name} fractured.")

        for left, right in combinations(factions, 2):
            rivalry_pressure = _rivalry_pressure(left, right)
            affinity = (
                (left.diplomacy + right.diplomacy) / 2
                + (left.cohesion + right.cohesion) * 0.08
                + (0.08 if left.ideology == right.ideology else -0.06)
            )
            espionage_friction = abs(left.espionage - right.espionage) * 0.05
            resource_envy = abs(left.economy - right.economy) * 0.05
            militarism = _militarism(left, right)
            trust = left.relations.get(right.name, affinity)
            trust = _bounded(
                trust
                + affinity * 0.018
                - espionage_friction
                - resource_envy
                - rivalry_pressure
                - militarism * 0.02
                - 0.004
            )
            left.relations[right.name] = trust
            right.relations[left.name] = trust

            if trust >= 0.72 and not _allied(state, left.name, right.name):
                purpose = _choose_alliance_purpose(left, right)
                state.alliances.append(Alliance(members=(left.name, right.name), trust=trust, purpose=purpose))
                state.record(f"{left.name} and {right.name} formed a {purpose} alliance.")


def _allied(state: SimulationState, left: str, right: str) -> bool:
    member_pair = {left, right}
    return any(set(alliance.members) == member_pair for alliance in state.alliances)


def _choose_alliance_purpose(left, right) -> str:
    if left.research_focus == right.research_focus:
        return "research"
    if left.economy + right.economy > left.military_power + right.military_power:
        return "trade"
    return "security"


def _militarism(left, right) -> float:
    score = 0.0
    if left.ideology in {"Militarist", "Expansionist"}:
        score += 0.5
    if right.ideology in {"Militarist", "Expansionist"}:
        score += 0.5
    return score


def _rivalry_pressure(left, right) -> float:
    return (
        abs(left.military_power - right.military_power) * 0.03
        + abs(left.population - right.population) / max(left.population + right.population, 1) * 0.05
        + abs(left.industrial_capacity - right.industrial_capacity) * 0.02
    )


def _bounded(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 2)
