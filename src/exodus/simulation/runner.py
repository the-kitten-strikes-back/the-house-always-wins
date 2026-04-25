from __future__ import annotations

from dataclasses import dataclass, field

from exodus.domain.factories import build_generated_state
from exodus.domain.state import SimulationState
from exodus.engine.diplomacy import DiplomacySystem
from exodus.engine.ecology import EcologySystem
from exodus.engine.economy import EconomySystem
from exodus.engine.expansion import ExpansionSystem
from exodus.engine.lifecycle import LifecycleSystem
from exodus.engine.technology import TechnologySystem
from exodus.engine.warfare import WarfareSystem
from exodus.simulation.config import SimulationConfig
from exodus.simulation.report import SimulationReport


@dataclass
class SimulationRunner:
    state: SimulationState
    systems: list = field(default_factory=list)

    @classmethod
    def from_config(cls, config: SimulationConfig) -> "SimulationRunner":
        state = build_generated_state(
            random_seed=config.random_seed,
            galaxy_count=config.galaxy_count,
            star_system_range=config.star_system_range,
            planet_range=config.planet_range,
            faction_range=config.faction_range,
        )
        systems = [
            EcologySystem(),
            EconomySystem(),
            TechnologySystem(),
            DiplomacySystem(),
            ExpansionSystem(),
            WarfareSystem(),
            LifecycleSystem(),
        ]
        return cls(state=state, systems=systems)

    def step(self) -> None:
        self.state.turn += 1
        for system in self.systems:
            system.update(self.state)

    def run(self, turns: int) -> SimulationReport:
        for _ in range(turns):
            self.step()
        return SimulationReport(state=self.state)
