# CSE-Discord-Bot

Discord bot for the WSU CSE-EE Discord server

## Usage

### Authentication

Create a file `.env` in the same directory as `bot.py` with the following contents:

```plaintext
# .env
DISCORD_TOKEN=INSERT_BOT_TOKEN_HERE
```

The token can be found at the [developer page](https://discord.com/developers/applications/) Under the `WSU CSE` project > Bot. Do NOT regenerate the token. This will revoke permissions for all instances of the bot.

Since adding multi-server support, the guild ID is no longer used. However, it is still nice to keep to have a pointer to the [CSE-EE Department Server](https://discord.gg/ks3pV7G). You can get the guild ID by going to the [server on Discord](https://discord.gg/ks3pV7G). `DISCORD_GUILD` is similarly unnecessary, but useful

**WARNING:** do not commit and/or push the .env file to a remote repository. Doing so will allow anyone to add custom commands or event handles to an already running instance of the bot.

### Initializing

Once you've got the `.env` file made and in the same directory as `bot.py`, starting up the bot is as simple as running `python3 bot.py`. Startup should take around 30-150 seconds.

## Code

### bot.py

This is the main script of the bot. It initializes the bot object and loads the cogs.

#### Global Variables

* `client` - the bot object. Gets passed to cogs
* `start_time` - Timestamp of the time the program starts to run (Unix standard time). Used to calculate startup duration
* `TOKEN` - Discord bot token loaded from .env (originally collected from the Discord developer page)

#### Functions

* `on_ready()` - Runs immediately after the bot is run (in main function). Handles startup procedures such as loading cogs and building server role menus.
* `on_command_error()` - Function to be run when a command errors. Sends and logs error message.
* `main` - Runs the bot initialized earlier

### Cogs

These are modules/extensions to the bot to add functionality that can be loaded/unloaded at will.

#### AdminCommands.py

This cog contains commands that should only admins should be permitted to run. These are separate from the `ServerManagement` in that the `ServerManagement` cog soley deals with creating/building the server's class channels. This cog contains the following commands:

##### downloadcorgis

Downloads a set of images of corgis from Bing images (the Google API sucks). These are cached locally for the `corgme` command.

Usage:
`-downloadcorgis` downloads 1000 images
`-downloadcorgis AMOUNT` downloads AMOUNT corgis

##### clear

Deletes the latest PARAMETER messages from the channel in which the command was run.

Usage:
`-clear AMOUNT` deletes the latest AMOUNT messages from the channel in which the command was run. Requires confirmation if deleting 10 or more messages.
`-clear all` deletes all messages in the channel in which the command was run. Requires confirmation.

##### status

Changes the status message of the bot.

Usage:
`-status STATUS MESSAGE` combines all arguments into one string and sets it as the status message

##### clearrole

Removes the mentioned role from all users who have it. Good for clearing out Dr. Cheatham's TAs.

Usage:
`-clearrole @ROLE` removes the role @ROLE from everyone who has it. Will print out who the role was taken from, or how many members it was taken from if the list is long.

##### restart

Fully restarts the bot. Requires confirmation

Usage:
`-restart`

##### stop

Shuts down the bot. Requires confirmation

Usage:
`-shutdown`
`-poweroff`
`-exit`

#### CogManagement

The CogManagement cog provides commands to manage other cogs. Useful for pushing updates to cogs without a full bot reload. Provides the following commands:

##### reload

Reloads the specified cog (use after making changes to a cog file).

Usage:
`-reload COGNAME`

##### unload

Unloads the specified cog. Useful for disabling cogs containing buggy commands.

Usage:
`-unload COGNAME`

#### load

Loads the specified cog. The cog can be in an unloaded state, or be a brand new cog never loaded before.

Usage:
`-load COGNAME`

#### ServerManagement

This is easily the most dangerous cog, as it is capable of deleting every class channel. It is used for reconfiguring the server for a new semester, removing old class channels and adding new ones in. It provides 3 commands and 2 event handles.

#### buildserver

Command to delete old class channels, then create new ones and generates the reaction role menus. First time run requires a JSON to be uploaded (see template_reaction_roles.json). The JSON is better described by reading the file rather than describing structure, though it should be noted that each of the outermost sections will be sent in a new message. After sending the JSON, it will cache it locally (saves to a different file for each guild) and will not need to be resent unless changes need to be made to the JSON, at which point a new one will need to be uploaded.

Usage:
`-buildserver` [Optionally attach role menu JSON] Requires confirmation

#### destroyserver

This deletes all roles and class channels/categories off a regex.

Usage:
`-destroyserver` Requires confirmation

#### rolemenu

Regenerates the reaction roles menus. Does NOT affect the class channels.

Usage:
`-rolemenu` [Optionally attach role menu JSON]

#### [Event] on_raw_reaction_add

Handle for adding a reaction. Any time anyone reacts to any message, this function is run. It checks a list of reaction role messages ids (dictionary keyed by guild id) and if the reaction was on one of those messages, processes what role is associated with that reaction, and assigns it to the user who reacted.

#### [Event] on_raw_reaction_remove

Handle for adding a reaction. Any time anyone removes a reaction from any message, this function is run. It checks a list of reaction role messages ids (dictionary keyed by guild id) and if the reaction was on one of those messages, processes what role is associated with that reaction, and removes it from the user who reacted.

#### StudentCommands

This holds a set of commands anyone can run.

##### corgme

Shows a random corgi picture! Or, if you specify a number, a specific corgi picture. `-downloadcorgis` required beforehand

Usage:
`-corgme` sends random corgi image
`-corgme NUMBER` sends the corgi image numbered NUMBER
`-corgmi` sends random corgi image
`-corgmi NUMBER` sends the corgi image numbered NUMBER

##### helloworld

Prints code for hello world in specified or random language

Usage:
`-helloworld` prints hello world in random language
`-helloworld random` prints hello world in random language
`-helloworld ls` list the available languages
`-helloworld LANGUAGE` prints hello world in LANGUAGE

##### poll

Sends a question and answer set with associated reactions (similar to reaction roles)

Usage:
`-poll "QUESTION" "ANSWER_1" "ANSWER_2"` quotes are required. Needs between 2 and 10 answers

##### roll

Dice parser courtesy of Alan Fleming. See [his GitHub repo](https://github.com/AlanCFleming/DiceParser) for more information

Usage:
`-roll STRING` passes STRING into the dice parser. Example string: `1d6`

##### support

Planned command to ping CSE Support for help and send them an email. Currently just prints out a message to contact us

Usage:
`-support QUESTION`

##### ping

Sends the server's latency to Discord's servers

Usage:
`-ping`
