import streamlit as st
import api_calls
import global_vars
import pandas as pd

st.set_page_config(layout="wide")

# Import Schedules
schedule = api_calls.get_schedule()

#Define Current Week
names = global_vars.extract_values(schedule, 'current_week')
current_wk = round(float(names[0]))
after_wk = current_wk - 1

st.title("Projected Standings After Week "+str(after_wk))

st.markdown("""<hr style="height:10px;border:none;color:#333;background-color:#333;" /> """, unsafe_allow_html=True)

# Get teams
franchises = api_calls.get_teams()
keep_cols = ["mfl_id", "division", "franchise_name", "division_name"]
df_franchises = pd.DataFrame(franchises)[keep_cols]

# Get Probabilities
probs_df = api_calls.get_probs()
keep_cols = ["franchise_id", "proj_wins", "week"]
current_wk_df = probs_df.loc[probs_df["week"] == 5][keep_cols]
current_wk_df["proj_wins"] = round(current_wk_df["proj_wins"].astype('float'),1)

merged_df = df_franchises.merge(current_wk_df, how = 'left', left_on = 'mfl_id', right_on = 'franchise_id').sort_values(by = 'division')

grid_row_count = 1
grid_col_count = 3

mygrid = global_vars.make_grid(grid_row_count,grid_col_count)

# #Table style
# st.markdown(global_vars.hide_table_row_index, unsafe_allow_html=True)
places_df = pd.DataFrame()

for col_num in list(range(grid_col_count)):
    div_df = merged_df.loc[merged_df["division"] == "0"+str(col_num)].rename(columns={"franchise_name": "Team", "proj_wins" : "Projected Wins"})\
    .sort_values(by = 'Projected Wins', ascending=False).reset_index()
    div_df["place"] = div_df.index + 1
    div_name = div_df[["division_name"]].values[0][0]
    mygrid[0][col_num].subheader(div_name, divider=True)
    mygrid[0][col_num].dataframe(div_df[["Team", "Projected Wins"]], hide_index=True, use_container_width = True)
    div_places_df = div_df[["division_name", "Team", "place" ]]
    places_df = pd.concat([places_df, div_places_df])

st.markdown("""<hr style="height:10px;border:none;color:#333;background-color:#333;" /> """, unsafe_allow_html=True)

st.header("Team Profiles")

# Get teams
drop_cols = ["division", "waiver_sort_order", "blind_bid_budget"]
df_franchises = pd.DataFrame(franchises).drop(drop_cols, axis=1)

drop_cols = ["id", "created_at", "week"]
current_wk_df = probs_df.loc[probs_df["week"] == 5].drop(drop_cols, axis=1)
current_wk_df["proj_wins"] = round(current_wk_df["proj_wins"].astype('float'),1)

profiles_df = df_franchises.merge(current_wk_df, how = 'left', left_on = 'mfl_id', right_on = 'franchise_id')

team = st.selectbox(
    'Choose a Team', [""] + sorted(profiles_df["franchise_name"].unique()))

team_df = profiles_df.loc[profiles_df["franchise_name"] == team]


try:
    helmet = team_df["icon_url"].values[0]
    proj_rk = places_df.loc[places_df["Team"] == team]["place"].values[0]
    if proj_rk == 1:
        proj_rk_ord = '1st'
    elif proj_rk == 2:
        proj_rk_ord = '2nd'
    elif proj_rk == 3:
        proj_rk_ord = '3rd'
    else:
        proj_rk_ord = '4th'
    div = team_df["division_name"].values[0]

    def extract_probs(prob):
        return float(team_df[prob].values[0])*100

    def format_probs(prob):
        return "{0:.2f}%".format(prob)

    playoffs = extract_probs("make_playoffs")
    one_seed = extract_probs("one_seed")
    bye = extract_probs("bye")
    win_div  = extract_probs("win_division")
    wild_card = extract_probs("wild_card")
    first_pick = extract_probs("first_pick")

    col1, col2 = st.columns(2, gap = "large")

    with col1:
        grid_row_count = 1
        grid_col_count = 2
        mygrid = global_vars.make_grid(grid_row_count,grid_col_count)
        mygrid[0][0].image(helmet)
        mygrid[0][1].header("Current Projected Place in the "+div+" division:")
        mygrid[0][1].metric("", proj_rk_ord)

    with col2:
        grid_row_count = 3
        grid_col_count = 2
        mygrid = global_vars.make_grid(grid_row_count,grid_col_count)
        mygrid[0][0].metric("**Make playoffs**", format_probs(playoffs))
        mygrid[0][1].metric("**Top Seed**", format_probs(one_seed))
        mygrid[1][0].metric("**First Round Bye**", format_probs(bye))
        mygrid[1][1].metric("**Division Champ**", format_probs(win_div))
        mygrid[2][0].metric("**Wild Card**", format_probs(wild_card))
        mygrid[2][1].metric("**#1 Draft Pick**", format_probs(first_pick))

except:
    st.write("Please select a team above")        




