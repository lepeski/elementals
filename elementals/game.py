"""Pygame powered single-player arena for the Elementals prototype."""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import pygame

from .abilities import loadout_for
from .elements import CampaignState, Element
from .entities import Actor, Obstacle, Projectile
from .physics import Vec2, clamp, collide_circles, distance

Color = Tuple[int, int, int]

SCREEN_WIDTH = 960
SCREEN_HEIGHT = 600

PLAYER_COLOR: Dict[Element, Color] = {
    Element.EARTH: (195, 170, 120),
    Element.WATER: (120, 190, 240),
    Element.FIRE: (255, 150, 80),
    Element.AIR: (180, 220, 255),
    Element.PSYCHIC: (210, 170, 255),
}

ENEMY_COLOR: Dict[Element, Color] = {
    Element.EARTH: (160, 130, 90),
    Element.WATER: (90, 150, 210),
    Element.FIRE: (220, 110, 70),
    Element.AIR: (140, 200, 240),
    Element.PSYCHIC: (190, 130, 240),
}

GUARDIAN_MATCHUP: Dict[Element, Element] = {
    Element.EARTH: Element.WATER,
    Element.WATER: Element.EARTH,
    Element.FIRE: Element.PSYCHIC,
    Element.AIR: Element.PSYCHIC,
    Element.PSYCHIC: Element.FIRE,
}


@dataclass
class EffectSprite:
    position: Vec2
    color: Color
    radius: float
    duration: float
    elapsed: float = 0.0

    def update(self, dt: float) -> bool:
        self.elapsed += dt
        return self.elapsed < self.duration

    @property
    def alpha(self) -> int:
        if self.duration <= 0:
            return 0
        return max(0, min(255, int(255 * (1.0 - self.elapsed / self.duration))))


@dataclass
class FloatingText:
    text: str
    position: Vec2
    color: Color
    duration: float = 1.0
    elapsed: float = 0.0

    def update(self, dt: float) -> bool:
        self.elapsed += dt
        self.position.y -= 28.0 * dt
        return self.elapsed < self.duration

    @property
    def alpha(self) -> int:
        if self.duration <= 0:
            return 0
        return max(0, min(255, int(255 * (1.0 - self.elapsed / self.duration))))


