from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from enum import Enum

from exodus.domain.entities import Faction, Planet
from exodus.simulation.config import SimulationConfig
from exodus.simulation.runner import SimulationRunner

BACKGROUND = (10, 12, 18)
TABLE = (18, 58, 48)
TABLE_DARK = (12, 38, 35)
PANEL = (20, 24, 34)
PANEL_ALT = (29, 35, 48)
PANEL_HOT = (54, 42, 28)
GOLD = (239, 188, 82)
RED = (202, 64, 70)
GREEN = (78, 184, 123)
BLUE = (78, 142, 210)
TEXT = (239, 242, 248)
MUTED = (159, 169, 187)
DISABLED = (92, 99, 113)
BLACK = (6, 8, 12)


class Market(Enum):
    FACTION = "Faction Dominance"
    IDEOLOGY = "Ideology Prominence"
    PLANET = "Planet Destruction"
    PAIR = "Trade / War"


@dataclass(slots=True)
class BetOption:
    market: Market
    label: str
    target: str
    odds: float
    note: str
    pair_names: tuple[str, str] | None = None
    pair_event: str | None = None


@dataclass(slots=True)
class Bet:
    option: BetOption
    stake: int


@dataclass(slots=True)
class SettledBet:
    bet: Bet
    won: bool
    payout: int
    result: str


@dataclass(slots=True)
class RoundSnapshot:
    active_wars: set[frozenset[str]] = field(default_factory=set)
    trade_links: set[frozenset[str]] = field(default_factory=set)
    destroyed_planets: set[str] = field(default_factory=set)


@dataclass(slots=True)
class Button:
    rect: object
    text: str
    action: str
    payload: object = None
    enabled: bool = True

    def contains(self, position: tuple[int, int]) -> bool:
        return self.enabled and self.rect.collidepoint(position)


