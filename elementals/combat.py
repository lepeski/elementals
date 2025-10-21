"""Utilities that power the single-player combat sandbox."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .abilities import ABILITY_NAME_TO_KEY, Ability
from .entities import (
    Player,
    vec_add,
    vec_clamp,
    vec_length,
    vec_normalize,
    vec_scale,
    vec_sub,
    vec_zero,
)
from .game_state import GameState


Vector = Tuple[float, float]


@dataclass(frozen=True)
class AbilityBehavior:
    """Gameplay metadata for an ability."""

    key: str
    cooldown: float
    damage: float = 0.0
    range: float = 6.0
    knockback: float = 0.0
    apply_status: Optional[Tuple[str, float]] = None
    self_status: Optional[Tuple[str, float]] = None
    stamina_cost: float = 10.0
    hydration_cost: float = 0.0
    heal: float = 0.0
    hydration_restore: float = 0.0
    stamina_restore: float = 0.0
    target_self: bool = False
    description: str = ""


DEFAULT_BEHAVIOR = AbilityBehavior(
    key="default",
    cooldown=4.0,
    damage=6.0,
    range=5.5,
    stamina_cost=12.0,
    description="A basic elemental blast that deals reliable damage.",
)


ABILITY_BEHAVIORS: Dict[str, AbilityBehavior] = {
    "force_push": AbilityBehavior(
        key="force_push",
        cooldown=4.0,
        damage=6.0,
        range=4.5,
        knockback=8.0,
        stamina_cost=14.0,
        description="Telekinetically shove an enemy and send them flying.",
    ),
    "sixth_sense": AbilityBehavior(
        key="sixth_sense",
        cooldown=10.0,
        target_self=True,
        stamina_cost=8.0,
        self_status=("sixth_sense", 10.0),
        description="Channel awareness that highlights enemy intent.",
    ),
    "mind_reading": AbilityBehavior(
        key="mind_reading",
        cooldown=0.0,
        target_self=True,
        stamina_cost=4.0,
        self_status=("mind_reading", 30.0),
        description="Focus to anticipate which element the opponent favors.",
    ),
    "bolt": AbilityBehavior(
        key="bolt",
        cooldown=5.0,
        damage=9.0,
        range=7.0,
        stamina_cost=16.0,
        description="Zap a target with crackling lightning.",
    ),
    "lightning": AbilityBehavior(
        key="lightning",
        cooldown=12.0,
        damage=14.0,
        range=8.0,
        apply_status=("stunned", 2.5),
        stamina_cost=20.0,
        description="Summon a devastating vertical lightning strike.",
    ),
    "whirlwind": AbilityBehavior(
        key="whirlwind",
        cooldown=6.0,
        damage=4.0,
        range=3.5,
        apply_status=("stunned", 2.5),
        knockback=4.0,
        stamina_cost=14.0,
        description="Create a mini tornado that juggles nearby foes.",
    ),
    "airhopper": AbilityBehavior(
        key="airhopper",
        cooldown=12.0,
        target_self=True,
        stamina_cost=6.0,
        self_status=("airhopper", 15.0),
        stamina_restore=12.0,
        description="Empower legs with a burst of air for agile movement.",
    ),
    "flight": AbilityBehavior(
        key="flight",
        cooldown=12.0,
        target_self=True,
        stamina_cost=18.0,
        self_status=("flying", 6.0),
        description="Take to the skies for a short burst of aerial control.",
    ),
    "hurricane": AbilityBehavior(
        key="hurricane",
        cooldown=10.0,
        damage=6.0,
        range=3.5,
        knockback=5.0,
        apply_status=("stunned", 3.0),
        stamina_cost=18.0,
        description="Channel a localized hurricane that scatters enemies.",
    ),
    "icicle": AbilityBehavior(
        key="icicle",
        cooldown=4.0,
        damage=7.0,
        range=6.0,
        apply_status=("bleeding", 6.0),
        stamina_cost=12.0,
        description="Launch a razor-sharp icicle that causes bleeding.",
    ),
    "freeze": AbilityBehavior(
        key="freeze",
        cooldown=6.0,
        damage=2.0,
        range=5.5,
        apply_status=("rooted", 4.0),
        stamina_cost=14.0,
        description="Freeze water around the foe to pin them in place.",
    ),
    "sap": AbilityBehavior(
        key="sap",
        cooldown=7.0,
        damage=5.0,
        range=5.0,
        hydration_restore=10.0,
        stamina_cost=14.0,
        description="Drain moisture from an opponent to empower yourself.",
    ),
    "draw_water": AbilityBehavior(
        key="draw_water",
        cooldown=6.0,
        target_self=True,
        stamina_cost=6.0,
        hydration_restore=20.0,
        stamina_restore=8.0,
        description="Gather nearby water to refill resources.",
    ),
    "throw_water": AbilityBehavior(
        key="throw_water",
        cooldown=4.0,
        damage=6.0,
        range=6.0,
        apply_status=("wet", 8.0),
        stamina_cost=10.0,
        description="Blast an opponent with a wave that leaves them soaked.",
    ),
    "bubble_shield": AbilityBehavior(
        key="bubble_shield",
        cooldown=10.0,
        target_self=True,
        stamina_cost=12.0,
        self_status=("bubble_shield", 8.0),
        description="Encapsulate yourself in a protective bubble.",
    ),
    "tsunami": AbilityBehavior(
        key="tsunami",
        cooldown=14.0,
        damage=10.0,
        range=6.5,
        apply_status=("stunned", 4.0),
        stamina_cost=22.0,
        description="Channel an overwhelming wave that engulfs foes.",
    ),
    "tree": AbilityBehavior(
        key="tree",
        cooldown=14.0,
        target_self=True,
        stamina_cost=16.0,
        heal=6.0,
        self_status=("tree_guard", 12.0),
        description="Grow a tree to shelter and slowly mend wounds.",
    ),
    "timber": AbilityBehavior(
        key="timber",
        cooldown=8.0,
        damage=9.0,
        range=4.5,
        apply_status=("stunned", 2.5),
        stamina_cost=16.0,
        description="Topple a grown tree onto the opponent.",
    ),
    "sticks": AbilityBehavior(
        key="sticks",
        cooldown=5.0,
        damage=6.0,
        range=6.0,
        apply_status=("bleeding", 6.0),
        stamina_cost=12.0,
        description="Fire a barrage of sharpened branches.",
    ),
    "roots": AbilityBehavior(
        key="roots",
        cooldown=7.0,
        damage=3.0,
        range=5.0,
        apply_status=("rooted", 5.0),
        stamina_cost=14.0,
        description="Entangle the foe with rapidly growing roots.",
    ),
    "raise_earth": AbilityBehavior(
        key="raise_earth",
        cooldown=6.0,
        damage=5.0,
        range=4.0,
        knockback=3.0,
        apply_status=("rooted", 2.5),
        stamina_cost=14.0,
        description="Jolt the ground upward beneath an opponent.",
    ),
    "fissure": AbilityBehavior(
        key="fissure",
        cooldown=7.0,
        damage=8.0,
        range=4.5,
        apply_status=("stunned", 2.5),
        stamina_cost=16.0,
        description="Rip the ground apart in front of you.",
    ),
    "earthquake": AbilityBehavior(
        key="earthquake",
        cooldown=12.0,
        damage=4.0,
        range=5.0,
        apply_status=("stunned", 3.0),
        stamina_cost=18.0,
        description="Channel a quake that rattles anyone nearby.",
    ),
    "boulder": AbilityBehavior(
        key="boulder",
        cooldown=8.0,
        damage=11.0,
        range=6.0,
        stamina_cost=18.0,
        description="Hurl a hefty boulder with crushing force.",
    ),
    "volcanic_geyser": AbilityBehavior(
        key="volcanic_geyser",
        cooldown=12.0,
        damage=12.0,
        range=5.0,
        apply_status=("burning", 6.0),
        stamina_cost=20.0,
        description="Erupt magma beneath the target's feet.",
    ),
    "ignite": AbilityBehavior(
        key="ignite",
        cooldown=4.0,
        damage=4.0,
        range=4.5,
        apply_status=("burning", 6.0),
        stamina_cost=10.0,
        description="Ignite an enemy or object in front of you.",
    ),
    "draw_fire": AbilityBehavior(
        key="draw_fire",
        cooldown=6.0,
        target_self=True,
        stamina_cost=4.0,
        stamina_restore=15.0,
        self_status=("fire_source", 10.0),
        description="Pull surrounding flames to empower yourself.",
    ),
    "throw_fire": AbilityBehavior(
        key="throw_fire",
        cooldown=6.0,
        damage=9.0,
        range=6.0,
        apply_status=("burning", 5.0),
        stamina_cost=16.0,
        description="Sling a concentrated fireball at a foe.",
    ),
    "flamebody": AbilityBehavior(
        key="flamebody",
        cooldown=10.0,
        target_self=True,
        stamina_cost=14.0,
        self_status=("flamebody", 8.0),
        description="Cloak yourself in an aura of flame.",
    ),
    "soularbeam": AbilityBehavior(
        key="soularbeam",
        cooldown=14.0,
        damage=15.0,
        range=7.0,
        stamina_cost=22.0,
        description="Channel a piercing beam of solar energy.",
    ),
    "psychic_ultimate": AbilityBehavior(
        key="psychic_ultimate",
        cooldown=18.0,
        damage=18.0,
        range=6.5,
        apply_status=("stunned", 4.0),
        stamina_cost=24.0,
        description="Overload an opponent with raw psionic force.",
    ),
}


@dataclass
class PlayerCommand:
    """Represents a player's input for a single simulation step."""

    move: Vector = vec_zero()
    ability: Optional[Ability] = None
    wait: bool = False