class GameSession:
    """Handles combat state for a single arena run."""

    def __init__(self, element: Element, campaign: CampaignState) -> None:
        self.zone = element
        self.campaign = campaign
        self.bounds = pygame.Rect(60, 60, SCREEN_WIDTH - 120, SCREEN_HEIGHT - 120)
        self.projectiles: List[Projectile] = []
        self.effects: List[EffectSprite] = []
        self.texts: List[FloatingText] = []
        self.obstacles: List[Obstacle] = self._build_obstacles()
        self.time = 0.0
        self.outcome: Optional[str] = None
        self.reveal_timer = 0.0
        self.shake_timer = 0.0
        self.shake_strength = 0.0
        self.shake_offset = Vec2()
        combos = sorted(campaign.unlocked_combos)

        self.player = self._spawn_actor(
            name="Seeker",
            element=element,
            position=Vec2(self.bounds.left + 120.0, SCREEN_HEIGHT / 2),
            color=PLAYER_COLOR.get(element, (220, 220, 220)),
            combos=combos,
        )
        guardian_element = GUARDIAN_MATCHUP.get(element, Element.WATER)
        self.guardian = self._spawn_actor(
            name="Guardian",
            element=guardian_element,
            position=Vec2(self.bounds.right - 120.0, SCREEN_HEIGHT / 2),
            color=ENEMY_COLOR.get(guardian_element, (200, 60, 80)),
            combos=[],
        )
        self.actors: List[Actor] = [self.player, self.guardian]
        self.guardian.ai_brain = self._guardian_ai

    # ------------------------------------------------------------------
    def _build_obstacles(self) -> List[Obstacle]:
        mid_x = SCREEN_WIDTH / 2 - 60
        return [
            Obstacle(mid_x, SCREEN_HEIGHT / 2 - 140, 120, 50),
            Obstacle(mid_x, SCREEN_HEIGHT / 2 + 90, 120, 50),
        ]

    def _spawn_actor(
        self,
        *,
        name: str,
        element: Element,
        position: Vec2,
        color: Color,
        combos: Iterable[Element],
    ) -> Actor:
        actor = Actor(name=name, element=element, position=position, color=color)
        for spec in loadout_for(element, combos):
            actor.bind_ability(spec.key, spec)
        actor.health = actor.max_health
        actor.energy = actor.max_energy
        return actor

    # ------------------------------------------------------------------
    def update(self, dt: float, player_move: Vec2, cursor_pos: Vec2, queued_casts: Sequence[str]) -> None:
        self.time += dt
        if self.outcome is not None:
            self._update_visuals(dt)
            return

        self.player.aim_towards(cursor_pos)
        self.player.apply_input(player_move, dt)

        for key in queued_casts:
            self.cast_ability(self.player, key)

        if self.guardian.ai_brain:
            self.guardian.ai_brain(self.guardian, self, dt)

        for actor in self.actors:
            actor.update(dt)
            self._apply_bounds(actor)
            self._resolve_obstacles(actor)

        self._update_projectiles(dt)
        self._update_visuals(dt)
        self._check_outcome()

    def _update_visuals(self, dt: float) -> None:
        if self.reveal_timer > 0:
            self.reveal_timer = max(0.0, self.reveal_timer - dt)
        if self.shake_timer > 0:
            self.shake_timer = max(0.0, self.shake_timer - dt)
            self.shake_offset = Vec2(
                random.uniform(-self.shake_strength, self.shake_strength),
                random.uniform(-self.shake_strength, self.shake_strength),
            )
        else:
            self.shake_offset = Vec2()
        self.effects = [effect for effect in self.effects if effect.update(dt)]
        self.texts = [text for text in self.texts if text.update(dt)]

    # ------------------------------------------------------------------
    def _apply_bounds(self, actor: Actor) -> None:
        actor.position.x = clamp(actor.position.x, self.bounds.left + actor.radius, self.bounds.right - actor.radius)
        actor.position.y = clamp(actor.position.y, self.bounds.top + actor.radius, self.bounds.bottom - actor.radius)

    def _resolve_obstacles(self, actor: Actor) -> None:
        for obstacle in self.obstacles:
            if obstacle.contains(actor.position):
                actor.position = obstacle.clamp_position(actor.position, actor.radius)
                actor.velocity = Vec2()

    def _update_projectiles(self, dt: float) -> None:
        remaining: List[Projectile] = []
        for projectile in self.projectiles:
            projectile.update(dt)
            if not projectile.alive:
                continue
            if not self.bounds.collidepoint(projectile.position.x, projectile.position.y):
                continue
            hit = False
            for obstacle in self.obstacles:
                if obstacle.contains(projectile.position):
                    hit = True
                    break
            if hit:
                continue
            for actor in self.actors:
                if actor is projectile.owner or not actor.is_alive:
                    continue
                if collide_circles(projectile.position, projectile.radius, actor.position, actor.radius):
                    if projectile.on_hit:
                        projectile.on_hit(self, projectile, actor)
                    else:
                        impulse = projectile.velocity.normalize() * projectile.knockback if projectile.knockback else None
                        self.deal_damage(actor, projectile.damage, source=projectile.owner, impulse=impulse)
                    hit = True
                    break
            if not hit:
                remaining.append(projectile)
        self.projectiles = remaining

    # ------------------------------------------------------------------
    def _check_outcome(self) -> None:
        if not self.player.is_alive and self.outcome is None:
            self.outcome = "defeat"
        elif not self.guardian.is_alive and self.outcome is None:
            self.outcome = "victory"

    # ------------------------------------------------------------------
    def cast_ability(self, actor: Actor, key: str) -> bool:
        ability_state = actor.abilities.get(key)
        if ability_state is None or not ability_state.ready:
            return False
        spec = ability_state.spec
        if spec.energy_cost > 0 and not actor.spend_energy(spec.energy_cost):
            return False
        spec.cast(self, actor)
        ability_state.trigger()
        return True

    def spawn_projectile(self, projectile: Projectile) -> None:
        self.projectiles.append(projectile)

    def spawn_effect(self, position: Vec2, color: Color, radius: float, duration: float) -> None:
        self.effects.append(EffectSprite(position=position.copy(), color=color, radius=radius, duration=duration))

    def spawn_text(self, text: str, position: Vec2, color: Color) -> None:
        self.texts.append(FloatingText(text=text, position=position.copy(), color=color))

    def shake(self, duration: float, strength: float = 12.0) -> None:
        self.shake_timer = max(self.shake_timer, duration)
        self.shake_strength = max(self.shake_strength, strength)

    def reveal_opponent(self) -> None:
        self.reveal_timer = max(self.reveal_timer, 3.0)

    # ------------------------------------------------------------------
    def deal_damage(
        self,
        target: Actor,
        amount: float,
        *,
        source: Actor | None = None,
        impulse: Vec2 | None = None,
    ) -> float:
        dealt = target.take_damage(amount, source, impulse)
        if dealt > 0:
            self.spawn_text(f"-{int(dealt)}", target.position, (255, 110, 90))
        return dealt

    def actors_in_radius(self, center: Vec2, radius: float, *, exclude: Actor | None = None) -> List[Actor]:
        results: List[Actor] = []
        for actor in self.actors:
            if actor is exclude or not actor.is_alive:
                continue
            if distance(actor.position, center) <= radius + actor.radius:
                results.append(actor)
        return results

    def iter_enemies(self, actor: Actor) -> Iterable[Actor]:
        for other in self.actors:
            if other is actor or not other.is_alive:
                continue
            yield other

    def push_actor(self, actor: Actor, impulse: Vec2) -> None:
        actor.velocity += impulse

    # ------------------------------------------------------------------
    def _guardian_ai(self, guardian: Actor, game: "GameSession", dt: float) -> None:
        if not self.player.is_alive:
            guardian.apply_input(Vec2(), dt)
            return
        to_player = self.player.position - guardian.position
        distance_to_player = to_player.length()
        desired = Vec2()
        if distance_to_player > 230:
            desired = to_player.normalize()
        elif distance_to_player < 140:
            desired = to_player.normalize() * -1.0
        guardian.aim_towards(self.player.position)
        guardian.apply_input(desired, dt)
        for key, ability_state in guardian.abilities.items():
            if ability_state.ready and guardian.energy >= ability_state.spec.energy_cost:
                self.cast_ability(guardian, key)
                break

    # ------------------------------------------------------------------
    @property
    def camera_offset(self) -> Vec2:
        return self.shake_offset

    @property
    def is_over(self) -> bool:
        return self.outcome is not None


