# Architecture

## Root Directory

### `bot.py`

The core file. Used to initialize the bot. Provides on-ready functionality and error handling.

### `diceParser.py`

Source: [Alan Fleming's dice parser](https://github.com/AlanCFleming/DiceParser)

Used for a -roll command to parse input and run dice roll calculations.

## Utils

### `WSU_mossScript.py`

Functionality for unzipping and checking code for plagarism with [Moss](https://theory.stanford.edu/~aiken/moss/).

### `WSU_mossnet.pl`

Pearl implemention for uploading file(s) to MOSS for plagarism checking.

### `rolebutton.py`

Callback for role buttons to properly handle role add and removal.

### `utils.py`

Contains numerous functions and methods for utility purposes, including logging and Discord management.

## Cogs

### `AdminCommands.py`

Cog that contains commands to be used exclusively by admins for server moderation.

### `Checkin.py`

Cog used to manage timing for CSE Dev Team members. Tracks time in and time out to calculate total hours spent.

### `CogManagement.py`

Cog used to load, unload, and reload other cogs. Cannot be unloaded

### `CourseManagement.py`

Cog used to manage courses within the CSE-EE Discord, including the ability to pop and push classes for a particular semester.

### `Faq.py`

Cog to read messages sent by users with a question mark and respond with a prompt if the "question" is within the `assets/FAQ/channels.txt` folder.

### `Gourmet.py`

Cog to select and manage potentional resturants to eat at in the greater Fairborn area.

### `Listeners.py`

Cog that contains generic event handlers and listeners that don't fit elsewhere.

### `MOSS.py`

Cog that allows Faculty, Staff, and Teaching Assistants to check a ZIP of student projects for potentional plagarism.

### `StudentCommands.py`

Cog that contains commands to be used by anyone. Mostly fun toys, but some useful commands