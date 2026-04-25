from __future__ import annotations

import random

from .entities import Faction, Galaxy, Planet, Species, StarSystem
from .state import SimulationState

GALAXY_PREFIXES = ["Andromeda", "Cygnus", "Orion", "Vela", "Draco", "Perseus", "Lyra", "Astra"]
SYSTEM_PREFIXES = ["Helios", "Nyx", "Vega", "Axiom", "Khepri", "Talon", "Cinder", "Erebus", "Lumen"]
PLANET_PREFIXES = ["Eden", "Kharon", "Vesta", "Mirage", "Thalos", "Iona", "Bastion", "Selene", "Aurelia"]
SPECIES_PREFIXES = ["Vor", "Ely", "Ka", "Sa", "Ty", "Oru", "Zen", "Myr", "Qua"]
SPECIES_SUFFIXES = ["ari", "eth", "ori", "uun", "yx", "ali", "ene", "or", "ith"]
FACTION_SUFFIXES = ["Union", "Compact", "Hegemony", "Collective", "Dynasty", "League", "Concord", "Assembly"]


def build_generated_state(
    *,
    random_seed: int,
    galaxy_count: int,
    star_system_range: tuple[int, int],
    planet_range: tuple[int, int],
    faction_range: tuple[int, int],
) -> SimulationState:
    rng = random.Random(random_seed)
    galaxies = [_build_galaxy(rng, index, star_system_range, planet_range, faction_range) for index in range(galaxy_count)]
    state = SimulationState(galaxies=galaxies)
    _ensure_intelligent_life(state, rng)
    state.record(
        f"Generated {len(state.galaxies)} galaxies from procedural seed {random_seed}."
    )
    return state


def _build_galaxy(
    rng: random.Random,
    galaxy_index: int,
    star_system_range: tuple[int, int],
    planet_range: tuple[int, int],
    faction_range: tuple[int, int],
) -> Galaxy:
    galaxy_name = _compose_name(rng, GALAXY_PREFIXES, "Expanse", galaxy_index)
    star_systems = [
        _build_star_system(rng, system_index, planet_range, faction_range)
        for system_index in range(rng.randint(*star_system_range))
    ]
    return Galaxy(name=galaxy_name, star_systems=star_systems)


def _build_star_system(
    rng: random.Random,
    system_index: int,
    planet_range: tuple[int, int],
    faction_range: tuple[int, int],
) -> StarSystem:
    system_name = _compose_name(rng, SYSTEM_PREFIXES, "System", system_index)
    planets = [
        _build_planet(rng, planet_index, faction_range)
        for planet_index in range(rng.randint(*planet_range))
    ]
    return StarSystem(name=system_name, planets=planets)


def _build_planet(rng: random.Random, planet_index: int, faction_range: tuple[int, int]) -> Planet:
    habitability = round(rng.uniform(0.18, 0.98), 2)
    resources = rng.randint(25, 100)
    species: list[Species] = []
    factions: list[Faction] = []
    planet_name = _compose_name(rng, PLANET_PREFIXES, "Prime", planet_index)

    if habitability >= 0.45 and rng.random() < 0.78:
        faction_count = rng.randint(*faction_range)
        for faction_index in range(faction_count):
            species.append(_build_species(rng, planet_name, faction_index))

        factions = [_build_faction(rng, species_entry, habitability, resources) for species_entry in species]

    return Planet(
        name=planet_name,
        habitability=habitability,
        resources=resources,
        species=species,
        factions=factions,
    )


def _build_species(rng: random.Random, planet_name: str, faction_index: int) -> Species:
    name = f"{rng.choice(SPECIES_PREFIXES)}{rng.choice(SPECIES_SUFFIXES)}"
    intelligence = round(rng.uniform(0.52, 0.97), 2)
    aggression = round(rng.uniform(0.18, 0.88), 2)
    adaptability = round(rng.uniform(0.34, 0.94), 2)
    return Species(
        name=f"{name} of {planet_name}-{faction_index + 1}",
        intelligence=intelligence,
        aggression=aggression,
        adaptability=adaptability,
    )


def _build_faction(rng: random.Random, species: Species, habitability: float, resources: int) -> Faction:
    species_root = species.name.split(" of ", maxsplit=1)[0]
    base_population = rng.randint(1_500_000, 11_000_000)
    population = int(base_population * (0.7 + habitability))
    stability = round(min(0.95, 0.35 + habitability * 0.4 + rng.uniform(0.0, 0.18)), 2)
    military_power = round(min(0.95, species.aggression * 0.5 + rng.uniform(0.15, 0.45)), 2)
    diplomacy = round(min(0.95, species.intelligence * 0.35 + (1 - species.aggression) * 0.4 + rng.uniform(0.1, 0.2)), 2)
    economy = round(min(0.95, resources / 140 + species.adaptability * 0.35 + rng.uniform(0.05, 0.16)), 2)
    return Faction(
        name=f"{species_root} {rng.choice(FACTION_SUFFIXES)}",
        species_name=species.name,
        population=population,
        stability=stability,
        military_power=military_power,
        diplomacy=diplomacy,
        economy=economy,
    )


def _ensure_intelligent_life(state: SimulationState, rng: random.Random) -> None:
    if any(planet.factions for galaxy in state.galaxies for system in galaxy.star_systems for planet in system.planets):
        return

    candidate = max(
        (
            planet
            for galaxy in state.galaxies
            for system in galaxy.star_systems
            for planet in system.planets
        ),
        key=lambda planet: (planet.habitability, planet.resources),
    )
    candidate.habitability = max(candidate.habitability, 0.72)
    emergent_species = _build_species(rng, candidate.name, 0)
    candidate.species.append(emergent_species)
    candidate.factions.append(_build_faction(rng, emergent_species, candidate.habitability, candidate.resources))


def _compose_name(rng: random.Random, prefixes: list[str], suffix: str, index: int) -> str:
    return f"{rng.choice(prefixes)} {suffix} {index + 1}"