def _distance(a: Vector, b: Vector) -> float:
    return vec_length(vec_sub(a, b))


@dataclass
class SkirmishMatch:
    """Manages a small-scale duel between two players."""

    game_state: GameState
    player: Player
    opponent: Player
    dt: float = 0.25
    arena_radius: float = 8.0
    cooldowns: Dict[int, Dict[str, float]] = field(default_factory=dict)
    elapsed: float = 0.0

    def __post_init__(self) -> None:
        self.cooldowns.setdefault(id(self.player), {})
        self.cooldowns.setdefault(id(self.opponent), {})
        self.player.body.position = (-3.0, 0.0)
        self.opponent.body.position = (3.0, 0.0)
        self.player.body.velocity = vec_zero()
        self.opponent.body.velocity = vec_zero()

    def behavior_for(self, ability: Ability) -> AbilityBehavior:
        key = ABILITY_NAME_TO_KEY.get(ability.name)
        if key is None:
            return DEFAULT_BEHAVIOR
        return ABILITY_BEHAVIORS.get(key, DEFAULT_BEHAVIOR)

    def available_abilities(self, actor: Player) -> List[Ability]:
        return actor.loadout.equipped()

    def cooldown_for(self, actor: Player, ability: Ability) -> float:
        return self.cooldowns.get(id(actor), {}).get(ability.name, 0.0)

    def can_cast(self, actor: Player, ability: Ability, target: Optional[Player]) -> Tuple[bool, str]:
        behavior = self.behavior_for(ability)
        cooldown_remaining = self.cooldown_for(actor, ability)
        if cooldown_remaining > 0.0:
            return False, f"{ability.name} ready in {cooldown_remaining:.1f}s."
        if not actor.stats.is_alive:
            return False, f"{actor.name} is incapacitated."
        if actor.has_effect("stunned"):
            return False, f"{actor.name} is stunned."
        if not behavior.target_self:
            if not target or not target.stats.is_alive:
                return False, "Target is unavailable."
            if actor is target:
                return False, "Cannot target self with this ability."
            distance = _distance(actor.body.position, target.body.position)
            if distance > behavior.range:
                return False, "Target is out of range."
        if actor.stats.stamina < behavior.stamina_cost:
            return False, "Not enough stamina."
        if actor.stats.hydration < behavior.hydration_cost:
            return False, "Not enough hydration."
        return True, ""

    def cast(self, actor: Player, ability: Ability, target: Optional[Player]) -> Tuple[bool, str]:
        ready, reason = self.can_cast(actor, ability, target)
        behavior = self.behavior_for(ability)
        actual_target: Player = actor if behavior.target_self else (target or actor)
        if not ready:
            return False, reason

        actor.stats.expend_stamina(behavior.stamina_cost)
        actor.stats.adjust_hydration(-behavior.hydration_cost)
        if behavior.stamina_restore:
            actor.stats.restore_stamina(behavior.stamina_restore)
        if behavior.hydration_restore:
            actor.stats.adjust_hydration(behavior.hydration_restore)
        if behavior.heal:
            actual_target.heal(behavior.heal)

        damage = behavior.damage
        notes: List[str] = []
        key = ABILITY_NAME_TO_KEY.get(ability.name, "")
        if key == "bolt" and target and target.has_effect("wet"):
            damage += 6.0
            notes.append("supercharged by moisture")
        if key == "sap" and target:
            if target.has_effect("bleeding"):
                damage += 4.0
                notes.append("bloodletting amplifies the drain")
            target.stats.adjust_hydration(-12.0)
        if key == "throw_fire" and target and target.has_effect("wet"):
            damage *= 0.5
            notes.append("steam dulls the flames")
        if key == "ignite" and target and target.has_effect("wet"):
            notes.append("the damp target resists ignition")
            damage *= 0.7
        if key == "lightning" and target:
            notes.append("thunderous strike")
        if key == "earthquake" and target:
            notes.append("ground shatters underfoot")
        if key == "tree":
            notes.append("a sturdy tree grows to shield you")

        dealt = 0.0
        if damage > 0.0 and actual_target.stats.is_alive:
            dealt = actual_target.take_damage(damage)

        if behavior.apply_status:
            status, duration = behavior.apply_status
            actual_target.add_effect(status, duration)
        if behavior.self_status:
            status, duration = behavior.self_status
            actor.add_effect(status, duration)

        if behavior.knockback and target and not behavior.target_self:
            direction = vec_normalize(vec_sub(target.body.position, actor.body.position))
            impulse = vec_scale(direction, behavior.knockback)
            target.body.velocity = vec_add(target.body.velocity, impulse)

        self.cooldowns.setdefault(id(actor), {})[ability.name] = behavior.cooldown

        note_suffix = f" ({'; '.join(notes)})" if notes else ""
        if behavior.target_self and behavior.heal > 0:
            return True, f"{ability.name} restores {behavior.heal:.0f} health{note_suffix}."
        if dealt > 0:
            return True, f"{ability.name} deals {dealt:.1f} damage{note_suffix}."
        return True, f"{ability.name} activated{note_suffix}."

    def apply_movement(self, actor: Player, direction: Vector, wait: bool = False) -> Optional[str]:
        if wait:
            actor.body.velocity = vec_zero()
            return None
        if actor.has_effect("stunned"):
            actor.body.velocity = vec_zero()
            return f"{actor.name} is stunned and cannot move."
        if actor.has_effect("rooted"):
            actor.body.velocity = vec_zero()
            return f"{actor.name} is rooted to the spot."
        desired = vec_clamp(direction, 1.0)
        if desired == (0.0, 0.0):
            actor.body.velocity = vec_zero()
            return None
        speed = actor.move_speed
        if actor.has_effect("airhopper"):
            speed *= 1.2
        if actor.has_effect("flying"):
            speed *= 1.4
        actor.body.velocity = vec_scale(desired, speed)
        return f"{actor.name} repositions." if vec_length(desired) > 0 else None

    def step(self) -> None:
        self.game_state.update(self.dt)
        self.elapsed += self.dt
        self._decay_cooldowns()
        self._clamp_positions()

    def execute_turn(
        self, player_command: PlayerCommand, ai_command: Optional[PlayerCommand] = None
    ) -> List[str]:
        log: List[str] = []

        if player_command.ability:
            success, message = self.cast(self.player, player_command.ability, self.opponent)
            prefix = "You" if success else "You"
            log.append(f"{prefix}: {message}")
        move_feedback = self.apply_movement(self.player, player_command.move, player_command.wait)
        if move_feedback:
            log.append(f"You: {move_feedback}")

        opponent_command = ai_command or SimpleAI(self, self.opponent).decide(self.player)
        if opponent_command.ability:
            success, message = self.cast(self.opponent, opponent_command.ability, self.player)
            actor_label = self.opponent.name
            log.append(f"{actor_label}: {message}")
        move_feedback = self.apply_movement(
            self.opponent, opponent_command.move, opponent_command.wait
        )
        if move_feedback:
            log.append(f"{self.opponent.name}: {move_feedback}")

        self.step()
        return log

    @property
    def is_over(self) -> bool:
        return not self.player.stats.is_alive or not self.opponent.stats.is_alive

    @property
    def winner(self) -> Optional[Player]:
        if self.player.stats.is_alive and not self.opponent.stats.is_alive:
            return self.player
        if self.opponent.stats.is_alive and not self.player.stats.is_alive:
            return self.opponent
        return None

    def _decay_cooldowns(self) -> None:
        for cd_map in self.cooldowns.values():
            for ability_name in list(cd_map.keys()):
                cd_map[ability_name] = max(0.0, cd_map[ability_name] - self.dt)

    def _clamp_positions(self) -> None:
        for combatant in (self.player, self.opponent):
            x, y = combatant.body.position
            x = max(-self.arena_radius, min(self.arena_radius, x))
            y = max(-self.arena_radius, min(self.arena_radius, y))
            combatant.body.position = (x, y)


