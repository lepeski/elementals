"""Ability definitions and metadata."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Iterable, List, Optional, Set


class AbilityTag(Enum):
    """High level categories that describe what an ability is good at."""

    DAMAGE = auto()
    DISABLE = auto()
    UTILITY = auto()
    MOBILITY = auto()
    CHANNEL = auto()
    PASSIVE = auto()
    INFORMATION = auto()
    AREA_CONTROL = auto()
    DEFENSE = auto()


@dataclass(frozen=True)
class Ability:
    """Represents a single castable ability or passive trait."""

    name: str
    element: str
    description: str
    tags: Set[AbilityTag] = field(default_factory=set)
    shorthand: Optional[str] = None

    def summary(self) -> str:
        """Return a user facing summary string."""

        tag_names = ", ".join(sorted(tag.name for tag in self.tags)) or "UNTAGGED"
        shorthand = f" ({self.shorthand})" if self.shorthand else ""
        return f"{self.name}{shorthand} [{self.element}] - {self.description} ({tag_names})"


def build_ability_catalog() -> Dict[str, Ability]:
    """Create the catalog of abilities derived from the design guidelines."""

    def tags(*values: AbilityTag) -> Set[AbilityTag]:
        return set(values)

    catalog: Dict[str, Ability] = {
        # Psychic
        "force_push": Ability(
            name="Force Push",
            element="Psychic",
            description="Knockback opponent with a telekinetic shove.",
            tags=tags(AbilityTag.DISABLE, AbilityTag.UTILITY),
        ),
        "sixth_sense": Ability(
            name="6th Sense",
            element="Psychic",
            description="Channel to reveal enemies through walls.",
            tags=tags(AbilityTag.INFORMATION, AbilityTag.CHANNEL),
        ),
        "mind_reading": Ability(
            name="Mind Reading",
            element="Psychic",
            description="Passive awareness of which elements opponents are using.",
            tags=tags(AbilityTag.PASSIVE, AbilityTag.INFORMATION),
        ),
        # Electric (Air + Psychic)
        "bolt": Ability(
            name="Bolt",
            element="Electric",
            description="Electrocute a target at medium range; guaranteed crit if target is wet.",
            tags=tags(AbilityTag.DAMAGE, AbilityTag.DISABLE),
        ),
        "lightning": Ability(
            name="Lightning",
            element="Electric",
            description="Channel to summon a lightning strike from the sky.",
            tags=tags(AbilityTag.DAMAGE, AbilityTag.CHANNEL),
        ),
        # Air
        "whirlwind": Ability(
            name="Whirlwind",
            element="Air",
            description="Create a whirlwind that juggles nearby opponents.",
            tags=tags(AbilityTag.DISABLE, AbilityTag.AREA_CONTROL),
        ),
        "airhopper": Ability(
            name="Airhopper",
            element="Air",
            description="Passive double jump capability.",
            tags=tags(AbilityTag.PASSIVE, AbilityTag.MOBILITY),
        ),
        "flight": Ability(
            name="Flight",
            element="Air",
            description="Fly for a limited duration.",
            tags=tags(AbilityTag.MOBILITY, AbilityTag.UTILITY),
        ),
        "hurricane": Ability(
            name="Hurricane",
            element="Air",
            description="Channel to create a hurricane that displaces enemies and debris.",
            tags=tags(AbilityTag.AREA_CONTROL, AbilityTag.CHANNEL, AbilityTag.DISABLE),
        ),
        # Ice (Air + Water)
        "icicle": Ability(
            name="Icicle",
            element="Ice",
            description="Launch an icicle that may cause bleeding.",
            tags=tags(AbilityTag.DAMAGE),
            shorthand="-w",
        ),
        "freeze": Ability(
            name="Freeze",
            element="Ice",
            description="Freeze water at medium distance.",
            tags=tags(AbilityTag.UTILITY, AbilityTag.AREA_CONTROL),
        ),
        "sap": Ability(
            name="Sap",
            element="Ice",
            description=(
                "Draw moisture from an opponent, reducing hydration and dealing damage if the target is bleeding."
            ),
            tags=tags(AbilityTag.DAMAGE, AbilityTag.DISABLE),
            shorthand="+w",
        ),
        # Water
        "draw_water": Ability(
            name="Draw Water",
            element="Water",
            description="Pull water from a nearby source.",
            tags=tags(AbilityTag.UTILITY),
            shorthand="+w",
        ),
        "throw_water": Ability(
            name="Throw Water",
            element="Water",
            description="Throw gathered water as a projectile.",
            tags=tags(AbilityTag.DAMAGE, AbilityTag.UTILITY),
            shorthand="-w",
        ),
        "bubble_shield": Ability(
            name="Bubble Shield",
            element="Water",
            description="Create a bubble barrier that blocks fire and allows underwater breathing.",
            tags=tags(AbilityTag.DEFENSE, AbilityTag.AREA_CONTROL),
            shorthand="-w",
        ),
        "tsunami": Ability(
            name="Tsunami",
            element="Water",
            description="Channel a tsunami that traps opponents for the duration.",
            tags=tags(AbilityTag.AREA_CONTROL, AbilityTag.CHANNEL, AbilityTag.DISABLE),
            shorthand="(WS)",
        ),
        # Nature (Water + Earth)
        "tree": Ability(
            name="Tree",
            element="Nature",
            description="Channel to grow a tree that alters the battlefield.",
            tags=tags(AbilityTag.AREA_CONTROL, AbilityTag.CHANNEL),
            shorthand="-w +N",
        ),
        "timber": Ability(
            name="Timber",
            element="Nature",
            description="Collapse a grown tree to crush foes.",
            tags=tags(AbilityTag.DAMAGE, AbilityTag.DISABLE),
            shorthand="-Nt",
        ),
        "sticks": Ability(
            name="Sticks",
            element="Nature",
            description="Shoot branches at a target with a chance to cause bleeding.",
            tags=tags(AbilityTag.DAMAGE),
            shorthand="-Nf",
        ),
        "roots": Ability(
            name="Roots",
            element="Nature",
            description="Grow roots that immobilize a target; duration reduced by melee or fire damage.",
            tags=tags(AbilityTag.DISABLE, AbilityTag.AREA_CONTROL),
            shorthand="-w (ES)",
        ),
        # Earth
        "raise_earth": Ability(
            name="Raise Earth",
            element="Earth",
            description="Raise the ground beneath a target to disrupt positioning.",
            tags=tags(AbilityTag.DISABLE, AbilityTag.AREA_CONTROL),
            shorthand="(ES)",
        ),
        "fissure": Ability(
            name="Fissure",
            element="Earth",
            description="Crack the ground in front of you, knocking opponents down.",
            tags=tags(AbilityTag.DISABLE, AbilityTag.DAMAGE),
            shorthand="(ES)",
        ),
        "earthquake": Ability(
            name="Earthquake",
            element="Earth",
            description="Channel to trigger an earthquake that interrupts all channeling.",
            tags=tags(AbilityTag.DISABLE, AbilityTag.CHANNEL, AbilityTag.AREA_CONTROL),
            shorthand="(ES)",
        ),
        "boulder": Ability(
            name="Boulder",
            element="Earth",
            description="Hurl a chunk of earth at a target.",
            tags=tags(AbilityTag.DAMAGE),
            shorthand="(ES)",
        ),
        # Magma (Earth + Fire)
        "volcanic_geyser": Ability(
            name="Volcanic Geyser",
            element="Magma",
            description="Channel to launch magma and rocks from beneath a target.",
            tags=tags(AbilityTag.DAMAGE, AbilityTag.CHANNEL),
            shorthand="(ES)",
        ),
        # Fire
        "ignite": Ability(
            name="Ignite",
            element="Fire",
            description="Set an object ablaze.",
            tags=tags(AbilityTag.DAMAGE, AbilityTag.UTILITY),
            shorthand="(NS)",
        ),
        "draw_fire": Ability(
            name="Draw Fire",
            element="Fire",
            description="Pull in nearby flames as a resource.",
            tags=tags(AbilityTag.UTILITY),
            shorthand="+f",
        ),
        "throw_fire": Ability(
            name="Throw Fire",
            element="Fire",
            description="Throw concentrated fire at a target.",
            tags=tags(AbilityTag.DAMAGE),
            shorthand="-f",
        ),
        "flamebody": Ability(
            name="Flamebody",
            element="Fire",
            description="Envelop yourself in fire, acting as a mobile flame source.",
            tags=tags(AbilityTag.UTILITY, AbilityTag.DAMAGE),
            shorthand="-f",
        ),
        # Solar (Fire + Psychic)
        "soularbeam": Ability(
            name="Soularbeam",
            element="Solar",
            description="Channel an intense beam of solar energy in a line.",
            tags=tags(AbilityTag.DAMAGE, AbilityTag.CHANNEL),
            shorthand="-f",
        ),
        # Psychic ultimate placeholder
        "psychic_ultimate": Ability(
            name="Psionic Overload",
            element="Psychic Ultimate",
            description="(Placeholder) Devastating psychic attack to be defined.",
            tags=tags(AbilityTag.DAMAGE, AbilityTag.DISABLE),
        ),
    }

    return catalog


ABILITY_CATALOG = build_ability_catalog()
ABILITY_NAME_TO_KEY = {ability.name: key for key, ability in ABILITY_CATALOG.items()}


def iter_abilities(elements: Iterable[str]) -> List[Ability]:
    """Return abilities that belong to the provided element list."""

    results: List[Ability] = []
    normalized = {element.lower() for element in elements}
    for ability in ABILITY_CATALOG.values():
        if ability.element.lower() in normalized:
            results.append(ability)
    return sorted(results, key=lambda ability: ability.name)


__all__ = ["Ability", "AbilityTag", "ABILITY_CATALOG", "ABILITY_NAME_TO_KEY", "iter_abilities"]
