import discord
import pandas as pd
import dataframe_image as dfi
from discord.ext import commands
from discord import app_commands
from typing import Literal, Optional
from discord.ext.commands import Greedy, Context # or a subclass of yours
from functools import cmp_to_key
import math
import json
import sys

from data import *
from checks import *
from button_views import *

import TOKEN

description = f'''
Here is a list of available commands:
'''

intents = discord.Intents.default()
intents.members = True
intents.message_content = True



def getChannelByName(ctx, name):
    channel = None
    for i in ctx.message.guild.channels:
        if i.name == name:
            channel = i
    return channel

if len(sys.argv) > 1 and sys.argv[1] == "y":
    BOT_TOKEN = TOKEN.BETA
    prefix = "?"
    data_path = "/home/trevor/UFAF_data/"
else:
    BOT_TOKEN = TOKEN.MAIN
    prefix = "!"
    data_path = "/mnt/rasp/"

def init():
    global player_records, teams, team_table, transaction_queue, players, league_settings
    with open("league_settings.json") as settings_file:
        league_settings = json.load(settings_file)

    player_records = pull_csv(data_path + "ROSTER.csv")
    players = []
    for p in player_records:
        players.append(Player(p))
    print(len(players))
    teams = pull_csv(data_path + "TEAMS.csv")
    team_table = {}
    for team in teams:
        team_table[team["ID"]] = team
init()
transaction_queue = {}

async def role_to_team_name(ctx, team_role):
    role = await commands.RoleConverter().convert(ctx, team_role)
    return role.name


bot = commands.Bot(command_prefix=prefix, description=description, intents=intents)

@bot.command()
@commands.guild_only()
@commands.is_owner()
async def sync(
  ctx: Context, guilds: Greedy[discord.Object], spec: Optional[Literal["~", "*", "^"]] = None) -> None:
    if not guilds:
        if spec == "~":
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "*":
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "^":
            ctx.bot.tree.clear_commands(guild=ctx.guild)
            await ctx.bot.tree.sync(guild=ctx.guild)
            synced = []
        else:
            synced = await ctx.bot.tree.sync()

        await ctx.send(
            f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
        )
        return

    ret = 0
    for guild in guilds:
        try:
            await ctx.bot.tree.sync(guild=guild)
        except discord.HTTPException:
            pass
        else:
            ret += 1

    await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")
async def setup(bot):
    await bot.add_cog(Everyone(bot))
    await bot.add_cog(TeamOwner(bot))
    await bot.add_cog(LeagueOwner(bot))

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

    await setup(bot)
    #await bot.tree.sync()

def cmp_items(a, b):
    if positions.index(a["POS"]) > positions.index(b["POS"]):
        return 1
    elif a["POS"] == b["POS"]:
        return 0
    else:
        return -1