class GameApp:
    """High level orchestration for menus, session, and rendering."""

    HOTKEYS = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6]

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Elementals Prototype")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font_small = pygame.font.SysFont("Arial", 16)
        self.font_medium = pygame.font.SysFont("Arial", 24)
        self.font_large = pygame.font.SysFont("Arial", 40)
        self.campaign = CampaignState.new()
        self.session: GameSession | None = None
        self.pending_casts: List[str] = []
        self.running = True
        self.cursor_world = Vec2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        self.current_zone: Element | None = None
        self.victory_recorded = False

    # ------------------------------------------------------------------
    def start(self) -> None:
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            self._handle_events()
            self._update(dt)
            self._draw()
        pygame.quit()

    # ------------------------------------------------------------------
    def _handle_events(self) -> None:
        self.pending_casts.clear()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif self.session is None:
                    self._handle_menu_key(event.key)
                else:
                    self._handle_game_key(event.key)
            elif event.type == pygame.MOUSEMOTION:
                if self.session is not None:
                    offset = self.session.camera_offset
                    self.cursor_world = Vec2(event.pos[0] - offset.x, event.pos[1] - offset.y)
                else:
                    self.cursor_world = Vec2(*event.pos)

    def _handle_menu_key(self, key: int) -> None:
        options = list(self.campaign.available_zones())
        bindings = [pygame.K_1, pygame.K_2, pygame.K_3]
        for option, binding in zip(options, bindings):
            if key == binding:
                self.start_zone(option)
                break

    def _handle_game_key(self, key: int) -> None:
        if self.session is None:
            return
        if self.session.is_over:
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self.session = None
                self.current_zone = None
            return
        for hotkey, ability_key in zip(self.HOTKEYS, self._player_ability_keys()):
            if key == hotkey:
                self.pending_casts.append(ability_key)
                break

    # ------------------------------------------------------------------
    def _update(self, dt: float) -> None:
        if self.session is None:
            return
        mouse_x, mouse_y = pygame.mouse.get_pos()
        offset = self.session.camera_offset
        self.cursor_world = Vec2(mouse_x - offset.x, mouse_y - offset.y)
        pressed = pygame.key.get_pressed()
        move = Vec2(
            float(pressed[pygame.K_d] or pressed[pygame.K_RIGHT]) - float(pressed[pygame.K_a] or pressed[pygame.K_LEFT]),
            float(pressed[pygame.K_s] or pressed[pygame.K_DOWN]) - float(pressed[pygame.K_w] or pressed[pygame.K_UP]),
        )
        if move.length_squared() > 0:
            move = move.normalize()
        else:
            move = Vec2()
        self.session.update(dt, move, self.cursor_world, self.pending_casts)
        if self.session.is_over and not self.victory_recorded:
            if self.session.outcome == "victory" and self.current_zone is not None:
                self.campaign.record_victory(self.current_zone)
            self.victory_recorded = True

    def _draw(self) -> None:
        self.screen.fill((18, 22, 26))
        if self.session is None:
            self._draw_menu()
        else:
            self._draw_session()
        pygame.display.flip()

    # ------------------------------------------------------------------
    def _draw_menu(self) -> None:
        title = self.font_large.render("Elementals Trials", True, (240, 240, 255))
        self.screen.blit(title, (SCREEN_WIDTH / 2 - title.get_width() / 2, 80))
        prompt = self.font_medium.render("Select your next zone", True, (200, 200, 220))
        self.screen.blit(prompt, (SCREEN_WIDTH / 2 - prompt.get_width() / 2, 160))
        options = list(self.campaign.available_zones())
        bindings = ["[1]", "[2]", "[3]"]
        for index, option in enumerate(options):
            label = f"{bindings[index]} {option.value.title()}"
            text = self.font_medium.render(label, True, (180, 220, 240))
            self.screen.blit(text, (SCREEN_WIDTH / 2 - text.get_width() / 2, 220 + index * 40))
        summary = self.font_small.render(self.campaign.describe_progress(), True, (170, 180, 200))
        self.screen.blit(summary, (SCREEN_WIDTH / 2 - summary.get_width() / 2, SCREEN_HEIGHT - 120))
        footer = self.font_small.render("WASD to move, mouse to aim, 1-6 to cast once in battle.", True, (150, 160, 180))
        self.screen.blit(footer, (SCREEN_WIDTH / 2 - footer.get_width() / 2, SCREEN_HEIGHT - 80))

    def _draw_session(self) -> None:
        assert self.session is not None
        offset = self.session.camera_offset
        arena_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        arena_surface.fill((26, 32, 36))
        pygame.draw.rect(arena_surface, (34, 44, 52), self.session.bounds, border_radius=16)
        for obstacle in self.session.obstacles:
            pygame.draw.rect(arena_surface, (60, 60, 70), obstacle.as_rect(), border_radius=10)
        for effect in self.session.effects:
            radius = int(effect.radius)
            surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*effect.color, effect.alpha), (radius, radius), radius)
            arena_surface.blit(surf, (effect.position.x - radius, effect.position.y - radius))
        for projectile in self.session.projectiles:
            pygame.draw.circle(
                arena_surface,
                projectile.color,
                (int(projectile.position.x), int(projectile.position.y)),
                int(projectile.radius),
            )
        for actor in self.session.actors:
            if not actor.is_alive:
                continue
            color = actor.color
            pygame.draw.circle(
                arena_surface,
                color,
                (int(actor.position.x), int(actor.position.y)),
                int(actor.radius),
            )
            self._draw_health_bar(arena_surface, actor)
            if actor is self.session.guardian and self.session.reveal_timer > 0:
                pygame.draw.circle(
                    arena_surface,
                    (255, 255, 255),
                    (int(actor.position.x), int(actor.position.y)),
                    int(actor.radius + 4),
                    width=2,
                )
        for text in self.session.texts:
            surface = self.font_small.render(text.text, True, text.color)
            surface.set_alpha(text.alpha)
            arena_surface.blit(surface, (text.position.x, text.position.y))
        self.screen.blit(arena_surface, (int(offset.x), int(offset.y)))
        self._draw_hud()
        if self.session.is_over:
            self._draw_outcome_overlay()

    def _draw_health_bar(self, surface: pygame.Surface, actor: Actor) -> None:
        width = 80
        height = 10
        x = actor.position.x - width / 2
        y = actor.position.y - actor.radius - 20
        bg_rect = pygame.Rect(int(x), int(y), width, height)
        pygame.draw.rect(surface, (30, 30, 30), bg_rect)
        pct = actor.health / actor.max_health if actor.max_health else 0
        fg_rect = pygame.Rect(int(x), int(y), int(width * pct), height)
        pygame.draw.rect(surface, (120, 220, 120), fg_rect)

    def _draw_hud(self) -> None:
        if self.session is None:
            return
        bar_y = SCREEN_HEIGHT - 60
        for index, ability_key in enumerate(self._player_ability_keys()):
            ability_state = self.session.player.abilities[ability_key]
            spec = ability_state.spec
            x = 80 + index * 120
            panel = pygame.Rect(x, bar_y, 110, 48)
            pygame.draw.rect(self.screen, (40, 48, 60), panel, border_radius=8)
            pygame.draw.rect(self.screen, spec.icon_color, panel, width=2, border_radius=8)
            name_surface = self.font_small.render(spec.name, True, (220, 230, 255))
            self.screen.blit(name_surface, (x + 8, bar_y + 6))
            key_text = self.font_small.render(f"{index + 1}", True, (170, 180, 200))
            self.screen.blit(key_text, (x + 4, bar_y + 26))
            cooldown_ratio = ability_state.cooldown_remaining / spec.cooldown if spec.cooldown else 0
            if cooldown_ratio > 0:
                overlay = pygame.Surface((panel.width, panel.height), pygame.SRCALPHA)
                alpha = int(160 * cooldown_ratio)
                overlay.fill((10, 10, 10, alpha))
                self.screen.blit(overlay, panel.topleft)
        stats = f"HP {int(self.session.player.health)}/{int(self.session.player.max_health)}  " \
                f"Energy {int(self.session.player.energy)}/{int(self.session.player.max_energy)}"
        stats_surface = self.font_small.render(stats, True, (200, 210, 230))
        self.screen.blit(stats_surface, (80, SCREEN_HEIGHT - 90))

    def _draw_outcome_overlay(self) -> None:
        assert self.session is not None
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        if self.session.outcome == "victory":
            text = "Victory!"
            color = (150, 235, 190)
        else:
            text = "Defeat"
            color = (255, 120, 120)
        label = self.font_large.render(text, True, color)
        self.screen.blit(label, (SCREEN_WIDTH / 2 - label.get_width() / 2, SCREEN_HEIGHT / 2 - 80))
        prompt = self.font_medium.render("Press Enter to continue", True, (220, 220, 230))
        self.screen.blit(prompt, (SCREEN_WIDTH / 2 - prompt.get_width() / 2, SCREEN_HEIGHT / 2))

    # ------------------------------------------------------------------
    def start_zone(self, element: Element) -> None:
        self.current_zone = element
        self.victory_recorded = False
        self.session = GameSession(element, self.campaign)

    def _player_ability_keys(self) -> List[str]:
        if self.session is None:
            return []
        return list(self.session.player.abilities.keys())[: len(self.HOTKEYS)]


def run_game() -> None:
    app = GameApp()
    app.start()
