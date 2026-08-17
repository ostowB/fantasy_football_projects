import requests
from openpyxl import Workbook

positions = ["QB", "RB", "WR", "TE"]
season = 2026

# Makes dicts with projections by position group
all_data = {}

for pos in positions:
    url = f"https://api.sleeper.com/projections/nfl/{season}?season_type=regular&position[]={pos}&order_by=adp_ppr"

    response = requests.get(url)
    data = response.json()

    # Filter out players with no real ADP (placeholder 999.0)
    ranked = [p for p in data if p['stats'].get('adp_ppr', 999) < 999]

    # Sort just to be safe, since API sort can be inconsistent
    ranked.sort(key=lambda p: p['stats'].get('adp_ppr', 999))

    all_data[pos] = ranked


# Create Excel workbook
wb = Workbook()

# Remove the default sheet
default_sheet = wb.active
wb.remove(default_sheet)


# Create one sheet for each position
for pos in positions:
    ws = wb.create_sheet(pos)

    # Different columns depending on position
    if pos == "QB":
        ws.append([
            "Rank",
            "Player",
            "ADP",
            "PPR Points",
            "Passing Yards",
            "Passing TDs"
        ])

    elif pos == "RB":
        ws.append([
            "Rank",
            "Player",
            "ADP",
            "PPR Points",
            "Rushing Yards",
            "Rushing TDs"
        ])

    else:  # WR and TE
        ws.append([
            "Rank",
            "Player",
            "ADP",
            "PPR Points",
            "Receiving Yards",
            "Receiving TDs"
        ])

    # Add players
    for rank, player in enumerate(all_data[pos], start=1):
        stats = player['stats']

        name = f"{player['player']['first_name']} {player['player']['last_name']}"
        adp = stats.get('adp_ppr', None)
        pts = stats.get('pts_ppr', None)

        # QB
        if pos == "QB":
            yards = stats.get('pass_yd', 0)
            tds = stats.get('pass_td', 0)

        # RB
        elif pos == "RB":
            yards = stats.get('rush_yd', 0)
            tds = stats.get('rush_td', 0)

        # WR and TE
        else:
            yards = stats.get('rec_yd', 0)
            tds = stats.get('rec_td', 0)

        ws.append([
            rank,
            name,
            adp,
            pts,
            yards,
            tds
        ])

    # Make columns wider
    ws.column_dimensions["A"].width = 10
    ws.column_dimensions["B"].width = 25
    ws.column_dimensions["C"].width = 12
    ws.column_dimensions["D"].width = 15
    ws.column_dimensions["E"].width = 18
    ws.column_dimensions["F"].width = 15


# Save the Excel file
wb.save("sleeper_2026_projections.xlsx")

print("Excel file created: sleeper_2026_projections.xlsx")