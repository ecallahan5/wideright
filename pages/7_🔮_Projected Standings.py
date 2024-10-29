import streamlit as st
import functions
import global_vars
import pandas as pd

st.set_page_config(layout="wide")



after_wk = functions.bq_query("SELECT recent_completed_week FROM `mfl-374514.dbt_production.dim_current_week`")[0]["recent_completed_week"]

st.title("Projected Standings After Week "+str(after_wk))

st.divider()

proj_wins = functions.bq_query(f"SELECT franchise_name as `Franchise Name`, round(proj_wins,1) as `Projected Wins`, division \
                               FROM `mfl-374514.dbt_production.fct_reg_season_model` a\
                               join `mfl-374514.dbt_production.dim_franchises` b \
                                   on a.franchise_id = b.franchise_id \
                               where after_week = {after_wk} \
                         order by 3, 2 desc ")
proj_wins_df = pd.DataFrame(proj_wins)

grid_row_count = 1
grid_col_count = 3

mygrid = global_vars.make_grid(grid_row_count,grid_col_count)

places_df = pd.DataFrame()

for col_num, division in enumerate(proj_wins_df["division"].unique()):
# Filter and sort the DataFrame for the specific division
    div_df = proj_wins_df.loc[proj_wins_df["division"] == division].sort_values(by='Projected Wins', ascending=False).reset_index()
    div_df["place"] = div_df.index + 1  # Add a 'place' column
    
    # Display the division name as a subheader in the appropriate column
    mygrid[0][col_num].subheader(division, divider=True)
    
    # Display the division's data in the appropriate column
    mygrid[0][col_num].dataframe(div_df[["Franchise Name", "Projected Wins"]], hide_index=True, use_container_width=True)
    
    # Prepare a DataFrame of the division's places and append to `places_df`
    div_places_df = div_df[["division", "Franchise Name", "place"]]
    places_df = pd.concat([places_df, div_places_df])

st.divider()
st.header("Team Profiles")

playoff_probs = functions.bq_query(f"SELECT * \
                               FROM `mfl-374514.dbt_production.fct_reg_season_model` a\
                               join `mfl-374514.dbt_production.dim_franchises` b \
                                   on a.franchise_id = b.franchise_id \
                               where after_week = {after_wk} \
                         order by 3, 2 desc ")
playoff_probs_df = pd.DataFrame(playoff_probs)


team = st.selectbox(
    '**View Team Profile**', sorted(playoff_probs_df["franchise_name"].unique()), \
        index=None, placeholder="Choose a team")

team_df = playoff_probs_df.loc[playoff_probs_df["franchise_name"] == team]

try:
    helmet = team_df["icon"].values[0]
    proj_rk = places_df.loc[places_df["Franchise Name"] == team]["place"].values[0]
    if proj_rk == 1:
        proj_rk_ord = '1st'
    elif proj_rk == 2:
        proj_rk_ord = '2nd'
    elif proj_rk == 3:
        proj_rk_ord = '3rd'
    else:
        proj_rk_ord = '4th'
    div = team_df["division"].values[0]

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
        mygrid[0][1].subheader("Current Projected Place in the "+div+" division:", divider = True)
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




