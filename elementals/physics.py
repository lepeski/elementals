"""Lightweight physics helpers."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Tuple

from .entities import Entity, PhysicsBody, vec_add, vec_scale


@dataclass
class PhysicsSettings:
    gravity: float = 0.0
    drag: float = 0.05


@dataclass
class PhysicsEngine:
    """Very small physics system intended for top-down movement."""

    settings: PhysicsSettings = field(default_factory=PhysicsSettings)

    def step(self, entities: Iterable[Entity], dt: float) -> None:
        for entity in entities:
            self.apply_environment(entity.body, dt)
            entity.tick(dt)

    def apply_environment(self, body: PhysicsBody, dt: float) -> None:
        """Apply drag and gravity to the body."""

        if self.settings.gravity:
            gravity_force = (0.0, -self.settings.gravity * body.mass)
            body.apply_force(gravity_force)

        if self.settings.drag:
            drag_force = vec_scale(body.velocity, -self.settings.drag)
            body.apply_force(drag_force)


@dataclass
class CollisionEvent:
    first: Entity
    second: Entity
    normal: Tuple[float, float]


@dataclass
class CollisionSystem:
    """Detects and resolves circular collisions."""

    def detect(self, entities: List[Entity]) -> List[CollisionEvent]:
        events: List[CollisionEvent] = []
        for i, first in enumerate(entities):
            for second in entities[i + 1 :]:
                if self._intersects(first.body, second.body):
                    normal = self._collision_normal(first.body, second.body)
                    events.append(CollisionEvent(first, second, normal))
        return events

    @staticmethod
    def _intersects(first: PhysicsBody, second: PhysicsBody) -> bool:
        dx = first.position[0] - second.position[0]
        dy = first.position[1] - second.position[1]
        radius = first.radius + second.radius
        return dx * dx + dy * dy <= radius * radius

    @staticmethod
    def _collision_normal(first: PhysicsBody, second: PhysicsBody) -> Tuple[float, float]:
        dx = first.position[0] - second.position[0]
        dy = first.position[1] - second.position[1]
        magnitude = (dx * dx + dy * dy) ** 0.5 or 1.0
        return dx / magnitude, dy / magnitude

    def resolve(self, events: List[CollisionEvent]) -> None:
        for event in events:
            self._resolve_event(event)

    def _resolve_event(self, event: CollisionEvent) -> None:
        n_x, n_y = event.normal
        overlap = event.first.body.radius + event.second.body.radius
        penetration = overlap / 2
        event.first.body.position = (
            event.first.body.position[0] + n_x * penetration,
            event.first.body.position[1] + n_y * penetration,
        )
        event.second.body.position = (
            event.second.body.position[0] - n_x * penetration,
            event.second.body.position[1] - n_y * penetration,
        )


__all__ = [
    "PhysicsSettings",
    "PhysicsEngine",
    "CollisionEvent",
    "CollisionSystem",
]
