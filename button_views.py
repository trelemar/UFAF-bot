import discord
from discord.ext import commands
import asyncio
from parse import *
from checks import *

from data_tables import *
#from players import *
#from teams_and_picks import DraftPick

class TradeTeamSelect(discord.ui.Select):
    #sel_team = "Albuquerque River Monsters"
    def __init__(self, trade_ctx):
        self.trade_ctx = trade_ctx

        #if len(args) >= 3:
        #    self.add_option(label=args[2][0])
        #    self.add_option(label=args[2][1])

        self.sel_team = None
        super().__init__(max_values=1,min_values=1, placeholder="Select a team")

    async def add_team(self, ctx, team_data, team):
        td = team_data[team]
        emoji = await commands.EmojiConverter().convert(ctx, removeSpacesAndPeriods(td["City"]))
        self.add_option(label=f'{td["City"]} {td["Name"]}', value=td["City"], description=td["Division"], emoji=emoji)
    async def add_all_teams(self, ctx, team_data):
        for team_key, v in team_data.items():
            emoji = await commands.EmojiConverter().convert(ctx, removeSpacesAndPeriods(v["City"]))
            self.add_option(label=f'{v["City"]} {v["Name"]}', value=v["City"], description=v["Division"], emoji=emoji)
    async def create_options_for_teams(self):
        #print(self.trade_ctx.teams)
        for i, v in enumerate(self.trade_ctx.teams):
            team = self.trade_ctx.team_data[v]
            #print(team)
            emoji = await commands.EmojiConverter().convert(self.trade_ctx.ctx, removeSpacesAndPeriods(team["City"]))
            self.add_option(label=f'{team["City"]} {team["Name"]}', value=team["City"], emoji=emoji)

    async def advance_callback(self, interaction: discord.Interaction):
        self.sel_team = self.values[0]
        self.trade_ctx.current_team = self.sel_team
        view = self.view
        for item in view.children:
            print(type(item))
            if isinstance(item, discord.ui.Select):
                view.remove_item(item)
            if isinstance(item, discord.ui.Button):
                # Do something if button label is the player you just selected.
                pass

        #print("Hi")
        ps = PositionSelect(self.trade_ctx)
        #ps.teams = [self.options[0].label, self.options[1].label]
        view.add_item(ps)
        await interaction.message.edit(view=view)
        await interaction.response.defer()

    async def callback(self, interaction: discord.Interaction):
        self.sel_team = self.values[0]
        await interaction.response.defer()

class ProposeTradeButton(discord.ui.Button):
    def __init__(self, *args):
        self.trade_ctx = args[0]
        super().__init__(label="Propose Trade", style=discord.ButtonStyle.green, row=4)
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.trade_ctx.requested = True
        self.trade_ctx.review = False
        owners = await self.trade_ctx.get_owners()
        #self.view.clear_items()
        msg = await self.trade_ctx.make_message_content()
        #await interaction.message.edit(content=msg, view=self.view)
        await interaction.message.edit(view=discord.ui.View())
        await self.trade_ctx.ctx.send(content="Trade request sent.")
        view = discord.ui.View()
        await owners[1].send(content=msg,view=view)

class ReviewButton(discord.ui.Button):
    def __init__(self, *args):
        self.trade_ctx = args[0]
        super().__init__(label="Review", style=discord.ButtonStyle.primary, row=4)
    async def callback(self, interaction: discord.Interaction):
        self.trade_ctx.review = True
        self.view.clear_items()
        self.view.add_item(ProposeTradeButton(self.trade_ctx))
        self.view.add_item(CancelTradeButton())
        msg = await self.trade_ctx.make_message_content()
        await interaction.message.edit(content=msg, view=self.view)
        await interaction.response.defer()

class CancelTradeButton(discord.ui.Button):
    def __init__(self, *args):
        #self.ctx = args[0]
        super().__init__(label="Cancel",style=discord.ButtonStyle.danger, row=4)
    async def callback(self, interaction: discord.Interaction):
        if is_interaction_from_original_author(interaction):
            await interaction.response.defer(ephemeral=True)
            await interaction.message.delete()
            await interaction.message.reference.cached_message.delete()

