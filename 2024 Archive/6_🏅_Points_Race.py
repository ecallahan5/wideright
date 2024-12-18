import streamlit as st
import functions
import global_vars
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("Points Race")
st.divider()

after_wk = functions.bq_query("SELECT recent_completed_week FROM `mfl-374514.dbt_production.dim_current_week`")[0]["recent_completed_week"]
last_wk = functions.bq_query("SELECT recent_completed_week - 1 as last_week FROM `mfl-374514.dbt_production.dim_current_week`")[0]["last_week"]

top_pts_probs = functions.bq_query(f"SELECT franchise_name as `Team`, top_pts, icon \
                                   FROM `mfl-374514.dbt_production.fct_reg_season_model` a \
                                   join `mfl-374514.dbt_production.dim_franchises` b \
                                   on a.franchise_id = b.franchise_id \
                                   where after_week = {after_wk} \
                                   order by top_pts desc \
                                   limit 3  ")
top_pts_probs_df = pd.DataFrame(top_pts_probs)

lw_probs = functions.bq_query(f"SELECT franchise_name as `Team`, top_pts as lw_top_pts \
                                   FROM `mfl-374514.dbt_production.fct_reg_season_model` a \
                                   join `mfl-374514.dbt_production.dim_franchises` b \
                                   on a.franchise_id = b.franchise_id \
                                   where after_week = {last_wk} \
                                   order by top_pts desc  ")
lw_probs_df = pd.DataFrame(lw_probs)

pts = functions.bq_query("SELECT franchise_name as `Franchise Name`, points_for as `Total Points` \
                               FROM `mfl-374514.dbt_production.dim_standings` a\
                               join `mfl-374514.dbt_production.dim_franchises` b \
                                   on a.franchise_id = b.franchise_id \
                         order by 2 desc ")
pts_df = pd.DataFrame(pts)

col1, col2 = st.columns(2, gap = "large")

with col1:
    st.subheader("Points Total After Week "+str(after_wk), divider=True)
    st.dataframe(pts_df, hide_index=True, use_container_width = True)
 
with col2: 
    st.subheader("Top 3 Likliest Winners", divider=True)
#     lw_prob_df = merged_df1.loc[merged_df1["current_wk"] == chosen_wk - 1][["franchise_name", "icon_url", "current_wk", "top_pts"]]\
#         .rename(columns={"franchise_name": "Team", "top_pts" : "lw_top_pts"}).drop(["icon_url", 'current_wk'], axis = 1)
    grid_row_count = 3
    grid_col_count = 2

    mygrid = global_vars.make_grid(grid_row_count,grid_col_count)
    for row_num in list(range(grid_row_count)):
        helmet = top_pts_probs_df["icon"].values[row_num]
        team = top_pts_probs_df["Team"].values[row_num]
        prob = float(top_pts_probs_df["top_pts"].values[row_num])*100
        lw_prob = float(lw_probs_df["lw_top_pts"].values[row_num])*100
        wow = prob - lw_prob
        mygrid[row_num][0].image(helmet)
        mygrid[row_num][1].metric(team,"{0:.2f}%".format(prob), "{0:.2f}%".format(wow))
        # mygrid[row_num][1].metric(team,"{0:.2f}%".format(prob))

######################################

# # Create Week Selector
# with st.sidebar:
#     wk_list = []
#     for wk in top_pts_probs_df["after_week"].unique():
#         wk_list.insert(0,wk)
#     chosen_wk = st.selectbox(
#         'Week Number', (wk_list))


# st.subheader("Trends", divider = True)
# merged_df2 = merged_df1.sort_values(by='current_wk')
# fig = px.line(merged_df2, x= "current_wk", y = "top_pts", color = "franchise_name", title = 'Points Title Probability Trends',\
#               labels=dict(top_pts="Probability", franchise_name="Team", current_wk="After Week"), markers = True)
# fig.update_xaxes(dtick=1)
# st.plotly_chart(fig, theme="streamlit", use_container_width=True)