from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass

from exodus.domain.entities import Planet
from exodus.simulation.config import SimulationConfig
from exodus.simulation.runner import SimulationRunner

BIOME_COLORS = {
    "Oceanic": (73, 146, 214),
    "Terran": (108, 179, 100),
    "Desert": (209, 168, 92),
    "Tundra": (167, 189, 214),
    "Jungle": (66, 140, 84),
    "Volcanic": (194, 89, 62),
    "Ice": (206, 226, 240),
    "Gas Colony": (165, 122, 209),
}
BACKGROUND = (8, 12, 24)
PANEL = (14, 20, 36)
PANEL_ALT = (20, 28, 48)
TEXT = (228, 233, 245)
SUBTLE = (151, 164, 189)
ACCENT = (111, 210, 189)
ALLIANCE = (92, 208, 146)
CONFLICT = (230, 92, 92)
SELECTION = (255, 224, 138)


@dataclass(slots=True)
class PlanetVisual:
    planet_name: str
    position: tuple[int, int]
    radius: int
    galaxy_name: str


def main() -> None:
    run_visualizer(config=SimulationConfig.default())


def run_visualizer(
    *,
    config: SimulationConfig,
    turns_per_second: float = 1.5,
    window_size: tuple[int, int] = (1440, 900),
) -> None:
    try:
        import pygame
    except ImportError as exc:
        raise RuntimeError(
            "pygame is not installed. Install the visualization extras with `pip install -e .[viz]`."
        ) from exc

    pygame.init()
    pygame.display.set_caption("Project EXODUS Visualizer")
    screen = pygame.display.set_mode(window_size, pygame.RESIZABLE)
    clock = pygame.time.Clock()

    fonts = {
        "title": pygame.font.SysFont("georgia", 26, bold=True),
        "body": pygame.font.SysFont("georgia", 18),
        "small": pygame.font.SysFont("georgia", 15),
        "tiny": pygame.font.SysFont("georgia", 13),
    }

    runner = SimulationRunner.from_config(config)
    selected_planet = next(iter(runner.state.iter_planets()), None)
    paused = False
    accumulator = 0.0

    while True:
        delta_seconds = clock.tick(60) / 1000.0
        accumulator += delta_seconds

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return
                if event.key == pygame.K_SPACE:
                    paused = not paused
                if event.key == pygame.K_RIGHT:
                    runner.step()
                if event.key == pygame.K_r:
                    runner = SimulationRunner.from_config(config)
                    selected_planet = next(iter(runner.state.iter_planets()), None)
                    accumulator = 0.0
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                visuals = _build_visual_layout(runner.state, screen.get_size())
                selected_planet = _planet_at_position(event.pos, visuals, runner)

        if not paused and turns_per_second > 0:
            turn_interval = 1.0 / turns_per_second
            while accumulator >= turn_interval:
                runner.step()
                accumulator -= turn_interval

        visuals = _build_visual_layout(runner.state, screen.get_size())
        if selected_planet is None:
            selected_planet = next(iter(runner.state.iter_planets()), None)

        _render_frame(screen, fonts, runner, visuals, selected_planet, paused, turns_per_second)
        pygame.display.flip()


def _render_frame(screen, fonts, runner, visuals, selected_planet, paused: bool, turns_per_second: float) -> None:
    import pygame

    width, height = screen.get_size()
    map_width = int(width * 0.68)
    sidebar_rect = pygame.Rect(map_width, 0, width - map_width, height)

    screen.fill(BACKGROUND)
    _draw_starfield(screen, width, height)
    _draw_galaxy_regions(screen, visuals, map_width, height)
    _draw_relationships(screen, runner, visuals)
    _draw_systems_and_planets(screen, runner, visuals, selected_planet)
    _draw_top_bar(screen, fonts, runner, map_width, paused, turns_per_second)
    _draw_sidebar(screen, fonts, runner, sidebar_rect, selected_planet)


