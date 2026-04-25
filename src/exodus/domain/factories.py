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
IDEOLOGIES = ["Expansionist", "Spiritual", "Technocratic", "Mercantile", "Ecologist", "Militarist", "Collectivist"]
RESEARCH_FIELDS = ["propulsion", "warfare", "biology", "computing", "materials", "energy"]
BIOMES = {
    "Oceanic": {"habitability": (0.65, 0.98), "resources": (45, 88), "capacity": (10_000_000, 28_000_000)},
    "Terran": {"habitability": (0.58, 0.95), "resources": (40, 84), "capacity": (8_000_000, 24_000_000)},
    "Desert": {"habitability": (0.22, 0.65), "resources": (55, 97), "capacity": (2_000_000, 10_000_000)},
    "Tundra": {"habitability": (0.25, 0.62), "resources": (38, 74), "capacity": (2_000_000, 8_000_000)},
    "Jungle": {"habitability": (0.52, 0.88), "resources": (52, 90), "capacity": (7_000_000, 19_000_000)},
    "Volcanic": {"habitability": (0.18, 0.48), "resources": (68, 100), "capacity": (1_000_000, 5_000_000)},
    "Ice": {"habitability": (0.12, 0.4), "resources": (28, 70), "capacity": (800_000, 4_000_000)},
    "Gas Colony": {"habitability": (0.14, 0.45), "resources": (62, 98), "capacity": (1_000_000, 6_000_000)},
}
CLIMATE_BANDS = ["Frozen", "Cold", "Temperate", "Warm", "Scorched"]


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
    _ensure_intelligent_life(state, rng, faction_range)
    state.record(f"Generated {len(state.galaxies)} galaxies from procedural seed {random_seed}.")
    state.record(f"Initial population: {sum(faction.population for faction in state.iter_factions()):,}.")
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
    biome = rng.choice(list(BIOMES))
    biome_profile = BIOMES[biome]
    habitability = round(rng.uniform(*biome_profile["habitability"]), 2)
    resources = rng.randint(*biome_profile["resources"])
    carrying_capacity = rng.randint(*biome_profile["capacity"])
    infrastructure = round(rng.uniform(0.08, 0.56), 2)
    strategic_value = round(min(1.0, resources / 100 + rng.uniform(0.0, 0.28)), 2)
    stability_modifier = round((habitability - 0.5) * 0.25 + rng.uniform(-0.04, 0.06), 2)
    planet_name = _compose_name(rng, PLANET_PREFIXES, "Prime", planet_index)

    species: list[Species] = []
    factions: list[Faction] = []
    if habitability >= 0.32 and rng.random() < habitability + 0.18:
        species_count = rng.randint(*faction_range) + (1 if habitability > 0.75 and rng.random() < 0.35 else 0)
        species = [_build_species(rng, planet_name, biome, index) for index in range(species_count)]
        factions = [_build_faction(rng, species_entry, planet_name, habitability, resources, infrastructure) for species_entry in species]

    return Planet(
        name=planet_name,
        biome=biome,
        climate_band=rng.choice(CLIMATE_BANDS),
        habitability=habitability,
        resources=resources,
        carrying_capacity=carrying_capacity,
        infrastructure=infrastructure,
        stability_modifier=stability_modifier,
        strategic_value=strategic_value,
        species=species,
        factions=factions,
    )


def _build_species(rng: random.Random, planet_name: str, biome: str, faction_index: int) -> Species:
    name = f"{rng.choice(SPECIES_PREFIXES)}{rng.choice(SPECIES_SUFFIXES)}"
    preferred_biomes = tuple(
        dict.fromkeys([biome, rng.choice(list(BIOMES)), rng.choice(list(BIOMES))])
    )
    return Species(
        name=f"{name} of {planet_name}-{faction_index + 1}",
        intelligence=round(rng.uniform(0.52, 0.97), 2),
        aggression=round(rng.uniform(0.18, 0.88), 2),
        adaptability=round(rng.uniform(0.34, 0.94), 2),
        curiosity=round(rng.uniform(0.24, 0.95), 2),
        resilience=round(rng.uniform(0.28, 0.96), 2),
        collectivism=round(rng.uniform(0.16, 0.92), 2),
        preferred_biomes=preferred_biomes,
    )


