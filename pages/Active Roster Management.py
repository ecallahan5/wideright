import numpy as np
import pandas as pd
import streamlit as st
import requests
import json
import plotly.express as px
import config
import global_vars
import api_calls

site_token = config.key

st.set_page_config(layout="wide")
st.title("Roster Construction")
st.markdown("""<hr style="height:10px;border:none;color:#333;background-color:#333;" /> """, unsafe_allow_html=True)

# Get the list of teams

franchises = api_calls.get_teams()
keep_cols = ["mfl_id", "division", "franchise_name", "icon_url"]
df_franchises = pd.DataFrame(franchises)[keep_cols]

# Get the current rosters
rosters = api_calls.get_rosters()
keep_cols = ["mfl_id", "franchise_name", "salary", "contract_years", "status"]
rosters_df = pd.DataFrame(rosters)[keep_cols]
rosters_df['mfl_id'] = rosters_df['mfl_id'].astype(str)

# Get player metadata
r = requests.get(url = global_vars.players_URL) 
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

st.markdown("""<hr style="height:10px;border:none;color:#333;background-color:#333;" /> """, unsafe_allow_html=True)

contract_yrs = global_vars.zipped_df.loc[global_vars.zipped_df["Year"] == year]["Contract Length"].values[0]
filtered_df = players_df1.loc[(players_df1["franchise_name"] == team) & ((players_df1["contract_years"]) >= contract_yrs)]
filtered_df["salary1"] = filtered_df["salary"].apply("${:,.2f}".format)
filtered_df['position_order'] = filtered_df['position'].map(global_vars.sort_mapping['index'])
filtered_df = filtered_df.rename(columns={"name": "Player", "position": "Position", "salary1": "Salary "}).sort_values('position_order')

# Table style
hide_table_row_index = """
            <style>
            thead tr th:first-child {display:none}
            tr:nth-child(even) {background-color: #f2f2f2;}
            tbody th {display:none}
            </style>
            """
st.markdown(hide_table_row_index, unsafe_allow_html=True)
table_cols = ["Player", "Position", "Salary "]
st.dataframe(filtered_df[table_cols], use_container_width=True, hide_index=True)

st.markdown("""<hr style="height:10px;border:none;color:#333;background-color:#333;" /> """, unsafe_allow_html=True)

cap_used = "${:,.2f}".format(filtered_df["salary"].sum())
contract_yrs_used = filtered_df["contract_years"].sum()
roster_spots_used = filtered_df["mfl_id"].count()

cap_space = "${:,.2f}".format(global_vars.salary_cap - filtered_df["salary"].sum())
contract_yrs_free = global_vars.contract_cap - contract_yrs_used
roster_spots_free = global_vars.roster_size - roster_spots_used

col1, col2, col3, col4, col5 = st.columns(5)

# #Cap Dollars
col1.image(global_vars.dollar_icon)
col1.metric("Cap Used", cap_used)
col1.metric("Cap Space", cap_space)

# Contract Years
col3.image(global_vars.contract_icon)
col3.metric("Contract Years Used", contract_yrs_used)
col3.metric("Contract Years Free", contract_yrs_free)

#Roster Spots
col5.image(global_vars.player_icon)
col5.metric("Roster Spots Used", roster_spots_used)
col5.metric("Roster Spots Free", roster_spots_free)

with st.expander("Positional Breakdowns"):
    pos1, pos2, pos3= st.columns(3)

    fig = px.pie(filtered_df, values= filtered_df["salary"], names= filtered_df["Position"], title='Cap Dollars by Position')
    fig.update_traces(textposition='inside', textinfo='value')
    pos1.plotly_chart(fig, use_container_width=True)

    fig = px.pie(filtered_df, values= filtered_df["contract_years"], names= filtered_df["Position"], title='Contract Years by Position')
    fig.update_traces(textposition='inside', textinfo='value')
    pos2.plotly_chart(fig, use_container_width=True)

    roster_values = filtered_df["mfl_id"].value_counts()
    fig = px.pie(filtered_df, values= roster_values, names= filtered_df["Position"], title='Roster Spots by Position')
    fig.update_traces(textposition='inside', textinfo='value')
    pos3.plotly_chart(fig, use_container_width=True)