@dataclass(slots=True)
class CasinoGame:
    runner: SimulationRunner
    rng: random.Random
    balance: int = 1_000
    stake: int = 50
    round_turns: int = 6
    selected_market: Market = Market.FACTION
    bets: list[Bet] = field(default_factory=list)
    last_results: list[SettledBet] = field(default_factory=list)
    destroyed_planets: set[str] = field(default_factory=set)
    selected_planet_name: str | None = None
    round_number: int = 1
    message: str = "Place bets before the next galactic spin."

    @classmethod
    def from_config(cls, config: SimulationConfig) -> "CasinoGame":
        return cls(
            runner=SimulationRunner.from_config(config),
            rng=random.Random(config.random_seed * 991 + 17),
        )

    def available_options(self) -> dict[Market, list[BetOption]]:
        factions = sorted(self.runner.state.iter_factions(), key=_dominance_score, reverse=True)[:8]
        ideologies = _ideology_scores(self.runner.state.iter_factions())
        planets = sorted(
            self.runner.state.iter_planets(),
            key=lambda planet: _destruction_pressure(planet, self.destroyed_planets),
            reverse=True,
        )[:8]
        pairs = _pair_options(self.runner.state.iter_factions())[:8]

        return {
            Market.FACTION: [
                BetOption(
                    market=Market.FACTION,
                    label=faction.name,
                    target=faction.name,
                    odds=_faction_odds(faction, factions),
                    note=f"Power {_dominance_score(faction):,.0f} | {faction.ideology}",
                )
                for faction in factions
            ],
            Market.IDEOLOGY: [
                BetOption(
                    market=Market.IDEOLOGY,
                    label=ideology,
                    target=ideology,
                    odds=_ideology_odds(score, ideologies),
                    note=f"Backed by {score:,.0f} influence",
                )
                for ideology, score in ideologies[:8]
            ],
            Market.PLANET: [
                BetOption(
                    market=Market.PLANET,
                    label=planet.name,
                    target=planet.name,
                    odds=_planet_odds(planet, self.destroyed_planets),
                    note=f"{planet.biome} | risk {_destruction_pressure(planet, self.destroyed_planets):.2f}",
                )
                for planet in planets
            ],
            Market.PAIR: pairs,
        }

    def add_bet(self, option: BetOption) -> None:
        if self.balance < self.stake:
            self.message = "Balance is too low for that stake."
            return
        self.balance -= self.stake
        self.bets.append(Bet(option=option, stake=self.stake))
        self.message = f"Booked {self.stake} credits on {option.label}."

    def adjust_stake(self, amount: int) -> None:
        self.stake = max(10, min(500, self.stake + amount))
        self.message = f"Stake set to {self.stake} credits."

    def clear_bets(self) -> None:
        refund = sum(bet.stake for bet in self.bets)
        self.balance += refund
        self.bets.clear()
        self.message = "Open wagers cleared."

    def spin_round(self) -> None:
        if not self.bets:
            self.message = "Place at least one wager before spinning."
            return

        before_conflicts = len(self.runner.state.conflicts)
        before_alliances = len(self.runner.state.alliances)
        destroyed_this_round: set[str] = set()

        for _ in range(self.round_turns):
            self.runner.step()
            destroyed_this_round.update(_roll_catastrophes(self.runner, self.rng, self.destroyed_planets))

        snapshot = RoundSnapshot(
            active_wars={
                frozenset((conflict.attacker, conflict.defender))
                for conflict in self.runner.state.conflicts[before_conflicts:]
            }
            | {
                frozenset((conflict.attacker, conflict.defender))
                for conflict in self.runner.state.conflicts
                if not conflict.resolved
            },
            trade_links={
                frozenset(alliance.members)
                for alliance in self.runner.state.alliances[before_alliances:]
                if alliance.purpose == "trade"
            }
            | {
                frozenset(alliance.members)
                for alliance in self.runner.state.alliances
                if alliance.purpose == "trade" and alliance.trust >= 0.76
            },
            destroyed_planets=destroyed_this_round,
        )
        self.destroyed_planets.update(destroyed_this_round)
        self.last_results = [_settle_bet(bet, self.runner, snapshot) for bet in self.bets]
        payout = sum(result.payout for result in self.last_results)
        self.balance += payout
        won = sum(1 for result in self.last_results if result.won)
        self.message = f"Round {self.round_number} settled: {won}/{len(self.last_results)} wins, payout {payout}."
        self.bets.clear()
        self.round_number += 1

    def reset(self, config: SimulationConfig) -> None:
        fresh = CasinoGame.from_config(config)
        self.runner = fresh.runner
        self.rng = fresh.rng
        self.balance = fresh.balance
        self.stake = fresh.stake
        self.round_turns = fresh.round_turns
        self.selected_market = fresh.selected_market
        self.bets.clear()
        self.last_results.clear()
        self.destroyed_planets.clear()
        self.selected_planet_name = fresh.selected_planet_name
        self.round_number = fresh.round_number
        self.message = "New casino table opened."


def main() -> None:
    run_casino(config=SimulationConfig.default())


def run_casino(
    *,
    config: SimulationConfig,
    window_size: tuple[int, int] = (1440, 900),
) -> None:
    try:
        import pygame
    except ImportError as exc:
        raise RuntimeError("pygame is not installed. Install it with `pip install -e .[viz]`.") from exc

    pygame.init()
    pygame.display.set_caption("EXODUS Casino: Galactic Futures")
    screen = pygame.display.set_mode(window_size, pygame.RESIZABLE)
    clock = pygame.time.Clock()
    fonts = {
        "title": pygame.font.SysFont("georgia", 30, bold=True),
        "heading": pygame.font.SysFont("georgia", 22, bold=True),
        "body": pygame.font.SysFont("georgia", 18),
        "small": pygame.font.SysFont("georgia", 15),
        "tiny": pygame.font.SysFont("georgia", 13),
    }
    game = CasinoGame.from_config(config)
    buttons: list[Button] = []
    map_rect = None

    while True:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return
                if event.key == pygame.K_SPACE:
                    game.spin_round()
                if event.key == pygame.K_c:
                    game.clear_bets()
                if event.key == pygame.K_r:
                    game.reset(config)
                if event.key in {pygame.K_MINUS, pygame.K_KP_MINUS}:
                    game.adjust_stake(-10)
                if event.key in {pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS}:
                    game.adjust_stake(10)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if map_rect is not None and map_rect.collidepoint(event.pos):
                    _select_map_planet(game, event.pos, map_rect)
                else:
                    for button in buttons:
                        if button.contains(event.pos):
                            _handle_button(game, button, config)
                            break

        buttons, map_rect = _render(screen, fonts, game)
        pygame.display.flip()