def _build_faction(
    rng: random.Random,
    species: Species,
    homeworld: str,
    habitability: float,
    resources: int,
    infrastructure: float,
) -> Faction:
    species_root = species.name.split(" of ", maxsplit=1)[0]
    ideology = rng.choice(IDEOLOGIES)
    research_focus = rng.choice(RESEARCH_FIELDS)
    base_population = rng.randint(1_200_000, 12_000_000)
    planetary_bonus = 0.55 + habitability + infrastructure * 0.4
    return Faction(
        name=f"{species_root} {rng.choice(FACTION_SUFFIXES)}",
        species_name=species.name,
        homeworld=homeworld,
        ideology=ideology,
        population=int(base_population * planetary_bonus),
        stability=round(min(0.95, 0.28 + habitability * 0.35 + infrastructure * 0.24 + rng.uniform(0.0, 0.16)), 2),
        military_power=round(min(0.95, species.aggression * 0.45 + species.resilience * 0.22 + rng.uniform(0.12, 0.28)), 2),
        diplomacy=round(min(0.95, species.intelligence * 0.28 + species.collectivism * 0.24 + rng.uniform(0.14, 0.24)), 2),
        economy=round(min(0.95, resources / 160 + infrastructure * 0.42 + species.adaptability * 0.22 + rng.uniform(0.08, 0.16)), 2),
        cohesion=round(min(0.95, species.collectivism * 0.45 + rng.uniform(0.2, 0.34)), 2),
        morale=round(min(0.95, 0.35 + habitability * 0.18 + rng.uniform(0.14, 0.28)), 2),
        industrial_capacity=round(min(0.95, infrastructure * 0.55 + resources / 190 + rng.uniform(0.05, 0.18)), 2),
        logistics=round(min(0.95, species.adaptability * 0.35 + infrastructure * 0.28 + rng.uniform(0.1, 0.2)), 2),
        espionage=round(min(0.95, species.intelligence * 0.25 + rng.uniform(0.08, 0.24)), 2),
        food_security=round(min(0.95, habitability * 0.55 + species.adaptability * 0.22 + rng.uniform(0.08, 0.18)), 2),
        energy_security=round(min(0.95, resources / 130 + infrastructure * 0.18 + rng.uniform(0.05, 0.15)), 2),
        research_focus=research_focus,
    )


def _ensure_intelligent_life(state: SimulationState, rng: random.Random, faction_range: tuple[int, int]) -> None:
    if any(planet.factions for planet in state.iter_planets()):
        return

    candidate = max(state.iter_planets(), key=lambda planet: (planet.habitability, planet.resources, planet.infrastructure))
    candidate.habitability = max(candidate.habitability, 0.72)
    candidate.infrastructure = max(candidate.infrastructure, 0.3)
    species = _build_species(rng, candidate.name, candidate.biome, 0)
    candidate.species.append(species)
    candidate.factions.append(
        _build_faction(rng, species, candidate.name, candidate.habitability, candidate.resources, candidate.infrastructure)
    )

    extra_factions = max(0, rng.randint(*faction_range) - 1)
    for index in range(extra_factions):
        sibling_species = _build_species(rng, candidate.name, candidate.biome, index + 1)
        candidate.species.append(sibling_species)
        candidate.factions.append(
            _build_faction(
                rng,
                sibling_species,
                candidate.name,
                candidate.habitability,
                candidate.resources,
                candidate.infrastructure,
            )
        )


def _compose_name(rng: random.Random, prefixes: list[str], suffix: str, index: int) -> str:
    return f"{rng.choice(prefixes)} {suffix} {index + 1}"
