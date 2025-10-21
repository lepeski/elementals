"""Element graph and combo helpers."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Iterable, List, Sequence, Set


class Element(str, Enum):
    EARTH = "earth"
    WATER = "water"
    FIRE = "fire"
    AIR = "air"
    PSYCHIC = "psychic"
    NATURE = "nature"
    MAGMA = "magma"
    ICE = "ice"
    ELECTRIC = "electric"
    SOLAR = "solar"


# Undirected graph describing the campaign layout. Each node exposes
# exactly two neighbors to respect the guideline "can only move to 1 of 2
# adjacent zones".
ZONE_GRAPH: Dict[Element, Sequence[Element]] = {
    Element.EARTH: (Element.WATER, Element.FIRE),
    Element.WATER: (Element.EARTH, Element.AIR),
    Element.FIRE: (Element.EARTH, Element.PSYCHIC),
    Element.AIR: (Element.WATER, Element.PSYCHIC),
    Element.PSYCHIC: (Element.FIRE, Element.AIR),
    Element.NATURE: (),
    Element.MAGMA: (),
    Element.ICE: (),
    Element.ELECTRIC: (),
    Element.SOLAR: (),
}


COMBO_LOOKUP: Dict[frozenset[Element], Element] = {
    frozenset({Element.EARTH, Element.WATER}): Element.NATURE,
    frozenset({Element.EARTH, Element.FIRE}): Element.MAGMA,
    frozenset({Element.WATER, Element.AIR}): Element.ICE,
    frozenset({Element.AIR, Element.PSYCHIC}): Element.ELECTRIC,
    frozenset({Element.FIRE, Element.PSYCHIC}): Element.SOLAR,
}


def combo_for(elements: Iterable[Element]) -> Element | None:
    key = frozenset(elements)
    return COMBO_LOOKUP.get(key)


@dataclass
class CampaignState:
    """Tracks unlocked zones and combo abilities."""

    completed: List[Element]
    unlocked_combos: Set[Element]

    @classmethod
    def new(cls) -> "CampaignState":
        return cls(completed=[], unlocked_combos=set())

    # ------------------------------------------------------------------
    def available_zones(self) -> Sequence[Element]:
        if not self.completed:
            return (Element.EARTH, Element.WATER)
        head = self.completed[-1]
        neighbors = ZONE_GRAPH.get(head, ())
        return tuple(elem for elem in neighbors if elem not in self.completed)

    def record_victory(self, element: Element) -> None:
        if element not in self.completed:
            self.completed.append(element)
        if len(self.completed) >= 2:
            combo = combo_for(self.completed[-2:])
            if combo:
                self.unlocked_combos.add(combo)

    # ------------------------------------------------------------------
    def describe_progress(self) -> str:
        if not self.completed:
            return "Choose Earth or Water to begin your trials."
        zone_names = ", ".join(elem.value.title() for elem in self.completed)
        combo_names = ", ".join(elem.value.title() for elem in sorted(self.unlocked_combos, key=lambda e: e.value))
        if combo_names:
            return f"Completed zones: {zone_names}. Combo unlocks: {combo_names}."
        return f"Completed zones: {zone_names}."
