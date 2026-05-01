# Project EXODUS

Project EXODUS is a Python civilisation simulation engine that models procedurally generated galaxies, star systems, planets, species, factions, wars, alliances, collapse, and technological progress.

## Architecture

The codebase is structured in layers:

- `exodus.domain`: core entities and simulation state.
- `exodus.engine`: simulation systems that evolve the world each turn.
- `exodus.simulation`: configuration, seeding, and high-level orchestration.
- `exodus.cli`: runnable entrypoint for local experimentation.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
exodus
```

Useful CLI examples:

```bash
exodus --turns 20 --seed 42 --galaxies 3
exodus --star-systems-min 3 --star-systems-max 6 --planets-min 2 --planets-max 7
exodus --factions-min 2 --factions-max 4 --events 20
exodus --turns 40 --all-events
exodus --turns 40 --all-events --output report.txt
```

To run the pygame visualizer:

```bash
pip install -e .[viz]
exodus --viz --speed 2.0 --width 1600 --height 1000
```

To run the pygame casino betting game:

```bash
pip install -e .[viz]
exodus --casino --width 1440 --height 900
```

If you want to run directly from the source tree without relying on the installed console scripts, prefix commands with `PYTHONPATH=src`:

```bash
PYTHONPATH=src python3 -m exodus.cli
PYTHONPATH=src python3 -m exodus.cli --viz --speed 2.0
PYTHONPATH=src python3 -m exodus.cli --casino --width 1440 --height 900
PYTHONPATH=src python3 -m unittest discover -s tests
```

Casino markets let players bet on the dominant faction, the most prominent ideology, planets destroyed during the next spin, and trade or war outcomes between faction pairs.

## Next extension points

- Tune the procedural generation tables for stronger lore variety.
- Persist snapshots for long-running worlds.
- Add event logs, diplomacy AI, and combat resolution depth.
- Expose the simulation through an API or UI.