class Everyone(commands.Cog, name="Everyone"):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name='player', with_app_command=True, description="Show a specific player's information.")
    @app_commands.describe(player_id="A player's full name or ID number.")
    async def player(self, ctx, player_id : str):
        player_id = str(player_id)
        init()
        '''See info about a player and manage them.'''
        p = getPlayer(players, player_id)
        height = int(p.attributes["Height"])
        feet = math.floor(height / 12)
        inches = height % 12
        height = str(feet) + "'" + str(inches) + '"'

        view = discord.ui.View()

        ownedTeams = get_owned_team_ids(ctx, ctx.message.author, teams)

        team_name = "Free Agent"
        emoji_name = "ufaf"
        if p.attributes["TEAMID"] > 0:
            team = team_table[p.attributes["TEAMID"]]
            team_name = team["CITY"] + " " + team["NICKNAME"]
            emoji_name = team["CITY"]

        try:
            role = await commands.RoleConverter().convert(ctx, team["CITY"] + " " + team["NICKNAME"])
        except:
            role = False
            
        color = 0
        if role:
            color = role.color

        path = f'{data_path}Player Portraits/Skin Tone {p.attributes["SKIN"]}/{p.attributes["PORTRAIT"]}.png'
        
        thumb = discord.File(path, filename="portrait.png")
        #title = f'**{p.full_name}** · {p.attributes["POS"]} · #{p.attributes["NUMBER"]}'
        team_emoji = get_team_emoji(ctx.message, emoji_name)
        #title = f'**{p.full_name}** · *SUPERSTAR*\n**{p.letter_grade()}** · {p.attributes["POS"]} · #{p.attributes["NUMBER"]}'
        title = f'{p.full_name} · {p.attributes["POS"]} · #{p.attributes["NUMBER"]}\n**{p.letter_grade()}** {p.attributes["DEV"]}'
        embedMsg = discord.Embed(title=title, description=f'{team_emoji} {team_name}', color=color)
        embedMsg.add_field(name="", value=f'**Age** {p.attributes["AGE"]}')
        embedMsg.add_field(name="", value=f'**Ht** {height} · **Wt** {p.attributes["Weight"]} lbs', inline=False)
        #embedMsg.add_field(name="", value=f'**College** {p["College"]} · **Hometown** {p["Hometown"]}, {p["State"]}', inline=False)
        for rating_name in core_attributes[p.attributes["POS"]]:
            l = p.rating_grade(attributes[rating_name])
            embedMsg.add_field(name=l, value=rating_name, inline=True)
        '''
        embedMsg.add_field(name="🌵 Gunslinger", value="+THP, -AWR for each active *🔪 Deep Threat* WR", inline=True)
        embedMsg.add_field(name="🏠 Homebody", value="+AWR when playing at home", inline=True)
        embedMsg.add_field(name="📈 Streaky", value="+AWR/-AWR per win/loss streak value", inline=True)
        '''
        embedMsg.set_author(name=f'{status_emojis[p.attributes["STATUS"]]} {p.attributes["STATUS"]}')
        #embedMsg = discord.Embed(title=title, description=f'{team_name}', color=color)
        embedMsg.set_thumbnail(url="attachment://portrait.png")

        if league_settings["LOCK"] == 0:
            if p.attributes["TEAMID"] == 0:
                view.add_item(SignButton(ctx, bot, p))
            elif p.attributes["TEAMID"] in ownedTeams:
                if p.attributes["STATUS"] == "Active":
                    view.add_item(DemoteButton(ctx, bot, p))
                elif p.attributes["STATUS"] == "Practice Squad":
                    view.add_item(PromoteButton(ctx, bot, p))
                view.add_item(ReleaseButton(ctx, bot, p))


        '''
        if p[f'S{league_settings["Season"]} Week'] == "PERM":
            for button in view.children:
                if button.label == "Demote" or button.label == "Release":
                    button.disabled = True
        '''

        await ctx.send(file=thumb, embed=embedMsg, view=view)

    
    @commands.hybrid_command(name="free_agents", with_app_command=True, description="Lists all free agents of a given position.")
    async def free_agents(self, ctx, position : str):
        #plist.sort(key=lambda x: x["OVR"], reverse=True)
        players.sort(key=lambda x: x.attributes["LAST"])
        msg = f'## Free Agent {position}s\n'
        for p in players:
            if p.attributes["POS"] == position and p.attributes["TEAMID"] == 0:
                msg = msg + f'**{p.letter_grade()}**\t{p.full_name}\t*ID#{p.attributes["INDEX"]}*\n'
        await ctx.reply(content=msg)

    @commands.hybrid_command(name="roster", with_app_command=True, description="List a team's entire roster.")
    async def roster(self, ctx, team_role : str):
        init()
        team_name = await role_to_team_name(ctx, team_role)
        tid = team_name_to_id(team_name, teams)
        msg = f"{team_name}'s active roster\n"
        depth_chart = get_depth_chart(tid, players)
        #team_player_records = sorted(players, key=cmp_to_key(positions_sort))
        count = 0

        for unit, positions in team_units.items():
            msg = f'## {team_name} {unit}:\n'

            for pos, player_list in depth_chart.items():
                if pos in positions:
                    if len(player_list) > 0:
                        msg += f"### {pos}\n"
                    for i, p in enumerate(player_list):
                        count += 1
                        msg = msg + f'{i+1}. **{p.letter_grade()}**\t#{p.attributes["NUMBER"]}\t{p.full_name}\t*ID#{p.attributes["INDEX"]}*\n'
            await ctx.send(msg)

        #msg = msg + f'### TOTAL: {count}'
        #await ctx.send(msg)
    @commands.hybrid_command(name="stats", with_app_command=True, description="List a player's stats.")
    async def stats(self, ctx, player_id):
        pass
        
        async def cog_command_error(self, ctx, error):
            await ctx.message.reply(error)

