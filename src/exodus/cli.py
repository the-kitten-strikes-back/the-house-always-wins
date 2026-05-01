from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

from .simulation.config import SimulationConfig
from .simulation.runner import SimulationRunner


def main() -> None:
    args = _build_parser().parse_args()
    default_config = SimulationConfig.default()
    config = replace(
        default_config,
        random_seed=args.seed,
        galaxy_count=args.galaxies,
        star_system_range=(args.star_systems_min, args.star_systems_max),
        planet_range=(args.planets_min, args.planets_max),
        faction_range=(args.factions_min, args.factions_max),
    )

    _validate_ranges(config)

    if args.casino:
        from .visualization.casino import run_casino

        run_casino(
            config=config,
            window_size=(args.width, args.height),
        )
        return

    if args.viz:
        from .visualization.app import run_visualizer

        run_visualizer(
            config=config,
            turns_per_second=args.speed,
            window_size=(args.width, args.height),
        )
        return

    runner = SimulationRunner.from_config(config)
    report = runner.run(turns=args.turns)
    rendered_report = report.render(max_events=args.events, include_all_events=args.all_events)
    Path(args.output).write_text(rendered_report + "\n", encoding="utf-8")
    print(rendered_report)


def _build_parser() -> argparse.ArgumentParser:
    defaults = SimulationConfig.default()
    parser = argparse.ArgumentParser(description="Run the EXODUS civilisation simulation.")
    parser.add_argument("--viz", action="store_true", help="Launch the pygame visualization instead of text mode.")
    parser.add_argument("--casino", action="store_true", help="Launch the pygame casino betting game instead of text mode.")
    parser.add_argument("--turns", type=int, default=5, help="Number of turns to simulate in text mode.")
    parser.add_argument("--events", type=int, default=10, help="Number of recent events to include in text reports.")
    parser.add_argument("--all-events", action="store_true", help="Print the full event log in the final text report.")
    parser.add_argument("--output", default="report.txt", help="Path to write the text report to.")
    parser.add_argument("--seed", type=int, default=defaults.random_seed, help="Procedural generation seed.")
    parser.add_argument("--galaxies", type=int, default=defaults.galaxy_count, help="Number of galaxies to generate.")
    parser.add_argument(
        "--star-systems-min",
        type=int,
        default=defaults.star_system_range[0],
        help="Minimum star systems per galaxy.",
    )
    parser.add_argument(
        "--star-systems-max",
        type=int,
        default=defaults.star_system_range[1],
        help="Maximum star systems per galaxy.",
    )
    parser.add_argument(
        "--planets-min",
        type=int,
        default=defaults.planet_range[0],
        help="Minimum planets per star system.",
    )
    parser.add_argument(
        "--planets-max",
        type=int,
        default=defaults.planet_range[1],
        help="Maximum planets per star system.",
    )
    parser.add_argument(
        "--factions-min",
        type=int,
        default=defaults.faction_range[0],
        help="Minimum starting factions on viable worlds.",
    )
    parser.add_argument(
        "--factions-max",
        type=int,
        default=defaults.faction_range[1],
        help="Maximum starting factions on viable worlds.",
    )
    parser.add_argument("--speed", type=float, default=1.5, help="Visualizer turns per second.")
    parser.add_argument("--width", type=int, default=1440, help="Visualizer window width.")
    parser.add_argument("--height", type=int, default=900, help="Visualizer window height.")
    return parser


def _validate_ranges(config: SimulationConfig) -> None:
    if config.galaxy_count < 1:
        raise SystemExit("--galaxies must be at least 1")
    if config.star_system_range[0] < 1 or config.star_system_range[0] > config.star_system_range[1]:
        raise SystemExit("--star-systems-min must be >= 1 and <= --star-systems-max")
    if config.planet_range[0] < 1 or config.planet_range[0] > config.planet_range[1]:
        raise SystemExit("--planets-min must be >= 1 and <= --planets-max")
    if config.faction_range[0] < 1 or config.faction_range[0] > config.faction_range[1]:
        raise SystemExit("--factions-min must be >= 1 and <= --factions-max")


if __name__ == "__main__":
    main()
