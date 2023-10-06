import pandas as pd
import streamlit as st
import requests
import json
import config
import api_calls
import global_vars

st.set_page_config(layout="wide")
st.title("Annual Free Extension Eligibility")
st.markdown("""<hr style="height:10px;border:none;color:#333;background-color:#333;" /> """, unsafe_allow_html=True)

# Get the list of teams
franchises = api_calls.get_teams()
keep_cols = ["mfl_id", "division", "franchise_name", "icon_url"]
df_franchises = pd.DataFrame(franchises)[keep_cols]

team = st.selectbox(
    '**Which Team is Extending a Player?**', [""] + sorted(df_franchises["franchise_name"].unique()))

# Get the current rosters
rosters = api_calls.get_rosters()
keep_cols = ["mfl_id", "franchise_name", "salary", "contract_years", "status"]
rosters_df = pd.DataFrame(rosters)[keep_cols]
rosters_df['mfl_id'] = rosters_df['mfl_id'].astype(str)

# Get player metadata
players = api_calls.get_players_wr()
keep_cols = ["position", "mfl_id", "first_name", "last_name"]
players_df = pd.DataFrame(players)[keep_cols]
players_df["mfl_id"] = players_df["mfl_id"].astype(str)

# Join player dfs
players_df1 = rosters_df.merge(players_df, how = 'left', on = 'mfl_id')

players_df1['position_order'] = players_df1['position'].map(global_vars.sort_mapping['index'])
filtered_df = players_df1.loc[(players_df1["franchise_name"] == team) & ((players_df1["contract_years"]) == 1)]
filtered_df = filtered_df.rename(columns={"first_name": "First Name", "last_name": "Last Name","position": "Position", "salary": "Salary "}).sort_values('position_order')

st.write("**Here is who is eligible to be extended**")
# Table style
st.markdown(global_vars.hide_table_row_index, unsafe_allow_html=True)

table_cols = ["First Name", "Last Name", "Position", "Salary "]
filtered_df["Salary "] = filtered_df["Salary "].apply("${:,.2f}".format)
st.dataframe(filtered_df[table_cols], use_container_width=True, hide_index=True)



