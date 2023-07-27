import numpy as np
import pandas as pd
import streamlit as st
import requests
import json
import config
import global_vars

site_token = config.key

st.set_page_config(layout="wide")
st.title("Draft Picks")
st.markdown("""<hr style="height:10px;border:none;color:#333;background-color:#333;" /> """, unsafe_allow_html=True)

# Get the list of teams
r = requests.get(url = global_vars.franchises_URL, headers={'Authorization': 'Bearer ' + site_token }) 
franchises = r.json()
keep_cols = ["mfl_id", "division", "franchise_name", "icon_url"]
df_franchises = pd.DataFrame(franchises)[keep_cols]

# Get the draft picks from the API
r = requests.get(url = global_vars.picks_URL, headers={'Authorization': 'Bearer ' + site_token }) 
data = r.json()["futureDraftPicks"]["franchise"]

picks = []

for team in data:
  for pick in team["futureDraftPick"]:
    pick["id"] = team["id"]
    picks.append(pick)

picks_df = pd.DataFrame(picks)
picks_df[["year", "round"]] = picks_df[["year", "round"]].apply(pd.to_numeric)

# Create filters    
year_select = st.multiselect(
    'Choose the Years',
    sorted(picks_df["year"].unique()),
    sorted(picks_df["year"].unique()),
    help = "Filter the picks for specific draft years.")

round_select = st.multiselect(
    'Choose the Round',
    sorted(picks_df["round"].unique()),
    sorted(picks_df["round"].unique()),
    help = "Filter the picks for specific rounds.")

picks_clean = picks_df.drop(["id", "originalPickFor"], axis = 1).rename(columns={"year": "Year", "round": "Round"}).sort_values(["Year", "Round"])[["Year", "Round"]]

#Table style
hide_table_row_index = """
            <style>
            thead tr th:first-child {display:none}
            tbody th {display:none}
            """
st.markdown(hide_table_row_index, unsafe_allow_html=True)

# Page Grid layout
def make_grid(cols,rows):
    grid = [0]*cols
    for i in range(cols):
        with st.container():
            grid[i] = st.columns(rows)
    return grid

grid_row_count = 6
grid_col_count = 2

mygrid = make_grid(grid_row_count,grid_col_count)

# Populating the grid with data
id_list = df_franchises["mfl_id"].unique()
i = 0
for row_num in list(range(grid_row_count)):
    for col_num in list(range(grid_col_count)):
        mygrid[row_num][col_num].title(df_franchises.loc[df_franchises["mfl_id"] == id_list[i]]["franchise_name"].values[0])
        mygrid[row_num][col_num].image(df_franchises.loc[df_franchises["mfl_id"] == id_list[i]]["icon_url"].values[0])
        mygrid[row_num][col_num].table(picks_clean.loc[(picks_df["id"] == id_list[i]) & (picks_df["year"].isin(year_select)) & (picks_df["round"].isin(round_select))])

        i +=1
      
