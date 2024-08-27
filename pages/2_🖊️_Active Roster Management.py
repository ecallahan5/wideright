import numpy as np
import pandas as pd
import streamlit as st
import json
import plotly.express as px
import config
import global_vars
import functions


st.set_page_config(layout="wide")
st.title("Roster Construction")
st.divider()

# Get the current rosters
rosters = functions.bq_query("SELECT c.franchise_name, a.player_id, contract_year, salary, team, b.player_name, position  \
                              FROM `mfl-374514.dbt_production.dim_rosters` a \
                             left join `mfl-374514.dbt_production.dim_players`  b\
                             on a.player_id = b.player_id \
                             left join mfl-374514.dbt_production.dim_franchises c \
                             on a.franchise_id = c.franchise_id\
                             where a.status != 'TAXI_SQUAD' ")
rosters_df = pd.DataFrame(rosters)

col1, col2 = st.columns(2)

with col1:
    # Team picker
    team = st.selectbox(
        '**Choose a team**',
        sorted(rosters_df["franchise_name"].unique()))
    
with col2:
    # Year Picker
        year = st.selectbox(
        '**Choose a league year**',
        global_vars.yr_list)

st.divider()

contract_yrs = global_vars.zipped_df.loc[global_vars.zipped_df["Year"] == year]["Contract Length"].values[0]
filtered_df = rosters_df.loc[(rosters_df["franchise_name"] == team) & ((rosters_df["contract_year"]) >= contract_yrs)]
# filtered_df["salary1"] = filtered_df["salary"].apply("${:,.2f}".format)
filtered_df['position_order'] = filtered_df['position'].map(global_vars.sort_mapping['index'])
filtered_df = filtered_df.rename(columns={"player_name": "Name", "position": "Position", "salary": "Salary"}).sort_values('position_order')


cap_used = "${:,.2f}".format(filtered_df["Salary"].sum())
contract_yrs_used = filtered_df["contract_year"].sum()
roster_spots_used = filtered_df["player_id"].count()

cap_space = "${:,.2f}".format(global_vars.salary_cap - filtered_df["Salary"].sum())
contract_yrs_free = global_vars.contract_cap - contract_yrs_used
roster_spots_free = global_vars.roster_size - roster_spots_used

col1, col2, col3, col4, col5 = st.columns(5)

#Cap Dollars
col1.subheader("Salary Cap")
col1.image(global_vars.dollar_icon)
col1.metric("Cap Used", cap_used)
col1.metric("Cap Space", cap_space)

# Contract Years
col3.subheader("Contracts")
col3.image(global_vars.contract_icon)
col3.metric("Contract Years Used", contract_yrs_used)
col3.metric("Contract Years Free", contract_yrs_free)

#Roster Spots
col5.subheader("Roster Spots")
col5.image(global_vars.player_icon)
col5.metric("Roster Spots Used", roster_spots_used)
col5.metric("Roster Spots Free", roster_spots_free)

with st.expander("Positional Breakdowns"):
    pos1, pos2, pos3= st.columns(3)

    fig = px.pie(filtered_df, values= filtered_df["Salary"], names= filtered_df["Position"], title='Cap Dollars by Position')
    fig.update_traces(textposition='inside', textinfo='value')
    pos1.plotly_chart(fig, use_container_width=True)

    fig = px.pie(filtered_df, values= filtered_df["contract_year"], names= filtered_df["Position"], title='Contract Years by Position')
    fig.update_traces(textposition='inside', textinfo='value')
    pos2.plotly_chart(fig, use_container_width=True)

    roster_values = filtered_df["player_id"].value_counts()
    fig = px.pie(filtered_df, values= roster_values, names= filtered_df["Position"], title='Roster Spots by Position')
    fig.update_traces(textposition='inside', textinfo='value')
    pos3.plotly_chart(fig, use_container_width=True)





