"""Zone progression logic for campaign style unlocks."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Set

from .abilities import ABILITY_CATALOG
from .elements import Element, ELEMENT_ABILITY_MAP, ELEMENT_ADJACENCY, combined_element


@dataclass
class ZoneState:
    """Mutable state associated with a zone."""

    element: Element
    completed: bool = False

    def unlocks(self) -> Set[Element]:
        """Return the set of elements that become available when this zone is cleared."""

        return ELEMENT_ADJACENCY.get(self.element, set())


@dataclass
class CampaignProgress:
    """Tracks which zones the player has cleared and which abilities were earned."""

    completed_zones: List[ZoneState] = field(default_factory=list)
    unlocked_elements: Set[Element] = field(default_factory=lambda: {Element.EARTH, Element.WATER})
    unlocked_abilities: Set[str] = field(default_factory=set)

    def complete_zone(self, element: Element) -> None:
        """Mark a zone as completed and unlock new elements or abilities."""

        if element not in self.unlocked_elements:
            raise ValueError(f"Zone {element.value} is not currently unlocked.")

        existing = next((zone for zone in self.completed_zones if zone.element == element), None)
        if existing and existing.completed:
            return

        zone_state = existing or ZoneState(element=element)
        zone_state.completed = True
        if not existing:
            self.completed_zones.append(zone_state)

        self.unlocked_elements.update(zone_state.unlocks())
        self._unlock_zone_abilities(element)
        self._unlock_combo_ability_if_applicable()

    def _unlock_zone_abilities(self, element: Element) -> None:
        """Unlock abilities that belong to the provided element."""

        for ability_key in ELEMENT_ABILITY_MAP.get(element, set()):
            if ability_key in ABILITY_CATALOG:
                self.unlocked_abilities.add(ability_key)

    def _unlock_combo_ability_if_applicable(self) -> None:
        """Unlock combined elements gained by finishing adjacent zones."""

        if len(self.completed_zones) < 2:
            return

        latest = self.completed_zones[-1].element
        second_latest = self.completed_zones[-2].element
        combo = combined_element(latest, second_latest)
        if combo is None:
            return

        for ability_key in ELEMENT_ABILITY_MAP.get(combo, set()):
            if ability_key in ABILITY_CATALOG:
                self.unlocked_abilities.add(ability_key)
        self.unlocked_elements.add(combo)

    def serialize(self) -> Dict[str, List[str]]:
        """Serialize the progress for save files."""

        return {
            "completed": [zone.element.value for zone in self.completed_zones if zone.completed],
            "unlocked": [element.value for element in self.unlocked_elements],
            "abilities": sorted(self.unlocked_abilities),
        }

    @classmethod
    def from_completed(cls, completed: Iterable[Element]) -> "CampaignProgress":
        """Construct a campaign state from a list of completed elements."""

        progress = cls()
        for element in completed:
            progress.complete_zone(element)
        return progress


__all__ = ["ZoneState", "CampaignProgress"]
