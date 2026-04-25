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

## Next extension points

- Tune the procedural generation tables for stronger lore variety.
- Persist snapshots for long-running worlds.
- Add event logs, diplomacy AI, and combat resolution depth.
- Expose the simulation through an API or UI.
