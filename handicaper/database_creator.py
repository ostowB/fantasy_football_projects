#add usernames to the array "names" to add more data to the database
#Doing so will add all users the new user has played with and all of their leagues
#leagues.json will store league information and user z-scores in each league
#users.json will save a username and user id

import requests
import json
import statistics
from helpers import get_user

current_year = 2026
names = ["boffk17","MrSpleen","baseballguy545","chiefs73351"]
my_league_ids = []

#writing all users to json file
try:
    with open("users.json", "r") as f:
        user_cache = json.load(f)
except FileNotFoundError:
    user_cache = {}

#loops through all of a users leagues and grabs the id nums
for name in names: 
    for year in range(2017,current_year+1):
        yearly_leagues = requests.get(f"https://api.sleeper.app/v1/user/" + get_user(username = name)["user_id"] + "/leagues/nfl/" + str(year)).json()
        for leagues in yearly_leagues: 
            if leagues["league_id"] not in my_league_ids:
                my_league_ids.append(leagues["league_id"])

#loops through leagues and writes player ids into json
for league in my_league_ids: 
    league_users = requests.get(f"https://api.sleeper.app/v1/league/" + league + "/users").json()
    for user in league_users: 
        if user["user_id"] in user_cache:
            continue
        else: 
            data = get_user(user_id = user["user_id"])
            user_cache[user["user_id"]] = {
                "username": data["username"],
                "user_id": data["user_id"]
            }
with open("users.json", "w") as f:
    json.dump(user_cache, f, indent=4)

#writes all leagues into json file
try:
    with open("league.json", "r") as f:
        league_cache = json.load(f)
except FileNotFoundError:
    league_cache = {}

#does this for every league in database
for i in my_league_ids: 
    roster_data = requests.get(f"https://api.sleeper.app/v1/league/" + i + "/rosters").json()
    league_data = requests.get(f"https://api.sleeper.app/v1/league/" + i).json()
    scores = []

    #creating avg/sd summary stats + basic league data 
    #real count makes sure there are at least 4 non-orphan teams
    real_count = 0
    for roster in roster_data: 
        if roster["owner_id"] is not None:
            real_count +=1
        scores.append(roster["settings"]["fpts"])
    avg = statistics.mean(scores)
    sd = statistics.pstdev(scores)

    #skips leagues that didn't play or had <4 members
    if avg == 0 or real_count < 4: 
        continue
    
    league_cache[i] = {
        "avg_score": avg,  
        "sd":sd,
        "name": league_data["name"],
        "year": league_data["season"],
        "z":{}
    }

    #save z score for each roster 
    for roster in roster_data: 
        fpts = roster["settings"]["fpts"]
        if sd == 0: 
            z = 0
        else: 
            z = (fpts-avg)/sd
        league_cache[i]["z"][roster["owner_id"]] = z

with open("league.json", "w") as f:
    json.dump(league_cache, f, indent=4)

print()
print("LEAGUE AND USER DATA UPDATED")
print()