def _draw_starfield(screen, width: int, height: int) -> None:
    import pygame

    for index in range(90):
        digest = hashlib.md5(f"star-{index}".encode("utf-8")).digest()
        x = int.from_bytes(digest[:2], "big") % width
        y = int.from_bytes(digest[2:4], "big") % height
        radius = 1 + digest[4] % 2
        brightness = 90 + digest[5] % 120
        pygame.draw.circle(screen, (brightness, brightness, brightness + 10), (x, y), radius)


def _draw_galaxy_regions(screen, visuals: dict[str, PlanetVisual], map_width: int, height: int) -> None:
    import pygame

    galaxies = sorted({visual.galaxy_name for visual in visuals.values()})
    if not galaxies:
        return

    band_height = max(1, height // len(galaxies))
    for index, _galaxy_name in enumerate(galaxies):
        top = index * band_height
        color_shift = 18 + (index % 3) * 8
        rect = pygame.Rect(0, top, map_width, band_height)
        pygame.draw.rect(screen, (10 + color_shift, 16 + color_shift, 32 + color_shift), rect, border_radius=24)


def _draw_relationships(screen, runner, visuals: dict[str, PlanetVisual]) -> None:
    import pygame

    for alliance in runner.state.alliances:
        left = runner.state.get_faction(alliance.members[0])
        right = runner.state.get_faction(alliance.members[1])
        if left is None or right is None:
            continue
        left_visual = visuals.get(left.homeworld)
        right_visual = visuals.get(right.homeworld)
        if left_visual is None or right_visual is None:
            continue
        line_color = ALLIANCE if alliance.purpose != "security" else (102, 176, 234)
        pygame.draw.aaline(screen, line_color, left_visual.position, right_visual.position)

    for conflict in runner.state.conflicts:
        if conflict.resolved:
            continue
        attacker = runner.state.get_faction(conflict.attacker)
        defender = runner.state.get_faction(conflict.defender)
        if attacker is None or defender is None:
            continue
        left_visual = visuals.get(attacker.homeworld)
        right_visual = visuals.get(defender.homeworld)
        if left_visual is None or right_visual is None:
            continue
        pygame.draw.line(screen, CONFLICT, left_visual.position, right_visual.position, width=2)


def _draw_systems_and_planets(screen, runner, visuals: dict[str, PlanetVisual], selected_planet: Planet | None) -> None:
    import pygame

    selected_name = selected_planet.name if selected_planet else None
    planets_by_name = {planet.name: planet for planet in runner.state.iter_planets()}

    for galaxy in runner.state.galaxies:
        for system in galaxy.star_systems:
            members = [visuals[planet.name] for planet in system.planets if planet.name in visuals]
            if not members:
                continue
            center_x = sum(visual.position[0] for visual in members) // len(members)
            center_y = sum(visual.position[1] for visual in members) // len(members)
            pygame.draw.circle(screen, (255, 238, 196), (center_x, center_y), 6)

            for visual in members:
                pygame.draw.aaline(screen, (72, 86, 120), (center_x, center_y), visual.position)
                planet = planets_by_name[visual.planet_name]
                base_color = BIOME_COLORS.get(planet.biome, (160, 160, 190))
                occupancy = min(1.0, sum(f.population for f in planet.factions) / max(planet.carrying_capacity, 1))
                halo_radius = visual.radius + 5 + int(planet.strategic_value * 7)
                halo_color = (
                    min(255, int(base_color[0] * (0.5 + occupancy * 0.7))),
                    min(255, int(base_color[1] * (0.5 + occupancy * 0.7))),
                    min(255, int(base_color[2] * (0.5 + occupancy * 0.7))),
                )
                pygame.draw.circle(screen, halo_color, visual.position, halo_radius, width=1)
                pygame.draw.circle(screen, base_color, visual.position, visual.radius)
                if planet.factions:
                    pygame.draw.circle(screen, ACCENT, visual.position, max(2, visual.radius // 3))
                if visual.planet_name == selected_name:
                    pygame.draw.circle(screen, SELECTION, visual.position, halo_radius + 4, width=2)


def _draw_top_bar(screen, fonts, runner, map_width: int, paused: bool, turns_per_second: float) -> None:
    import pygame

    bar_rect = pygame.Rect(16, 16, map_width - 32, 76)
    pygame.draw.rect(screen, (8, 14, 26), bar_rect, border_radius=18)
    pygame.draw.rect(screen, (50, 74, 118), bar_rect, width=1, border_radius=18)

    planets = list(runner.state.iter_planets())
    factions = list(runner.state.iter_factions())
    active_conflicts = len([conflict for conflict in runner.state.conflicts if not conflict.resolved])
    colonised = len([planet for planet in planets if planet.factions])

    _blit_text(screen, fonts["title"], f"Project EXODUS  |  Turn {runner.state.turn}", (36, 30), TEXT)
    _blit_text(
        screen,
        fonts["small"],
        f"Colonised worlds {colonised}   Factions {len(factions)}   Alliances {len(runner.state.alliances)}   Conflicts {active_conflicts}",
        (38, 60),
        SUBTLE,
    )
    _blit_text(
        screen,
        fonts["small"],
        f"{'Paused' if paused else 'Running'} at {turns_per_second:.1f} turns/sec   |   Space pause   Right Arrow step   R reset",
        (map_width - 425, 60),
        SUBTLE,
    )


def _draw_sidebar(screen, fonts, runner, sidebar_rect, selected_planet: Planet | None) -> None:
    import pygame

    pygame.draw.rect(screen, PANEL, sidebar_rect)
    pygame.draw.rect(screen, (50, 74, 118), sidebar_rect, width=1)

    cursor_y = 24
    x = sidebar_rect.x + 22

    _blit_text(screen, fonts["title"], "World Inspector", (x, cursor_y), TEXT)
    cursor_y += 42

    if selected_planet is not None:
        cursor_y = _draw_selected_planet_panel(screen, fonts, selected_planet, x, cursor_y, sidebar_rect.width - 44)
        cursor_y += 20

    _draw_recent_events(screen, fonts, runner, x, cursor_y, sidebar_rect.width - 44, sidebar_rect.bottom - 24)


def _draw_selected_planet_panel(screen, fonts, planet: Planet, x: int, top: int, width: int) -> int:
    import pygame

    factions = planet.factions[:4]
    rect_height = 210 + len(factions) * 52
    rect = pygame.Rect(x - 12, top - 8, width + 24, rect_height)
    pygame.draw.rect(screen, PANEL_ALT, rect, border_radius=18)
    pygame.draw.rect(screen, (64, 88, 134), rect, width=1, border_radius=18)

    total_population = sum(faction.population for faction in planet.factions)
    pressure = total_population / max(planet.carrying_capacity, 1)

    _blit_text(screen, fonts["title"], planet.name, (x, top), TEXT)
    _blit_text(screen, fonts["small"], f"{planet.biome}  |  {planet.climate_band}", (x, top + 34), SUBTLE)
    _blit_text(
        screen,
        fonts["small"],
        f"Habitability {planet.habitability:.2f}   Resources {planet.resources}   Infrastructure {planet.infrastructure:.2f}",
        (x, top + 60),
        TEXT,
    )
    _blit_text(
        screen,
        fonts["small"],
        f"Capacity {planet.carrying_capacity:,}   Population {total_population:,}   Pressure {pressure:.2f}",
        (x, top + 84),
        TEXT,
    )
    _blit_text(
        screen,
        fonts["small"],
        f"Strategic value {planet.strategic_value:.2f}   Stability modifier {planet.stability_modifier:.2f}",
        (x, top + 108),
        TEXT,
    )

    row_top = top + 146
    for faction in factions:
        _blit_text(screen, fonts["small"], f"{faction.name} [{faction.ideology}]", (x, row_top), ACCENT)
        _blit_text(
            screen,
            fonts["tiny"],
            f"Pop {faction.population:,}  Eco {faction.economy:.2f}  Mil {faction.military_power:.2f}  Dip {faction.diplomacy:.2f}  Tech {faction.technology.level}",
            (x, row_top + 22),
            TEXT,
        )
        _blit_text(
            screen,
            fonts["tiny"],
            f"Morale {faction.morale:.2f}  Cohesion {faction.cohesion:.2f}  Logistics {faction.logistics:.2f}  Focus {faction.research_focus}",
            (x, row_top + 40),
            SUBTLE,
        )
        row_top += 52

    if len(planet.factions) > len(factions):
        _blit_text(screen, fonts["tiny"], f"+{len(planet.factions) - len(factions)} more factions", (x, row_top + 6), SUBTLE)

    return rect.bottom


def _draw_recent_events(screen, fonts, runner, x: int, top: int, width: int, bottom: int) -> None:
    import pygame

    rect = pygame.Rect(x - 12, top - 8, width + 24, max(140, bottom - top))
    pygame.draw.rect(screen, PANEL_ALT, rect, border_radius=18)
    pygame.draw.rect(screen, (64, 88, 134), rect, width=1, border_radius=18)

    _blit_text(screen, fonts["title"], "Recent Events", (x, top), TEXT)
    cursor_y = top + 34
    max_lines = max(5, (rect.height - 48) // 22)
    for event in runner.state.event_log[-max_lines:]:
        _blit_text(screen, fonts["tiny"], event, (x, cursor_y), SUBTLE)
        cursor_y += 22


def _planet_at_position(position: tuple[int, int], visuals: dict[str, PlanetVisual], runner: SimulationRunner) -> Planet | None:
    for visual in visuals.values():
        dx = position[0] - visual.position[0]
        dy = position[1] - visual.position[1]
        if dx * dx + dy * dy <= (visual.radius + 8) ** 2:
            for planet in runner.state.iter_planets():
                if planet.name == visual.planet_name:
                    return planet
    return None


def _build_visual_layout(state, window_size: tuple[int, int]) -> dict[str, PlanetVisual]:
    width, height = window_size
    map_width = int(width * 0.68)
    margin_x = 70
    margin_y = 120
    galaxies = state.galaxies
    layout: dict[str, PlanetVisual] = {}

    if not galaxies:
        return layout

    band_height = max(1, (height - margin_y * 2) // len(galaxies))
    for galaxy_index, galaxy in enumerate(galaxies):
        systems = galaxy.star_systems
        if not systems:
            continue
        band_top = margin_y + galaxy_index * band_height
        system_gap = max(120, (map_width - margin_x * 2) // max(1, len(systems)))

        for system_index, system in enumerate(systems):
            center_x = margin_x + system_gap // 2 + system_index * system_gap
            center_y = band_top + band_height // 2 + _name_noise(system.name, -band_height // 4, band_height // 4)

            for planet_index, planet in enumerate(system.planets):
                angle = (2 * math.pi * planet_index) / max(1, len(system.planets))
                orbit = 34 + planet_index * 20 + _name_noise(planet.name, -4, 12)
                position = (
                    int(center_x + math.cos(angle) * orbit),
                    int(center_y + math.sin(angle) * orbit),
                )
                radius = max(6, 8 + int(planet.infrastructure * 7) + len(planet.factions))
                layout[planet.name] = PlanetVisual(
                    planet_name=planet.name,
                    position=position,
                    radius=radius,
                    galaxy_name=galaxy.name,
                )

    return layout


def _name_noise(name: str, minimum: int, maximum: int) -> int:
    digest = hashlib.md5(name.encode("utf-8")).digest()
    span = maximum - minimum
    if span <= 0:
        return minimum
    return minimum + (int.from_bytes(digest[:2], "big") % (span + 1))


def _blit_text(screen, font, text: str, position: tuple[int, int], color: tuple[int, int, int]) -> None:
    surface = font.render(text, True, color)
    screen.blit(surface, position)
