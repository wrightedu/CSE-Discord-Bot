# Architecture

## Root Directory

### `bot.py`

The core file. Used to initialize the bot. Provides on-ready functionality and error handling.

### `utils.py`

Contains a bunch of nice utilities. Most files

```py
from utils import *
```

### `diceParser.py`

Source: [Alan Fleming's dice parser](https://github.com/AlanCFleming/DiceParser)

Used for a -roll command to parse input and run dice roll calculations

## Cogs

### `AdminCommands.py`

Commands to be used exclusively by admins for server moderation

### `CogManagement.py`

Cog used to load, unload, and reload other cogs. Cannot be unloaded

### `Listeners.py`

Any generic event handles or listeners that don't belong in any other cog

### `ServerManagement.py`

Used to create/destroy class channels/role menus

### `StudentCommands.py`

Commands to be used by anyone in a server. Mostly fun toys, but some useful commands
