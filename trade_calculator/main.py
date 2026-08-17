from league import League

LEAGUE_ID = 1314415651854483456
USERNAME = "boffk17"

league = League(LEAGUE_ID)
my_team = league.get_team_by_username(USERNAME)

print(my_team.trade(None,None,league))

