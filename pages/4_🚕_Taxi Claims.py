import pandas as pd
import streamlit as st
import requests
import json
import config
import functions
import global_vars

site_token = config.key

st.set_page_config(layout="wide")

# st.image(global_vars.coming_soon)


current_wk = functions.bq_query("SELECT current_week FROM `mfl-374514.dbt_production.dim_current_week`")[0]["current_week"]

st.title("Taxi Claims for Week "+str(current_wk) )
st.divider()

# Import Claimables
claimables = functions.bq_query("SELECT * FROM `mfl-374514.dbt_production.taxi_claimables`")
claimables_df = pd.DataFrame(claimables)

# Get the list of teams
team = st.selectbox(
    'Which Team is Making the Claim?', [""] + sorted(claimables_df["claiming_team_name"].unique()))


# #Table style
st.markdown(global_vars.hide_table_row_index, unsafe_allow_html=True)
keep_cols = ["player_name", 'position', "ytd_pts", "current_team_name"]



claimables_df = claimables_df.loc[claimables_df["claiming_team_name"] == team][keep_cols].rename \
    ({'player_name' : 'Name', 'position' : 'Position', 'current_team_name' : 'Owner' , 'ytd_pts' : '2024 Pts'}, axis = 1)
claimables_df['2024 Pts'] = claimables_df['2024 Pts'].map('{:.2f}'.format)
st.table(claimables_df)
##################################


# # with st.chat_message("Norwood", avatar = "https://kubrick.htvapps.com/htv-prod-media.s3.amazonaws.com/images/scott-norwood-1486054177.jpg?crop=1.00xw:0.358xh;0,0.226xh&resize=900:*"):
# #     st.write("What team are you claming for?")

# # Get the list of players
# players = api_calls.get_players_wr()
# df_players = pd.DataFrame(players)


# # # ID Claim Eligible Players by Scores
# @st.cache_data
# def filter_players(df_players):
#     qb = df_players[df_players.position=='QB'].sort_values(by=['prior_weeks_score'], ascending = False).head(15)
#     rb = df_players[df_players.position=='RB'].sort_values(by=['prior_weeks_score'], ascending = False).head(60)
#     wr = df_players[df_players.position=='WR'].sort_values(by=['prior_weeks_score'], ascending = False).head(60)
#     te = df_players[df_players.position=='TE'].sort_values(by=['prior_weeks_score'], ascending = False).head(30)
#     pk = df_players[df_players.position=='PK'].sort_values(by=['prior_weeks_score'], ascending = False).head(15)
#     all = pd.concat([qb, rb, wr, te, pk])

# # # On Taxi Squad, Not FFP (depends on week), Not claimed
# #     # Cannot be cut, traded, or claimed off of the Taxi Squad, for the first 8 weeks of the regular season.
#     if current_wk < 8:
#         claim_elig = all[(all.is_on_taxi == True) & (all.claimed == False) & (all.game_started == False) & (all.is_ffp == False)]
#     else:
#         claim_elig = all[(all.is_on_taxi == True) & (all.claimed == False) & (all.game_started == False)]

#     return claim_elig

# claimable_players = filter_players(df_players)

# rosters = pd.DataFrame(api_calls.get_rosters())

# current_wk = (str(current_wk))
# next_wk =    (str(next_wk))

# current_wk_dict = {}
# next_wk_dict = {}

# # I create a dictionary of the schedule for the current week
# current_wk_schedule = schedule['matchups_by_week'][current_wk]
# next_wk_schedule = schedule['matchups_by_week'][next_wk]

# for matchup in current_wk_schedule:
#   ids = [ matchup[k] for k in ('home_franchise_id', 'away_franchise_id')]
#   current_wk_dict[ids[0]] = [ids[1]]
#   current_wk_dict[ids[1]] = [ids[0]]

# team_exclusions = {}
# for key in set().union(current_wk_dict, next_wk_dict):
#   if key in current_wk_dict: team_exclusions.setdefault(key, []).extend(current_wk_dict[key])
#   if key in next_wk_dict:    team_exclusions.setdefault(key, []).extend(next_wk_dict[key])
# for k, v in team_exclusions.items():
#   v.append(k)

# df_team_exclusions = pd.DataFrame(team_exclusions).T.rename({0 : 'Excl1', 1 : 'Excl2', 2 : 'Self'}, axis=1)

# # Create subtable with franchise names and IDs
# names_dict = {}
# for matchup in current_wk_schedule:
#   ids = [ matchup[k] for k in ('home_franchise_id', 'home_franchise', 'away_franchise_id', 'away_franchise')]
#   names_dict[ids[0]] = ids[1]
#   names_dict[ids[2]] = ids[3]
# names_df = pd.DataFrame([names_dict]).T
# names_df['franchise_id'] = names_df.index
# names_df.columns = ['franchise_name', 'franchise_id']

# claim_elig1 = claimable_players.merge(rosters, left_on='mfl_id', right_on='mfl_id')
# claim_elig2 = claim_elig1[['mfl_id', 'position', 'first_name', 'last_name', 'franchise_name']]\
#   .rename({'position' : 'Position', 'first_name' : 'First Name', 'last_name' : 'Last Name' , 'franchise_name' : 'Current Team'}, axis = 1)
# claim_elig3 = claim_elig2.merge(names_df, left_on = 'Current Team', right_on = 'franchise_name')

# claimables = {}

# for franchise, a in df_team_exclusions.iterrows():
#   claimables[franchise] = []
#   for player, b in claim_elig3.iterrows():
#      if claim_elig3.loc[player, 'franchise_id'] not in list(df_team_exclusions.loc[franchise]):
#       claimables[franchise].append(int(claim_elig3.loc[player, 'mfl_id']))

# # -------------------------






