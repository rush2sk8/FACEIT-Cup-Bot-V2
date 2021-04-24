import os
from pathlib import Path

import discord
from dotenv import load_dotenv
from PIL import Image

load_dotenv(dotenv_path=Path('.')/'.env')

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
CUP_ROLE = os.getenv('CUP_ROLE')
CUP_CHANNEL = os.getenv('CUP_CHANNEL')
CUP_CHANNEL_ID = os.getenv('CUP_CHANNEL_ID')
GUILD_ID = os.getenv('GUILD_ID')
NUM_PLAYERS = 3

curr_cup = {
    "message": None,
    "users": []
}

client = discord.Client()

async def get_reactions_from_message(message):
    """Fetch all non-bot users from the message reaction"""
    users = set()
    for reaction in message.reactions:
        async for user in reaction.users():
            if not user.bot:
                users.add(user)
    return users

def has_message():
    """See if there is a current message"""
    return curr_cup["message"] is not None

async def get_user_msg_reaction_from_payload(payload):
    """Given a payload it will fetch the user, message, and reaction"""
    user = await client.fetch_user(payload.user_id)
    message = await client.get_channel(payload.channel_id).fetch_message(payload.message_id)
    reaction = message.reactions
    return (user, message, reaction)

def is_cup_channel(message):
    """Returns true if the message is from CUP_CHANNEL"""
    return message.channel.name == CUP_CHANNEL

async def send_cup_message(message):
    users = list(await get_reactions_from_message(message))

    embed = discord.Embed(title="FACEIT Cup Team", description=f"The [team]({message.jump_url}) will consist of:", color=0xffbb00)

    for i, user in enumerate(users):
        # Add user to embed message
        embed.add_field(name=f'Player {i+1}', value=user.name, inline=False)

        # Download player avatars
        await user.avatar_url.save(f'player{i}.png')


    # Create a special tiled image
    player1 = Image.open('player0.png')
    player2 = Image.open('player1.png')
    # player3 = Image.open('player2.png')
    # player4 = Image.open('player3.png')
    # player5 = Image.open('player4.png')

    image_size = player1.size

    # Create blank image
    new = Image.new('RGB', (3*image_size[0],2*image_size[1]), (0,0,0))

    # Paste in players
    new.paste(player1, (0,0))
    new.paste(player2, (image_size[0],0))
    # new.paste(player3, (image_size[0]*2,0))
    # new.paste(player4, (image_size[0] - (int(image_size[0]/2)), image_size[0]))
    # new.paste(player5, (image_size[0] + (int(image_size[0]/2)), image_size[0]))

    # Save image
    new.save('gallery.png', 'PNG')

    # Embed the new image
    embed_image = discord.File('gallery.png', filename='image.png')
    embed.set_thumbnail(url='attachment://image.png')
    embed.set_footer(text="by rush2sk8")

    # Send the message
    await message.channel.send(file=embed_image, embed=embed)

    # We don't care if they're there or not
    try:
        os.remove('gallery.png')

        # Delete the files
        for i in range(0, NUM_PLAYERS - 1):
            os.remove(f'player{i}.png')
    except FileNotFoundError:
        pass

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Streaming(name="by rush2sk8", url='https://www.twitch.tv/rush2sk8'))
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if is_cup_channel(message):

        # Start a cup
        if message.content.startswith('!cup'):
            if not has_message():
                curr_cup["message"] = await message.channel.send(f'<@&{CUP_ROLE}> Please react to this if you want to play in the cup.')
                await curr_cup["message"].add_reaction('✋')
            else:
                await message.channel.send('There is a cup in progress')

        # Command for me to load an old cup
        elif message.content.startswith('!loadcup') and message.author.id == 142457707289378816:
            cup_id = message.content.split()[1]
            loaded_message = await message.channel.fetch_message(cup_id)

            # In case I load a cup while one is running
            if has_message():
                await message.channel.send('Cannot load cup. There is a currently running cup')
            else:
                # Otherwise load the cup
                curr_cup['message'] = loaded_message

                users = await get_reactions_from_message(loaded_message)

                curr_cup['users'] = list(users)

        elif message.content.startswith('!echo'):
            await message.channel.send(message.content)

        elif message.content.startswith('!endcup') and message.author.id == 142457707289378816:
            curr_cup['message'] = None
            curr_cup['users'] = []

    print(message.content)
    print(curr_cup)


@client.event
async def on_raw_reaction_add(payload):
    user, message, reaction = await get_user_msg_reaction_from_payload(payload)

    # Return if the reaction is not part of the guild, from the curr cup message, or a bot reaction
    if user.bot or \
        not (str(payload.guild_id) == GUILD_ID) or \
        (has_message() and not (payload.message_id == curr_cup['message'].id)):
        return

    # If we have a current running cup and the reaction is to the current message
    if has_message() and payload.message_id == curr_cup['message'].id:

        # Remove emoji if they add another one or have more than normal
        if payload.emoji.name != '✋':
            await message.remove_reaction(payload.emoji, user)
            return

        # if the emoji is a hand and they add more than the number of the players then remove it
        if payload.emoji.name == '✋' and reaction[0].count > NUM_PLAYERS:
            await message.remove_reaction(payload.emoji, user)
            return

        # If the number of reactions is enough to start a cup
        if reaction[0].count == NUM_PLAYERS:
            await send_cup_message(message)

@client.event
async def on_raw_reaction_remove(payload):
    user, _, _ = await get_user_msg_reaction_from_payload(payload)

    if user.bot or \
        not (str(payload.guild_id) == GUILD_ID) or \
        (has_message() and not (payload.message_id == curr_cup['message'].id)) or \
        payload.emoji.name != '✋':
        return

    # If there is a cup running and the message is the same
    if has_message() and payload.message_id == curr_cup['message'].id:

        # Find and remove the user from the current cup.
        for user in curr_cup['users']:
            if user.id == payload.user_id:
                curr_cup['users'].remove(user)

client.run(DISCORD_TOKEN)
