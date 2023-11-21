import streamlit as st
import api_calls
import global_vars
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("Points Race")
st.markdown("""<hr style="height:10px;border:none;color:#333;background-color:#333;" /> """, unsafe_allow_html=True)

# Import Schedules
schedule = api_calls.get_schedule()

#Define Current, Next Weeks
names = global_vars.extract_values(schedule, 'current_week')
current_wk = round(float(names[0]))
after_wk = current_wk - 1

# Get Probabilities
probs_df = api_calls.get_probs()
keep_cols = ["franchise_id", "top_pts", "week"]
current_wk_df = probs_df[keep_cols].sort_values(by = 'top_pts', ascending=False)
current_wk_df["top_pts"] = current_wk_df["top_pts"].astype('float')*100

# Create Week Selector
with st.sidebar:
    wk_list = []
    for wk in probs_df["week"].unique():
        wk_list.insert(0,wk)
    chosen_wk = st.selectbox(
        'Week Number', (wk_list))

#Get Standings
standings, latest_wk = api_calls.get_standings()
keep_cols = ["franchise_id", "points_for", "current_wk"]
cur_standings = standings[keep_cols].sort_values(by = 'points_for', ascending=False)

#Merge DFs
merged_df = current_wk_df.merge(cur_standings, how = 'left', left_on = ['franchise_id', 'week'], right_on = ['franchise_id', 'current_wk'])

# Get the list of teams
franchises = api_calls.get_teams()
keep_cols = ["mfl_id", "division", "franchise_name", "icon_url"]
df_franchises = pd.DataFrame(franchises)[keep_cols]

#Merge DFs
keep_cols = ["franchise_name", "top_pts", "points_for", "icon_url", "current_wk"]
merged_df1 = merged_df.merge(df_franchises, how = 'left', left_on = 'franchise_id', right_on = 'mfl_id').sort_values(by = 'top_pts', ascending=False)[keep_cols]
# Remove commas and convert "points_for" to a numeric value
merged_df1["points_for"] = merged_df1["points_for"].str.replace(',', '').astype(float)
# Sort the DataFrame by the "points_for" column in descending order
merged_df1 = merged_df1.sort_values(by="points_for", ascending=False)
# Apply formatting with thousands separator to the "points_for" column
merged_df1["points_for"] = merged_df1["points_for"].apply(lambda x: "{:,.2f}".format(x))

col1, col2 = st.columns(2, gap = "large")

with col1:
    st.subheader("Points Total entering Week "+str(chosen_wk), divider=True)
    # Points Table
    pts_df = merged_df1.loc[merged_df1["current_wk"] == chosen_wk][["franchise_name", "points_for"]]\
                            .rename(columns={"franchise_name": "Team", "points_for": "Total Points"})
    st.dataframe(pts_df, hide_index=True, use_container_width = True)
    
with col2: 
    st.subheader("Top 3 Likliest Winners", divider=True)
    prob_df = merged_df1.loc[merged_df1["current_wk"] == chosen_wk][["franchise_name", "icon_url", "current_wk", "top_pts"]]\
        .rename(columns={"franchise_name": "Team"})[0:3]
    lw_prob_df = merged_df1.loc[merged_df1["current_wk"] == chosen_wk - 1][["franchise_name", "icon_url", "current_wk", "top_pts"]]\
        .rename(columns={"franchise_name": "Team", "top_pts" : "lw_top_pts"}).drop(["icon_url", 'current_wk'], axis = 1)
    all_prob_df = prob_df.merge(lw_prob_df, how = 'left', on = ["Team"])
    grid_row_count = 3
    grid_col_count = 2

    mygrid = global_vars.make_grid(grid_row_count,grid_col_count)
    for row_num in list(range(grid_row_count)):
        helmet = all_prob_df["icon_url"].values[row_num]
        team = all_prob_df["Team"].values[row_num]
        prob = float(all_prob_df["top_pts"].values[row_num])
        lw_prob = float(all_prob_df["lw_top_pts"].values[row_num])
        wow = prob - lw_prob
        mygrid[row_num][0].image(helmet)
        mygrid[row_num][1].metric(team,"{0:.2f}%".format(prob), "{0:.2f}%".format(wow))

st.subheader("Trends", divider = True)
merged_df2 = merged_df1.sort_values(by='current_wk')
fig = px.line(merged_df2, x= "current_wk", y = "top_pts", color = "franchise_name", title = 'Points Title Probability Trends',\
              labels=dict(top_pts="Probability", franchise_name="Team", current_wk="After Week"), markers = True)
fig.update_xaxes(dtick=1)
st.plotly_chart(fig, theme="streamlit", use_container_width=True)