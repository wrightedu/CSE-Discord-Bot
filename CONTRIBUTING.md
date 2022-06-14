# Contributing

## Background Knowledge

Read through the [Architecture Guide](ARCHITECTURE.md) before making any contributions.

## Standards

All code should comply with a modified version of the [PEP-8 standard](https://pep8.org/), excluding line lengths. Keep line lengths to around 100 characters. No hard limit.

All functions and methods should have docstrings following the [Google docstring standard](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html)

## Workspace Setup

### Dependencies

This Discord bot requires the dependencies listed in [REQUIREMENTS.txt](REQUIREMENTS.txt). Any time a new dependency is added or an old one is updated, REQUIREMENTS.txt should be updated accordingly.

You can `pip install -r REQUIREMENTS.txt` to install all dependencies in one command. We recommend using an environment, either a Python built-in environment or [Anaconda](https://www.anaconda.com/products/individual).

### Discord Bot Authentication

Create a file `.env` in the same directory as `bot.py` with the following contents:

```plaintext
# .env
DISCORD_TOKEN=INSERT_BOT_TOKEN_HERE
```

If you do not have a Discord token, you can create one at the [developer page](https://discord.com/developers/applications/). Do NOT regenerate the token. This will revoke permissions for all instances of the bot.

**WARNING:** do not commit and/or push the .env file to a remote repository. Doing so will allow anyone to add custom commands or event handles to an already running instance of the bot.

## Workflow

1. [Fork](https://docs.github.com/en/get-started/quickstart/fork-a-repo) this repository
2. [Create a branch](https://docs.github.com/en/github/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-and-deleting-branches-within-your-repository) off the development branch for the edits you wish to make
3. Make a [pull request](https://docs.github.com/en/github/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request) in this repository from your branch to the development branch of this repository.
