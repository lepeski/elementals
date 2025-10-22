# Elementals – Real-Time Prototype

This repository now contains a playable, physics-driven top-down arena inspired by the elemental campaign layout. You can pilot a guardian through successive zones, unlock combo abilities, and duel an AI opponent with tactile projectiles, knockbacks, shields, and crowd-control effects.

## Requirements

- Python 3.10+
- [`pygame`](https://www.pygame.org/docs/) (`python -m pip install pygame`)

The prototype renders in a desktop window and requires keyboard and mouse input.

## Running the Game

```bash
python main.py
```

1. Use the number keys shown on the menu (`1`, `2`, …) to pick the next zone. You always start with **Earth** or **Water**.
2. During combat:
   - **W/A/S/D** (or arrow keys) move your avatar.
   - **Mouse** aims your abilities; the guardian will face your cursor.
   - **Keys 1–6** trigger the abilities listed on the HUD. Combo unlocks appear after clearing adjacent zones.
   - Watch your health and energy bars in the bottom-left HUD, and look for status icons or floating numbers to understand incoming effects.
3. Win the duel to unlock the next pair of adjacent zones, following the layout guidelines. Clearing compatible pairs grants combo abilities such as Roots (Nature), Volcanic Geyser (Magma), and Freeze (Ice).

If you lose, press **Enter** to return to the zone menu and try again.

## Project Structure

- `elementals/elements.py` – campaign graph, combo lookup, and progression helpers.
- `elementals/abilities.py` – ability specifications and their in-game behaviors (projectiles, AoE bursts, buffs, and crowd-control).
- `elementals/entities.py` – physics primitives, actors, status effects, and projectile representations.
- `elementals/game.py` – Pygame loop, AI control, rendering, HUD, and arena management.
- `elementals/physics.py` – vector math and collision helpers.
- `main.py` – launches the real-time prototype.

## Next Steps

- Expand arena variety with new props, hazards, and cover layouts.
- Add audio cues and particle systems for richer spell feedback.
- Introduce additional guardian archetypes so each zone feels distinct.
- Layer networking on top of the current systems to enable co-op or competitive multiplayer once the core combat loop feels solid.
