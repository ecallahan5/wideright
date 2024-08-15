import streamlit as st
import pandas as pd
import global_vars
import functions

st.set_page_config(layout="wide")
st.title("Draft Picks")
st.divider()

# Get the draft picks 
picks = functions.bq_query("SELECT * FROM `mfl-374514.dbt_production.fct_draft_picks`")
picks_df = pd.DataFrame(picks)
picks_df[["year", "round_num", "pick_num"]] = picks_df[["year", "round_num", "pick_num"]].apply(pd.to_numeric, downcast="integer")

# Get the list of teams
teams = functions.bq_query("SELECT franchise_id, franchise_name, division, icon FROM `mfl-374514.dbt_production.fct_franchises`")
teams_df = pd.DataFrame(teams)

picks_clean = picks_df.drop(["pick_owner"], axis = 1).rename(columns={"year": "Year", "round_num": "Round", "pick_num": "Pick"}).sort_values(["Year", "Round"])

# Create filters    
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

# Populating the grid with data
id_list = teams_df["franchise_id"].unique()
i = 0
for row_num in list(range(grid_row_count)):
    for col_num in list(range(grid_col_count)):
        mygrid[row_num][col_num].subheader(teams_df.loc[teams_df["franchise_id"] == id_list[i]]["franchise_name"].values[0], divider = True)
        mygrid[row_num][col_num].image(teams_df.loc[teams_df["franchise_id"] == id_list[i]]["icon"].values[0])
        mygrid[row_num][col_num].table(picks_clean.loc[(picks_df["pick_owner"] == id_list[i]) & (picks_df["year"].isin(year_select)) & (picks_df["round_num"].isin(round_select))])

        i +=1








      
