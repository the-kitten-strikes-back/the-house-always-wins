from __future__ import annotations

from dataclasses import dataclass

from exodus.domain.state import SimulationState


@dataclass(slots=True)
class SimulationReport:
    state: SimulationState

    def render(self) -> str:
        factions = list(self.state.iter_factions())
        planets = list(self.state.iter_planets())
        active_conflicts = [conflict for conflict in self.state.conflicts if not conflict.resolved]
        total_population = sum(faction.population for faction in factions)
        avg_tech = sum(faction.technology.level for faction in factions) / max(1, len(factions))
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
            f"Ecologically strained worlds: {strained_worlds}",
            "",
            "Recent events:",
        ]
        lines.extend(self.state.event_log[-10:] or ["No events recorded."])
        return "\n".join(lines)
