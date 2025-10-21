"""Lightweight 2D vector and collision helpers for the Elementals prototype."""
from __future__ import annotations

from dataclasses import dataclass
from math import atan2, cos, hypot, sin
from typing import Iterable, Tuple


@dataclass
class Vec2:
    """Simple 2D vector with convenience helpers."""

    x: float = 0.0
    y: float = 0.0

    # ------------------------------------------------------------------
    # Basic operations
    # ------------------------------------------------------------------
    def __add__(self, other: "Vec2") -> "Vec2":
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vec2") -> "Vec2":
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> "Vec2":
        return Vec2(self.x * scalar, self.y * scalar)

    __rmul__ = __mul__

    def __truediv__(self, scalar: float) -> "Vec2":
        if scalar == 0:
            return Vec2(self.x, self.y)
        return Vec2(self.x / scalar, self.y / scalar)

    # ------------------------------------------------------------------
    def copy(self) -> "Vec2":
        return Vec2(self.x, self.y)

    def as_tuple(self) -> Tuple[float, float]:
        return self.x, self.y

    def length(self) -> float:
        return hypot(self.x, self.y)

    def length_squared(self) -> float:
        return self.x * self.x + self.y * self.y

    def normalize(self) -> "Vec2":
        mag = self.length()
        if mag == 0:
            return Vec2(0.0, 0.0)
        return Vec2(self.x / mag, self.y / mag)

    def clamp_length(self, max_length: float) -> "Vec2":
        mag_sq = self.length_squared()
        if mag_sq <= max_length * max_length:
            return self
        mag = mag_sq ** 0.5
        if mag == 0:
            return Vec2(0.0, 0.0)
        scale = max_length / mag
        return Vec2(self.x * scale, self.y * scale)

    def angle(self) -> float:
        return atan2(self.y, self.x)

    @staticmethod
    def from_angle(angle: float, magnitude: float = 1.0) -> "Vec2":
        return Vec2(cos(angle) * magnitude, sin(angle) * magnitude)


def average(points: Iterable[Vec2]) -> Vec2:
    total = Vec2()
    count = 0
    for point in points:
        total.x += point.x
        total.y += point.y
        count += 1
    if count == 0:
        return Vec2()
    return total / count


def clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(value, max_value))


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def distance(a: Vec2, b: Vec2) -> float:
    return hypot(a.x - b.x, a.y - b.y)


def direction(a: Vec2, b: Vec2) -> Vec2:
    return Vec2(b.x - a.x, b.y - a.y).normalize()


def collide_circles(pos_a: Vec2, radius_a: float, pos_b: Vec2, radius_b: float) -> bool:
    radii = radius_a + radius_b
    return (pos_a.x - pos_b.x) ** 2 + (pos_a.y - pos_b.y) ** 2 <= radii * radii


def reflect(velocity: Vec2, normal: Vec2) -> Vec2:
    # v' = v - 2 * (v · n) * n
    dot = velocity.x * normal.x + velocity.y * normal.y
    return Vec2(velocity.x - 2 * dot * normal.x, velocity.y - 2 * dot * normal.y)


def normal_from_points(a: Vec2, b: Vec2) -> Vec2:
    """Return a normalized perpendicular vector from segment AB."""

    dx = b.x - a.x
    dy = b.y - a.y
    normal = Vec2(-dy, dx)
    return normal.normalize()
