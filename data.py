import pandas as pd
import dataframe_image as dfi
import csv
from functools import cmp_to_key
from parse import *
import random
from math import *
#players_data = pd.read_csv("ROSTER.csv")

#player_list = players_data.to_dict("records")

#print(player_list[0]["FIRST"])

#player_list[0]["FIRST"] = "Steven"

#players_data = pd.DataFrame.from_records(player_list)

#print(players_data)
star_levels = {
    "🥉" : range(0, 60),
    "🥈" : range(60, 70),
    "🥇" : range(70, 80),
    "🏆" : range(80, 90),
    "👑" : range(90, 100)
}

status_emojis = {
    "Active" : "🟢",
    "Injured" : "🔴",
    "Practice Squad" : "🟡",
    "Free Agent" : "🔵"
}

dev_levels = {"Bronze" : 0.05, "Silver" : 0.075, "Gold" : 0.1, "Platinum" : 0.125}
dev_weights = [5, 3, .5, 0.1]

depth_order = ["QB", "RB", "FB", "WR", "TE", "LT", "LG", "C", "RG", "RT", "DE", "DT", "DE", "OLB", "MLB", "OLB", "MLB", "DB", "SS", "FS", "DB", "K", "P"]
position_fills = [1, 1, 1, 5, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 3, 1, 1]

positions = ["QB", "RB", "FB", "TE", "WR", "OL", "LT", "LG", "C", "RG", "RT", "DL", "DE", "DT", "LB", "OLB", "MLB", "CB", "FS", "SS", "DB", "K", "P"]
team_units = {
    "Offense" : ["QB", "RB", "FB", "TE", "WR", "OL", "LT", "LG", "C", "RG", "RT"],
    "Defense" : ["DL", "DE", "DT", "LB", "OLB", "MLB", "DB", "FS", "SS", "DB"],
    "Special Teams" : ["K", "P"]
}

attributes = {
    "AWR" : "AWARE",
    "SPD" : "SPEED",
    "TLB" : "TLK BRK",
    "FUM" : "FUMBLE",
    "CAT" : "CATCH",
    "RTRN" : "RTRN",
    "PBLK" : "PAS BLK",
    "RBLK" : "RUN BLK",
    "THP" : "THR PWR",
    "THA" : "THR ACC",
    "KPW" : "KCK PWR",
    "KAC" : "KCK ACC",
    "BSHD" : "BLK SHD",
    "PRSH" : "PAS RSH",
    "TKL" : "TACKLE",
    "HTP" : "HIT PWR",
    "MCOV" : "M COV",
    "ZCOV" : "Z COV", 
    "FIT" : "FITNESS",
    "DIS" : "DISCIPLINE",
    "POT" : "POTENTIAL"
}

core_attributes = {
    'QB' : ['THP',  'THA',  'AWR',  'SPD',  'FIT',  'FUM'],
    'RB' : ['TLB',  'SPD',  'FUM', 'AWR', 'CAT',  'RTRN', 'PBLK'],
    'FB' : ['RBLK', 'PBLK', 'SPD',  'TLB',  'FUM',  'AWR'],
    'WR' : ['SPD',  'CAT',  'RTRN', 'FUM',  'FIT'],
    'TE' : ['SPD',  'CAT',  'RBLK', 'AWR',  'RTRN', 'PBLK', 'TLB'],
    'LT' : ['RBLK', 'PBLK', 'AWR',  'SPD',  'FIT',  'SPD',  'FIT'],
    'LG' : ['RBLK', 'PBLK', 'AWR',  'SPD',  'FIT',  'SPD',  'FIT'],
    'C' : ['RBLK', 'PBLK', 'AWR',  'SPD',  'FIT',  'SPD',  'FIT'],
    'RG' : ['RBLK', 'PBLK', 'AWR',  'SPD',  'FIT',  'SPD',  'FIT'],
    'RT' : ['RBLK', 'PBLK', 'AWR',  'SPD',  'FIT',  'SPD',  'FIT'],
    'DE' : ['SPD',  'TKL',  'BSHD', 'PRSH', 'AWR',  'HTP',  'FIT'],
    'DT' : ['PRSH', 'BSHD', 'TKL',  'AWR',  'SPD',  'HTP',  'FIT'],
    'OLB' : ['TKL',  'HTP',  'SPD',  'PRSH', 'BSHD', 'AWR',  'ZCOV', 'MCOV', 'CAT'],
    'MLB' : ['SPD',  'TKL',  'BSHD', 'HTP',  'AWR',  'ZCOV', 'PRSH', 'FIT',  'MCOV'],
    'DB' : ['SPD',  'MCOV', 'ZCOV', 'CAT',  'TKL',  'AWR',  'BSHD', 'HTP',  'FIT'],
    'FS' : ['SPD',  'ZCOV', 'TKL',  'MCOV', 'HTP',  'BSHD', 'AWR',  'CAT',  'FIT'],
    'SS' : ['SPD',  'ZCOV', 'TKL',  'MCOV', 'HTP',  'BSHD', 'AWR',  'CAT',  'FIT'],
    'K' :  ['KPW',  'KAC',  'AWR',  'SPD',  'THP',  'THA',  'TKL',  'BSHD', 'FIT'],
    'P' :  ['KPW',  'KAC',  'AWR',  'SPD',  'THP',  'THA',  'TKL',  'BSHD', 'FIT']
}

