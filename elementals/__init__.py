"""Core exports for the Elementals real-time prototype."""
from .abilities import ABILITY_LIBRARY, AbilitySpec, COMBO_ABILITIES, DEFAULT_LOADOUTS, loadout_for
from .elements import CampaignState, Element, combo_for
from .game import GameApp, GameSession, run_game
from .physics import Vec2

__all__ = [
    "ABILITY_LIBRARY",
    "AbilitySpec",
    "CampaignState",
    "COMBO_ABILITIES",
    "DEFAULT_LOADOUTS",
    "Element",
    "GameApp",
    "GameSession",
    "Vec2",
    "combo_for",
    "loadout_for",
    "run_game",
]
