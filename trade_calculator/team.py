import requests
from itertools import combinations

BASE_URL = "https://api.sleeper.app/v1"
players = requests.get(f"{BASE_URL}/players/nfl").json()

class Team:
    def __init__(self, roster, user, league_id):
        self.league_id = league_id
        self.roster_id = roster["roster_id"]
        self.owner_id = roster["owner_id"]
        self.name = user.get("metadata", {}).get("team_name") or user["display_name"]
        self.wins = roster["settings"]["wins"]
        self.losses = roster["settings"]["losses"]
        self.week = self.wins + self.losses + roster["settings"]["ties"]
        self.roster = []
        for player_id in roster["players"]:
            if player_id and player_id in players:
                self.roster.append(players[player_id])
        self.starters = []
        for player_id in roster["starters"]:
            if player_id and player_id in players:
                self.starters.append(players[player_id])
    
    def get_all_projections(self, season, week):
          res = requests.get(f"https://api.sleeper.com/projections/nfl/{season}/{week}?season_type=regular")
          res.raise_for_status()
          return {p["player_id"]: p for p in res.json()}
    
    def get_my_projections(self, season, week):
        res = requests.get(f"https://api.sleeper.com/projections/nfl/{season}/{week}?season_type=regular")
        res.raise_for_status()
        projections = res.json()
        projections_by_id = {p["player_id"]: p for p in projections}
        my_projections = {}
        for player in self.roster:
            player_id = player["player_id"]
            my_projections[player_id] = projections_by_id.get(player_id, {})
        return my_projections
    
    def get_player_value(self,player,projections,league_avgs,league):
        pos = player["position"]
        if pos not in league_avgs:
            return 0
        pts = projections.get(player["player_id"], {}).get("stats", {}).get("pts_ppr", 0)
        league_avg = league_avgs[pos]
        if league_avg == 0:
            return 0
        
        age_multiplier = 1 
        prime_ages = {"QB": 29, "RB": 26, "WR": 28, "TE": 29  }
        if league.type == 2: 
            age = player['age'] 
            if age is None: 
                age_multiplier = 1
            else: 
                age_multiplier = prime_ages[pos]/age

        return age_multiplier * (pts / league_avg) 

    def package_value(self, player_values):
        sorted_vals = sorted(player_values, reverse=True)
        total = 0
        for i, val in enumerate(sorted_vals):
            total += val * (0.7 ** i)  # each extra player worth 70% of previous
        return total
    
    def get_needs(self,league,projections): 
        
        totals = {"QB": 0, "RB": 0, "WR": 0, "TE": 0}
        counts = {"QB": 0, "RB": 0, "WR": 0, "TE": 0}
    
        for player in self.starters:
            pos = player["position"]
            if pos in totals:
                proj = projections.get(player["player_id"], {})
                totals[pos] += proj.get("stats", {}).get("pts_ppr", 0)
                counts[pos] += 1
    
        my_qb_avg = totals["QB"] / counts["QB"] if counts["QB"] > 0 else 0
        my_rb_avg = totals["RB"] / counts["RB"] if counts["RB"] > 0 else 0
        my_wr_avg = totals["WR"] / counts["WR"] if counts["WR"] > 0 else 0
        my_te_avg = totals["TE"] / counts["TE"] if counts["TE"] > 0 else 0
        my_avgs = {"QB": my_qb_avg, "RB": my_rb_avg, "WR": my_wr_avg, "TE": my_te_avg}
        
        my_depth = {"QB": 0, "RB": 0, "WR": 0, "TE": 0}
        for player in self.roster:
            pos = player["position"]
            if pos in my_depth:
                my_depth[pos] += 1

        league_depth = {pos: league.get_depth(pos) for pos in ["QB", "RB", "WR", "TE"]}
        league_avgs = {pos: league.get_starter_avg(pos,projections) for pos in ["QB", "RB", "WR", "TE"]}

        needs = []
        surplus = []
        for pos, my_avg in my_avgs.items():
            league_avg = league_avgs[pos]
            if (my_avg < league_avg * 0.85 and my_depth[pos] < league_depth[pos]-1) or my_depth[pos] == 0:
                needs.append(pos)
            elif (my_avg > league_avg * 1.20 and my_depth[pos]>counts[pos]) or (my_depth[pos] > league_depth[pos]+1 and my_avg > league_avg * 0.85):
                surplus.append(pos)
        
        return {"needs": needs, "surplus": surplus}
    
    def trade(self, pos_want, pos_give, league): 
        projections = self.get_all_projections("2025", 3)
        league_avgs = {pos: league.get_starter_avg(pos, projections) for pos in ["QB", "RB", "WR", "TE"]}
       
        my_needs = self.get_needs(league,projections)
        skill_pos = {"QB","RB","WR","TE"}
        if pos_want in skill_pos and pos_want not in my_needs["needs"]: 
            my_needs["needs"].append(pos_want)
        if pos_give in skill_pos and pos_give not in my_needs["surplus"]: 
            my_needs["surplus"].append(pos_give)
        
        all_offers = {}
        for team in league.teams:
            if team.owner_id == self.owner_id:
                continue
            their_needs = team.get_needs(league,projections)
            
            get = [pos for pos in my_needs["needs"] if pos in their_needs["surplus"]]
            give = [pos for pos in my_needs["surplus"] if pos in their_needs["needs"]]
        
            their_tradeable = [p for p in team.roster if p["position"] in get]
            my_tradeable = [p for p in self.roster if p["position"] in give]
            trade_offers = []

            for their_player in their_tradeable: 
                their_value = self.get_player_value(their_player, projections, league_avgs, league)
                for size in range(1,4): 
                    for combo in combinations(self.roster,size):
                         my_values = [self.get_player_value(p, projections, league_avgs, league) for p in combo]
                         my_pkg_value = self.package_value(my_values)
                         if their_value == 0: 
                             continue
                         if abs(my_pkg_value - their_value) / their_value < 0.10:
                             trade_offers.append({
                            "give": [p["first_name"] + " " + p["last_name"] for p in combo],
                            "get": their_player["first_name"] + " " + their_player["last_name"],
                            "value": round(their_value - my_pkg_value, 2)
                            })
            for my_player in my_tradeable:
                my_value = self.get_player_value(my_player, projections, league_avgs, league)
                for size in range(1, 4):
                    for combo in combinations(team.roster, size):
                        their_values = [self.get_player_value(p, projections, league_avgs, league) for p in combo]
                        their_pkg_value = self.package_value(their_values)
                        if my_value == 0:
                            continue
                        if abs(their_pkg_value - my_value) / my_value < 0.10:
                            trade_offers.append({
                            "give": my_player["first_name"] + " " + my_player["last_name"],
                            "get": [p["first_name"] + " " + p["last_name"] for p in combo],
                            "value": round(their_pkg_value - my_value,2)
                            })
            unique = []
            for offer in trade_offers:
                if offer not in unique:
                    unique.append(offer)
            all_offers[team.name] = unique
        return all_offers