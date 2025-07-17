import streamlit as st
import pandas as pd
import global_vars
import functions

st.set_page_config(layout="wide")
st.title("Draft Picks")
st.divider()

# Get the draft picks 
picks = functions.bq_query("SELECT * FROM `mfl-374514.dbt_production.dim_draft_picks`")
picks_df = pd.DataFrame(picks)
picks_df[["year", "round_num", "pick_num"]] = picks_df[["year", "round_num", "pick_num"]].apply(pd.to_numeric, downcast="integer")

# Optionally, fill NaN values if any (you can fill them with 0 or another value, or drop them)
picks_df["pick_num"] = picks_df["pick_num"].fillna(0).astype(int)

# Get the list of teams
teams = functions.bq_query("SELECT franchise_id, franchise_name, division, icon FROM `mfl-374514.dbt_production.dim_franchises`")
teams_df = pd.DataFrame(teams)

picks_clean = picks_df.drop(["pick_owner"], axis = 1).rename(columns={"year": "Year", "round_num": "Round", "pick_num": "Pick"}).sort_values(["Year", "Round"])

# Create filters    
team_select = st.multiselect(
    'Choose the Teams',
    sorted(teams_df["franchise_name"].unique()),
    sorted(teams_df["franchise_name"].unique()),
    help = "Filter the picks for specific rounds.")

year_select = st.multiselect(
    'Choose the Years',
    sorted(picks_df["year"].unique()),
    sorted(picks_df["year"].unique()),
    help = "Filter the picks for specific draft years.")

round_select = st.multiselect(
    'Choose the Round',
    sorted(picks_df["round_num"].unique()),
    sorted(picks_df["round_num"].unique()),
    help = "Filter the picks for specific rounds.")

grid_row_count = 6
grid_col_count = 2

mygrid = global_vars.make_grid(grid_row_count,grid_col_count)

#Table style
st.html("<style>  thead tr th:first-child {display:none}tbody th {display:none} ")

selected_team_names = team_select

# Flatten the grid for easier and safer iteration
grid_cells = [col for row in mygrid for col in row]

# Iterate over the selected teams and the grid cells at the same time.
# zip() gracefully stops when it runs out of teams or grid cells.
for team_name, cell in zip(selected_team_names, grid_cells):
    
    # Find the team's full details using its name
    team_info = teams_df.loc[teams_df["franchise_name"] == team_name]

    # Ensure the team was actually found before proceeding
    if not team_info.empty:
        # Extract the ID and icon URL from the found data
        franchise_id = team_info["franchise_id"].values[0]
        icon_url = team_info["icon"].values[0]
        
        # 1. Populate the subheader and image in the cell
        cell.subheader(team_name, divider=True)
        cell.image(icon_url)

        # 2. Use the correct franchise_id to filter the picks
        filtered_picks = picks_clean.loc[
            (picks_df["pick_owner"] == franchise_id) &
            (picks_df["year"].isin(year_select)) &
            (picks_df["round_num"].isin(round_select))
        ]
        
        # 3. Display the filtered table of picks
        cell.table(filtered_picks)
