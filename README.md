# CSE-Discord-Bot

Discord bot for the WSU CSE-EE Discord server

## Usage

### Authentication

Create a file `.env` in the same directory as `bot.py` with the following contents:

```
# .env
DISCORD_TOKEN=INSERT_BOT_TOKEN_HERE
```

The token can be found at the [developer page](https://discord.com/developers/applications/) Under the `WSU CSE` project > Bot. Do NOT regenerate the token. This will revoke permissions for all instances of the bot.

Since adding multi-server support, the guild ID is no longer used. However, it is still nice to keep to have a pointer to the [CSE-EE Department Server](https://discord.gg/ks3pV7G). You can get the guild ID by going to the [server on Discord](https://discord.gg/ks3pV7G). `DISCORD_GUILD` is similarly unnecessary, but useful

**WARNING:** do not commit and/or push the .env file to a remote repository. Doing so will allow anyone to add custom commands or event handles to an already running instance of the bot.

### Initializing

Once you've got the `.env` file made and in the same directory as `bot.py`, starting up the bot is as simple as running `python3 bot.py`. Startup should take around 30-60 seconds.
