import os
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv
from PIL import Image

load_dotenv(dotenv_path=Path('.')/'.env')

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
CUP_ROLE = os.getenv('CUP_ROLE')
CUP_CHANNEL = os.getenv('CUP_CHANNEL')
CUP_CHANNEL_ID = os.getenv('CUP_CHANNEL_ID')
GUILD_ID = os.getenv('GUILD_ID')
ADMIN_USER_ID = os.getenv('ADMIN_USER_ID')
NUM_PLAYERS = 6

curr_cup = {
    "message": None,
    "users": []
}

bot = commands.Bot(command_prefix='!', intents= discord.Intents.default())

def has_cup():
    """See if there is a current message"""
    return curr_cup["message"] is not None

def is_cup_channel(message):
    """Returns true if the message is from CUP_CHANNEL"""
    return message.channel.name == CUP_CHANNEL

async def get_reactions_from_message(message):
    """Fetch all non-bot users from the message reaction"""
    users = set()
    for reaction in message.reactions:
        async for user in reaction.users():
            if not user.bot:
                users.add(user)
    return users

async def ping_players(message):
    """Ping cup players"""
    if not has_cup():
        await message.channel.send('There currently no cup in progress')
    else:
        to_send = f'You have been pinged by {message.author.mention}:\n'

        for user in curr_cup['users']:
            to_send += f'{user.mention} \n'

        await message.channel.send(to_send)

async def get_user_msg_reaction_from_payload(payload):
    """Given a payload it will fetch the user, message, and reaction"""
    user = await bot.fetch_user(payload.user_id)
    message = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
    reaction = message.reactions
    return (user, message, reaction)

async def send_cup_message(message):
    """Sends the team message in an embed"""
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
    player3 = Image.open('player2.png')
    player4 = Image.open('player3.png')
    player5 = Image.open('player4.png')

    image_size = player1.size

    # Create blank image
    new = Image.new('RGB', (3*image_size[0],2*image_size[1]), (0,0,0))

    # Paste in players
    new.paste(player1, (0,0))
    new.paste(player2, (image_size[0],0))
    new.paste(player3, (image_size[0]*2,0))
    new.paste(player4, (image_size[0] - (int(image_size[0]/2)), image_size[0]))
    new.paste(player5, (image_size[0] + (int(image_size[0]/2)), image_size[0]))

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

@bot.event
async def on_command_error(ctx, error):
    """Handle cooldown error"""
    if isinstance(error, commands.CommandOnCooldown):
        msg = '**Still on cooldown**, please try again in {:.2f}s'.format(error.retry_after)
        await ctx.send(msg)

@bot.event
async def on_ready():
    """Event when the bot logs in"""
    await bot.change_presence(activity=discord.Streaming(name="by rush2sk8", url='https://www.twitch.tv/rush2sk8'))
    print('We have logged in as {0.user}'.format(bot))

@bot.command()
async def cup(ctx):
    message = ctx.message

    if is_cup_channel(message):
        if not has_cup():
            curr_cup["message"] = await ctx.send(f'<@&{CUP_ROLE}> Please react to this if you want to play in the cup.')
            await curr_cup["message"].add_reaction('✋')
        else:
            await ctx.send('There is a cup in progress')

@bot.command()
@commands.cooldown(1, 30, commands.BucketType.channel)
async def ping(ctx):
    if is_cup_channel(ctx.message) and has_cup():
        if len(curr_cup['users']) == NUM_PLAYERS:
            await ping_players(ctx.message)

@bot.command()
async def team(ctx):
    if is_cup_channel(ctx.message) and has_cup():
        if len(curr_cup['users']) == NUM_PLAYERS:
            await send_cup_message(ctx.message)

@bot.command()
async def loadcup(ctx, arg):
    message = ctx.message

    if is_cup_channel(message) and str(message.author.id) == ADMIN_USER_ID:
        if len(message.content.split()) == 1:
                return

        cup_id = message.content.split()[1]
        loaded_message = await message.channel.fetch_message(cup_id)

        # In case I load a cup while one is running
        if has_cup():
            await message.author.send('Cannot load cup. There is a cup in progress')
        else:
            # Otherwise load the cup
            curr_cup['message'] = loaded_message

            users = await get_reactions_from_message(loaded_message)

            curr_cup['users'] = list(users)
            await message.author.send("Loaded Cup!")

        await message.delete()

@bot.command()
async def endcup(ctx):
    if is_cup_channel(ctx.message) and str(ctx.message.author.id) == ADMIN_USER_ID:
        curr_cup['message'] = None
        curr_cup['users'] = []
        await ctx.send("The cup has now ended")

@bot.event
async def on_raw_reaction_add(payload):
    """Raw event for reactions"""
    user, message, reaction = await get_user_msg_reaction_from_payload(payload)

    # Return if the reaction is not part of the guild, from the curr cup message, or a bot reaction
    if user.bot or \
        not (str(payload.guild_id) == GUILD_ID) or \
        (has_cup() and not (payload.message_id == curr_cup['message'].id)):
        return

    # If we have a current running cup and the reaction is to the current message
    if has_cup() and payload.message_id == curr_cup['message'].id:

        # Remove emoji if they add another one or have more than normal
        if payload.emoji.name != '✋':
            await message.remove_reaction(payload.emoji, user)
            return

        # if the emoji is a hand and they add more than the number of the players then remove it
        if payload.emoji.name == '✋' and reaction[0].count > NUM_PLAYERS:
            await message.remove_reaction(payload.emoji, user)
            return

        curr_cup['users'].append(user)

        # If the number of reactions is enough to start a cup
        if reaction[0].count == NUM_PLAYERS:
            await send_cup_message(message)

@bot.event
async def on_raw_reaction_remove(payload):
    """Raw event when someone removes a reaction from a message"""
    user, _, _ = await get_user_msg_reaction_from_payload(payload)

    if user.bot or \
        not (str(payload.guild_id) == GUILD_ID) or \
        (has_cup() and not (payload.message_id == curr_cup['message'].id)) or \
        payload.emoji.name != '✋':
        return

    # If there is a cup running and the message is the same
    if has_cup() and payload.message_id == curr_cup['message'].id:

        # Find and remove the user from the current cup.
        for user in curr_cup['users']:
            if user.id == payload.user_id:
                curr_cup['users'].remove(user)

bot.run(DISCORD_TOKEN)
