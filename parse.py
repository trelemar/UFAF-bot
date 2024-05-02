def removeSpaces(string): return string.replace(" ", "")

def removeSpacesAndPeriods(string): 
    string = string.replace(" ", "")
    string = string.replace(".", "")
    return string

def weeksStrToList(weeks_string):
    weeks_string = str(weeks_string)
    weeks_list = [*weeks_string]
    for index, value in enumerate(weeks_list):
        try:
            weeks_list[index] = int(value)
        except:
            pass
        if value == "0" or value == 0: weeks_list[index] = 10
        elif value == "a": weeks_list[index] = 11
        elif value == "b": weeks_list[index] = 12
        elif value == "c": weeks_list[index] = 13
        elif value == "d": weeks_list[index] = 14
    return weeks_list

def weeksListToStr(weeks_list):
    weeks_string = ""
    for value in weeks_list:
        if value == 10: value = str("0")
        elif value == 11: value = "a"
        elif value == 12: value = "b"
        elif value == 13: value = "c"
        elif value == 14: value = "d"
        weeks_string = weeks_string + str(value)
    return weeks_string

def ordinal(n: int):
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    else:
        suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
    return str(n) + suffix