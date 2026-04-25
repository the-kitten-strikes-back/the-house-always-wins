from __future__ import annotations

from dataclasses import dataclass, field

from .entities import Alliance, Conflict, Galaxy


@dataclass(slots=True)
class SimulationState:
    turn: int = 0
    galaxies: list[Galaxy] = field(default_factory=list)
    conflicts: list[Conflict] = field(default_factory=list)
    alliances: list[Alliance] = field(default_factory=list)
    event_log: list[str] = field(default_factory=list)

    def record(self, message: str) -> None:
        self.event_log.append(f"Turn {self.turn}: {message}")

