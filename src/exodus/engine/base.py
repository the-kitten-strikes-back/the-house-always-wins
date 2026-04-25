from __future__ import annotations

from abc import ABC, abstractmethod

from exodus.domain.state import SimulationState


class SimulationSystem(ABC):
    @abstractmethod
    def update(self, state: SimulationState) -> None:
        """Advance one aspect of the simulation."""

