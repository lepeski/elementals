# Elementals Prototype

This repository contains a top-down, physics-driven magic battle prototype inspired by the provided elemental layout. The current milestone makes the game playable in a single-player skirmish so the combat systems can be playtested before multiplayer networking is introduced.

## Features

- **Element Graph** – `elementals/elements.py` codifies the zone progression, unlock rules, and combined elements between adjacent regions.
- **Ability Catalog** – `elementals/abilities.py` captures each elemental ability with descriptions, design tags, and metadata for the combat sandbox.
- **Campaign Progression** – `elementals/zones.py` enforces the two starting zones (Earth and Water) and unlocks adjacent regions and combo abilities after completion.
- **Combat Sandbox** – `elementals/combat.py` defines ability behaviors, status effects, and a lightweight AI to drive playtest duels.
- **Entity & Physics Layer** – `elementals/entities.py` and `elementals/physics.py` provide lightweight components for top-down movement, stats, resource management, and collision handling.
- **Game State Container** – `elementals/game_state.py` glues everything together, allowing quick iteration on campaign unlocks and arena simulations.
- **Playtest Entry Point** – `main.py` launches an interactive console skirmish (or an automated demo) so designers can exercise the systems.

## Running the Playtest

```bash
python main.py
```

Follow the on-screen instructions to choose a starting element (Earth or Water), then issue commands such as `move north` or `cast primary` to battle the AI-controlled guardian. You can combine actions in a single line (e.g. `cast primary move east`).

To watch the systems play out automatically, run:

```bash
python main.py --demo --turns 12
```

## Next Steps

- Add additional encounter types, props, and environmental hazards to broaden playtesting.
- Build graphical input handling and rendering using a 2D framework (e.g., Pygame, Godot, or a custom engine).
- Introduce persistence for save files and expand the AI roster to cover each elemental path.
- Layer in multiplayer via an authoritative server model once single-player combat is polished.
