"""Game state container and high level update loop."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List

from .abilities import ABILITY_CATALOG, Ability
from .elements import ELEMENT_ABILITY_MAP, Element
from .entities import Entity, PhysicsBody, Player
from .physics import CollisionSystem, PhysicsEngine
from .zones import CampaignProgress


@dataclass
class World:
    """Holds entities and shared systems for a match."""

    players: List[Player] = field(default_factory=list)
    projectiles: List[Entity] = field(default_factory=list)
    physics: PhysicsEngine = field(default_factory=PhysicsEngine)
    collisions: CollisionSystem = field(default_factory=CollisionSystem)

    def step(self, dt: float) -> None:
        self.physics.step(self._all_entities(), dt)
        events = self.collisions.detect(self._all_entities())
        self.collisions.resolve(events)
        self._prune_projectiles()

    def _all_entities(self) -> List[Entity]:
        return self.players + self.projectiles

    def _prune_projectiles(self) -> None:
        self.projectiles = [projectile for projectile in self.projectiles if getattr(projectile, "lifetime", 0) > 0]


@dataclass
class GameState:
    """Top level state for campaign and skirmish modes."""

    world: World = field(default_factory=World)
    campaign: CampaignProgress = field(default_factory=CampaignProgress)

    def add_player(self, name: str, element: Element) -> Player:
        player = Player(body=PhysicsBody(position=(0.0, 0.0)), name=name, element_affinity=element.value)
        self._equip_initial_abilities(player, element)
        self.world.players.append(player)
        return player

    def _equip_initial_abilities(self, player: Player, element: Element) -> None:
        ability_keys = self.campaign.serialize()["abilities"]
        if not ability_keys:
            # Fallback to at least one ability from the requested element
            ability_keys = list(ELEMENT_ABILITY_MAP.get(element, []))
        self._assign_loadout(player, ability_keys)

    def _assign_loadout(self, player: Player, ability_keys: Iterable[str]) -> None:
        slots = ("primary", "secondary", "utility", "ultimate")
        for slot, key in zip(slots, ability_keys):
            ability = ABILITY_CATALOG.get(key)
            if ability:
                setattr(player.loadout, slot, ability)

    def assign_loadout(self, player: Player, ability_keys: Iterable[str]) -> None:
        """Assign specific abilities to an existing player."""

        self._assign_loadout(player, ability_keys)

    def add_opponent(self, name: str, element: Element, ability_keys: Iterable[str]) -> Player:
        opponent = Player(body=PhysicsBody(position=(0.0, 0.0)), name=name, element_affinity=element.value)
        self._assign_loadout(opponent, ability_keys)
        self.world.players.append(opponent)
        return opponent

    def update(self, dt: float) -> None:
        self.world.step(dt)

    def complete_zone(self, element: Element) -> None:
        self.campaign.complete_zone(element)

    def available_elements(self) -> List[str]:
        return [element.value for element in sorted(self.campaign.unlocked_elements, key=lambda e: e.value)]


__all__ = ["World", "GameState"]