class ComponentButton(discord.ui.Button):
    def __init__(self, *args):
        self.trade_ctx = args[0]
        self.is_pick = False
        if isinstance(args[1], DraftPick):
            self.is_pick = True
        print(type(args[1]))
        if self.is_pick:
            self.draftpick = args[1]
            lbl = f'S {self.draftpick.season} R {self.draftpick.round} {self.draftpick.cell.value}'
        else:
            self.player = args[1]
            self.player_name = self.player["Full Name"]
            lbl = self.player_name
        super().__init__(label=lbl, emoji=args[2])
    async def callback(self, interaction: discord.Interaction):
        if self.is_pick:
            del self.trade_ctx.components[self.label]
        else:
            del self.trade_ctx.components[self.label]
        #self.trade_ctx.components.remove(self.player_name)
        self.view.remove_item(self)
        valid = await self.trade_ctx.check_if_both_teams_have_component()
        if not valid:
            for item in self.view.children:
                if isinstance(item, ReviewButton):
                    #if item.label == "Review":
                    item.disabled = True
        msg = await self.trade_ctx.make_message_content()
        await interaction.message.edit(content=msg, view=self.view)
        await interaction.response.defer()


class ComponentSelect(discord.ui.Select):
    def __init__(self, trade_ctx, players):
        self.trade_ctx = trade_ctx
        self.team = self.trade_ctx.current_team
        self.selected = None
        super().__init__(max_values=1,min_values=1, options=players, placeholder= "Select a player to add")
    async def callback(self, interaction: discord.Interaction):
        #await interaction.response.send_message(content=f"Your choice is {self.values[0]}!",ephemeral=True)
        self.selected = self.values[0]
        view = self.view
        for item in view.children:
            #print(type(item))
            if isinstance(item, discord.ui.Select):
                view.remove_item(item)
            if isinstance(item, discord.ui.Button):
                # Do something if button label is the player you just selected.
                print(f'{item.label} {item.label in self.trade_ctx.components}')
                if not item.label in self.trade_ctx.components:
                    view.remove_item(item)
        emoji = await commands.EmojiConverter().convert(self.trade_ctx.ctx, removeSpacesAndPeriods(self.team))
        #self.trade_ctx.components.append(self.selected)

        component = None
        for i, p in enumerate(self.trade_ctx.player_data):
            if p["Full Name"] == self.selected:
                component = p

        print(f'selected: {self.selected}')
        if component == None:
            selected_split = self.selected.split()
            pseason = int(selected_split[1])
            pround = int(selected_split[3])
            val = " ".join(selected_split[4:len(selected_split)])
            print("Value: " + val)
            for i, pick in enumerate(self.trade_ctx.team_data[self.team]["picks"]):
                print(pick)
                if pick.season == pseason and pick.round == pround and pick.cell.value == val:
                    print("Found draft pick")
                    component = pick

        self.trade_ctx.components[self.selected] = component
        b = ComponentButton(self.trade_ctx, component, emoji)
        view.add_item(b)

        tts = TradeTeamSelect(self.trade_ctx)
        await tts.create_options_for_teams()
        tts.callback = tts.advance_callback
        view.add_item(tts)

        valid = await self.trade_ctx.check_if_both_teams_have_component()
        if valid:
            #view.add_item(discord.ui.Button(label="Review", style=discord.ButtonStyle.primary, row=4))
            view.add_item(ReviewButton(self.trade_ctx))
            view.add_item(CancelTradeButton())
            #view.add_item(discord.ui.Button(label="Cancel", style=discord.ButtonStyle.red, row=4))

        msg = await self.trade_ctx.make_message_content()
        await interaction.message.edit(content=msg, view=view)
        await interaction.response.defer()


