import unittest

from exodus.domain.factories import build_generated_state
from exodus.simulation.config import SimulationConfig
from exodus.simulation.runner import SimulationRunner


class SimulationRunnerTest(unittest.TestCase):
    def test_runner_advances_turns_and_records_events(self) -> None:
        runner = SimulationRunner.from_config(SimulationConfig.default())

        report = runner.run(turns=3)

        self.assertEqual(report.state.turn, 3)
        self.assertTrue(report.state.event_log)

    def test_procedural_generation_is_deterministic_from_seed(self) -> None:
        config = SimulationConfig.default()

        left = build_generated_state(
            random_seed=config.random_seed,
            galaxy_count=config.galaxy_count,
            star_system_range=config.star_system_range,
            planet_range=config.planet_range,
            faction_range=config.faction_range,
        )
        right = build_generated_state(
            random_seed=config.random_seed,
            galaxy_count=config.galaxy_count,
            star_system_range=config.star_system_range,
            planet_range=config.planet_range,
            faction_range=config.faction_range,
        )

        self.assertEqual(left.galaxies, right.galaxies)
        self.assertTrue(
            any(planet.factions for galaxy in left.galaxies for system in galaxy.star_systems for planet in system.planets)
        )


if __name__ == "__main__":
    unittest.main()
