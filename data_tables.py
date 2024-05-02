def irange(start, end): return range(start, end + 1)

upgrade_table = {
    "Normal": {
        "1" : irange(0, 75),
        "2" : irange(76, 80),
        "4" : irange(81, 85),
        "8" : irange(86, 89),
        "12" : irange(90, 91),
        "16" : irange(92, 93),
        "20" : irange(94, 95),
        "30" : irange(96, 96),
        "50" : irange(97, 97),
        "75" : irange(98, 98),
        "100" : irange(99, 99)
    },
    "Star"  : {
        "1" : irange(0, 80),
        "2" : irange(81, 85),
        "4" : irange(86, 89),
        "8" : irange(90, 91),
        "12" : irange(92, 93),
        "16" : irange(94, 95),
        "20" : irange(96, 96),
        "30" : irange(97, 97),
        "50" : irange(98, 98),
        "80" : irange(99, 99)
    },
    "Superstar": {
        "1" : irange(0, 85),
        "2" : irange(86, 89),
        "4" : irange(90, 91),
        "8" : irange(92, 93),
        "12" : irange(94, 95),
        "16" : irange(96, 96),
        "20" : irange(97, 97),
        "40" : irange(98, 98),
        "65" : irange(99, 99)
    },
    "Elite": {
        "1" : irange(0, 89),
        "2" : irange(90, 91),
        "4" : irange(92, 93),
        "8" : irange(94, 95),
        "12" : irange(96, 96),
        "16" : irange(97, 97),
        "30" : irange(98, 98),
        "50" : irange(99, 99)
    }
}

def getCostOfUpgrade(rating_current_level, amount, dev_trait):
    rating_new_level = rating_current_level + amount
    cost = 0
    for level in irange(rating_current_level + 1, rating_new_level):
        for points, level_range in upgrade_table[dev_trait].items():
            if int(level) in level_range:
                cost = cost + int(points)
                print(points)
    return cost

def maxContract(ovr : int, age : int):
    length = 1
    if ovr <=70:
        if age <= 28:
            length = 2
        else:
            length = 1
    elif ovr <= 75:
        if age <= 30:
            length = 2
        else:
            length = 1
    elif ovr <= 80:
        if age <= 29:
            length = 3
        elif age <= 32:
            length = 2
        else:
            length = 1
    elif ovr <= 85:
        if age <= 26:
            length = 4
        elif age <= 30:
            length = 3
        elif age <= 34:
            length = 2
        else:
            length = 1
    elif ovr >= 86:
        if age <= 26:
            length = 5
        elif age <= 28:
            length = 4
        elif age <= 31:
            length = 3
        elif age <= 36:
            length = 2
        else:
            length = 1
    return length

valid_positions = [
    "QB",
    "RB",
    "FB",
    "TE",
    "WR",
    "LT",
    "LG",
    "C",
    "RG",
    "RT",
    "DE",
    "DT",
    "MLB",
    "OLB",
    "SS",
    "FS",
    "CB",
    "K",
    "P"
]

oline_positions = ["RT", "RG", "LT", "LG", "C"]
db_positions = ['FS', "SS", "CB"]

reassignments = {
    "QB" : [],
    "RB" : ["FB", "WR"],
    "FB" : ["TE"],
    "WR" : ["RB"],
    "TE" : ["FB"],
    "DE" : ["DT", "OLB"],
    "DT" : ["DE"],
    "OLB" : ["DE", "MLB"],
    "MLB" : ["OLB"],
    "K" : [],
    "P" : []
}


#bio_info = ["Age", "Exp"]

statuses = {
    "Injured" : "I",
    "Active" : "A",
    "Practice Squad" : "PS",
    "Free Agent" : "FA"
}

status_emojis = {
    "Active" : "🟢",
    "Injured" : "🔴",
    "Practice Squad" : "🟡",
    "Free Agent" : "🔵"
}

status_emojis_alt = {
    "Active" : "🏃",
    "Injured" : "🤕",
    "Practice Squad" : "🟡",
    "Free Agent" : "🔵"
}

stat_sheet_names = [
    "Passing",
    "Rushing",
    "Receiving",
    "Defensive",
    "Return",
    "Kicking"
]