import requests
from openpyxl import Workbook

positions = ["RB", "WR", "TE"]
season = 2026

# Get projections for RB, WR, and TE
all_players = []

for pos in positions:
    url = f"https://api.sleeper.com/projections/nfl/{season}?season_type=regular&position[]={pos}&order_by=adp_ppr"

    response = requests.get(url)
    data = response.json()

    # Filter out players with no real ADP
    ranked = [p for p in data if p["stats"].get("adp_ppr", 999) < 999]

    # Add position
    for player in ranked:
        player["position"] = pos

    all_players.extend(ranked)


# Sort all FLEX players together by ADP
all_players.sort(key=lambda p: p["stats"].get("adp_ppr", 999))


# Create Excel workbook
wb = Workbook()
ws = wb.active
ws.title = "Flex Rankings"


# Headers
ws.append([
    "Rank",
    "Player",
    "Position",
    "ADP",
    "PPR Points",
    "Yards",
    "TDs"
])


# Add players
for rank, player in enumerate(all_players, start=1):

    stats = player["stats"]
    pos = player["position"]

    name = f"{player['player']['first_name']} {player['player']['last_name']}"

    adp = stats.get("adp_ppr", None)
    pts = stats.get("pts_ppr", None)

    # RB = rushing stats
    if pos == "RB":
        yards = stats.get("rush_yd", 0)
        tds = stats.get("rush_td", 0)

    # WR/TE = receiving stats
    else:
        yards = stats.get("rec_yd", 0)
        tds = stats.get("rec_td", 0)

    ws.append([
        rank,
        name,
        pos,
        adp,
        pts,
        yards,
        tds
    ])


# Make columns wider
ws.column_dimensions["A"].width = 10
ws.column_dimensions["B"].width = 25
ws.column_dimensions["C"].width = 12
ws.column_dimensions["D"].width = 12
ws.column_dimensions["E"].width = 15
ws.column_dimensions["F"].width = 18
ws.column_dimensions["G"].width = 15


# Save
wb.save("sleeper_2026_flex_rankings.xlsx")

print("Excel file created: sleeper_2026_flex_rankings.xlsx")