print(core_attributes["DB"])

def simplest_type(s):
    try:
        return literal_eval(s)
    except:
        return s


def pull_csv(filename):
    players_data = pd.read_csv(filename)
    return players_data.to_dict("records")

def push_csv(records, filename):
    players_data = pd.DataFrame.from_records(records)
    players_data.to_csv(filename, index=False)

def positions_sort(a, b):
    if positions.index(a.attributes["POS"]) > positions.index(b.attributes["POS"]):
        return 1
    elif a.attributes["POS"] == b.attributes["POS"]:
        return 0
    else:
        return -1

stat_breakdowns = {
    "passing"  : {
        "QBCompletions" : "COMP",
        "QBAttempts" : "ATT",
        "QBPassYards" : "YDS",
        "QBInts" : "INT"
    }
}

'''
def stats(player_name):
    stats_df = pd.read_csv("/media/trevor/DECK/UFAF/Season 1/S1_W1.csv")
    stats_data = stats_df.to_dict("records")
    for entry in stats_data:
        name = entry["FirstName"] + " " + entry["LastName"]
        if name == player_name.upper():
            records = entry

    part = {}
    for name, value in records.items():
        if name in stat_breakdowns["passing"]:
            part[stat_breakdowns["passing"][name]] = value
    part["PCT"] = '{:,.2%}'.format(part["COMP"] / part["ATT"])
    return part

print(stats("Jude Zimmerman"))
'''

weights = pull_csv("WEIGHTS.csv")

letter_grades = {
    "D-"    :   range(0, 49),
    "D "     :   range(49, 58),
    "D+"    :   range(58, 67),
    "C-"    :   range(67, 71),
    "C "     :   range(71, 76),
    "C+"    :   range(76, 81),
    "B-"    :   range(81, 84),
    "B "     :   range(84, 87),
    "B+"    :   range(87, 91),
    "A-"    :   range(91, 94),
    "A "     :   range(94, 97),
    "A+"    :   range(97, 100)
}

def get_team_emoji(message, team):
    if message.guild == None:
        return ""
    emoji_id = 0
    if team == 0: team = "ufaf"
    for emoji in message.guild.emojis:
        if emoji.name == removeSpacesAndPeriods(team):
            emoji_id = emoji.id
    emoji_string = "<:{}:{}>".format(removeSpacesAndPeriods(team), emoji_id)
    return emoji_string

class Player:
    def __init__(self, attributes):
        self.attributes = attributes
        self.full_name = self.attributes["FIRST"] + " " + self.attributes["LAST"]
    def get_overall(self):
        #weights = pull_csv("WEIGHTS.csv")

        player_weights = []
        rating_index = 0
        weight_sum = 0
        for i, v in enumerate(weights):
            if v["Pos"] == self.attributes["POS"]:
                weight_sum = v["SUM"]
                rating_index = i
                for name, value in v.items():
                    if name != "Pos" and name != "SUM":
                        player_weights.append(self.attributes[name] * floor(value))


        #(rating * weight)+(rating *weight)
        return(round(sum(player_weights)/weight_sum))
    def rating_grade(self, rating_name):
        v = self.attributes[rating_name]
        l = ""
        for letter, rng in letter_grades.items():
            if floor(v) in rng:
                l = letter
        return l
    def letter_grade(self):
        g = ""
        ovr = self.get_overall()
        for letter, r in letter_grades.items():
            if ovr in r:
                g = letter
        return g
    def practice(self):
        advancements = {}
        for name in core_attributes[self.attributes["POS"]]:
            att_name = attributes[name]
            old_grade = self.rating_grade(att_name)
            self.attributes[att_name] = round(self.attributes[att_name] + dev_levels[self.attributes["DEV"]], 3)
            new_grade = self.rating_grade(att_name)
            if old_grade != new_grade: advancements[name] = new_grade
        print(f'{self.full_name} advanced: {advancements}')
        return advancements

        print(self.attributes["SPEED"])
    def team_emoji(self, ctx, teams_table):
        tid = self.attributes["TEAMID"]
        if tid > 0:
            team_city = teams_table[tid]["CITY"]
        else:
            team_city = "ufaf"

        if ctx.guild == None:
            return ""
        for emoji in ctx.guild.emojis:
            if emoji.name == removeSpacesAndPeriods(team_city):
                emoji_id = emoji.id
        emoji_string = "<:{}:{}>".format(removeSpacesAndPeriods(team_city), emoji_id)
        return emoji_string

    def quick_info(self):
        return f'**{self.letter_grade()}**\t{self.attributes["POS"]}\t#{self.attributes["NUMBER"]}\t{self.full_name}\t*ID#{self.attributes["INDEX"]}*'

    def assign_random_dev_trait(self):
        self.attributes["DEV"] = random.choices(dev_levels.keys(), weights=dev_weights)[0]

        self
