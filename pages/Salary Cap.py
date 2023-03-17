import numpy as np
import pandas as pd
import streamlit as st
import requests
import json
import config
import global_vars


site_token = config.key

st.set_page_config(layout="wide")
st.title("Salary Cap")
st.markdown("""<hr style="height:10px;border:none;color:#333;background-color:#333;" /> """, unsafe_allow_html=True)

# Get the list of teams
r = requests.get(url = global_vars.franchises_URL, headers={'Authorization': 'Bearer ' + site_token }) 
franchises = r.json()
keep_cols = ["mfl_id", "division", "franchise_name", "icon_url"]
df_franchises = pd.DataFrame(franchises)[keep_cols]

# Get the current rosters
r = requests.get(url = global_vars.rosters_URL, headers={'Authorization': 'Bearer ' + site_token }) 
rosters = r.json()
keep_cols = ["mfl_id", "franchise_name", "salary", "contract_years", "status"]
rosters_df = pd.DataFrame(rosters)[keep_cols]
rosters_df['mfl_id'] = rosters_df['mfl_id'].astype(str)

# Get player metadata
r = requests.get(url = global_vars.players_url) 
players = r.json()["players"]["player"]
keep_cols = ["position", "id", "name"]
players_df = pd.DataFrame(players)[keep_cols]

# Join player dfs
players_df1 = rosters_df.merge(players_df, how = 'left', left_on = 'mfl_id', right_on = 'id').drop(['id'], axis=1)

col1, col2 = st.columns(2)

with col1:
    # Team picker
    team = st.selectbox(
        ' Choose a team',
        sorted(players_df1["franchise_name"].unique()))
    
with col2:
    # Year Picker
        year = st.selectbox(
        'Choose a league year',
        global_vars.yr_list)

contract_yrs = global_vars.zipped_df.loc[global_vars.zipped_df["Year"] == year]["Contract Length"].values[0]
filtered_df = players_df1.loc[(players_df1["franchise_name"] == team) & ((players_df1["contract_years"]) >= contract_yrs)]

cap_used = filtered_df["salary"].sum()
contract_yrs_used = filtered_df["contract_years"].sum()
roster_spots_used = filtered_df["mfl_id"].count()

cap_space = "${:,.2f}".format(global_vars.salary_cap - cap_used)
contract_yrs_free = global_vars.contract_cap - contract_yrs_used
roster_spots_free = global_vars.roster_size - roster_spots_used

col1, col2, col3 = st.columns(3)
col1.metric("Cap Space", cap_space)
col2.metric("Contract Years Free", contract_yrs_free)
col3.metric("Roster Spots Free", roster_spots_free)



