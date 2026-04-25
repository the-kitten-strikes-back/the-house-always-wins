from __future__ import annotations

from itertools import combinations

from exodus.domain.entities import Conflict
from exodus.domain.state import SimulationState
from exodus.engine.base import SimulationSystem


class WarfareSystem(SimulationSystem):
    def update(self, state: SimulationState) -> None:
        factions = list(state.iter_factions())

        for left, right in combinations(factions, 2):
            hostility = 1 - ((left.relations.get(right.name, 0.5) + right.relations.get(left.name, 0.5)) / 2)
            pressure = (
                (left.military_power + right.military_power) / 2 * hostility
                + abs(left.ideology != right.ideology) * 0.08
                + abs(left.strategic_posture() - right.strategic_posture()) * 0.05
            )
            if pressure > 0.62 and not _active_conflict(state, left.name, right.name):
                state.conflicts.append(
                    Conflict(
                        attacker=left.name,
                        defender=right.name,
                        theatre=_select_theatre(left, right),
                        intensity=round(pressure, 2),
                        turn_started=state.turn,
                    )
                )
                state.record(f"War erupted between {left.name} and {right.name} in the {state.conflicts[-1].theatre}.")

        for conflict in state.conflicts:
            if conflict.resolved:
                continue
            attacker = state.get_faction(conflict.attacker)
            defender = state.get_faction(conflict.defender)
            if attacker is None or defender is None:
                conflict.resolved = True
                continue

            conflict_length = state.turn - conflict.turn_started + 1
            attacker_force = attacker.military_power + attacker.logistics + attacker.technology.fields["warfare"] * 0.06
            defender_force = defender.military_power + defender.logistics + defender.technology.fields["materials"] * 0.04
            battle_pressure = max(0.08, conflict.intensity + abs(attacker_force - defender_force) * 0.18)
            casualties = int((attacker.population + defender.population) * battle_pressure * 0.0025)
            devastation = round(min(1.0, conflict.devastation + battle_pressure * 0.06), 2)

            attacker_loss = max(20_000, int(casualties * (0.45 + defender_force * 0.1)))
            defender_loss = max(20_000, int(casualties * (0.55 + attacker_force * 0.1)))
            attacker.population = max(100_000, attacker.population - attacker_loss)
            defender.population = max(100_000, defender.population - defender_loss)
            attacker.morale = _bounded(attacker.morale - battle_pressure * 0.08)
            defender.morale = _bounded(defender.morale - battle_pressure * 0.08)
            attacker.stability = _bounded(attacker.stability - battle_pressure * 0.05)
            defender.stability = _bounded(defender.stability - battle_pressure * 0.06)
            attacker.military_power = _bounded(attacker.military_power - battle_pressure * 0.02 + 0.01)
            defender.military_power = _bounded(defender.military_power - battle_pressure * 0.02 + 0.01)
            attacker.relations[defender.name] = _bounded(attacker.relations.get(defender.name, 0.5) - 0.12)
            defender.relations[attacker.name] = _bounded(defender.relations.get(attacker.name, 0.5) - 0.12)
            conflict.casualties += attacker_loss + defender_loss
            conflict.devastation = devastation

            state.record(
                f"{conflict.attacker} and {conflict.defender} fought in the {conflict.theatre}; "
                f"casualties={attacker_loss + defender_loss:,}, devastation={devastation:.2f}."
            )

            exhaustion = (
                (1 - attacker.morale)
                + (1 - defender.morale)
                + conflict.devastation
                + conflict_length * 0.12
            )
            if exhaustion > 1.55 or attacker.population < 700_000 or defender.population < 700_000:
                conflict.resolved = True
                state.record(
                    f"The conflict between {conflict.attacker} and {conflict.defender} subsided after "
                    f"{conflict.casualties:,} casualties."
                )


def _active_conflict(state: SimulationState, left: str, right: str) -> bool:
    member_pair = {left, right}
    return any(
        not conflict.resolved and {conflict.attacker, conflict.defender} == member_pair for conflict in state.conflicts
    )


def _select_theatre(attacker, defender) -> str:
    if attacker.technology.fields["propulsion"] + defender.technology.fields["propulsion"] > 2.4:
        return "deep void"
    if attacker.homeworld == defender.homeworld:
        return "homeworld orbit"
    return "frontier corridor"


def _bounded(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 2)
