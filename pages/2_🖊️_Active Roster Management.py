import numpy as np
import pandas as pd
import streamlit as st
import json
import plotly.express as px
import config
import global_vars
import functions

st.set_page_config(layout="wide")
st.title("🖊️ Roster Construction & Management")
st.divider()

# Get the current rosters (including Taxi Squad and IR)
rosters = functions.bq_query("""
    SELECT c.franchise_name, a.player_id, contract_year, salary, team, b.player_name, position, a.status  
    FROM `mfl-374514.dbt_production.dim_rosters` a 
    left join `mfl-374514.dbt_production.dim_players` b on a.player_id = b.player_id 
    left join `mfl-374514.dbt_production.dim_franchises` c on a.franchise_id = c.franchise_id
""")
rosters_df = pd.DataFrame(rosters)

# Get penalties
penalties = functions.bq_query("SELECT * from `mfl-374514.dbt_production.fct_cap_penalties_total`")
penalties_df = pd.DataFrame(penalties)

col1, col2 = st.columns(2)

with col1:
    team = st.selectbox(
        '**Choose a team**',
        sorted(rosters_df["franchise_name"].dropna().unique())
    )
    
with col2:
    year = st.selectbox(
        '**Choose a league year**',
        global_vars.yr_list
    )

st.divider()

# Filter data for selected team
team_roster_all = rosters_df.loc[rosters_df["franchise_name"] == team].copy()

# Map positional sorting order
team_roster_all['position_order'] = team_roster_all['position'].map(global_vars.sort_mapping['index']).fillna(99)
team_roster_all = team_roster_all.sort_values('position_order')

# Determine active roster vs taxi squad
active_roster = team_roster_all.loc[team_roster_all["status"] != 'TAXI_SQUAD'].copy()
taxi_squad = team_roster_all.loc[team_roster_all["status"] == 'TAXI_SQUAD'].copy()

# Calculate active roster metrics
# Note: contract length check maps to how many contract years are remaining relative to current year offset
contract_yrs = global_vars.zipped_df.loc[global_vars.zipped_df["Year"] == year]["Contract Length"].values[0]
filtered_active = active_roster.loc[active_roster["contract_year"] >= contract_yrs].copy()

numeric_cap_used = filtered_active["salary"].apply(lambda x: float(str(x).replace('$', '').replace(',', '')) if pd.notna(x) else 0.0).sum()

team_penalties_df = penalties_df.loc[(penalties_df["franchise_name"] == team) & (penalties_df["adjustment_year"] == year)]
numeric_cap_penalties = team_penalties_df["adjustment_amt"].sum()
numeric_cap_space = global_vars.salary_cap - numeric_cap_used - numeric_cap_penalties

contract_yrs_used = filtered_active["contract_year"].sum()
roster_spots_used = len(filtered_active.loc[filtered_active["status"] != 'INJURED_RESERVE'])

contract_yrs_free = global_vars.contract_cap - contract_yrs_used
roster_spots_free = global_vars.roster_size - roster_spots_used

# Display Metrics Cards
m_col1, m_col2, m_col3 = st.columns(3)

with m_col1:
    with st.container(border=True):
        st.markdown("### 💰 Salary Cap")
        st.metric(
            label="Remaining Cap Space", 
            value="${:,.2f}".format(numeric_cap_space),
            delta="${:,.2f}".format(numeric_cap_space) if numeric_cap_space >= 0 else "-${:,.2f}".format(abs(numeric_cap_space)),
            delta_color="normal" if numeric_cap_space >= 0 else "inverse"
        )
        st.metric(label="Cap Used", value="${:,.2f}".format(numeric_cap_used))
        st.metric(label="Cap Penalties", value="${:,.2f}".format(numeric_cap_penalties))

with m_col2:
    with st.container(border=True):
        st.markdown("### 📜 Contracts")
        st.metric(
            label="Contract Years Free", 
            value=f"{contract_yrs_free} Years",
            delta=f"{contract_yrs_free} free" if contract_yrs_free >= 0 else f"{abs(contract_yrs_free)} over",
            delta_color="normal" if contract_yrs_free >= 0 else "inverse"
        )
        st.metric(label="Contract Years Used", value=f"{contract_yrs_used} Years")

with m_col3:
    with st.container(border=True):
        st.markdown("### 🏈 Roster Spots")
        st.metric(
            label="Roster Spots Free", 
            value=f"{roster_spots_free} / {global_vars.roster_size}",
            delta=f"{roster_spots_free} free" if roster_spots_free >= 0 else f"{abs(roster_spots_free)} over",
            delta_color="normal" if roster_spots_free >= 0 else "inverse"
        )
        st.metric(label="Active Players Used", value=f"{roster_spots_used}")

st.divider()

# Display Player list in tabs
tab_roster, tab_taxi = st.tabs(["📋 Active Roster", "🚕 Taxi Squad"])

with tab_roster:
    st.subheader("Active Roster Players")
    if filtered_active.empty:
        st.info("No active roster players found running past this contract year.")
    else:
        # Format display columns
        display_roster = filtered_active.rename(columns={
            "player_name": "Player Name",
            "position": "Position",
            "team": "NFL Team",
            "salary": "Salary",
            "contract_year": "Contract Year",
            "status": "Status"
        })
        st.dataframe(
            display_roster[["Player Name", "Position", "NFL Team", "Salary", "Contract Year", "Status"]], 
            use_container_width=True, 
            hide_index=True
        )

with tab_taxi:
    st.subheader("Taxi Squad Players")
    if taxi_squad.empty:
        st.info("No players currently on the Taxi Squad.")
    else:
        display_taxi = taxi_squad.rename(columns={
            "player_name": "Player Name",
            "position": "Position",
            "team": "NFL Team",
            "salary": "Salary",
            "contract_year": "Contract Year",
            "status": "Status"
        })
        st.dataframe(
            display_taxi[["Player Name", "Position", "NFL Team", "Salary", "Contract Year", "Status"]], 
            use_container_width=True, 
            hide_index=True
        )

st.divider()

with st.expander("📊 Positional Breakdowns"):
    pos1, pos2, pos3 = st.columns(3)

    if filtered_active.empty:
        st.info("No active roster data available for charts.")
    else:
        # Plotly chart calculations need numeric salary
        chart_df = filtered_active.copy()
        chart_df["Salary Numeric"] = chart_df["salary"].apply(lambda x: float(str(x).replace('$', '').replace(',', '')) if pd.notna(x) else 0.0)

        # Chart 1: Cap Dollars by Position
        fig_cap = px.pie(chart_df, values="Salary Numeric", names="position", title='Cap Dollars by Position')
        fig_cap.update_traces(textposition='inside', textinfo='value+percent')
        pos1.plotly_chart(fig_cap, use_container_width=True)

        # Chart 2: Contract Years by Position
        fig_contract = px.pie(chart_df, values="contract_year", names="position", title='Contract Years by Position')
        fig_contract.update_traces(textposition='inside', textinfo='value+percent')
        pos2.plotly_chart(fig_contract, use_container_width=True)

        # Chart 3: Roster Spots by Position
        fig_roster = px.pie(chart_df, names="position", title='Roster Spots by Position')
        fig_roster.update_traces(textposition='inside', textinfo='value+percent')
        pos3.plotly_chart(fig_roster, use_container_width=True)
