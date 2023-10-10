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

st.title("Projected Standings")

st.header("After Week "+str(after_wk))
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

#Table style
st.markdown(global_vars.hide_table_row_index, unsafe_allow_html=True)

for col_num in list(range(grid_col_count)):
    div_df = merged_df.loc[merged_df["division"] == "0"+str(col_num)].rename(columns={"franchise_name": "Team", "proj_wins" : "Projected Wins"})\
    .sort_values(by = 'Projected Wins', ascending=False)
    div_name = div_df[["division_name"]].values[0][0]
    mygrid[0][col_num].subheader(div_name, divider=True)
    mygrid[0][col_num].dataframe(div_df[["Team", "Projected Wins"]], hide_index=True, use_container_width = True)
