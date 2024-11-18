import numpy as np
import pandas as pd
import streamlit as st
import requests
import json
import config
import global_vars
import functions

st.set_page_config(layout="wide")
st.title("Payouts")

st.subheader("Seasons to Date Winnings", divider=True)

payouts = functions.bq_query(f"SELECT b.franchise_name as `Franchise Name`, sum(a.payout) as Winnings \
                               FROM `mfl-374514.external.payouts` a\
                               join `mfl-374514.dbt_production.dim_franchises` b \
                                   on a.franchise_id = b.franchise_id \
                             group by 1 order by 2 desc ")
payouts_df = pd.DataFrame(payouts)

st.dataframe(payouts_df, hide_index=True, use_container_width = True)
###########################################################################

# st.subheader("Regular Season Standings", divider=True)

# reg_season = pd.DataFrame({
#      'Event': ["Left Upright Winner", "Crossbar Winner", "Right Upright Winner", "Wild Card 1", "Wild Card 2", "Wild Card 3", ],
#      'Payout': ["50", "50", "50", "30", "30", "30"],
#      'Winner' : ["Brooklyn Big Blue", "The Van Buren Boys", "The Uncaught Exceptions", "Maize 'N Blue", "Moneyballers", "The Gurley Tates"]
#      })
# st.dataframe(reg_season, hide_index=True, use_container_width = True)

# st.subheader("Playoff Results", divider=True)

# playoffs = pd.DataFrame({
#      'Event': [ "League Champ", "League Runner-up", "League 3rd Place"],
#      'Payout': ["335", "160", "65"],
#      'Winner' : ["The Uncaught Exceptions", "Maize 'N Blue", "The Van Buren Boys"]
#      })
# st.dataframe(playoffs, hide_index=True, use_container_width = True)

# st.subheader("Extras", divider=True)

# extras = pd.DataFrame({
#      'Event': ["WCP Winner (tie)", "WCP Winner (tie)", "Points Title",],
#      'Payout': ["25", "25", "60", ],
#      'Winner' : [ "The Uncaught Exceptions", "Moneyballers", "Brooklyn Big Blue", ]
#      })
# st.dataframe(extras, hide_index=True, use_container_width = True)

# # Import Schedules
# schedule = functions.get_schedule()
# results_dict =schedule["matchups_by_week"]

# #Define Current, Next Weeks
# names = global_vars.extract_values(schedule, 'current_week')
# current_wk = round(float(names[0]))

# # Get game scores
# scores = []

# for week, results in results_dict.items():
#     if int(week) < current_wk:
#         for matchup in results:
#             home_score = {}
#             away_score = {}
#             home_score["week"] = int(week)
#             home_score["franchise"] = matchup["home_franchise"] 
#             home_score["score"] = float(matchup["home_franchise_score"])
#             away_score["week"] = int(week)
#             away_score["franchise"] = matchup["away_franchise"] 
#             away_score["score"] = float(matchup["away_franchise_score"])
#             scores.append(home_score)
#             scores.append(away_score)

# scores_df = pd.DataFrame(scores)
# results_df = pd.DataFrame([])

# pot = 15
# for week in range(1,current_wk):
#     skins_winner = 'None'
#     week_df = scores_df.loc[scores_df["week"] == week].sort_values(by="score", ascending=False).head(2).reset_index()
#     spread = week_df["score"][0] - week_df["score"][1]
#     if spread >= 12:
#         skins_winner = week_df["franchise"][0]
#         winnings = pot
#         pot = 15
#     else:
#         pot += 15
#         winnings = 0
#     wk_df = pd.DataFrame({"Week" : week, "Winner": skins_winner, "Winnings": winnings , "Next Pot" : pot}, index=[0])
#     results_df = pd.concat([results_df, wk_df])
# results_df["Winnings"] = results_df["Winnings"]
# results_df["Next Pot"] = results_df["Next Pot"].apply("${:,.0f}".format)

# col1, col2 = st.columns(2, gap = "large")

# with col1:
#     st.subheader("Current Skins Pot", divider=True)
#     st.write("See you in 2024!")
#     # Need to figure out how to handle Week 14 ...
#     # st.metric("Week "+str(current_wk), "${:,.0f}".format(pot))
    
# with col2: 
#     st.subheader("Season's Skins Winners", divider=True)
#     grouped_winnings = results_df.groupby('Winner').sum().sort_values(by='Winnings', ascending=False).reset_index()
#     final_skin = {'Winner': 'Cromarties Bastards', 'Week': '14','Winnings': 15}
#     # grouped_winnings = grouped_winnings.append(final_skin, ignore_index=True)
#     grouped_winnings = pd.concat([grouped_winnings, pd.DataFrame([final_skin])], ignore_index=True)
#     grouped_winnings["Winnings"] = grouped_winnings["Winnings"].apply(lambda x: "${:,.0f}".format(x))
#     grouped_winnings = st.dataframe(grouped_winnings.loc[grouped_winnings['Winner'] != 'None'][["Winner", "Winnings"]] , hide_index=True, use_container_width = True)
    
