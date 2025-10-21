"""Core game entities and components."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .abilities import Ability


Vector = Tuple[float, float]


def vec_add(a: Vector, b: Vector) -> Vector:
    return a[0] + b[0], a[1] + b[1]


def vec_sub(a: Vector, b: Vector) -> Vector:
    return a[0] - b[0], a[1] - b[1]


def vec_scale(a: Vector, scale: float) -> Vector:
    return a[0] * scale, a[1] * scale


def vec_length(a: Vector) -> float:
    return math.hypot(a[0], a[1])


def vec_normalize(a: Vector) -> Vector:
    length = vec_length(a)
    if length == 0:
        return (0.0, 0.0)
    return a[0] / length, a[1] / length


def vec_clamp(a: Vector, limit: float) -> Vector:
    length = vec_length(a)
    if length <= limit or length == 0:
        return a
    scale = limit / length
    return a[0] * scale, a[1] * scale


def vec_zero() -> Vector:
    return 0.0, 0.0


@dataclass
class Stats:
    max_health: float = 100.0
    health: float = 100.0
    max_stamina: float = 100.0
    stamina: float = 100.0
    max_hydration: float = 100.0
    hydration: float = 100.0

    def apply_damage(self, amount: float) -> None:
        self.health = max(0.0, self.health - amount)

    def restore_health(self, amount: float) -> None:
        self.health = min(self.max_health, self.health + amount)

    def expend_stamina(self, amount: float) -> None:
        self.stamina = max(0.0, self.stamina - amount)

    def restore_stamina(self, amount: float) -> None:
        self.stamina = min(self.max_stamina, self.stamina + amount)

    def adjust_hydration(self, amount: float) -> None:
        self.hydration = max(0.0, min(self.max_hydration, self.hydration + amount))

    def regenerate(self, dt: float, stamina_rate: float = 12.0, hydration_rate: float = 2.0) -> None:
        self.restore_stamina(stamina_rate * dt)
        self.adjust_hydration(hydration_rate * dt)

    @property
    def is_alive(self) -> bool:
        return self.health > 0.0


@dataclass
class PhysicsBody:
    position: Vector
    velocity: Vector = field(default_factory=vec_zero)
    acceleration: Vector = field(default_factory=vec_zero)
    radius: float = 0.5
    mass: float = 1.0

    def integrate(self, dt: float) -> None:
        self.velocity = vec_add(self.velocity, vec_scale(self.acceleration, dt))
        self.position = vec_add(self.position, vec_scale(self.velocity, dt))
        self.acceleration = vec_zero()

    def apply_force(self, force: Vector) -> None:
        if self.mass <= 0:
            return
        ax = force[0] / self.mass
        ay = force[1] / self.mass
        self.acceleration = vec_add(self.acceleration, (ax, ay))


@dataclass
class Entity:
    body: PhysicsBody
    stats: Stats = field(default_factory=Stats)
    element_affinity: Optional[str] = None
    active_effects: Dict[str, float] = field(default_factory=dict)

    def tick(self, dt: float) -> None:
        self.body.integrate(dt)
        self.stats.regenerate(dt)
        self._tick_effects(dt)

    def _tick_effects(self, dt: float) -> None:
        if not self.active_effects:
            return
        for name in list(self.active_effects.keys()):
            if name == "burning":
                self.take_damage(1.2 * dt)
            elif name == "bleeding":
                self.take_damage(0.8 * dt)
            self.active_effects[name] = max(0.0, self.active_effects[name] - dt)
            if self.active_effects[name] <= 0.0:
                del self.active_effects[name]

    def take_damage(self, amount: float) -> float:
        if amount <= 0.0:
            return 0.0
        final_amount = amount
        if self.has_effect("bubble_shield"):
            final_amount *= 0.6
        if self.has_effect("tree_guard"):
            final_amount *= 0.85
        self.stats.apply_damage(final_amount)
        return final_amount

    def heal(self, amount: float) -> None:
        if amount > 0:
            self.stats.restore_health(amount)

    def add_effect(self, name: str, duration: float) -> None:
        if duration <= 0:
            return
        current = self.active_effects.get(name, 0.0)
        self.active_effects[name] = max(current, duration)

    def remove_effect(self, name: str) -> None:
        self.active_effects.pop(name, None)

    def has_effect(self, name: str) -> bool:
        return self.active_effects.get(name, 0.0) > 0.0


@dataclass
class AbilityLoadout:
    primary: Optional[Ability] = None
    secondary: Optional[Ability] = None
    utility: Optional[Ability] = None
    ultimate: Optional[Ability] = None

    def equipped(self) -> List[Ability]:
        return [ability for ability in (self.primary, self.secondary, self.utility, self.ultimate) if ability]

    def slots(self) -> Dict[str, Ability]:
        return {
            slot: ability
            for slot, ability in (
                ("primary", self.primary),
                ("secondary", self.secondary),
                ("utility", self.utility),
                ("ultimate", self.ultimate),
            )
            if ability is not None
        }


@dataclass
class Player(Entity):
    name: str = "Player"
    loadout: AbilityLoadout = field(default_factory=AbilityLoadout)
    inventory: List[str] = field(default_factory=list)
    move_speed: float = 6.0

    def cast(self, ability: Ability, target: Entity) -> None:
        """Placeholder cast hook; the combat system will live here."""

        # The actual implementation will apply ability specific logic.
        target.stats.apply_damage(5.0)
        target.body.apply_force((0.0, 0.0))


@dataclass
class Projectile(Entity):
    source_player_id: Optional[int] = None
    lifetime: float = 5.0

    def tick(self, dt: float) -> None:  # type: ignore[override]
        super().tick(dt)
        self.lifetime -= dt


__all__ = [
    "Vector",
    "vec_add",
    "vec_sub",
    "vec_scale",
    "vec_length",
    "vec_normalize",
    "vec_clamp",
    "vec_zero",
    "Stats",
    "PhysicsBody",
    "Entity",
    "AbilityLoadout",
    "Player",
    "Projectile",
]
