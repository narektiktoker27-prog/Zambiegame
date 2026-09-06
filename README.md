# 🧟 Վարակված Քաղաքը — Telegram Multiplayer

## Features

- 2–100 real Telegram players
- No single-player start
- Creator-only `/deletegame`
- Confirmation before deleting a game
- Per-group RAM game state
- NPC zombie AI with states
- Human / infected-player gameplay
- Infection and player-controlled zombie actions
- Random map objectives
- Locked areas and keys
- Search, inventory, bullets, hiding, fleeing and first aid
- Random horror events
- Dynamic zombie pressure
- Special medicine + special weapon + healing bullet finale
- Cinematic victory/defeat sequence
- Railway-ready
- No external database

## Environment

Set:

`BOT_TOKEN=<your Telegram bot token>`

Never put the token in source code.

## Run

`python main.py`

## Telegram

Add the bot to a group, then:

`/startgame`

The Creator can start only after at least 2 players have joined.

`/game` shows the private game panel.

`/deletegame` can only be used by the Creator and requires confirmation.

## RAM-only state

Active games are stored in Python memory. A Railway restart/redeploy clears active games by design.

## Important Telegram limitation

A bot can only send a user a private message if that user has previously opened/started the bot or otherwise made a private interaction possible. The game detects private-message failures instead of silently pretending the message was delivered.
