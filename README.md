# FACEIT-Cup-Bot-V2
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

## Launching the bot
Launch with [`pm2`](https://www.npmjs.com/package/pm2)

`pm2 start bot.py`
