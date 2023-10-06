import streamlit as st
import api_calls
import global_vars
import pandas as pd

st.set_page_config(layout="wide")
st.title("Points Race")
st.markdown("""<hr style="height:10px;border:none;color:#333;background-color:#333;" /> """, unsafe_allow_html=True)

# st.image(global_vars.coming_soon)

# Import Schedules
schedule = api_calls.get_schedule()

def extract_values(obj, key):
    """Pull all values of specified key from nested JSON."""
    arr = []

    def extract(obj, arr, key):
        """Recursively search for values of key in JSON tree."""
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    extract(v, arr, key)
                elif k == key:
                    arr.append(v)
        elif isinstance(obj, list):
            for item in obj:
                extract(item, arr, key)
        return arr

    results = extract(obj, arr, key)
    return results

# #Define Current, Next Weeks
names = extract_values(schedule, 'current_week')
current_wk = round(float(names[0]))

# Get Probabilities
probs_df = api_calls.get_probs()
keep_cols = ["franchise_id", "top_pts"]
current_wk_df = probs_df.loc[probs_df["week"] == current_wk][keep_cols].sort_values(by = 'top_pts', ascending=False)
current_wk_df["top_pts"] = current_wk_df["top_pts"].astype('float')*100

#Get Standings
standings, latest_wk = api_calls.get_standings()
keep_cols = ["franchise_id", "points_for"]
cur_standings = standings.loc[standings["after_week"] == latest_wk][keep_cols].sort_values(by = 'points_for', ascending=False)

#Merge DFs
merged_df = current_wk_df.merge(cur_standings, how = 'left', on = 'franchise_id')

# Get the list of teams
franchises = api_calls.get_teams()
keep_cols = ["mfl_id", "division", "franchise_name", "icon_url"]
df_franchises = pd.DataFrame(franchises)[keep_cols]

#Merge DFs
keep_cols = ["franchise_name", "top_pts", "points_for", "icon_url"]
merged_df1 = merged_df.merge(df_franchises, how = 'left', left_on = 'franchise_id', right_on = 'mfl_id').sort_values(by = 'top_pts', ascending=False)[keep_cols]
merged_df1["top_pts"] = merged_df1["top_pts"].apply("{0:.2f}%".format)

col1, col2 = st.columns(2, gap = "large")

#Table style
st.markdown(global_vars.hide_table_row_index, unsafe_allow_html=True)

with col1:
    st.subheader("Current Points", divider=True)
    # Points Table
    pts_df = merged_df1[["franchise_name", "points_for"]].rename(columns={"franchise_name": "Team", "points_for": "Total Points"}).sort_values(by = 'Total Points', ascending=False)
    st.table(pts_df)
    
with col2: 
    st.subheader("Projections", divider=True)
    col3, col4 = st.columns(2)

    with col3:
        # Probability Leaders
        prob_df = merged_df1[["franchise_name", "icon_url"]].rename(columns={"franchise_name": "Team"})[0:3]
        for team in prob_df["Team"].unique():
            st.image(prob_df.loc[prob_df["Team"] == team]["icon_url"].values[0])
            # col3.metric(team, helmet)
            # helmet

    with col4:
        # Probability Leaders
        prob_df = merged_df1[["franchise_name", "top_pts"]].rename(columns={"franchise_name": "Team"}).sort_values(by = 'top_pts', ascending=False)[0:3]
        for team in prob_df["Team"].unique():
            prob = prob_df.loc[prob_df["Team"] == team]["top_pts"].values[0]
            col4.metric(team, prob)