def _handle_button(game: CasinoGame, button: Button, config: SimulationConfig) -> None:
    if button.action == "market":
        game.selected_market = button.payload
    elif button.action == "bet":
        game.add_bet(button.payload)
    elif button.action == "stake":
        game.adjust_stake(button.payload)
    elif button.action == "spin":
        game.spin_round()
    elif button.action == "clear":
        game.clear_bets()
    elif button.action == "reset":
        game.reset(config)


def _render(screen, fonts, game: CasinoGame) -> tuple[list[Button], object]:
    import pygame

    width, height = screen.get_size()
    buttons: list[Button] = []
    screen.fill(BACKGROUND)
    _draw_table_felt(screen, width, height)

    header = pygame.Rect(20, 16, width - 40, 92)
    pygame.draw.rect(screen, BLACK, header, border_radius=8)
    pygame.draw.rect(screen, GOLD, header, width=1, border_radius=8)
    _blit_text(screen, fonts["title"], "EXODUS CASINO", (42, 30), GOLD)
    _blit_text(screen, fonts["body"], "Galactic Futures Sportsbook", (44, 68), TEXT)
    _blit_text(
        screen,
        fonts["heading"],
        f"Balance {game.balance:,}   Stake {game.stake}   Turn {game.runner.state.turn}",
        (width - 470, 32),
        TEXT,
    )
    _blit_text(screen, fonts["small"], game.message, (width - 470, 70), MUTED)

    map_width = max(500, int(width * 0.4))
    casino_width = width - map_width - 44
    map_rect = pygame.Rect(casino_width + 24, 124, map_width, height - 144)
    market_width = 230
    slip_width = 280
    book_width = max(220, casino_width - 20 - market_width - slip_width - 24)
    markets_rect = pygame.Rect(20, 124, market_width, height - 144)
    book_rect = pygame.Rect(markets_rect.right + 12, 124, book_width, height - 144)
    slip_rect = pygame.Rect(book_rect.right + 12, 124, slip_width, height - 144)
    _panel(screen, markets_rect, TABLE_DARK)
    _panel(screen, book_rect, PANEL)
    _panel(screen, slip_rect, PANEL)
    _panel(screen, map_rect, BLACK)

    buttons.extend(_draw_market_tabs(screen, fonts, game, markets_rect))
    buttons.extend(_draw_book(screen, fonts, game, book_rect))
    buttons.extend(_draw_bet_slip(screen, fonts, game, slip_rect))
    _draw_live_map(screen, fonts, game, map_rect)
    return buttons, map_rect


def _draw_table_felt(screen, width: int, height: int) -> None:
    import pygame

    screen.fill(TABLE)
    for index in range(80):
        digest = hashlib.md5(f"casino-star-{index}".encode("utf-8")).digest()
        x = int.from_bytes(digest[:2], "big") % max(width, 1)
        y = int.from_bytes(digest[2:4], "big") % max(height, 1)
        color = (24 + digest[4] % 18, 72 + digest[5] % 24, 59 + digest[6] % 20)
        pygame.draw.circle(screen, color, (x, y), 1 + digest[7] % 2)


