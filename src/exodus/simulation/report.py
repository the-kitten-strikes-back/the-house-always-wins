from __future__ import annotations

from dataclasses import dataclass

from exodus.domain.state import SimulationState


@dataclass(slots=True)
class SimulationReport:
    state: SimulationState

    def render(self) -> str:
        lines = [
            "EXODUS Simulation Report",
            f"Turns elapsed: {self.state.turn}",
            f"Alliances: {len(self.state.alliances)}",
            f"Conflicts: {len([conflict for conflict in self.state.conflicts if not conflict.resolved])}",
            "",
            "Recent events:",
        ]
        lines.extend(self.state.event_log[-10:] or ["No events recorded."])
        return "\n".join(lines)

