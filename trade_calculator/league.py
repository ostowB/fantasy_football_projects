import requests
from team import Team

BASE_URL = "https://api.sleeper.app/v1"

class League:
    def __init__(self, league_id):
        self.league_id = league_id
        data = requests.get(f"{BASE_URL}/league/{league_id}").json()
        self.name = data["name"]
        self.type = data["settings"]["type"]
        self.total_rosters = data["total_rosters"]
        self.scoring_settings = data["scoring_settings"]
        self.roster_positions = data["roster_positions"]
        self.playoff_week_start = data["settings"]["playoff_week_start"]
        self.trade_deadline = data["settings"]["trade_deadline"]
        self.season = data["season"]

        rosters = requests.get(f"{BASE_URL}/league/{league_id}/rosters").json()
        users = requests.get(f"{BASE_URL}/league/{league_id}/users").json()
        user_map = {u["user_id"]: u for u in users}

        self.teams = [Team(r, user_map[r["owner_id"]],self.league_id) for r in rosters if r["owner_id"] in user_map]

    def get_team_by_username(self, username):
        res = requests.get(f"{BASE_URL}/user/{username}").json()
        user_id = res["user_id"]
        return next((t for t in self.teams if t.owner_id == user_id), None)

    def get_team_by_roster_id(self, roster_id):
        return next((t for t in self.teams if t.roster_id == roster_id), None)
    
    def get_starter_avg(self, pos, projections): 
        total = 0
        count = 0
        for team in self.teams:
            for player in team.starters:
                if player["position"] == pos:
                    proj = projections.get(player["player_id"], {})
                    total += proj.get("stats", {}).get("pts_ppr", 0)
                    count += 1
        return total / count if count > 0 else 0
    
    def get_depth(self, pos): 
        total = 0 
        num_teams = 0
        for team in self.teams:
            num_teams+=1
            for player in team.roster:
                if player["position"] == pos:
                    total += 1
        return total / num_teams