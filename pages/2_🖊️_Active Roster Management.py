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
rosters = functions.bq_query("SELECT c.franchise_name, a.player_id, contract_year, salary, team, b.player_name, position, a.status  \
                              FROM `mfl-374514.dbt_production.dim_rosters` a \
                             left join `mfl-374514.dbt_production.dim_players`  b\
                             on a.player_id = b.player_id \
                             left join mfl-374514.dbt_production.dim_franchises c \
                             on a.franchise_id = c.franchise_id\
                             where a.status != 'TAXI_SQUAD' ")
rosters_df = pd.DataFrame(rosters)

penalties = functions.bq_query("SELECT b.franchise_id, a.team_name, b.franchise_name, a.Penalty_Applied_Year, sum(a.penalty_Amount) as cap_penalty \
                              FROM `mfl-374514.external.cap_penalties` a \
                             left join mfl-374514.dbt_production.dim_franchises b \
                             on trim(a.team_name) = trim(b.franchise_name) \
                               group by 1,2,3,4")
penalties_df = pd.DataFrame(penalties)

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
filtered_df['position_order'] = filtered_df['position'].map(global_vars.sort_mapping['index'])
filtered_df = filtered_df.rename(columns={"player_name": "Name", "position": "Position", "salary": "Salary"}).sort_values('position_order')

# Filter penalties for the selected team and year
team_penalties_df = penalties_df.loc[(penalties_df["franchise_name"] == team) & (penalties_df["Penalty_Applied_Year"] == year)]

numeric_cap_used = filtered_df["Salary"].sum()
numeric_cap_penalties = team_penalties_df["cap_penalty"].sum()
numeric_cap_space = global_vars.salary_cap - numeric_cap_used - numeric_cap_penalties

contract_yrs_used = filtered_df["contract_year"].sum()
roster_spots_used = len(filtered_df.loc[filtered_df["status"] != 'INJURED_RESERVE'])

contract_yrs_free = global_vars.contract_cap - contract_yrs_used
roster_spots_free = global_vars.roster_size - roster_spots_used

# Format the calculated numbers into strings for display ---
display_cap_used = "${:,.2f}".format(numeric_cap_used)
display_cap_penalties = "${:,.2f}".format(numeric_cap_penalties)
display_cap_space = "${:,.2f}".format(numeric_cap_space)

col1, col2, col3, col4, col5 = st.columns(5)

#Cap Dollars
col1.subheader("Salary Cap")
col1.image(global_vars.dollar_icon)
col1.metric("Cap Used", display_cap_used)
col1.metric("Cap Penalties", display_cap_penalties)
col1.metric("Cap Space", display_cap_space)

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

    # Corrected Chart 1: Cap Dollars by Position
    fig_cap = px.pie(filtered_df, values="Salary", names="Position", title='Cap Dollars by Position')
    fig_cap.update_traces(textposition='inside', textinfo='value')
    pos1.plotly_chart(fig_cap, use_container_width=True)

    # Corrected Chart 2: Contract Years by Position
    fig_contract = px.pie(filtered_df, values="contract_year", names="Position", title='Contract Years by Position')
    fig_contract.update_traces(textposition='inside', textinfo='value')
    pos2.plotly_chart(fig_contract, use_container_width=True)

    # Corrected Chart 3: Roster Spots by Position
    fig_roster = px.pie(filtered_df, names="Position", title='Roster Spots by Position')
    fig_roster.update_traces(textposition='inside', textinfo='value') # 'value' will now be the count
    pos3.plotly_chart(fig_roster, use_container_width=True)


