# MTA1Mzc2Nzk2MjAzODkxNTE3Mg.GOc00k.qjHaAOdp8gg8JQWZ76nBM19S31l6OX6UKx6dao
import requests
import re
from PIL import Image
from PIL import ImageDraw
import time
import json
import discord
from discord.ext import commands, tasks

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
prefix = '!'
client = commands.Bot(command_prefix=prefix, case_insensitive=True, intents=intents)
try:
    with open('team_stats.txt', 'r') as newf:
        playerdata = json.loads(newf.read())
except json.decoder.JSONDecodeError:
    playerdata = {}

types_of_stats = ['pvp', 'misc', 'resources']


def change_nickname(original_name, new_name):
    try:
        playerdata[original_name]['nickname'] = new_name
        with open('team_stats.txt', 'w') as newf:
            newf.write(json.dumps(playerdata, indent=4))
        return True
    except KeyError:
        return False


def get_profile_pictures(players):
    for player in players:
        steam_page = requests.get(f'https://steamcommunity.com/profiles/{playerdata[player]["player_id"]}')
        avatar_link = steam_page.text.split('<div class="playerAvatarAutoSizeInner">')[1]
        img_data = requests.get(re.search("(?P<url>https?://[^\s]+)", avatar_link).group("url")[:-2]).content
        with open(f'{player}av.png', 'wb') as handler:
            handler.write(img_data)


def draw_picture(players):
    players = sorted(players, key=lambda e: players[e]['pvp']['pvp_player_kills_total'], reverse=True)
    height = len(players) * 100
    new_im = Image.new('RGBA', (400, height))
    im = Image.open("first.png").convert('RGBA')
    paste_location = 0
    for player in players:
        im1 = Image.open(f"{player}av.png").convert('RGBA')
        im1.thumbnail((70, 70))
        im2 = Image.open("player_template.png").convert('RGBA')
        im.paste(im1, (10, 18), im1)
        im.paste(im2, (0, 0), im2)
        ImageDraw.Draw(im).text((10, 5), playerdata[player]['nickname'], fill=(0, 0, 0))
        ImageDraw.Draw(im).text((150, 10), str(playerdata[player]['pvp']['pvp_player_kills_total']), fill=(0, 0, 0))
        ImageDraw.Draw(im).text((267, 10), str(playerdata[player]['pvp']['pvp_player_deaths_total']), fill=(0, 0, 0))
        ImageDraw.Draw(im).text((370, 10), str(playerdata[player]['pvp']['kdr']), fill=(0, 0, 0))
        ImageDraw.Draw(im).text((158, 40), str(playerdata[player]['resources']['farming_resource_stone_harvested']),
                                fill=(0, 0, 0))
        ImageDraw.Draw(im).text((220, 40), str(playerdata[player]['resources']['farming_resource_stone_harvested']),
                                fill=(0, 0, 0))
        ImageDraw.Draw(im).text((275, 40), str(playerdata[player]['resources']['farming_resource_wood_harvested']),
                                fill=(0, 0, 0))
        ImageDraw.Draw(im).text((320, 40), str(playerdata[player]['resources']['farming_resource_wood_harvested']),
                                fill=(0, 0, 0))
        ImageDraw.Draw(im).text((170, 80), str(round(playerdata[player]['misc']['player_time_played'] / 60, 2)),
                                fill=(0, 0, 0))
        ImageDraw.Draw(im).text((350, 80), str(round(playerdata[player]['pvp']['pvp_player_kills_total'] / (
                playerdata[player]['misc']['player_time_played'] / 60), 2)), fill=(0, 0, 0))
        new_im.paste(im, (0, paste_location), im)
        paste_location += 100
    # new_im.show()
    new_im.save('statistics.png')


def update_stats(players):
    if len(players) >= 1:
        for player in players:
            for stat in types_of_stats:
                playerdata[player][stat] = requests.get(
                    f'https://api.rustoria.co/statistics/leaderboards/2x_mondays_us/{stat}?from=0&sortBy=total&orderBy=asc&username={player}').json()[
                    'leaderboard'][0]['data']
                time.sleep(1)


def add_to_data(players):
    for player in players:
        if len(requests.get(
                f'https://api.rustoria.co/statistics/leaderboards/2x_mondays_us/pvp?from=0&sortBy=total&orderBy=asc&username={player}').json()[
                   'leaderboard']) == 0:
            continue
        playerdata[player] = {}
        playerdata[player]['nickname'] = player
        playerdata[player]['player_id'] = requests.get(
            f'https://api.rustoria.co/statistics/leaderboards/2x_mondays_us/pvp?from=0&sortBy=total&orderBy=asc&username={player}').json()[
            'leaderboard'][0]["userId"]
        time.sleep(1)
        for stat in types_of_stats:
            playerdata[player][stat] = requests.get(
                f'https://api.rustoria.co/statistics/leaderboards/2x_mondays_us/{stat}?from=0&sortBy=total&orderBy=asc&username={player}').json()[
                'leaderboard'][0]['data']
            time.sleep(1)
        get_profile_pictures([player])
    with open('team_stats.txt', 'w') as newf:
        newf.write(json.dumps(playerdata, indent=4))


@client.event
async def on_ready():
    print('we ready')


@tasks.loop(minutes=4)
async def update_team():
    update_stats(playerdata)


@client.command()
async def add(ctx, *players):
    await ctx.channel.send(f'Adding {" ".join(players)}')
    add_to_data([" ".join(players)])


@client.command()
async def change(ctx, original, new):
    if not change_nickname(original, new):
        await ctx.channel.send('Invalid current name')
        return
    await ctx.channel.send(f'Changed {original} to {new}')


@client.command()
async def stats(ctx):
    if playerdata == {}:
        await ctx.channel.send('No one in group, add them using !add ')
        return
    draw_picture(playerdata)
    await ctx.channel.send(file=discord.File('statistics.png'))


@client.command()
async def remove(ctx, *player):
    try:
        del playerdata[' '.join(player)]
        await ctx.channel.send(f'Deleted {" ".join(player)}')
    except KeyError:
        await ctx.channel.send('KeyError !!! type it right')


client.run('MTA1Mzc2Nzk2MjAzODkxNTE3Mg.GOc00k.qjHaAOdp8gg8JQWZ76nBM19S31l6OX6UKx6dao')
