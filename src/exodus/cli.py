from __future__ import annotations

from .simulation.config import SimulationConfig
from .simulation.runner import SimulationRunner


def main() -> None:
    config = SimulationConfig.default()
    runner = SimulationRunner.from_config(config)
    report = runner.run(turns=5)
    print(report.render())


if __name__ == "__main__":
    main()