def getPlayer(records, pid):
    found = False
    player = None
    pid = pid.replace('"', "")
    pid = pid.replace("'", "")
    print(f"Attempting to find: {pid}")
    for p in records:
        if pid.isdigit() and int(pid) == p.attributes["INDEX"]:
            print("Found")
            found = True
            player = p
            break
        elif pid == p.attributes["FIRST"] + " " + p.attributes["LAST"]:
            print("Found")
            found = True
            player = p
            break
    if found:
        #print(calculate_overall(player))
        return p
    else:
        raise Exception("Player not found")

def get_all_team_players(team_id, team_records):
    roster = []
    for p in team_records:
        if p.attributes["TEAMID"] == int(team_id):
            roster.append(p)
    roster = sorted(roster, key=cmp_to_key(positions_sort))
    return roster

def get_depth_chart(team_id, team_records):
    roster = get_all_team_players(team_id, team_records)
    depth_chart = {}
    for i, position in enumerate(positions):
        depth_chart[position] = []
    for position, player_list in depth_chart.items():
        for p in roster:
            if p.attributes["POS"] == position:
                player_list.append(p)
    for position, player_list in depth_chart.items():
        player_list.sort(key=lambda p: p.attributes["DEPTH"])
        for i, p in enumerate(player_list):
            print(f'{position} {p.full_name} {p.attributes["DEPTH"]}')
    return depth_chart
'''
def calculate_overall(player):
    weights = pull_csv("WEIGHTS.csv")

    player_weights = []
    rating_index = 0
    weight_sum = 0
    for i, v in enumerate(weights):
        if v["Pos"] == player.attributes["POS"]:
            weight_sum = v["SUM"]
            rating_index = i
            for name, value in v.items():
                if name != "Pos" and name != "SUM":
                    player_weights.append(player.attributes[name] * value)


    #(rating * weight)+(rating *weight)
    return(round(sum(player_weights)/weight_sum))
'''
def full_name(player):
    return f'{player["FIRST"]} {player["LAST"]}'

def get_level_emoji(player):
    emoji = ""
    ovr = calculate_overall(player)
    for k, rng in star_levels.items():
        if ovr in rng:
            emoji = k
    return emoji

def hot_string(player, team_records):
    abv = ""
    if player.attributes["TEAMID"] > 0:
        for team in team_records:
            if player.attributes["TEAMID"] == team["ID"]:
                abv = team["ABV"]
    return f'{player.attributes["POS"]} {get_level_emoji(player)} {player.full_name} *({player.attributes["INDEX"]})*'

def get_owned_team_ids(ctx, user, team_records):
    isOwner = False
    ownedTeams = []
    member = ctx.guild.get_member(user.id)
    has_roles = member.roles

    for role in has_roles:
        if role.name == "Team Owner":
            isOwner = True
            print(f'{user.name} is a Team Owner')
        if role.name == "League Owner":
            isOwner = True

    if isOwner:
        for team in team_records:
            print(f'Checking team: {team["NICKNAME"]}')
            for role in has_roles:
                if role.name == team["CITY"] + " " + team["NICKNAME"]:
                    print(f"{user.name} owns {role.name}")
                    ownedTeams.append(team["ID"])

    return ownedTeams

def team_name_to_id(team_name, team_records):
    found = False
    tid = None
    for team in team_records:
        if team["CITY"] + " " + team["NICKNAME"] == team_name:
            found = True
            tid = team["ID"]
    if not found: 
        raise Exception("Team not found.")
    return tid