@dataclass
class SimpleAI:
    """A light-weight AI that makes greedy combat decisions."""

    match: SkirmishMatch
    actor: Player

    def decide(self, opponent: Player) -> PlayerCommand:
        if not self.actor.stats.is_alive:
            return PlayerCommand(wait=True)
        if self.actor.has_effect("stunned"):
            return PlayerCommand(wait=True)

        ability = self._choose_ability(opponent)
        move_vector = vec_zero()

        if ability:
            behavior = self.match.behavior_for(ability)
            if behavior.target_self:
                move_vector = vec_zero()
            elif opponent.stats.is_alive:
                distance = _distance(self.actor.body.position, opponent.body.position)
                if distance > behavior.range * 0.85:
                    move_vector = vec_normalize(vec_sub(opponent.body.position, self.actor.body.position))
                elif distance < behavior.range * 0.55:
                    move_vector = vec_normalize(vec_sub(self.actor.body.position, opponent.body.position))
        else:
            if opponent.stats.is_alive:
                move_vector = vec_normalize(vec_sub(opponent.body.position, self.actor.body.position))

        # Occasionally strafe to avoid deterministic duels.
        if move_vector != (0.0, 0.0) and random.random() < 0.2:
            move_vector = vec_normalize((move_vector[1], -move_vector[0]))

        return PlayerCommand(move=move_vector, ability=ability)

    def _choose_ability(self, opponent: Player) -> Optional[Ability]:
        for ability in self.match.available_abilities(self.actor):
            behavior = self.match.behavior_for(ability)
            target = self.actor if behavior.target_self else opponent
            ready, _ = self.match.can_cast(self.actor, ability, target)
            if ready:
                return ability
        return None


__all__ = [
    "AbilityBehavior",
    "ABILITY_BEHAVIORS",
    "DEFAULT_BEHAVIOR",
    "PlayerCommand",
    "SkirmishMatch",
    "SimpleAI",
]
