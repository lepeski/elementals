"""Command line entry point for playtesting the single-player prototype."""
from __future__ import annotations

import argparse
import textwrap
from typing import Dict, List, Optional

from elementals import ELEMENT_ABILITY_MAP, Element, GameState
from elementals.abilities import ABILITY_CATALOG
from elementals.combat import PlayerCommand, SimpleAI, SkirmishMatch
from elementals.entities import Player, vec_zero


DIRECTION_MAP: Dict[str, tuple[float, float]] = {
    "n": (0.0, 1.0),
    "north": (0.0, 1.0),
    "s": (0.0, -1.0),
    "south": (0.0, -1.0),
    "e": (1.0, 0.0),
    "east": (1.0, 0.0),
    "w": (-1.0, 0.0),
    "west": (-1.0, 0.0),
    "ne": (1.0, 1.0),
    "nw": (-1.0, 1.0),
    "se": (1.0, -1.0),
    "sw": (-1.0, -1.0),
    "up": (0.0, 1.0),
    "down": (0.0, -1.0),
    "left": (-1.0, 0.0),
    "right": (1.0, 0.0),
}


class SinglePlayerSession:
    """Wraps an interactive skirmish session."""

    def __init__(self, dt: float = 0.25) -> None:
        self.dt = dt
        self.game_state = GameState()
        self.match: Optional[SkirmishMatch] = None
        self.player: Optional[Player] = None
        self.opponent: Optional[Player] = None

    # ------------------------------------------------------------------
    # Setup helpers
    # ------------------------------------------------------------------
    def configure(self, player_element: Element, opponent_element: Optional[Element] = None) -> None:
        """Configure a new match between the player and an AI opponent."""

        self.game_state = GameState()
        self.game_state.complete_zone(player_element)
        self.player = self.game_state.add_player("Seeker", player_element)

        player_abilities = self.game_state.campaign.serialize()["abilities"][:4]
        if not player_abilities:
            player_abilities = list(ELEMENT_ABILITY_MAP.get(player_element, []))[:4]
        self.game_state.assign_loadout(self.player, player_abilities)

        opponent_element = opponent_element or (Element.WATER if player_element == Element.EARTH else Element.EARTH)
        opponent_abilities = list(ELEMENT_ABILITY_MAP.get(opponent_element, []))[:4]
        if not opponent_abilities:
            opponent_abilities = [key for key in ABILITY_CATALOG][:4]
        self.opponent = self.game_state.add_opponent("Guardian", opponent_element, opponent_abilities)

        self.match = SkirmishMatch(self.game_state, self.player, self.opponent, dt=self.dt)

    # ------------------------------------------------------------------
    # Interactive flow
    # ------------------------------------------------------------------
    def interactive(self) -> None:
        element = self._prompt_for_element()
        self.configure(element)
        assert self.match and self.player and self.opponent
        self._print_intro(element)
        while not self.match.is_over:
            self._display_status()
            try:
                raw = input("Action (type 'help' for options)> ").strip()
            except EOFError:
                print()
                break
            if not raw:
                continue
            lowered = raw.lower()
            if lowered in {"quit", "exit", "q"}:
                print("Exiting match early.")
                return
            if self._handle_meta_command(lowered):
                continue
            command = self._parse_command(raw)
            if command is None:
                continue
            for message in self.match.execute_turn(command):
                print(f"  {message}")
        winner = self.match.winner
        if winner is None:
            print("The duel ends inconclusively.")
        elif winner is self.player:
            print("Victory! You have bested the elemental guardian.")
        else:
            print("Defeat. Reflect on the encounter and try again!")

    def run_demo(self, turns: int = 10) -> None:
        """Run an automated match to showcase the systems."""

        self.configure(Element.EARTH, Element.WATER)
        assert self.match and self.player and self.opponent
        auto_player = SimpleAI(self.match, self.player)
        print("Running automated elemental duel demo...\n")
        for turn in range(1, turns + 1):
            if self.match.is_over:
                break
            player_command = auto_player.decide(self.opponent)
            print(f"Turn {turn}")
            for message in self.match.execute_turn(player_command):
                print(f"  {message}")
            self._display_status(compact=True)
            print()
        winner = self.match.winner
        if winner is None:
            print("The combatants reach a stalemate.")
        else:
            print(f"Winner: {winner.name}")

    # ------------------------------------------------------------------
    # Command parsing helpers
    # ------------------------------------------------------------------
    def _handle_meta_command(self, lowered: str) -> bool:
        if lowered in {"help", "?"}:
            self._print_help()
            return True
        if lowered in {"status", "state"}:
            self._display_status()
            return True
        if lowered in {"abilities", "spells"}:
            self._show_abilities()
            return True
        return False

    def _parse_command(self, raw: str) -> Optional[PlayerCommand]:
        if not self.match or not self.player:
            return None
        tokens = raw.lower().split()
        index = 0
        command = PlayerCommand()
        while index < len(tokens):
            token = tokens[index]
            if token in {"move", "m", "go"}:
                index += 1
                if index >= len(tokens):
                    print("Please specify a direction to move (e.g. 'move north').")
                    return None
                direction = self._parse_direction(tokens[index])
                if direction is None:
                    print("Unknown direction. Try north, south, east, west, or diagonals like ne.")
                    return None
                command.move = direction
                command.wait = False
                index += 1
                continue
            if token in {"cast", "c"}:
                index += 1
                if index >= len(tokens):
                    print("Specify which ability to cast (e.g. 'cast primary').")
                    return None
                ability_tokens: List[str] = []
                while index < len(tokens) and tokens[index] not in {"move", "m", "go", "cast", "c", "wait", "hold", "rest"}:
                    ability_tokens.append(tokens[index])
                    index += 1
                ability_name = " ".join(ability_tokens)
                ability = self._resolve_ability(ability_name)
                if ability is None:
                    print("Unable to find that ability in your loadout.")
                    return None
                command.ability = ability
                continue
            if token in {"wait", "hold", "rest"}:
                command.wait = True
                command.move = vec_zero()
                index += 1
                continue
            print("Unknown action. Type 'help' for the list of commands.")
            return None
        return command

    def _parse_direction(self, token: str) -> Optional[tuple[float, float]]:
        return DIRECTION_MAP.get(token.lower())

    def _resolve_ability(self, phrase: str):
        if not self.match or not self.player:
            return None
        slots = self.player.loadout.slots()
        lowered = phrase.strip().lower()
        if not lowered:
            return None
        if lowered in slots:
            return slots[lowered]
        for ability in slots.values():
            if ability.name.lower() == lowered:
                return ability
        return None

    # ------------------------------------------------------------------
    # Presentation helpers
    # ------------------------------------------------------------------
    def _print_intro(self, element: Element) -> None:
        print(
            textwrap.dedent(
                f"""
                Welcome to the Elementals skirmish prototype!
                You channel the power of {element.value}. Face the guardian to test your abilities.
                Available commands:
                  - move <direction> (e.g. move north)
                  - cast <slot|ability name> (e.g. cast primary, cast bolt)
                  - wait (skip movement for a moment to recover)
                  - abilities (list your current loadout and cooldowns)
                  - status (show combatant health and effects)
                  - help (repeat this message)
                  - quit (leave the match)
                Combine actions in one line, such as 'cast primary move north'.
                """
            ).strip()
        )

    def _print_help(self) -> None:
        print(
            "Commands: move <dir>, cast <slot|name>, wait, abilities, status, help, quit."
        )

    def _display_status(self, compact: bool = False) -> None:
        if not self.match or not self.player or not self.opponent:
            return
        player = self.player
        opponent = self.opponent
        player_line = (
            f"You [{player.element_affinity}] - HP {player.stats.health:.0f}/{player.stats.max_health:.0f} "
            f"ST {player.stats.stamina:.0f}/{player.stats.max_stamina:.0f} "
            f"HY {player.stats.hydration:.0f}/{player.stats.max_hydration:.0f}"
        )
        opponent_line = (
            f"{opponent.name} [{opponent.element_affinity}] - HP {opponent.stats.health:.0f}/{opponent.stats.max_health:.0f} "
            f"ST {opponent.stats.stamina:.0f}/{opponent.stats.max_stamina:.0f} "
            f"HY {opponent.stats.hydration:.0f}/{opponent.stats.max_hydration:.0f}"
        )
        print(player_line)
        if not compact:
            print("  Effects:", self._format_effects(player))
        print(opponent_line)
        if not compact:
            print(f"  {opponent.name} effects:", self._format_effects(opponent))

    def _show_abilities(self) -> None:
        if not self.match or not self.player:
            return
        print("Active loadout:")
        for slot, ability in self.player.loadout.slots().items():
            behavior = self.match.behavior_for(ability)
            cooldown = self.match.cooldown_for(self.player, ability)
            ready_text = "READY" if cooldown <= 0.0 else f"CD {cooldown:.1f}s"
            print(
                f"  {slot.title():<9} {ability.name:<20} | {behavior.description} | Cost ST {behavior.stamina_cost:.0f} HY {behavior.hydration_cost:.0f} | {ready_text}"
            )

    def _format_effects(self, actor: Player) -> str:
        if not actor.active_effects:
            return "none"
        parts = [f"{name} {duration:.1f}s" for name, duration in actor.active_effects.items()]
        return ", ".join(parts)

    def _prompt_for_element(self) -> Element:
        options = {"earth": Element.EARTH, "water": Element.WATER}
        prompt = "Choose your starting zone (earth/water): "
        while True:
            choice = input(prompt).strip().lower()
            if choice in options:
                return options[choice]
            print("Please choose either 'earth' or 'water'.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Elementals single-player playtest")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run an automated battle showcasing the systems instead of the interactive mode.",
    )
    parser.add_argument(
        "--turns", type=int, default=10, help="Number of turns to simulate during demo mode."
    )
    args = parser.parse_args()

    session = SinglePlayerSession()
    if args.demo:
        session.run_demo(turns=args.turns)
    else:
        session.interactive()


if __name__ == "__main__":
    main()
