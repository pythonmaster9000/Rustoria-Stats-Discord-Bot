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
    with open('team_stats.txt', 'r', encoding="utf-8") as newf:
        playerdata = json.loads(newf.read())
except json.decoder.JSONDecodeError:
    playerdata = {}

try:
    with open("token.txt", 'r') as r:
        token = r.read()
except FileNotFoundError:
    raise "MAKE A FILE CALLED 'token.txt' AND PUT YER TOKEN IN IT"

types_of_stats = ['pvp', 'misc', 'resources']


def change_nickname(original_name, new_name):
    try:
        playerdata[original_name]['nickname'] = new_name
        with open('team_stats.txt', 'w') as newf:
            newf.write(json.dumps(playerdata, indent=4))
        return True
    except KeyError:
        return False


def get_player(player_id: int):
    steam_page = requests.get(f'https://steamcommunity.com/profiles/{player_id}')
    player_username = steam_page.text.split('<title>Steam Community ::')[1].split("</")[0].lstrip()
    player_avatar_url = re.search("(?P<url>https?://[^\s]+)",
                                  steam_page.text.split('<div class="playerAvatarAutoSizeInner">')[1]).group("url")[:-2]

    return player_username, player_avatar_url


def download_player_image(player_username: str, image_url: str):
    img_data = requests.get(image_url).content
    with open(f'{player_username}av.png', 'wb') as handler:
        handler.write(img_data)


def draw_picture(players: dict):
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
        draw = ImageDraw.Draw(im)

        draw.text((10, 5), playerdata[player]['nickname'].encode("ascii", "ignore").decode(),
                  fill=(0, 0, 0))  # .encode("ascii", "ignore").decode() removes special characters (PIL DONT LIKE IT)
        draw.text((150, 10), str(playerdata[player]['pvp']['pvp_player_kills_total']),
                  fill=(0, 0, 0) if playerdata[player]['pvp']['pvp_player_kills_total'] ==
                                    sorted(playerdata, key=lambda e: playerdata[e]['pvp']['pvp_player_kills_total'])[
                                    ::-1][0]['pvp']['pvp_player_kills_total'] else (1, 2, 1))
        draw.text((267, 10), str(playerdata[player]['pvp']['pvp_player_deaths_total']), fill=(0, 0, 0))
        draw.text((370, 10), str(playerdata[player]['pvp']['kdr']), fill=(0, 0, 0))
        draw.text((158, 40), str(playerdata[player]['resources']['farming_resource_stone_harvested']), fill=(0, 0, 0))
        draw.text((220, 40), str(playerdata[player]['resources']['farming_resource_stone_harvested']), fill=(0, 0, 0))
        draw.text((275, 40), str(playerdata[player]['resources']['farming_resource_wood_harvested']), fill=(0, 0, 0))
        draw.text((320, 40), str(playerdata[player]['resources']['farming_resource_wood_harvested']), fill=(0, 0, 0))
        draw.text((170, 80), str(round(playerdata[player]['misc']['player_time_played'] / 60, 2)), fill=(0, 0, 0))
        draw.text((350, 80), str(round(playerdata[player]['pvp']['pvp_player_kills_total'] / (
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


def add_to_data(player: str):
    for index, stat in enumerate(types_of_stats):
        # Checks to see if the player exists & grabs steam information
        stat_data = requests.get(
            f'https://api.rustoria.co/statistics/leaderboards/2x_mondays_us/{stat}?from=0&sortBy=total&orderBy=asc&username={player}').json()[
            'leaderboard'][0]
        if index == 0:
            if len(stat_data) == 0:  # No results on the page (invalid player name)
                return 0

            player_user_id = stat_data['userId']
            steam_name, player_image_url = get_player(
                player_id=player_user_id)  # Gets the players steam name & steam avatar
            print(steam_name)
            playerdata[steam_name] = {}
            playerdata[steam_name]['player_id'] = player_user_id
            playerdata[steam_name]['nickname'] = steam_name

        playerdata[steam_name][stat] = stat_data['data']

    download_player_image(player_username=steam_name, image_url=player_image_url)  # Downloads the players image locally

    with open('team_stats.txt', 'w', encoding="utf-8") as newf:
        newf.write(json.dumps(playerdata, indent=4))


@client.event
async def on_ready():
    print('we ready')


@tasks.loop(minutes=4)
async def update_team():
    update_stats(playerdata)


@client.command()
async def add(ctx, *player):
    player_name = " ".join(player)
    await ctx.channel.send(f'Adding {player_name}')
    add_to_data(player_name)


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


client.run(token)
