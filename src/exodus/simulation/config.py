from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SimulationConfig:
    random_seed: int
    galaxy_count: int
    star_system_range: tuple[int, int]
    planet_range: tuple[int, int]
    faction_range: tuple[int, int]

    @classmethod
    def default(cls) -> "SimulationConfig":
        return cls(
            random_seed=7,
            galaxy_count=2,
            star_system_range=(2, 4),
            planet_range=(2, 5),
            faction_range=(1, 2),
        )
