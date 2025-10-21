"""Core package for the Elementals prototype game."""

from .elements import Element, ELEMENT_ADJACENCY, ELEMENT_ABILITY_MAP
from .abilities import Ability, AbilityTag
from .game_state import GameState

__all__ = [
    "Ability",
    "AbilityTag",
    "Element",
    "ELEMENT_ADJACENCY",
    "ELEMENT_ABILITY_MAP",
    "GameState",
]