class PositionSelect(discord.ui.Select):
    def __init__(self, trade_ctx):
        self.trade_ctx = trade_ctx
        self.team = self.trade_ctx.current_team
        print(self.team)
        self.sel_pos = None
        self.teams = self.trade_ctx.teams
        super().__init__(max_values=1,min_values=1, placeholder="Select a position")

        for i in range(self.trade_ctx.current_season + 1, self.trade_ctx.current_season + 4):
            self.add_option(label=f"Season {i} Draft Pick")

        pcounts = {}
        for pos in valid_positions:
            pcounts[pos] = 0
        for i, p in enumerate(self.trade_ctx.player_data):
            if p["Team"] == self.trade_ctx.current_team:
                if not p["Full Name"] in self.trade_ctx.components:
                    pcounts[p["Pos"]] += 1
        for pos, count in pcounts.items():
            if count > 0:
                self.add_option(label=pos)
    async def callback(self, interaction: discord.Interaction):
        #await interaction.response.send_message(content=f"Your choice is {self.values[0]}!",ephemeral=True)
        self.sel_pos = self.values[0]
        if "Draft" in self.sel_pos:
            options = []
            season = int(self.sel_pos.split()[1])
            print(f'Pick season: {season}')

            for pick in self.trade_ctx.team_data[self.team]["picks"]:
                if pick.season == season:
                    options.append(discord.SelectOption(label=f'S {pick.season} R {pick.round} {pick.cell.value}'))
        else:
            options = []
            for p in self.trade_ctx.player_data:
                if p["Team"] == self.team and p["Pos"] == self.sel_pos and not p["Full Name"] in self.trade_ctx.components:
                    lbl = f'{status_emojis[p["Status"]]} {p["OVR"]} OVR - {p["Pos"]} {p["Full Name"]}'
                    des = {}
                    options.append(discord.SelectOption(label=lbl, value=p["Full Name"]))
        view = self.view
        for item in view.children:
            if isinstance(item, discord.ui.Select):
                view.remove_item(item)
        ps = ComponentSelect(self.trade_ctx, options)
        ps.teams = self.teams
        view.add_item(ps)
        await interaction.message.edit(view=view)
        await interaction.response.defer()


class TeamSelect(discord.ui.Select):
    #sel_team = "Albuquerque River Monsters"
    def __init__(self, *args):
        self.ctx = args[0]
        self.sel_team = None
        #print(self.ctx)
        super().__init__(max_values=1,min_values=1)
    async def callback(self, interaction: discord.Interaction):
        #await interaction.response.send_message(content=f"Your choice is {self.values[0]}!",ephemeral=True)
        if is_interaction_from_original_author(self.ctx, interaction):
            self.sel_team = self.values[0]
            #command = self.ctx.bot.get_command("set")
            #await command(self.ctx, "Signing-Team", self.values[0])
            await interaction.response.defer()

class TestButton(discord.ui.Button):
    def __init__(self, *args):
        self.ctx = args[0]
        self.bot = args[1]
        super().__init__(label="TEST")
    async def callback(self, interaction: discord.Interaction):
        command = self.bot.get_command("set")
        await command(self.ctx, "week", 1)
        await interaction.response.send_message(content="HIIIIII")

class PracticeSquadSign(discord.ui.Button):
    def __init__(self, *args):
        self.ctx = args[0]
        self.bot = args[1]
        super().__init__(label="Practice Squad")
    async def callback(self, interaction: discord.Interaction):
        pass

class LOSignButton(discord.ui.Button):
    def __init__(self, *args):
        self.ctx = args[0]
        self.bot = args[1]
        self.player = args[2]
        self.dropdown = args[3]
        super().__init__(label="Sign",style=discord.ButtonStyle.gray,emoji="📋")
    async def callback(self, interaction: discord.Interaction):
        if is_interaction_from_original_author(self.ctx, interaction):
            await interaction.message.edit(view=None)
            await interaction.response.defer()
            #team_role = await commands.RoleConverter().convert(ctx, TeamSelect.sel_team)
            command = self.bot.get_command("sign")
            await command(self.ctx, self.player, 1, self.dropdown.sel_team)
            #await interaction.followup.send(content="Hi")

class SignButton(discord.ui.Button):
    def __init__(self, *args):
        self.ctx = args[0]
        self.bot = args[1]
        self.player = args[2]
        super().__init__(label="Sign",style=discord.ButtonStyle.gray,emoji="📋")
    async def callback(self, interaction: discord.Interaction):
        if is_interaction_from_original_author(self.ctx, interaction):
            await interaction.message.edit(view=None)
            await interaction.response.defer()
            command = self.bot.get_command("sign")
            await command(self.ctx, str(self.player.attributes["INDEX"]))

class ReleaseButton(discord.ui.Button):
    def __init__(self, *args):
        self.ctx = args[0]
        self.bot = args[1]
        self.player = args[2]
        super().__init__(label="Release",style=discord.ButtonStyle.gray,emoji="✂️")
    async def callback(self, interaction: discord.Interaction):
        await interaction.message.edit(view=None)
        await interaction.response.defer()
        command = self.bot.get_command("release")
        await command(self.ctx, str(self.player.attributes["INDEX"]))

class PromoteButton(discord.ui.Button):
    def __init__(self, *args):
        self.ctx = args[0]
        self.bot = args[1]
        self.player = args[2]
        super().__init__(label="Move to roster",style=discord.ButtonStyle.gray,emoji="⬆️")
    async def callback(self, interaction: discord.Interaction):
        await interaction.message.edit(view=None)
        await interaction.response.defer()
        command = self.bot.get_command("promote")
        await command(self.ctx, str(self.player.attributes["INDEX"]))

