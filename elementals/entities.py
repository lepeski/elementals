"""Entity model for the real-time prototype."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional

from .elements import Element
from .physics import Vec2, clamp

if False:  # pragma: no cover - for type checking only
    from .abilities import AbilitySpec


# ---------------------------------------------------------------------------
# Status effects
# ---------------------------------------------------------------------------


@dataclass
class StatusEffect:
    name: str
    duration: float
    slow_factor: float = 1.0
    damage_per_second: float = 0.0
    shield: float = 0.0
    stun: bool = False
    color: tuple[int, int, int] | None = None
    data: Dict[str, float] = field(default_factory=dict)

    def tick(self, actor: "Actor", dt: float) -> None:
        if self.damage_per_second > 0:
            actor.take_damage(self.damage_per_second * dt, source=None)
        self.duration -= dt

    @property
    def expired(self) -> bool:
        return self.duration <= 0


# ---------------------------------------------------------------------------
# Abilities
# ---------------------------------------------------------------------------


@dataclass
class AbilityState:
    spec: "AbilitySpec"
    cooldown_remaining: float = 0.0

    def update(self, dt: float) -> None:
        if self.cooldown_remaining > 0:
            self.cooldown_remaining = max(0.0, self.cooldown_remaining - dt)

    @property
    def ready(self) -> bool:
        return self.cooldown_remaining <= 0

    def trigger(self) -> None:
        self.cooldown_remaining = self.spec.cooldown


# ---------------------------------------------------------------------------
# Actor and projectiles
# ---------------------------------------------------------------------------


@dataclass
class Actor:
    name: str
    element: Element
    position: Vec2
    color: tuple[int, int, int]
    radius: float = 18.0
    mass: float = 1.0
    max_health: float = 120.0
    max_energy: float = 100.0
    health: float = 120.0
    energy: float = 100.0
    speed: float = 220.0
    acceleration: float = 900.0
    friction: float = 6.0
    facing: Vec2 = field(default_factory=lambda: Vec2(1.0, 0.0))
    velocity: Vec2 = field(default_factory=Vec2)
    abilities: Dict[str, AbilityState] = field(default_factory=dict)
    statuses: List[StatusEffect] = field(default_factory=list)
    ai_brain: Optional[Callable[["Actor", "GameSession", float], None]] = None

    def update(self, dt: float) -> None:
        self.velocity = self.velocity * max(0.0, 1.0 - self.friction * dt)
        self.position += self.velocity * dt
        for ability in self.abilities.values():
            ability.update(dt)
        remaining: List[StatusEffect] = []
        for status in self.statuses:
            status.tick(self, dt)
            if not status.expired:
                remaining.append(status)
        self.statuses = remaining
        self.energy = clamp(self.energy + 12.0 * dt, 0.0, self.max_energy)

    # ------------------------------------------------------------------
    def apply_input(self, direction: Vec2, dt: float) -> None:
        if self.is_stunned:
            return
        desired = direction.clamp_length(1.0)
        self.velocity += desired * self.acceleration * dt
        speed_limit = self.speed * self.speed_multiplier
        self.velocity = self.velocity.clamp_length(speed_limit)
        if desired.length_squared() > 0:
            self.facing = desired.normalize()

    def set_velocity(self, velocity: Vec2) -> None:
        self.velocity = velocity

    def take_damage(self, amount: float, source: "Actor" | None, impulse: Vec2 | None = None) -> float:
        if amount <= 0:
            return 0.0
        remaining = amount
        for status in self.statuses:
            if status.shield > 0:
                current = status.data.setdefault("shield_remaining", status.shield)
                if current <= 0:
                    continue
                absorbed = min(current, remaining)
                current -= absorbed
                status.data["shield_remaining"] = current
                remaining -= absorbed
                if remaining <= 0:
                    break
        if remaining <= 0:
            return 0.0
        self.health = max(0.0, self.health - remaining)
        if impulse is not None and self.mass > 0:
            self.velocity += impulse / self.mass
        return remaining

    def restore_health(self, amount: float) -> None:
        if amount > 0:
            self.health = clamp(self.health + amount, 0.0, self.max_health)

    def spend_energy(self, amount: float) -> bool:
        if amount <= self.energy:
            self.energy -= amount
            return True
        return False

    def add_status(self, status: StatusEffect) -> None:
        self.statuses.append(status)

    def has_status(self, name: str) -> bool:
        return any(status.name == name for status in self.statuses)

    @property
    def is_alive(self) -> bool:
        return self.health > 0

    @property
    def is_stunned(self) -> bool:
        return any(status.stun for status in self.statuses)

    @property
    def speed_multiplier(self) -> float:
        multiplier = 1.0
        for status in self.statuses:
            multiplier *= status.slow_factor
        return max(0.1, multiplier)

    def aim_towards(self, target: Vec2) -> None:
        delta = target - self.position
        if delta.length_squared() > 0.001:
            self.facing = delta.normalize()

    # ------------------------------------------------------------------
    def ability_list(self) -> Iterable[AbilityState]:
        return self.abilities.values()

    def bind_ability(self, key: str, ability: "AbilitySpec") -> None:
        self.abilities[key] = AbilityState(spec=ability)


@dataclass
class Projectile:
    position: Vec2
    velocity: Vec2
    radius: float
    damage: float
    color: tuple[int, int, int]
    owner: Actor
    lifespan: float = 2.0
    knockback: float = 0.0
    on_hit: Optional[Callable[["GameSession", "Projectile", Actor], None]] = None

    def update(self, dt: float) -> None:
        self.position += self.velocity * dt
        self.lifespan -= dt

    @property
    def alive(self) -> bool:
        return self.lifespan > 0


@dataclass
class Obstacle:
    x: float
    y: float
    w: float
    h: float

    def contains(self, point: Vec2) -> bool:
        return self.x <= point.x <= self.x + self.w and self.y <= point.y <= self.y + self.h

    def clamp_position(self, position: Vec2, radius: float) -> Vec2:
        px = clamp(position.x, self.x + radius, self.x + self.w - radius)
        py = clamp(position.y, self.y + radius, self.y + self.h - radius)
        return Vec2(px, py)

    def as_rect(self) -> tuple[int, int, int, int]:
        return int(self.x), int(self.y), int(self.w), int(self.h)


GameSession = "GameSession"
