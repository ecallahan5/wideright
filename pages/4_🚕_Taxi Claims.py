import pandas as pd
import streamlit as st
import requests
import functions
import global_vars
from datetime import datetime, timedelta

st.set_page_config(layout="wide")

current_wk = functions.bq_query("SELECT current_week FROM `mfl-374514.dbt_production.dim_current_week`")[0]["current_week"]

st.title("Taxi Claims for Week "+str(current_wk) )
st.divider()

# Import Claimables
if current_wk >= 8:
    claimables = functions.bq_query("SELECT a.*, b.discord_id as claiming_discord, c.discord_id as owning_discord\
                                     FROM `mfl-374514.dbt_production.taxi_claimables` a \
                                    left join `mfl-374514.external.discord` b\
                                    on a.claiming_team_id = b.franchise_id \
                                    left join `mfl-374514.external.discord` c\
                                    on a.owning_team = c.franchise_id ")
else:
    claimables = functions.bq_query("SELECT a.*, b.discord_id as claiming_discord, c.discord_id as owning_discord\
                                     FROM `mfl-374514.dbt_production.taxi_claimables` a \
                                    left join `mfl-374514.external.discord` b\
                                    on a.claiming_team_id = b.franchise_id \
                                    left join `mfl-374514.external.discord` c\
                                    on a.owning_team = c.franchise_id\
                                    where ffp_flag = 0`")
    
claimables_df = pd.DataFrame(claimables)

# #Table style
st.markdown(global_vars.hide_table_row_index, unsafe_allow_html=True)

# #Table style
st.markdown(global_vars.hide_table_row_index, unsafe_allow_html=True)
keep_cols = ["player_name", 'position', "ytd_pts", "current_team_name", "ffp_flag", "comp_pick", "claiming_discord", "owning_discord"]


with st.chat_message("Norwood", avatar = global_vars.norwood_avatar):
    st.write("What team are you claming for?")
    team = st.selectbox(
    '', [""] + sorted(claimables_df["claiming_team_name"].unique()))
    if team:
        st.write("Here are the players that " + team + " can claim:" )

        pts_col_name = f"{global_vars.league_year} Pts"
        claimables_df = claimables_df.loc[claimables_df["claiming_team_name"] == team][keep_cols].rename \
            ({'player_name' : 'Name', 'position' : 'Position', 'current_team_name' : 'Owner' , 'ytd_pts' : pts_col_name}, axis = 1).sort_values([pts_col_name], ascending = False)
        claimables_df[pts_col_name] = claimables_df[pts_col_name].map('{:.2f}'.format)
        claimables_df["comp_pick"] = claimables_df["comp_pick"].fillna(0).astype(int)
        st.table(claimables_df.iloc[:, :4])

        st.write("Would you like to claim any of these players?")
        claim = st.checkbox("Yes!")
        if claim:
            claiming = st.radio("Who would you like to claim?", claimables_df)
            name = claimables_df.loc[claimables_df["Name"] == claiming]["Name"].values[0]
            owner = claimables_df.loc[claimables_df["Name"] == claiming]["Owner"].values[0]

            comp_pick = claimables_df.loc[claimables_df["Name"] == claiming]["comp_pick"].values[0]
            if claimables_df.loc[claimables_df["Name"] == name]["ffp_flag"].values[0] == 1:
                st.warning(name+" is a designated Future Franchise Player (FFP). If you'd like to claim him you must surrender a future pick in Round "+str(comp_pick), icon="⚠️")
            st.write("Would you like to claim " + name + " from " + owner + " ?")
            claim_action = st.button("Claim him!")
            if claim_action:
                webhook_url = st.secrets["discord"]["test_url"]
                current_time = datetime.now()
                one_week_later = (datetime.now() + timedelta(weeks=1)).strftime("%A, %B %d, %I:%M %p")
                claiming_discord = claimables_df.loc[claimables_df["Name"] == name]["claiming_discord"].values[0]
                owning_discord = claimables_df.loc[claimables_df["Name"] == name]["owning_discord"].values[0]
                if claimables_df.loc[claimables_df["Name"] == name]["ffp_flag"].values[0] == 1:
                    payload = {"content": "**<@" + claiming_discord + ">** is submitting a 🚕 claim on **" + name + "** from **<@" + owning_discord + ">**.  This is an FFP claim and carries draft pick compensation. The claim must be resolved by **" + one_week_later + "**."}
                else:
                    payload = {"content": "**<@" + claiming_discord + ">** is submitting a 🚕 claim on **" + name + "** from **<@" + owning_discord + ">**. The claim must be resolved by **" + one_week_later + "**."}
                r = requests.post(url = webhook_url, data = payload)
                if r: 
                    st.toast("Your claim has been submitted!", icon='🎉')