class DemoteButton(discord.ui.Button):
    def __init__(self, *args):
        self.ctx = args[0]
        self.bot = args[1]
        self.player = args[2]
        super().__init__(label="Move to practice squad",style=discord.ButtonStyle.gray,emoji="⬇️")
    async def callback(self, interaction: discord.Interaction):
        await interaction.message.edit(view=None)
        await interaction.response.defer()
        command = self.bot.get_command("demote")
        await command(self.ctx, str(self.player.attributes["INDEX"]))


class PlayerOptions(discord.ui.View):
    def __init__(self, *args, timeout=180):
        self.ctx = args[0]
        self.bot = args[1]
        self.player = args[2]
        #print(args)
        super().__init__(timeout=timeout)

    @discord.ui.button(label="Sign",style=discord.ButtonStyle.gray,emoji="📋")
    async def sign_button(self,interaction:discord.Interaction,button:discord.ui.Button):
        #await interaction.response.defer(ephemeral=True)
        await interaction.response.edit_message(view=None)
        sign_command = self.bot.get_command("sign")
        if isLeagueOwner(interaction.user):
            await sign_command(self.ctx, self.player, 1, selected_team)
        else:
            await sign_command(self.ctx, self.player, 1)
        selected_team = None
    @discord.ui.button(label="Release",style=discord.ButtonStyle.gray,emoji="✂️")
    async def release_button(self,interaction:discord.Interaction,button:discord.ui.Button):
        await interaction.response.edit_message(view=None)
        command = self.bot.get_command("release")
        await command(self.ctx, self.player)
    @discord.ui.button(label="Promote",style=discord.ButtonStyle.gray,emoji="⬆️")
    async def promote_button(self,interaction:discord.Interaction,button:discord.ui.Button):
        await interaction.response.edit_message(view=None)
        command = self.bot.get_command("promote")
        await command(self.ctx, self.player)
    @discord.ui.button(label="Demote",style=discord.ButtonStyle.gray,emoji="⬇️")
    async def demote_button(self,interaction:discord.Interaction,button:discord.ui.Button):
        await interaction.response.edit_message(view=None)
        command = self.bot.get_command("demote")
        await command(self.ctx, self.player)

class ActiveRosteredOptions(discord.ui.View):
    def __init__(self, *args, timeout=180):
        self.ctx = args[0]
        self.bot = args[1]
        self.player = args[2]
        print(args)
        super().__init__(timeout=timeout)
    @discord.ui.button(label="Release",style=discord.ButtonStyle.gray,emoji="✂️")
    async def release_button(self,interaction:discord.Interaction,button:discord.ui.Button):
        await PlayerOptions.release_button(self,interaction,button)
    @discord.ui.button(label="Demote",style=discord.ButtonStyle.gray,emoji="⬇️")
    async def demote_button(self,interaction:discord.Interaction,button:discord.ui.Button):
        await PlayerOptions.demote_button(self,interaction,button)

class PracticeSquadRosteredOptions(discord.ui.View):
    def __init__(self, *args, timeout=180):
        self.ctx = args[0]
        self.bot = args[1]
        self.player = args[2]
        print(args)
        super().__init__(timeout=timeout)
    @discord.ui.button(label="Release",style=discord.ButtonStyle.gray,emoji="✂️")
    async def release_button(self,interaction:discord.Interaction,button:discord.ui.Button):
        await PlayerOptions.release_button(self,interaction,button)
    @discord.ui.button(label="Promote",style=discord.ButtonStyle.gray,emoji="⬆️")
    async def promote_button(self,interaction:discord.Interaction,button:discord.ui.Button):
        await PlayerOptions.promote_button(self,interaction,button)

class FreeAgentOptions(discord.ui.View):
    def __init__(self, *args, timeout=180):
        self.ctx = args[0]
        self.bot = args[1]
        self.player = args[2]
        self.teams_list = args[3]
        print(args)
        super().__init__(timeout=timeout)
        self.add_item(TeamSelect(self.ctx, self.bot, self.teams_list))
    @discord.ui.button(label="Sign",style=discord.ButtonStyle.gray,emoji="📋")
    async def sign_button(self,interaction:discord.Interaction,button:discord.ui.Button):
        await PlayerOptions.sign_button(self,interaction,button)