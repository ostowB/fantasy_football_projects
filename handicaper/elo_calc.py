#differentials dictionary contains entries for each user id which contain an 
#array of arrays each giving a league name/year and the adjusted differential from it
#username_differentials, handicaps, and avg_differentials are all arrays where each 
#index is a new user and all the lists are linked

import json
import statistics
from helpers import get_user
from helpers import z_to_percentile

with open("league.json") as f:
    league_cache = json.load(f)
with open("users.json") as f:
    user_cache = json.load(f)

differentials = {}
year = 2017
current_year = 2026

#loops through all leagues in the csv
while year<current_year:
    yearly_differentials = {}
    for league in league_cache.values(): 
        #makes sure we are going year by year chronologically
        if league["year"] == str(year): 
            league_strength = 0
            league_members = 0
            #calculate member strength and then league strength
            for id in league["z"]: 
                if id in differentials: 
                    scores = [entry[0] for entry in differentials[id]]
                    league_strength += statistics.mean(scores)
                else: 
                    league_strength+=0
                league_members+=1
            league_strength/=league_members
            #adds to yearly differentials based on sum of league strength and z-score
            for id in league["z"]: 
                if id not in yearly_differentials: 
                    yearly_differentials[id] = []
                yearly_differentials[id].append([league_strength + league["z"][id],league["name"],league["year"]])
    #copies yearly differentials into permanent differentials
    for id in yearly_differentials: 
        if id not in differentials: 
            differentials[id] = []
        for d in yearly_differentials[id]: 
            differentials[id].append(d)
    year+=1

#gets the avg_differentials and handicaps and useranmes for all players
username_differentials = []
avg_differential = []
handicaps = []
for d in differentials: 
    username_differentials.append(get_user(user_id = d)["username"])
    scores = [entry[0] for entry in differentials[d]]
    avg_differential.append(statistics.mean(scores))
    last_ten = scores[-10:]
    best_five = sorted(last_ten, reverse = True)[:5]
    handicaps.append(statistics.mean(best_five))

eight_sdcounter = 0
eight_sum = 0 
ten_sdcounter = 0
ten_sum = 0 
twelve_sdcounter = 0
twelve_sum = 0 
twenty_sdcounter = 0
twenty_sum = 0 
thirty_sdcounter = 0
thirty_sum = 0 
for league in league_cache.values():
    size = len(league["z"])
    if size<=8: 
        eight_sdcounter += league["sd"]
        eight_sum += 1
    elif size==10: 
        ten_sdcounter += league["sd"]
        ten_sum += 1
    elif size==12: 
        twelve_sdcounter += league["sd"]
        twelve_sum += 1
    elif size<=24: 
        twenty_sdcounter += league["sd"]
        twenty_sum += 1
    else: 
        thirty_sdcounter += league["sd"]
        thirty_sum += 1

eight_sdcounter/=eight_sum
ten_sdcounter/=ten_sum
twelve_sdcounter/=twelve_sum
twenty_sdcounter/=twenty_sum
thirty_sdcounter/=thirty_sum

def calculate_matchup(user1, user2, league_size):
    index1 = None
    index2 = None
    for i in range (len(username_differentials)): 
        if username_differentials[i] == user1: 
            index1=i
        if username_differentials[i] == user2: 
            index2=i
    difference = handicaps[index1] - handicaps[index2]
    if league_size<=8: 
        return (difference * eight_sdcounter)/14
    if league_size == 10: 
        return (difference * ten_sdcounter)/14
    if league_size == 12: 
        return (difference * twelve_sdcounter)/14
    if league_size <=24: 
        return (difference * twenty_sdcounter)/14
    else: 
        return (difference * thirty_sdcounter)/14

#prints all handicaps and avgs 
#for i in range (len(username_differentials)): #
    #print(f"{username_differentials[i]} {avg_differential[i]} {handicaps[i]}")

#prints all of one users differentials and labeled by league
#print(differentials[get_user(username = "MrSpleen")["user_id"]])

#tells you how many points player 1 should give player 2 per week
#print(calculate_matchup("boffk17","mrspleen",10))