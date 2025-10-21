"""Element graph and helper utilities."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Sequence, Set, Tuple


class Element(Enum):
    """Playable element domains."""

    EARTH = "Earth"
    WATER = "Water"
    NATURE = "Nature"
    AIR = "Air"
    ICE = "Ice"
    FIRE = "Fire"
    MAGMA = "Magma"
    PSYCHIC = "Psychic"
    ELECTRIC = "Electric"
    SOLAR = "Solar"
    PSYCHIC_ULTIMATE = "Psychic Ultimate"
    MAGMA_ULTIMATE = "Magma Ultimate"
    NATURE_ULTIMATE = "Nature Ultimate"
    SOLAR_ULTIMATE = "Solar Ultimate"
    ELECTRIC_ULTIMATE = "Electric Ultimate"

    @property
    def is_base_zone(self) -> bool:
        return self in {Element.EARTH, Element.WATER}


ELEMENT_ADJACENCY: Dict[Element, Set[Element]] = {
    Element.PSYCHIC_ULTIMATE: {Element.SOLAR_ULTIMATE, Element.ELECTRIC_ULTIMATE, Element.PSYCHIC},
    Element.SOLAR_ULTIMATE: {Element.FIRE, Element.SOLAR, Element.PSYCHIC_ULTIMATE},
    Element.ELECTRIC_ULTIMATE: {Element.AIR, Element.ELECTRIC, Element.PSYCHIC_ULTIMATE},
    Element.MAGMA_ULTIMATE: {Element.EARTH, Element.FIRE},
    Element.NATURE_ULTIMATE: {Element.EARTH, Element.WATER},
    Element.ELECTRIC: {Element.AIR, Element.PSYCHIC},
    Element.SOLAR: {Element.FIRE, Element.PSYCHIC},
    Element.ICE: {Element.AIR, Element.WATER},
    Element.NATURE: {Element.EARTH, Element.WATER},
    Element.MAGMA: {Element.EARTH, Element.FIRE},
    Element.AIR: {Element.ICE, Element.ELECTRIC, Element.SOLAR_ULTIMATE},
    Element.WATER: {Element.ICE, Element.NATURE, Element.NATURE_ULTIMATE},
    Element.EARTH: {Element.NATURE, Element.MAGMA, Element.MAGMA_ULTIMATE},
    Element.FIRE: {Element.MAGMA, Element.SOLAR, Element.SOLAR_ULTIMATE},
    Element.PSYCHIC: {Element.SOLAR, Element.ELECTRIC, Element.PSYCHIC_ULTIMATE},
}


@dataclass(frozen=True)
class Zone:
    """Represents a progression zone."""

    element: Element
    unlocked: bool = False


def get_unlockable_elements(completed: Sequence[Element]) -> Set[Element]:
    """Return the set of elements that can be visited next."""

    if not completed:
        return {element for element in Element if element.is_base_zone}

    last = completed[-1]
    return ELEMENT_ADJACENCY.get(last, set())


def combined_element(element_a: Element, element_b: Element) -> Optional[Element]:
    """Return the combined element unlocked by completing two adjacent zones."""

    for element, neighbors in ELEMENT_ADJACENCY.items():
        if {element_a, element_b} <= neighbors:
            return element
    return None


def path_to_element(target: Element) -> Optional[List[Element]]:
    """Derive one valid progression path to reach the target element."""

    visited: Set[Element] = set()
    queue: List[Tuple[Element, List[Element]]] = []

    for start in (Element.EARTH, Element.WATER):
        queue.append((start, [start]))

    while queue:
        current, path = queue.pop(0)
        if current == target:
            return path
        if current in visited:
            continue
        visited.add(current)
        for neighbor in ELEMENT_ADJACENCY.get(current, set()):
            if neighbor not in path:
                queue.append((neighbor, path + [neighbor]))
    return None


ELEMENT_ABILITY_MAP: Dict[Element, Set[str]] = {
    Element.PSYCHIC: {
        "force_push",
        "sixth_sense",
        "mind_reading",
    },
    Element.ELECTRIC: {"bolt", "lightning"},
    Element.AIR: {"whirlwind", "airhopper", "flight", "hurricane"},
    Element.ICE: {"icicle", "freeze", "sap"},
    Element.WATER: {"draw_water", "throw_water", "bubble_shield", "tsunami"},
    Element.NATURE: {"tree", "timber", "sticks", "roots"},
    Element.EARTH: {"raise_earth", "fissure", "earthquake", "boulder"},
    Element.MAGMA: {"volcanic_geyser"},
    Element.FIRE: {"ignite", "draw_fire", "throw_fire", "flamebody"},
    Element.SOLAR: {"soularbeam"},
    Element.PSYCHIC_ULTIMATE: {"psychic_ultimate"},
}


__all__ = [
    "Element",
    "Zone",
    "ELEMENT_ADJACENCY",
    "ELEMENT_ABILITY_MAP",
    "get_unlockable_elements",
    "combined_element",
    "path_to_element",
]
