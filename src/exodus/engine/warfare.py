from __future__ import annotations

from itertools import combinations

from exodus.domain.entities import Conflict
from exodus.domain.state import SimulationState
from exodus.engine.base import SimulationSystem


class WarfareSystem(SimulationSystem):
    def update(self, state: SimulationState) -> None:
        factions = list(state.iter_factions())
        engaged_factions = {
            name
            for conflict in state.conflicts
            if not conflict.resolved
            for name in (conflict.attacker, conflict.defender)
        }
        new_conflicts_started = 0
        max_new_conflicts = max(1, len(factions) // 10)

        for left, right in combinations(factions, 2):
            if new_conflicts_started >= max_new_conflicts:
                break
            if _allied(state, left.name, right.name):
                continue
            if left.name in engaged_factions or right.name in engaged_factions:
                continue

            if _recently_resolved(state, left.name, right.name, cooldown=6):
                continue

            hostility = 1 - ((left.relations.get(right.name, 0.5) + right.relations.get(left.name, 0.5)) / 2)
            if hostility < 0.42:
                continue

            militarism = _militarism_pressure(left, right)
            expansionism = _expansion_pressure(left, right)
            tech_arms_race = abs(left.technology.fields["warfare"] - right.technology.fields["warfare"]) * 0.04
            kinship_drag = _kinship_drag(left, right)
            pressure = (
                (left.military_power + right.military_power) / 2 * hostility
                + abs(left.ideology != right.ideology) * 0.06
                + abs(left.strategic_posture() - right.strategic_posture()) * 0.05
                + militarism
                + expansionism
                + tech_arms_race
                - kinship_drag
            )
            if pressure > 0.68 and not _active_conflict(state, left.name, right.name):
                state.conflicts.append(
                    Conflict(
                        attacker=left.name,
                        defender=right.name,
                        theatre=_select_theatre(left, right),
                        intensity=round(pressure, 2),
                        turn_started=state.turn,
                    )
                )
                engaged_factions.update({left.name, right.name})
                new_conflicts_started += 1
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
            battle_pressure = max(0.06, conflict.intensity * 0.55 + abs(attacker_force - defender_force) * 0.1)
            casualties = int((attacker.population + defender.population) * battle_pressure * 0.0009)
            devastation = round(min(1.0, conflict.devastation + battle_pressure * 0.03), 2)

            attacker_loss = max(8_000, int(casualties * (0.45 + defender_force * 0.06)))
            defender_loss = max(8_000, int(casualties * (0.55 + attacker_force * 0.06)))
            attacker.population = max(100_000, attacker.population - attacker_loss)
            defender.population = max(100_000, defender.population - defender_loss)
            attacker.morale = _bounded(attacker.morale - battle_pressure * 0.04)
            defender.morale = _bounded(defender.morale - battle_pressure * 0.04)
            attacker.stability = _bounded(attacker.stability - battle_pressure * 0.03)
            defender.stability = _bounded(defender.stability - battle_pressure * 0.035)
            attacker.military_power = _bounded(attacker.military_power - battle_pressure * 0.012 + 0.008)
            defender.military_power = _bounded(defender.military_power - battle_pressure * 0.012 + 0.008)
            attacker.relations[defender.name] = _bounded(attacker.relations.get(defender.name, 0.5) - 0.05)
            defender.relations[attacker.name] = _bounded(defender.relations.get(attacker.name, 0.5) - 0.05)
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
                + conflict_length * 0.1
            )
            if exhaustion > 2.15 or attacker.population < 450_000 or defender.population < 450_000:
                conflict.resolved = True
                conflict.turn_resolved = state.turn
                state.record(
                    f"The conflict between {conflict.attacker} and {conflict.defender} subsided after "
                    f"{conflict.casualties:,} casualties."
                )


def _active_conflict(state: SimulationState, left: str, right: str) -> bool:
    member_pair = {left, right}
    return any(
        not conflict.resolved and {conflict.attacker, conflict.defender} == member_pair for conflict in state.conflicts
    )


def _allied(state: SimulationState, left: str, right: str) -> bool:
    member_pair = {left, right}
    return any(set(alliance.members) == member_pair for alliance in state.alliances)


def _recently_resolved(state: SimulationState, left: str, right: str, cooldown: int) -> bool:
    member_pair = {left, right}
    for conflict in reversed(state.conflicts):
        if {conflict.attacker, conflict.defender} != member_pair:
            continue
        if not conflict.resolved or conflict.turn_resolved is None:
            return False
        return state.turn - conflict.turn_resolved <= cooldown
    return False


def _militarism_pressure(left, right) -> float:
    pressure = 0.0
    if left.ideology == "Militarist":
        pressure += 0.04
    if right.ideology == "Militarist":
        pressure += 0.04
    if left.ideology == "Expansionist":
        pressure += 0.025
    if right.ideology == "Expansionist":
        pressure += 0.025
    return pressure


def _expansion_pressure(left, right) -> float:
    same_home_region = 0.03 if left.homeworld.split()[0] == right.homeworld.split()[0] else 0.0
    return same_home_region + abs(left.economy - right.economy) * 0.015


def _kinship_drag(left, right) -> float:
    drag = 0.0
    if left.species_name == right.species_name:
        drag += 0.08
    if left.ideology == right.ideology:
        drag += 0.03
    return drag


def _select_theatre(attacker, defender) -> str:
    if attacker.technology.fields["propulsion"] + defender.technology.fields["propulsion"] > 2.4:
        return "deep void"
    if attacker.homeworld == defender.homeworld:
        return "homeworld orbit"
    return "frontier corridor"


def _bounded(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 2)
