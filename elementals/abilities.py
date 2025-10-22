"""Ability specifications and gameplay behaviors."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Tuple, TYPE_CHECKING

from .elements import Element
from .entities import StatusEffect
from .physics import Vec2

if TYPE_CHECKING:  # pragma: no cover
    from .entities import Actor
    from .game import GameSession

Color = Tuple[int, int, int]


@dataclass
class AbilitySpec:
    key: str
    name: str
    element: Element
    description: str
    cooldown: float
    energy_cost: float
    icon_color: Color
    cast: Callable[["GameSession", "Actor"], None]


# ---------------------------------------------------------------------------
# Helper utilities used by ability behaviors
# ---------------------------------------------------------------------------


def _spawn_projectile(
    game: "GameSession",
    caster: "Actor",
    *,
    speed: float,
    damage: float,
    radius: float,
    color: Color,
    lifespan: float = 2.0,
    knockback: float = 0.0,
    status_factory: Callable[[], "StatusEffect"] | None = None,
) -> None:
    from .entities import Projectile

    direction = caster.facing.normalize()
    spawn = caster.position + direction * (caster.radius + radius + 4.0)
    projectile = Projectile(
        position=spawn,
        velocity=direction * speed,
        radius=radius,
        damage=damage,
        color=color,
        owner=caster,
        lifespan=lifespan,
        knockback=knockback,
    )

    def on_hit(game: "GameSession", proj: Projectile, target: "Actor") -> None:
        impulse = direction * proj.knockback if proj.knockback else None
        game.deal_damage(target, proj.damage, source=caster, impulse=impulse)
        if status_factory is not None:
            target.add_status(status_factory())

    projectile.on_hit = on_hit
    game.spawn_projectile(projectile)
    game.spawn_effect(spawn, color, radius + 6.0, 0.15)


def _aoe(
    game: "GameSession",
    caster: "Actor",
    center: Vec2,
    radius: float,
    damage: float,
    *,
    knockback: float = 0.0,
    slow_factor: float | None = None,
    slow_duration: float = 0.0,
    dot_damage: float = 0.0,
    dot_duration: float = 0.0,
    stun_duration: float = 0.0,
    color: Color = (255, 255, 255),
) -> None:
    for actor in game.actors_in_radius(center, radius, exclude=caster):
        impulse: Vec2 | None = None
        if knockback:
            impulse = (actor.position - center).normalize() * knockback
        game.deal_damage(actor, damage, source=caster, impulse=impulse)
        if slow_factor is not None and slow_duration > 0:
            actor.add_status(
                StatusEffect(
                    name="slow",
                    duration=slow_duration,
                    slow_factor=slow_factor,
                    color=color,
                )
            )
        if dot_damage > 0 and dot_duration > 0:
            actor.add_status(
                StatusEffect(
                    name="burn",
                    duration=dot_duration,
                    damage_per_second=dot_damage,
                    color=color,
                )
            )
        if stun_duration > 0:
            actor.add_status(
                StatusEffect(
                    name="stun",
                    duration=stun_duration,
                    stun=True,
                    color=color,
                )
            )
    game.spawn_effect(center, color, radius, 0.3)


def _front_point(caster: "Actor", distance: float) -> Vec2:
    return caster.position + caster.facing.normalize() * distance


# ---------------------------------------------------------------------------
# Element ability implementations
# ---------------------------------------------------------------------------


def earth_boulder(game: "GameSession", caster: "Actor") -> None:
    _spawn_projectile(
        game,
        caster,
        speed=360.0,
        damage=18.0,
        radius=12.0,
        color=(196, 173, 133),
        knockback=280.0,
    )


def earth_fissure(game: "GameSession", caster: "Actor") -> None:
    center = _front_point(caster, 80.0)
    _aoe(
        game,
        caster,
        center=center,
        radius=85.0,
        damage=14.0,
        knockback=260.0,
        slow_factor=0.55,
        slow_duration=1.4,
        color=(205, 140, 90),
    )


def earth_fortify(game: "GameSession", caster: "Actor") -> None:
    caster.add_status(
        StatusEffect(
            name="stone_shield",
            duration=6.0,
            shield=70.0,
            slow_factor=0.95,
            color=(210, 195, 150),
        )
    )
    game.spawn_effect(caster.position, (210, 195, 150), 44.0, 0.5)


def earth_quake(game: "GameSession", caster: "Actor") -> None:
    _aoe(
        game,
        caster,
        center=caster.position,
        radius=180.0,
        damage=22.0,
        knockback=360.0,
        slow_factor=0.5,
        slow_duration=1.2,
        color=(235, 200, 160),
    )
    game.shake(0.35)


def water_bolt(game: "GameSession", caster: "Actor") -> None:
    def soaked() -> StatusEffect:
        return StatusEffect(
            name="soaked",
            duration=3.0,
            slow_factor=0.75,
            color=(110, 180, 235),
        )

    _spawn_projectile(
        game,
        caster,
        speed=420.0,
        damage=12.0,
        radius=10.0,
        color=(90, 165, 230),
        knockback=160.0,
        status_factory=soaked,
    )


def water_bubble(game: "GameSession", caster: "Actor") -> None:
    caster.add_status(
        StatusEffect(
            name="bubble",
            duration=4.0,
            shield=80.0,
            slow_factor=1.0,
            color=(130, 200, 255),
        )
    )
    game.spawn_effect(caster.position, (130, 200, 255), 48.0, 0.6)


def water_draw(game: "GameSession", caster: "Actor") -> None:
    caster.restore_health(28.0)
    caster.energy = min(caster.max_energy, caster.energy + 20.0)
    game.spawn_effect(caster.position, (110, 190, 220), 36.0, 0.35)


def water_tsunami(game: "GameSession", caster: "Actor") -> None:
    center = _front_point(caster, 120.0)
    _aoe(
        game,
        caster,
        center=center,
        radius=170.0,
        damage=10.0,
        knockback=280.0,
        slow_factor=0.6,
        slow_duration=2.4,
        color=(120, 190, 240),
    )


def fire_bolt(game: "GameSession", caster: "Actor") -> None:
    def burning() -> StatusEffect:
        return StatusEffect(
            name="burn",
            duration=3.5,
            damage_per_second=4.0,
            color=(255, 140, 60),
        )

    _spawn_projectile(
        game,
        caster,
        speed=450.0,
        damage=16.0,
        radius=9.0,
        color=(255, 110, 50),
        knockback=140.0,
        status_factory=burning,
    )


def fire_flamebody(game: "GameSession", caster: "Actor") -> None:
    caster.add_status(
        StatusEffect(
            name="flamebody",
            duration=6.0,
            damage_per_second=2.5,
            slow_factor=1.05,
            color=(255, 120, 70),
        )
    )
    caster.add_status(
        StatusEffect(
            name="fire_shield",
            duration=6.0,
            shield=45.0,
            color=(255, 170, 90),
        )
    )
    game.spawn_effect(caster.position, (255, 160, 80), 42.0, 0.5)


def fire_scorch(game: "GameSession", caster: "Actor") -> None:
    center = _front_point(caster, 90.0)
    _aoe(
        game,
        caster,
        center=center,
        radius=120.0,
        damage=14.0,
        dot_damage=5.0,
        dot_duration=3.0,
        color=(255, 150, 80),
    )


def fire_dash(game: "GameSession", caster: "Actor") -> None:
    caster.set_velocity(caster.facing.normalize() * 520.0)
    game.spawn_effect(caster.position, (255, 130, 70), 36.0, 0.25)


def air_whirlwind(game: "GameSession", caster: "Actor") -> None:
    center = _front_point(caster, 90.0)
    _aoe(
        game,
        caster,
        center=center,
        radius=130.0,
        damage=8.0,
        knockback=320.0,
        slow_factor=0.7,
        slow_duration=1.5,
        color=(160, 210, 255),
    )


def air_dash(game: "GameSession", caster: "Actor") -> None:
    caster.set_velocity(caster.facing.normalize() * 560.0)
    game.spawn_effect(caster.position, (150, 210, 255), 32.0, 0.2)


def air_hurricane(game: "GameSession", caster: "Actor") -> None:
    _aoe(
        game,
        caster,
        center=caster.position,
        radius=190.0,
        damage=12.0,
        knockback=380.0,
        slow_factor=0.65,
        slow_duration=2.0,
        color=(180, 225, 255),
    )


def air_updraft(game: "GameSession", caster: "Actor") -> None:
    caster.add_status(
        StatusEffect(
            name="updraft",
            duration=4.0,
            slow_factor=1.15,
            color=(170, 220, 255),
        )
    )
    game.spawn_effect(caster.position, (170, 220, 255), 40.0, 0.3)


def psychic_push(game: "GameSession", caster: "Actor") -> None:
    for actor in game.actors_in_radius(_front_point(caster, 110.0), 110.0, exclude=caster):
        impulse = (actor.position - caster.position).normalize() * 420.0
        game.deal_damage(actor, 6.0, source=caster, impulse=impulse)
        actor.add_status(
            StatusEffect(name="dazed", duration=0.8, slow_factor=0.6, color=(200, 120, 255))
        )


def psychic_stasis(game: "GameSession", caster: "Actor") -> None:
    center = _front_point(caster, 90.0)
    _aoe(
        game,
        caster,
        center=center,
        radius=110.0,
        damage=4.0,
        slow_factor=0.2,
        slow_duration=1.6,
        stun_duration=0.6,
        color=(200, 150, 255),
    )


def psychic_mindspike(game: "GameSession", caster: "Actor") -> None:
    _spawn_projectile(
        game,
        caster,
        speed=480.0,
        damage=14.0,
        radius=8.0,
        color=(220, 180, 255),
        knockback=120.0,
        status_factory=lambda: StatusEffect(name="mind_slow", duration=2.0, slow_factor=0.7, color=(220, 180, 255)),
    )


def psychic_insight(game: "GameSession", caster: "Actor") -> None:
    caster.add_status(StatusEffect(name="insight", duration=5.0, slow_factor=1.1, color=(240, 200, 255)))
    game.reveal_opponent()


def nature_roots(game: "GameSession", caster: "Actor") -> None:
    center = _front_point(caster, 130.0)
    for actor in game.actors_in_radius(center, 120.0, exclude=caster):
        actor.add_status(
            StatusEffect(
                name="rooted",
                duration=2.2,
                stun=True,
                slow_factor=0.1,
                color=(140, 200, 120),
            )
        )
        game.deal_damage(actor, 12.0, source=caster)
    game.spawn_effect(center, (140, 200, 120), 110.0, 0.6)


def magma_geyser(game: "GameSession", caster: "Actor") -> None:
    center = _front_point(caster, 120.0)
    _aoe(
        game,
        caster,
        center=center,
        radius=120.0,
        damage=24.0,
        dot_damage=6.0,
        dot_duration=4.0,
        knockback=200.0,
        color=(255, 120, 60),
    )


def ice_freeze(game: "GameSession", caster: "Actor") -> None:
    center = _front_point(caster, 120.0)
    for actor in game.actors_in_radius(center, 130.0, exclude=caster):
        actor.add_status(
            StatusEffect(
                name="frozen",
                duration=2.5,
                slow_factor=0.1,
                stun=True,
                color=(200, 240, 255),
            )
        )
        game.deal_damage(actor, 16.0, source=caster)
    game.spawn_effect(center, (200, 240, 255), 120.0, 0.6)


def electric_burst(game: "GameSession", caster: "Actor") -> None:
    center = _front_point(caster, 100.0)
    _aoe(
        game,
        caster,
        center=center,
        radius=140.0,
        damage=18.0,
        slow_factor=0.75,
        slow_duration=1.2,
        stun_duration=0.4,
        color=(190, 230, 255),
    )


def solar_beam(game: "GameSession", caster: "Actor") -> None:
    origin = caster.position
    forward = caster.facing.normalize()
    width = 70.0
    length = 360.0
    for actor in game.iter_enemies(caster):
        to_target = actor.position - origin
        projection = to_target.x * forward.x + to_target.y * forward.y
        if 0 < projection <= length:
            perpendicular = abs(forward.x * to_target.y - forward.y * to_target.x)
            if perpendicular <= width:
                impulse = forward * 320.0
                game.deal_damage(actor, 30.0, source=caster, impulse=impulse)
                actor.add_status(StatusEffect(name="radiance", duration=2.0, slow_factor=0.85, color=(255, 230, 170)))
    game.spawn_effect(origin + forward * (length * 0.5), (255, 220, 150), length * 0.5, 0.3)


# ---------------------------------------------------------------------------
# Catalog setup
# ---------------------------------------------------------------------------


ABILITY_LIBRARY: Dict[str, AbilitySpec] = {
    # Earth
    "earth_boulder": AbilitySpec(
        key="earth_boulder",
        name="Boulder",
        element=Element.EARTH,
        description="Hurl a heavy boulder that knocks foes back.",
        cooldown=1.4,
        energy_cost=12.0,
        icon_color=(190, 160, 120),
        cast=earth_boulder,
    ),
    "earth_fissure": AbilitySpec(
        key="earth_fissure",
        name="Fissure",
        element=Element.EARTH,
        description="Rend the ground ahead, staggering opponents.",
        cooldown=4.0,
        energy_cost=16.0,
        icon_color=(205, 140, 90),
        cast=earth_fissure,
    ),
    "earth_fortify": AbilitySpec(
        key="earth_fortify",
        name="Stone Guard",
        element=Element.EARTH,
        description="Wrap yourself in protective earth.",
        cooldown=8.0,
        energy_cost=18.0,
        icon_color=(210, 195, 150),
        cast=earth_fortify,
    ),
    "earth_quake": AbilitySpec(
        key="earth_quake",
        name="Earthquake",
        element=Element.EARTH,
        description="Shake the battlefield with a brutal quake.",
        cooldown=10.0,
        energy_cost=24.0,
        icon_color=(235, 200, 160),
        cast=earth_quake,
    ),
    # Water
    "water_bolt": AbilitySpec(
        key="water_bolt",
        name="Water Bolt",
        element=Element.WATER,
        description="Launch a chilling bolt that soaks foes.",
        cooldown=1.2,
        energy_cost=10.0,
        icon_color=(100, 170, 235),
        cast=water_bolt,
    ),
    "water_bubble": AbilitySpec(
        key="water_bubble",
        name="Bubble Shield",
        element=Element.WATER,
        description="Summon a shield of water to absorb hits.",
        cooldown=7.0,
        energy_cost=20.0,
        icon_color=(130, 200, 255),
        cast=water_bubble,
    ),
    "water_draw": AbilitySpec(
        key="water_draw",
        name="Draw Water",
        element=Element.WATER,
        description="Heal and restore energy.",
        cooldown=6.5,
        energy_cost=0.0,
        icon_color=(110, 190, 220),
        cast=water_draw,
    ),
    "water_tsunami": AbilitySpec(
        key="water_tsunami",
        name="Tsunami",
        element=Element.WATER,
        description="Crash a wave forward, pushing foes away.",
        cooldown=9.0,
        energy_cost=24.0,
        icon_color=(120, 190, 240),
        cast=water_tsunami,
    ),
    # Fire
    "fire_bolt": AbilitySpec(
        key="fire_bolt",
        name="Flame Shot",
        element=Element.FIRE,
        description="Ignite enemies with a searing projectile.",
        cooldown=1.0,
        energy_cost=12.0,
        icon_color=(255, 120, 70),
        cast=fire_bolt,
    ),
    "fire_flamebody": AbilitySpec(
        key="fire_flamebody",
        name="Flamebody",
        element=Element.FIRE,
        description="Envelop yourself in living fire.",
        cooldown=10.0,
        energy_cost=22.0,
        icon_color=(255, 160, 80),
        cast=fire_flamebody,
    ),
    "fire_scorch": AbilitySpec(
        key="fire_scorch",
        name="Scorch Field",
        element=Element.FIRE,
        description="Create a burning patch ahead of you.",
        cooldown=6.5,
        energy_cost=18.0,
        icon_color=(255, 150, 80),
        cast=fire_scorch,
    ),
    "fire_dash": AbilitySpec(
        key="fire_dash",
        name="Blazing Dash",
        element=Element.FIRE,
        description="Dash forward leaving a burning trail.",
        cooldown=4.5,
        energy_cost=14.0,
        icon_color=(255, 130, 70),
        cast=fire_dash,
    ),
    # Air
    "air_whirlwind": AbilitySpec(
        key="air_whirlwind",
        name="Whirlwind",
        element=Element.AIR,
        description="Create a disruptive whirlwind ahead.",
        cooldown=3.5,
        energy_cost=16.0,
        icon_color=(170, 220, 255),
        cast=air_whirlwind,
    ),
    "air_dash": AbilitySpec(
        key="air_dash",
        name="Gale Dash",
        element=Element.AIR,
        description="Ride the wind forward instantly.",
        cooldown=4.0,
        energy_cost=12.0,
        icon_color=(150, 210, 255),
        cast=air_dash,
    ),
    "air_hurricane": AbilitySpec(
        key="air_hurricane",
        name="Hurricane",
        element=Element.AIR,
        description="Unleash a swirling storm around you.",
        cooldown=10.0,
        energy_cost=24.0,
        icon_color=(180, 225, 255),
        cast=air_hurricane,
    ),
    "air_updraft": AbilitySpec(
        key="air_updraft",
        name="Updraft",
        element=Element.AIR,
        description="Lighten your steps with an updraft.",
        cooldown=6.0,
        energy_cost=14.0,
        icon_color=(170, 220, 255),
        cast=air_updraft,
    ),
    # Psychic
    "psychic_push": AbilitySpec(
        key="psychic_push",
        name="Force Push",
        element=Element.PSYCHIC,
        description="Blast foes away telekinetically.",
        cooldown=3.0,
        energy_cost=14.0,
        icon_color=(200, 150, 255),
        cast=psychic_push,
    ),
    "psychic_stasis": AbilitySpec(
        key="psychic_stasis",
        name="Stasis Field",
        element=Element.PSYCHIC,
        description="Suspend enemies in front of you.",
        cooldown=8.0,
        energy_cost=20.0,
        icon_color=(200, 150, 255),
        cast=psychic_stasis,
    ),
    "psychic_mindspike": AbilitySpec(
        key="psychic_mindspike",
        name="Mind Spike",
        element=Element.PSYCHIC,
        description="Launch a piercing psychic bolt.",
        cooldown=1.2,
        energy_cost=12.0,
        icon_color=(220, 180, 255),
        cast=psychic_mindspike,
    ),
    "psychic_insight": AbilitySpec(
        key="psychic_insight",
        name="Sixth Sense",
        element=Element.PSYCHIC,
        description="Briefly reveal your foe's intent.",
        cooldown=12.0,
        energy_cost=16.0,
        icon_color=(240, 200, 255),
        cast=psychic_insight,
    ),
    # Combo abilities
    "nature_roots": AbilitySpec(
        key="nature_roots",
        name="Roots",
        element=Element.NATURE,
        description="Entangle and stun enemies ahead.",
        cooldown=9.0,
        energy_cost=20.0,
        icon_color=(140, 200, 120),
        cast=nature_roots,
    ),
    "magma_geyser": AbilitySpec(
        key="magma_geyser",
        name="Volcanic Geyser",
        element=Element.MAGMA,
        description="Erupt the ground under distant foes.",
        cooldown=11.0,
        energy_cost=24.0,
        icon_color=(255, 120, 60),
        cast=magma_geyser,
    ),
    "ice_freeze": AbilitySpec(
        key="ice_freeze",
        name="Freeze",
        element=Element.ICE,
        description="Freeze enemies solid in an area.",
        cooldown=10.0,
        energy_cost=22.0,
        icon_color=(200, 240, 255),
        cast=ice_freeze,
    ),
    "electric_burst": AbilitySpec(
        key="electric_burst",
        name="Lightning Burst",
        element=Element.ELECTRIC,
        description="Stunning burst of electricity.",
        cooldown=9.0,
        energy_cost=20.0,
        icon_color=(190, 230, 255),
        cast=electric_burst,
    ),
    "solar_beam": AbilitySpec(
        key="solar_beam",
        name="Soularbeam",
        element=Element.SOLAR,
        description="Channel a piercing solar beam.",
        cooldown=12.0,
        energy_cost=28.0,
        icon_color=(255, 220, 150),
        cast=solar_beam,
    ),
}


DEFAULT_LOADOUTS: Dict[Element, List[str]] = {
    Element.EARTH: ["earth_boulder", "earth_fissure", "earth_fortify", "earth_quake"],
    Element.WATER: ["water_bolt", "water_bubble", "water_draw", "water_tsunami"],
    Element.FIRE: ["fire_bolt", "fire_scorch", "fire_flamebody", "fire_dash"],
    Element.AIR: ["air_whirlwind", "air_dash", "air_updraft", "air_hurricane"],
    Element.PSYCHIC: ["psychic_mindspike", "psychic_push", "psychic_stasis", "psychic_insight"],
}


COMBO_ABILITIES: Dict[Element, str] = {
    Element.NATURE: "nature_roots",
    Element.MAGMA: "magma_geyser",
    Element.ICE: "ice_freeze",
    Element.ELECTRIC: "electric_burst",
    Element.SOLAR: "solar_beam",
}


def loadout_for(element: Element, combos: Iterable[Element] = ()) -> List[AbilitySpec]:
    specs = [ABILITY_LIBRARY[key] for key in DEFAULT_LOADOUTS[element]]
    for combo in combos:
        key = COMBO_ABILITIES.get(combo)
        if key:
            specs.append(ABILITY_LIBRARY[key])
    return specs