def _draw_market_tabs(screen, fonts, game: CasinoGame, rect) -> list[Button]:
    import pygame

    buttons: list[Button] = []
    _blit_text(screen, fonts["heading"], "Markets", (rect.x + 18, rect.y + 18), GOLD)
    cursor_y = rect.y + 62
    for market in Market:
        tab = pygame.Rect(rect.x + 16, cursor_y, rect.width - 32, 54)
        selected = market == game.selected_market
        color = PANEL_HOT if selected else PANEL_ALT
        pygame.draw.rect(screen, color, tab, border_radius=8)
        pygame.draw.rect(screen, GOLD if selected else (61, 70, 86), tab, width=1, border_radius=8)
        _blit_text(screen, fonts["body"], market.value, (tab.x + 14, tab.y + 16), TEXT)
        buttons.append(Button(tab, market.value, "market", market))
        cursor_y += 66

    _blit_text(screen, fonts["small"], "Controls", (rect.x + 18, cursor_y + 10), GOLD)
    shortcuts = ["Space: spin", "C: clear bets", "+ / -: stake", "R: reset", "Esc: quit"]
    for index, line in enumerate(shortcuts):
        _blit_text(screen, fonts["small"], line, (rect.x + 18, cursor_y + 38 + index * 24), MUTED)
    return buttons


def _draw_book(screen, fonts, game: CasinoGame, rect) -> list[Button]:
    import pygame

    buttons: list[Button] = []
    options = game.available_options()[game.selected_market]
    _blit_text(screen, fonts["heading"], game.selected_market.value, (rect.x + 22, rect.y + 18), GOLD)
    _draw_market_hint(screen, fonts, game.selected_market, (rect.x + 22, rect.y + 48), rect.width - 44)

    cursor_y = rect.y + 90
    row_height = 72
    for option in options:
        row = pygame.Rect(rect.x + 18, cursor_y, rect.width - 36, row_height)
        pygame.draw.rect(screen, PANEL_ALT, row, border_radius=8)
        pygame.draw.rect(screen, (60, 70, 88), row, width=1, border_radius=8)
        _blit_clipped(screen, fonts["body"], option.label, (row.x + 14, row.y + 10), TEXT, row.width - 150)
        _blit_clipped(screen, fonts["small"], option.note, (row.x + 14, row.y + 40), MUTED, row.width - 150)
        odds_rect = pygame.Rect(row.right - 118, row.y + 14, 96, 44)
        pygame.draw.rect(screen, GOLD if game.balance >= game.stake else DISABLED, odds_rect, border_radius=8)
        _blit_text(screen, fonts["body"], f"{option.odds:.1f}x", (odds_rect.x + 26, odds_rect.y + 12), BLACK)
        buttons.append(Button(odds_rect, option.label, "bet", option, enabled=game.balance >= game.stake))
        cursor_y += row_height + 12
        if cursor_y + row_height > rect.bottom - 12:
            break
    return buttons


def _draw_market_hint(screen, fonts, market: Market, position: tuple[int, int], width: int) -> None:
    hints = {
        Market.FACTION: "Pays if this faction has the highest dominance score after the spin.",
        Market.IDEOLOGY: "Pays if this ideology controls the most population-weighted influence.",
        Market.PLANET: "Pays only when that planet is destroyed during this spin.",
        Market.PAIR: "Pays if the selected pair hits the listed trade or war event.",
    }
    _wrapped_text(screen, fonts["small"], hints[market], position, width, MUTED, line_height=20)