class ConfirmButton(discord.ui.Button):
    def __init__(self, *args):
        self.ctx = args[0]
        self.bot = args[1]
        super().__init__(label="Confirm",style=discord.ButtonStyle.success)
    async def callback(self, interaction: discord.Interaction):
        if is_interaction_from_original_author(interaction):
            await interaction.message.edit(view=None)
            await interaction.response.defer(thinking=True)
            msg = await processTransaction(str(interaction.message.id), interaction.message)

            followup = await interaction.followup.send(content=msg)
            #await interaction.message.edit(content=msg, view=None)
            #await followup.delete()

class PSButton(discord.ui.Button):
    def __init__(self, *args):
        self.ctx = args[0]
        self.bot = args[1]
        super().__init__(label="Practice Squad",style=discord.ButtonStyle.primary)
    async def callback(self, interaction: discord.Interaction):
        if is_interaction_from_original_author(interaction):
            await interaction.message.edit(view=None)
            await interaction.response.defer(thinking=True)
            transaction_queue[str(interaction.message.id)]["ps"] = True
            msg = await processTransaction(str(interaction.message.id), interaction.message)

            followup = await interaction.followup.send(content=msg)
            await interaction.message.edit(content=msg, view=None)
            await followup.delete()

class CancelButton(discord.ui.Button):
    def __init__(self, *args):
        self.ctx = args[0]
        self.bot = args[1]
        super().__init__(label="Cancel",style=discord.ButtonStyle.danger)
    async def callback(self, interaction: discord.Interaction):
        if is_interaction_from_original_author(interaction):
            await interaction.response.defer(ephemeral=True)
            await interaction.message.delete()
            await interaction.message.reference.cached_message.delete()
            del transaction_queue[str(interaction.message.id)]
            #await reaction.message.row(content = "Canceled")
            print("Cancel")

async def processTransaction(msg_id, message):
    #global last_known_update_time

    for i in message.guild.channels:
        if i.name == "transactions-feed":
            transactions_feed = i
        elif i.name == "player-upgrades":
            player_upgrade_channel = i

    msg = ""
    transaction = transaction_queue[msg_id]

    p = transaction["player"]

    team = team_table[transaction["team_id"]]

    depth_chart = get_depth_chart(transaction["team_id"], players)

    if transaction["type"] == "sign":
        p.attributes["TEAMID"] = transaction["team_id"]
        if transaction["ps"] == True:
            p.attributes["STATUS"] = "Practice Squad"
            p.attributes["DEPTH"] = "NA"
        elif transaction["ps"] == False:
            p.attributes["STATUS"] = "Active"
            p.attributes["DEPTH"] = len(depth_chart[p.attributes["POS"]]) + 1
        msg = f'{p.full_name} has signed with {team["CITY"]}'
        transaction_message = f'**{team["CITY"]}** sign:\n{p.attributes["POS"]} {p.full_name}'
        if transaction["ps"] == True:
            transaction_message += "\n\nTo their practice squad."
    elif transaction["type"] == "release":
        p.attributes["TEAMID"] = 0
        p.attributes["DEPTH"] = "NA"
        p.attributes["STATUS"] = "Free Agent"
        msg = f'{team["CITY"]} has released {p.full_name}'
        transaction_message = f'**{team["CITY"]}** release:\n{p.attributes["POS"]} {p.full_name}'
    elif transaction["type"] == "promote":
        p.attributes["STATUS"] = "Active"
        p.attributes["DEPTH"] = len(depth_chart[p.attributes["POS"]])
        msg = f'{team["CITY"]} has promoted {p.full_name}'
        transaction_message = f'**{team["CITY"]}** promote:\n{p.attributes["POS"]} {p.full_name}'
    elif transaction["type"] == "demote":
        p.attributes["STATUS"] = "Practice Squad"
        p.attributes["DEPTH"] = "NA"
        msg = f'{team["CITY"]} has demoted {p.full_name}'
        transaction_message = f'**{team["CITY"]}** demote:\n{p.attributes["POS"]} {p.full_name}'

    player_records = []
    for p in players:
        player_records.append(p.attributes)

    push_csv(player_records, data_path + "ROSTER.csv")

    await transactions_feed.send(transaction_message)

    del transaction_queue[msg_id]
    print("Queue size: {}".format(len(transaction_queue)))
    print("transaction processed.")
    #print(last_known_update_time)
    #last_known_update_time = sh.get_lastUpdateTime()
    return msg

