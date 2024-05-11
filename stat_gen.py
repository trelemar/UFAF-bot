import os
import pandas
import data
import sys


def main():

	stat_path = sys.argv[1]
	out_path = sys.argv[2]
	#stat_path = "/mnt/rasp/stat_logs/s1/"
	players = data.pull_csv(stat_path + "../../ROSTER.csv")
	p_dict = {}
	teams = data.pull_csv(f'{stat_path}../../TEAMS.csv')

	team_table = {}
	for team in teams:
		team_table[team["ID"]] = team


	stat_files = []
	for i in os.listdir(stat_path):
		if not os.path.isdir(i):
			stat_files.append(i)

	print(stat_files)

	stat_data = []
	week_stats = []
	for f in stat_files:
		team_abv = f.split()[0]
		print(team_abv)
		game_stats = pandas.read_csv(f'{stat_path}{f}').to_dict("records")
		print(game_stats[0])
		for k, team in team_table.items():
			if team_abv == team["ABV"]: 
				team_id = team["ID"]
				for p in game_stats:
					#p["TEAMID"] = team_id
					pid = None
					for prec in players:
						if p["FirstName"] == prec["FIRST"].upper() and p["LastName"] == prec["LAST"].upper() and prec["TEAMID"] == team_id:
							pid = prec["INDEX"]
					p = {"PID" : pid, "TEAMID" : team_id, **p}
					week_stats.append(p)
				#print(team_id)

	data.push_csv(week_stats, out_path)


if __name__ == "__main__":
	main()