def _draw_bet_slip(screen, fonts, game: CasinoGame, rect) -> list[Button]:
    import pygame

    buttons: list[Button] = []
    _blit_text(screen, fonts["heading"], "Bet Slip", (rect.x + 18, rect.y + 18), GOLD)
    stake_y = rect.y + 58
    minus = pygame.Rect(rect.x + 18, stake_y, 42, 36)
    plus = pygame.Rect(rect.x + 68, stake_y, 42, 36)
    _small_button(screen, fonts, minus, "-10", enabled=True)
    _small_button(screen, fonts, plus, "+10", enabled=True)
    buttons.append(Button(minus, "-10", "stake", -10))
    buttons.append(Button(plus, "+10", "stake", 10))
    _blit_text(screen, fonts["small"], f"Current stake: {game.stake}", (rect.x + 128, stake_y + 10), TEXT)

    cursor_y = rect.y + 112
    _blit_text(screen, fonts["small"], "Open Wagers", (rect.x + 18, cursor_y), GOLD)
    cursor_y += 28
    if not game.bets:
        _wrapped_text(screen, fonts["small"], "No open wagers. Pick odds from the book.", (rect.x + 18, cursor_y), rect.width - 36, MUTED)
        cursor_y += 58
    else:
        for bet in game.bets[-7:]:
            line = f"{bet.stake} on {bet.option.label} at {bet.option.odds:.1f}x"
            _blit_clipped(screen, fonts["tiny"], line, (rect.x + 18, cursor_y), TEXT, rect.width - 36)
            cursor_y += 24

    spin = pygame.Rect(rect.x + 18, rect.y + 330, rect.width - 36, 48)
    clear = pygame.Rect(rect.x + 18, rect.y + 388, rect.width - 36, 40)
    reset = pygame.Rect(rect.x + 18, rect.y + 438, rect.width - 36, 40)
    _large_button(screen, fonts, spin, "SPIN ROUND", GREEN, enabled=bool(game.bets))
    _large_button(screen, fonts, clear, "CLEAR BETS", BLUE, enabled=bool(game.bets))
    _large_button(screen, fonts, reset, "RESET TABLE", RED, enabled=True)
    buttons.append(Button(spin, "spin", "spin", enabled=bool(game.bets)))
    buttons.append(Button(clear, "clear", "clear", enabled=bool(game.bets)))
    buttons.append(Button(reset, "reset", "reset"))

    result_top = rect.y + 506
    _blit_text(screen, fonts["small"], "Last Results", (rect.x + 18, result_top), GOLD)
    cursor_y = result_top + 28
    if not game.last_results:
        _wrapped_text(screen, fonts["small"], "Results appear here after a spin.", (rect.x + 18, cursor_y), rect.width - 36, MUTED)
    else:
        for result in game.last_results[-8:]:
            color = GREEN if result.won else RED
            outcome = "WIN" if result.won else "LOSE"
            _blit_text(screen, fonts["tiny"], f"{outcome} +{result.payout}" if result.won else outcome, (rect.x + 18, cursor_y), color)
            _blit_clipped(screen, fonts["tiny"], result.result, (rect.x + 78, cursor_y), TEXT, rect.width - 96)
            cursor_y += 24
            if cursor_y > rect.bottom - 20:
                break
    return buttons


def _draw_live_map(screen, fonts, game: CasinoGame, rect) -> None:
    import pygame

    from exodus.visualization.app import _build_visual_layout, _render_frame

    inner = rect.inflate(-12, -12)
    source_size = _map_source_size(inner.size)
    map_surface = pygame.Surface(source_size)
    selected_planet = _selected_planet(game)
    visuals = _build_visual_layout(game.runner.state, source_size)
    _render_frame(
        map_surface,
        fonts,
        game.runner,
        visuals,
        selected_planet,
        True,
        0.0,
    )
    scaled = pygame.transform.smoothscale(map_surface, inner.size)
    screen.blit(scaled, inner.topleft)
    pygame.draw.rect(screen, GOLD, inner, width=1, border_radius=8)
    _blit_text(screen, fonts["small"], "Live Map Feed", (inner.x + 16, inner.y + 12), GOLD)


def _select_map_planet(game: CasinoGame, position: tuple[int, int], rect) -> None:
    from exodus.visualization.app import _build_visual_layout, _planet_at_position

    inner = rect.inflate(-12, -12)
    source_size = _map_source_size(inner.size)
    scale_x = source_size[0] / max(1, inner.width)
    scale_y = source_size[1] / max(1, inner.height)
    source_position = (
        int((position[0] - inner.x) * scale_x),
        int((position[1] - inner.y) * scale_y),
    )
    visuals = _build_visual_layout(game.runner.state, source_size)
    planet = _planet_at_position(source_position, visuals, game.runner)
    if planet is not None:
        game.selected_planet_name = planet.name
        game.message = f"Map selected {planet.name}."


def _map_source_size(target_size: tuple[int, int]) -> tuple[int, int]:
    _width, height = target_size
    return (1100, max(720, height))


