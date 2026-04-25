import unittest

from exodus.domain.entities import Faction, Galaxy, Planet, StarSystem, TechnologyTree
from exodus.domain.state import SimulationState
from exodus.engine.expansion import ExpansionSystem
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
        first_planet = next(iter(left.iter_planets()))
        first_faction = next(iter(left.iter_factions()))
        self.assertTrue(first_planet.biome)
        self.assertGreater(first_planet.carrying_capacity, 0)
        self.assertTrue(first_faction.ideology)
        self.assertIn(first_faction.research_focus, {"propulsion", "warfare", "biology", "computing", "materials", "energy"})

    def test_expansion_stops_cleanly_when_targets_run_out(self) -> None:
        populated = Planet(
            name="Origin",
            biome="Terran",
            climate_band="Temperate",
            habitability=0.9,
            resources=80,
            carrying_capacity=20_000_000,
            infrastructure=0.7,
            stability_modifier=0.1,
            strategic_value=0.7,
            factions=[
                Faction(
                    name="Alpha Union",
                    species_name="Alpha",
                    homeworld="Origin",
                    ideology="Technocratic",
                    population=8_000_000,
                    stability=0.8,
                    military_power=0.5,
                    diplomacy=0.5,
                    economy=0.9,
                    cohesion=0.8,
                    morale=0.8,
                    industrial_capacity=0.8,
                    logistics=0.9,
                    espionage=0.4,
                    food_security=0.8,
                    energy_security=0.8,
                    research_focus="propulsion",
                    technology=TechnologyTree(fields={"propulsion": 5.0, "warfare": 0.0, "biology": 0.0, "computing": 0.0, "materials": 0.0, "energy": 0.0}),
                ),
                Faction(
                    name="Beta League",
                    species_name="Beta",
                    homeworld="Origin",
                    ideology="Technocratic",
                    population=8_500_000,
                    stability=0.8,
                    military_power=0.5,
                    diplomacy=0.5,
                    economy=0.9,
                    cohesion=0.8,
                    morale=0.8,
                    industrial_capacity=0.8,
                    logistics=0.9,
                    espionage=0.4,
                    food_security=0.8,
                    energy_security=0.8,
                    research_focus="propulsion",
                    technology=TechnologyTree(fields={"propulsion": 5.0, "warfare": 0.0, "biology": 0.0, "computing": 0.0, "materials": 0.0, "energy": 0.0}),
                ),
            ],
        )
        frontier = Planet(
            name="Frontier",
            biome="Terran",
            climate_band="Temperate",
            habitability=0.8,
            resources=70,
            carrying_capacity=10_000_000,
            infrastructure=0.2,
            stability_modifier=0.05,
            strategic_value=0.6,
        )
        state = SimulationState(
            galaxies=[Galaxy(name="Test Galaxy", star_systems=[StarSystem(name="Test System", planets=[populated, frontier])])]
        )

        ExpansionSystem().update(state)

        self.assertEqual(len(frontier.factions), 1)
        self.assertEqual(frontier.factions[0].homeworld, "Frontier")


if __name__ == "__main__":
    unittest.main()