class LeagueOwner(commands.Cog, name="League Owner"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_any_role("DEVELOPER", "League Owner")
    async def set(self, ctx, setting, value, quiet=False):
        '''Changes league settings like the current week, season, etc.
        '''
        '''
        if not isLeagueOwner(ctx.message.author):
            await ctx.message.reply("You don't have permission to do that!")
            return
        '''
        setting = setting.upper()
        league_settings[setting] = simplest_type(value)
        if league_settings[setting].isdigit():
            league_settings[setting] = int(league_settings[setting])

        with open('league_settings.json', 'w') as settings_file:
            json.dump(league_settings, settings_file)

        await ctx.message.reply(f'League setting "{setting}" has been set to "{value}"')

    @commands.command()
    @commands.has_any_role("DEVELOPER", "League Owner")
    async def toggle(self, ctx, setting):
        '''Toggle a league setting on/off if it is toggleable. This is useful for locking and unlocking the rosters.'''
        '''
        if not isLeagueOwner(ctx.message.author):
            await ctx.message.reply("You don't have permission to do that!")
            return
        '''
        setting = setting.upper()

        if league_settings[setting] == 0:
            league_settings[setting] = 1
        elif league_settings[setting] == 1:
            league_settings[setting] = 0

        #league_settings[setting] = simplest_type(value)

        with open('league_settings.json', 'w') as settings_file:
            json.dump(league_settings, settings_file)

        await ctx.message.reply(f'League setting "{setting}" has been set to "{league_settings[setting]}"')

    @commands.command()
    @commands.has_role("League Owner")
    async def build(self, ctx, team_id):
        init()
        roster = get_all_team_players(team_id, players)
        depth_chart = get_depth_chart(team_id, players)

        msg = ""
        used = []
        export_list = []
        for pos_idx, pos in enumerate(depth_order):
            for amount in range(position_fills[pos_idx]):
                print(f'{pos} #{amount}')
                player = depth_chart[pos][amount]
                count = 1
                while player.attributes["INDEX"] in used:
                    player = depth_chart[pos][amount + count]
                    count += 1
                msg = msg + f'{pos} - {player.full_name}\n'
                export_list.append(player.attributes)
                used.append(player.attributes["INDEX"])
                '''
                for p in roster:
                    if p.attributes["POS"] == pos and not p.attributes["INDEX"] in used:
                        used.append(p.attributes["INDEX"])
                        msg = msg + f'{pos} - {p.full_name}\n'
                        break
                '''
        for i, p in enumerate(roster):
            if not p.attributes["INDEX"] in used:
                export_list.append(p.attributes)
        await ctx.reply(msg)
        push_csv(export_list, data_path + "EXPORT.csv")

class TeamOwner(commands.Cog, name="Team Owner"):
    def __init__(self, bot):
        self.bot = bot
    #group = app_commands.Group(name="team_owner", description="...")
    @commands.hybrid_command(name="set_depth", with_app_command=True, description="Set a player's depth chart position.")
    @commands.has_role("Team Owner")
    async def set_depth(self, ctx, player_id: str, depth_position : int):
        if league_settings["LOCK"] == 1:
            print("LOCKED")
            await ctx.reply("Team rosters are currently locked.")
            return
        init()
        ownedTeams = get_owned_team_ids(ctx, ctx.message.author, teams)
        p = getPlayer(players, player_id)

        if p.attributes["TEAMID"] in ownedTeams:
            if depth_position in range(1, 20):
                msg = f'{team_table[p.attributes["TEAMID"]]["CITY"]} {p.attributes["POS"]}: \n'
                old = p.attributes["DEPTH"]
                p.attributes["DEPTH"] = depth_position
                depth_pos_players = get_depth_chart(p.attributes["TEAMID"], players)[p.attributes["POS"]]
                for i, player in enumerate(depth_pos_players):
                    if player.attributes["INDEX"] != p.attributes["INDEX"] and player.attributes["DEPTH"] == depth_position:
                        modifier = -1
                        if old > depth_position:
                            modifier = 1

                        player.attributes["DEPTH"] = depth_position + modifier

                    #msg = msg + f'{i}. {player.full_name}\n'
                depth_pos_players.sort(key=lambda x: x.attributes["DEPTH"])
                players.sort(key=lambda x: x.attributes["INDEX"])
                for i, player in enumerate(depth_pos_players):
                    player.attributes["DEPTH"] = i + 1
                    players[player.attributes["INDEX"]] = player
                    if player.attributes["INDEX"] == p.attributes["INDEX"]: msg += "__"
                    msg = msg + f'{i+1}. **{player.letter_grade()}**\t#{player.attributes["NUMBER"]}\t{player.full_name}\t*ID#{player.attributes["INDEX"]}*\n'
                    if player.attributes["INDEX"] == p.attributes["INDEX"]: msg += "__"
                    #msg += f'{i}. (DEPTH: {player.attributes["DEPTH"]}) {player.attributes["NUMBER"]} {player.full_name}\n'



                player_records = []
                for p in players:
                    player_records.append(p.attributes)

                push_csv(player_records, data_path + "ROSTER.csv")

                await ctx.send(msg)
            else:
                await ctx.send("Please use a valid number")
        else:
            await ctx.send(f'{p.full_name} is not on your roster.')
    
    @commands.hybrid_command(name="sign", with_app_command=True, description="Sign a player to a team's roster")
    @commands.has_role("Team Owner")
    async def sign(self, ctx, player_id : str, team_role):
        if league_settings["LOCK"] == 1:
            print("LOCKED")
            await ctx.reply("Team rosters are currently locked.")
            return
        init()
        ownedTeams = get_owned_team_ids(ctx, ctx.message.author, teams)
        p = getPlayer(players, player_id)

        if p.attributes["TEAMID"] != 0:
            await ctx.reply(f'{p.full_name} is not a free agent.')
            return

        print(len(ownedTeams))
        tid = ownedTeams[0]
        city = team_table[tid]["CITY"]

        try:
            role = await commands.RoleConverter().convert(ctx, team_role)
            print(role.name)
            for team in teams:
                if role.name == f'{team["CITY"]} {team["NICKNAME"]}':
                    tid = team["ID"]
                    city = team["CITY"]
        except IndexError:
            pass

        view = discord.ui.View()
        active_button = ConfirmButton(ctx, bot)
        active_button.label = "Active Roster"
        view.add_item(active_button)
        view.add_item(PSButton(ctx, bot))
        view.add_item(CancelButton(ctx, bot))

        msg = await ctx.send(f'Sign {p.full_name} to {city}?', view=view)
        transaction_queue[str(msg.id)] = {"player" : p, "type" : "sign", "team_id" : tid, "ps" : False}

    @commands.hybrid_command(name="release", with_app_command=True, description="Release a player from a team you own.")
    @commands.has_role("Team Owner")
    async def release(self, ctx, player_id : str):
        if league_settings["LOCK"] == 1:
            print("LOCKED")
            await ctx.reply("Team rosters are currently locked.")
            return
        init()
        pid = str(player_id)
        ownedTeams = get_owned_team_ids(ctx, ctx.message.author, teams)
        p = getPlayer(players, pid)

        if p.attributes["TEAMID"] in ownedTeams:
            team = team_table[p.attributes["TEAMID"]]
            view = discord.ui.View()
            drop_button = ConfirmButton(ctx, bot)
            drop_button.label = "Release"
            view.add_item(drop_button)
            view.add_item(CancelButton(ctx, bot))

            msg  = await ctx.reply(f"Are you sure you want to release {p.full_name}?", view=view)
            transaction_queue[str(msg.id)] = {"player" : p, "type" : "release", "team_id" : p.attributes["TEAMID"]}
        else:
            await ctx.reply(f'{p.full_name} is not on a team you own.')

    @commands.hybrid_command(name="promote", with_app_command=True, description="Move a player to the active roster.")
    @commands.has_role("Team Owner")
    async def promote(self, ctx, player_id : str):
        if league_settings["LOCK"] == 1:
            print("LOCKED")
            await ctx.reply("Team rosters are currently locked.")
            return
        init()
        ownedTeams = get_owned_team_ids(ctx, ctx.message.author, teams)
        p = getPlayer(players, player_id)

        team = team_table[p.attributes["TEAMID"]]

        if p.attributes["TEAMID"] in ownedTeams:
            if p.attributes["STATUS"] == "Active":
                await ctx.reply(f'{p.full_name} is already on {team["CITY"]}\'s active roster.')
                return
            elif p.attributes["STATUS"] == "Practice Squad":
                view = discord.ui.View()
                view.add_item(ConfirmButton(ctx, bot))
                view.add_item(CancelButton(ctx, bot))
                msg  = await ctx.reply(f"Are you sure you want to move {p.full_name} to {team['CITY']}'s active roster?", view=view)
                transaction_queue[str(msg.id)] = {"player" : p, "type" : "promote", "team_id" : p.attributes["TEAMID"]}
        else:
            await ctx.reply(f'{p.full_name} is not on a team you own.')

    @commands.hybrid_command(name="demote", with_app_command=True, description="Move a player to the practice squad")
    @commands.has_role("Team Owner")
    async def demote(self, ctx, player_id : str):
        if league_settings["LOCK"] == 1:
            print("LOCKED")
            await ctx.reply("Team rosters are currently locked.")
            return
        init()
        ownedTeams = get_owned_team_ids(ctx, ctx.message.author, teams)
        p = getPlayer(players, player_id)

        team = team_table[p.attributes["TEAMID"]]

        if p.attributes["TEAMID"] in ownedTeams:
            if p.attributes["STATUS"] == "Practice Squad":
                await ctx.reply(f'{p.full_name} is already on {team["CITY"]}\'s practice squad.')
                return
            elif p.attributes["STATUS"] == "Active":
                view = discord.ui.View()
                view.add_item(ConfirmButton(ctx, bot))
                view.add_item(CancelButton(ctx, bot))
                msg  = await ctx.reply(f"Are you sure you want to move {p.full_name} to {team['CITY']}'s practice squad?", view=view)
                transaction_queue[str(msg.id)] = {"player" : p, "type" : "demote", "team_id" : p.attributes["TEAMID"]}
        else:
            await ctx.reply(f'{p.full_name} is not on a team you own.')


    async def cog_command_error(self, ctx, error):
        await ctx.message.reply(error)

bot.run(BOT_TOKEN)