def _selected_planet(game: CasinoGame) -> Planet | None:
    if game.selected_planet_name is not None:
        for planet in game.runner.state.iter_planets():
            if planet.name == game.selected_planet_name:
                return planet

    selected = next(iter(game.runner.state.iter_planets()), None)
    if selected is not None:
        game.selected_planet_name = selected.name
    return selected


def _panel(screen, rect, color: tuple[int, int, int]) -> None:
    import pygame

    pygame.draw.rect(screen, color, rect, border_radius=8)
    pygame.draw.rect(screen, (70, 78, 92), rect, width=1, border_radius=8)


def _small_button(screen, fonts, rect, text: str, *, enabled: bool) -> None:
    import pygame

    color = GOLD if enabled else DISABLED
    pygame.draw.rect(screen, color, rect, border_radius=8)
    _blit_text(screen, fonts["small"], text, (rect.x + 9, rect.y + 10), BLACK)


def _large_button(screen, fonts, rect, text: str, color: tuple[int, int, int], *, enabled: bool) -> None:
    import pygame

    pygame.draw.rect(screen, color if enabled else DISABLED, rect, border_radius=8)
    surface = fonts["body"].render(text, True, BLACK if enabled else (35, 39, 46))
    screen.blit(surface, (rect.centerx - surface.get_width() // 2, rect.centery - surface.get_height() // 2))


def _roll_catastrophes(runner: SimulationRunner, rng: random.Random, already_destroyed: set[str]) -> set[str]:
    destroyed: set[str] = set()
    for planet in runner.state.iter_planets():
        if planet.name in already_destroyed:
            continue
        risk = _destruction_pressure(planet, already_destroyed)
        if rng.random() < risk * 0.016:
            destroyed.add(planet.name)
            planet.habitability = 0.0
            planet.resources = 10
            planet.infrastructure = 0.0
            planet.stability_modifier = -0.25
            for faction in planet.factions:
                losses = int(faction.population * rng.uniform(0.72, 0.94))
                faction.population = max(100_000, faction.population - losses)
                faction.stability = max(0.0, round(faction.stability - 0.35, 2))
                faction.morale = max(0.0, round(faction.morale - 0.35, 2))
            runner.state.record(f"{planet.name} was destroyed by a cascading void disaster.")
    return destroyed


def _settle_bet(bet: Bet, runner: SimulationRunner, snapshot: RoundSnapshot) -> SettledBet:
    option = bet.option
    won = False
    result = ""

    if option.market == Market.FACTION:
        winner = max(runner.state.iter_factions(), key=_dominance_score)
        won = winner.name == option.target
        result = f"Dominant faction: {winner.name}"
    elif option.market == Market.IDEOLOGY:
        winner, _score = _ideology_scores(runner.state.iter_factions())[0]
        won = winner == option.target
        result = f"Prominent ideology: {winner}"
    elif option.market == Market.PLANET:
        won = option.target in snapshot.destroyed_planets
        result = f"Destroyed: {', '.join(sorted(snapshot.destroyed_planets)) or 'none'}"
    elif option.market == Market.PAIR and option.pair_names and option.pair_event:
        pair = frozenset(option.pair_names)
        if option.pair_event == "trade":
            won = pair in snapshot.trade_links
            result = f"Trade links: {len(snapshot.trade_links)}"
        else:
            won = pair in snapshot.active_wars
            result = f"War fronts: {len(snapshot.active_wars)}"

    payout = int(bet.stake * option.odds) if won else 0
    return SettledBet(bet=bet, won=won, payout=payout, result=result)


def _dominance_score(faction: Faction) -> float:
    tech_score = faction.technology.level + sum(faction.technology.fields.values()) * 0.25
    capability = (
        faction.economy
        + faction.military_power
        + faction.diplomacy
        + faction.industrial_capacity
        + faction.logistics
        + faction.stability
        + faction.morale
    )
    return faction.population * max(0.1, capability) * max(1.0, tech_score)


def _ideology_scores(factions) -> list[tuple[str, float]]:
    scores: dict[str, float] = {}
    for faction in factions:
        scores[faction.ideology] = scores.get(faction.ideology, 0.0) + _dominance_score(faction)
    return sorted(scores.items(), key=lambda item: item[1], reverse=True)


def _pair_options(factions) -> list[BetOption]:
    faction_list = sorted(factions, key=_dominance_score, reverse=True)[:7]
    options: list[BetOption] = []
    for index, left in enumerate(faction_list):
        for right in faction_list[index + 1 :]:
            relation = (left.relations.get(right.name, 0.5) + right.relations.get(left.name, 0.5)) / 2
            trade_chance = max(0.05, min(0.65, (left.diplomacy + right.diplomacy) * 0.24 + relation * 0.28))
            war_chance = max(
                0.04,
                min(0.7, (left.military_power + right.military_power) * 0.22 + (1 - relation) * 0.34),
            )
            label_base = f"{left.name} / {right.name}"
            options.append(
                BetOption(
                    market=Market.PAIR,
                    label=f"TRADE: {label_base}",
                    target=label_base,
                    odds=round(1.0 / trade_chance, 1),
                    note=f"Trust {relation:.2f} | diplomacy {(left.diplomacy + right.diplomacy) / 2:.2f}",
                    pair_names=(left.name, right.name),
                    pair_event="trade",
                )
            )
            options.append(
                BetOption(
                    market=Market.PAIR,
                    label=f"WAR: {label_base}",
                    target=label_base,
                    odds=round(1.0 / war_chance, 1),
                    note=f"Hostility {1 - relation:.2f} | military {(left.military_power + right.military_power) / 2:.2f}",
                    pair_names=(left.name, right.name),
                    pair_event="war",
                )
            )
    return sorted(options, key=lambda option: option.odds)[:8]


def _faction_odds(faction: Faction, top_factions: list[Faction]) -> float:
    total = sum(_dominance_score(entry) for entry in top_factions) or 1.0
    implied = max(0.04, _dominance_score(faction) / total)
    return round(max(1.2, min(12.0, 0.86 / implied)), 1)


def _ideology_odds(score: float, ideologies: list[tuple[str, float]]) -> float:
    total = sum(entry_score for _ideology, entry_score in ideologies) or 1.0
    implied = max(0.04, score / total)
    return round(max(1.2, min(14.0, 0.88 / implied)), 1)


def _planet_odds(planet: Planet, destroyed_planets: set[str]) -> float:
    risk = _destruction_pressure(planet, destroyed_planets)
    return round(max(3.0, min(30.0, 1.0 / max(0.035, risk * 0.18))), 1)


def _destruction_pressure(planet: Planet, destroyed_planets: set[str]) -> float:
    if planet.name in destroyed_planets:
        return 0.0
    population_load = sum(faction.population for faction in planet.factions) / max(planet.carrying_capacity, 1)
    militarization = sum(faction.military_power for faction in planet.factions) / max(1, len(planet.factions))
    fragility = (1 - planet.habitability) * 0.35 + max(0.0, population_load - 0.9) * 0.3
    extraction = (100 - planet.resources) / 100 * 0.12 + planet.infrastructure * 0.08
    return max(0.02, min(1.0, fragility + extraction + militarization * 0.12 + planet.strategic_value * 0.08))


def _wrapped_text(screen, font, text: str, position: tuple[int, int], width: int, color, line_height: int = 22) -> int:
    words = text.split()
    x, y = position
    line = ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if font.size(candidate)[0] <= width:
            line = candidate
            continue
        if line:
            _blit_text(screen, font, line, (x, y), color)
            y += line_height
        line = word
    if line:
        _blit_text(screen, font, line, (x, y), color)
        y += line_height
    return y


def _blit_clipped(screen, font, text: str, position: tuple[int, int], color, max_width: int) -> None:
    clipped = text
    while clipped and font.size(clipped)[0] > max_width:
        clipped = clipped[:-2].rstrip() + "."
    _blit_text(screen, font, clipped, position, color)


def _blit_text(screen, font, text: str, position: tuple[int, int], color: tuple[int, int, int]) -> None:
    surface = font.render(text, True, color)
    screen.blit(surface, position)
