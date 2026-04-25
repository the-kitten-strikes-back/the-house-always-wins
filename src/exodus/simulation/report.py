from __future__ import annotations

from dataclasses import dataclass

from exodus.domain.state import SimulationState


@dataclass(slots=True)
class SimulationReport:
    state: SimulationState

    def render(self, max_events: int = 10, include_all_events: bool = False) -> str:
        factions = list(self.state.iter_factions())
        planets = list(self.state.iter_planets())
        active_conflicts = [conflict for conflict in self.state.conflicts if not conflict.resolved]
        resolved_conflicts = [conflict for conflict in self.state.conflicts if conflict.resolved]
        total_population = sum(faction.population for faction in factions)
        avg_tech = sum(faction.technology.level for faction in factions) / max(1, len(factions))
        total_casualties = sum(conflict.casualties for conflict in self.state.conflicts)
        strained_worlds = sum(
            1
            for planet in planets
            if sum(faction.population for faction in planet.factions) > planet.carrying_capacity
        )
        lines = [
            "EXODUS Simulation Report",
            f"Turns elapsed: {self.state.turn}",
            f"Galaxies: {len(self.state.galaxies)}",
            f"Colonised worlds: {len([planet for planet in planets if planet.factions])}",
            f"Factions: {len(factions)}",
            f"Population: {total_population:,}",
            f"Average tech tier: {avg_tech:.2f}",
            f"Alliances: {len(self.state.alliances)}",
            f"Conflicts: {len(active_conflicts)}",
            f"Resolved wars: {len(resolved_conflicts)}",
            f"Total wars recorded: {len(self.state.conflicts)}",
            f"War casualties: {total_casualties:,}",
            f"Ecologically strained worlds: {strained_worlds}",
            "",
            "All events:" if include_all_events else "Recent events:",
        ]
        if include_all_events:
            lines.extend(self.state.event_log or ["No events recorded."])
        else:
            lines.extend(self.state.event_log[-max_events:] or ["No events recorded."])
        return "\n".join(lines)
