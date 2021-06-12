# FACEIT-Cup-Bot-V2
[![Deploy bot](https://github.com/rush2sk8/FACEIT-Cup-Bot-V2/actions/workflows/main.yml/badge.svg)](https://github.com/rush2sk8/FACEIT-Cup-Bot-V2/actions/workflows/main.yml)
A rewrite of Faceit Cup bot V1
Discord bot to ask people to play in a faceit cup

## Installation

`pip install -r requirements.txt`

## Necessary files

* `.env` with the following fields
  - `DISCORD_TOKEN` Discord api token
  - `CUP_ROLE` Discord cup role id
  - `CUP_CHANNEL` Discord cup channel name
  - `CUP_CHANNEL_ID` Channel to look in
  - `GUILD_ID` ID of the guild to run it in
  - `ADMIN_USER_ID` ID admin user

## Launching the bot
Launch with [`pm2`](https://www.npmjs.com/package/pm2)

`pm2 start bot.py`

## Commands 
Base features:

`!team` - List the current team

`!cup` - Start a single FaceiT Cup

`!endcup` - Ends the current cup

`!ping` - Pings the team. Cooldown of 30seconds
