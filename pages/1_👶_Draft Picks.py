import streamlit as st
import pandas as pd
import plotly.express as px
import global_vars
import functions

st.set_page_config(layout="wide")
st.title("👶 Draft Picks")
st.divider()

def standardize_df(df, required_cols):
    if df is None:
        return pd.DataFrame(columns=required_cols)
    # Standardize column names to lowercase
    df.columns = [col.lower() for col in df.columns]
    # Ensure all required columns exist (fill with None if missing)
    for col in required_cols:
        if col not in df.columns:
            df[col] = None
    return df

# 1. Fetch Draft Picks and Franchises Data
picks = functions.bq_query("SELECT * FROM `mfl-374514.dbt_production.dim_draft_picks`")
picks_df = pd.DataFrame(picks)
picks_df = standardize_df(picks_df, ["year", "round_num", "pick_num", "original_owner", "pick_owner"])

# Convert columns to numeric, handling empty/NaN values safely
picks_df["year"] = pd.to_numeric(picks_df["year"], errors="coerce").fillna(0).astype(int)
picks_df["round_num"] = pd.to_numeric(picks_df["round_num"], errors="coerce").fillna(0).astype(int)
picks_df["pick_num"] = pd.to_numeric(picks_df["pick_num"], errors="coerce").fillna(0).astype(int)

teams = functions.bq_query("SELECT franchise_id, franchise_name, division, icon FROM `mfl-374514.dbt_production.dim_franchises`")
teams_df = pd.DataFrame(teams)
teams_df = standardize_df(teams_df, ["franchise_id", "franchise_name", "division", "icon"])

# 2. Build Franchise ID to Name Lookup Map for Trade Tracing
id_to_name = dict(zip(teams_df["franchise_id"], teams_df["franchise_name"]))

# 3. Create Collapsible Sidebar Filters
st.sidebar.header("Filter Options")

team_select = st.sidebar.multiselect(
    "Choose the Teams",
    sorted(teams_df["franchise_name"].unique()),
    default=sorted(teams_df["franchise_name"].unique()),
    help="Filter the picks for specific franchises."
)

year_select = st.sidebar.multiselect(
    "Choose the Years",
    sorted(picks_df["year"].unique()),
    default=sorted(picks_df["year"].unique()),
    help="Filter the picks for specific draft years."
)

round_select = st.sidebar.multiselect(
    "Choose the Rounds",
    sorted(picks_df["round_num"].unique()),
    default=sorted(picks_df["round_num"].unique()),
    help="Filter the picks for specific rounds."
)

# 4. Implement Tabs Layout
tab_grid, tab_leaderboard = st.tabs(["Grid View", "Leaderboard"])

# Helper function to generate styled badge HTML
def make_badge(text, bg_color):
    return f'<span style="background-color:{bg_color}; color:white; padding:4px 8px; border-radius:12px; font-weight:bold; font-size:11px; margin-right:5px; display:inline-block; margin-bottom:5px; font-family:sans-serif; box-shadow: 0 1px 3px rgba(0,0,0,0.12);">{text}</span>'

# Define badge colors for each round
ROUND_COLORS = {
    1: "#4CAF50",  # Green
    2: "#2196F3",  # Blue
    3: "#FF9800",  # Orange
    4: "#757575",  # Grey
    5: "#9E9E9E",  # Light Grey
}

# --- TAB 1: Grid View ---
with tab_grid:
    if not team_select:
        st.warning("Please select at least one team in the sidebar to display draft picks.")
    else:
        # Lay out teams in 3-column rows
        cols_per_row = 3
        selected_teams = sorted(team_select)
        
        for i in range(0, len(selected_teams), cols_per_row):
            row_teams = selected_teams[i:i + cols_per_row]
            cols = st.columns(cols_per_row)
            
            for team_name, col in zip(row_teams, cols):
                with col:
                    # Find team info
                    team_info = teams_df.loc[teams_df["franchise_name"] == team_name]
                    if not team_info.empty:
                        franchise_id = team_info["franchise_id"].values[0]
                        icon_url = team_info["icon"].values[0]
                        division = team_info["division"].values[0]
                        
                        # Create card container
                        with st.container(border=True):
                            # Header with avatar logo and details
                            header_col1, header_col2 = st.columns([1, 3])
                            header_col1.image(icon_url, width=64)
                            header_col2.markdown(f"### **{team_name}**")
                            header_col2.markdown(f"<small style='color:grey;'>Division: {division}</small>", unsafe_allow_html=True)
                            
                            st.divider()
                            
                            # Filter picks for this owner
                            team_picks = picks_df.loc[
                                (picks_df["pick_owner"] == franchise_id) &
                                (picks_df["year"].isin(year_select)) &
                                (picks_df["round_num"].isin(round_select))
                            ].sort_values(["year", "round_num"])
                            
                            if team_picks.empty:
                                st.info("No matching draft picks found.")
                            else:
                                # Group picks by year
                                for year, year_df in team_picks.groupby("year"):
                                    st.markdown(f"**🗓️ {year}**")
                                    badge_html = ""
                                    
                                    for _, pick in year_df.iterrows():
                                        round_val = int(pick["round_num"])
                                        pick_val = int(pick["pick_num"])
                                        orig_owner_id = pick["original_owner"]
                                        
                                        # Determine round color
                                        color = ROUND_COLORS.get(round_val, "#9E9E9E")
                                        
                                        # Construct label
                                        label = f"Rd {round_val}"
                                        if pick_val > 0:
                                            label += f" ({round_val}.{pick_val:02d})"
                                            
                                        # Add trade tracing
                                        if orig_owner_id != franchise_id:
                                            orig_name = id_to_name.get(orig_owner_id, orig_owner_id)
                                            label += f" via {orig_name}"
                                            
                                        badge_html += make_badge(label, color)
                                        
                                    st.markdown(badge_html, unsafe_allow_html=True)
                                    st.write("") # Tiny spacer

# --- TAB 2: Leaderboard & Insights ---
with tab_leaderboard:
    st.subheader("📊 Draft Capital Insights")
    
    # 1. Total Draft Picks Count Leaderboard
    # Group draft picks by owner
    leaderboard_data = picks_df.loc[
        (picks_df["year"].isin(year_select)) &
        (picks_df["round_num"].isin(round_select))
    ].groupby("pick_owner").size().reset_index(name="Picks Owned")
    
    # Merge with team names
    leaderboard_data = leaderboard_data.merge(teams_df, left_on="pick_owner", right_on="franchise_id")
    leaderboard_data = leaderboard_data.sort_values("Picks Owned", ascending=True) # Ascending for horizontal bar orientation
    
    if leaderboard_data.empty:
        st.info("No data available for the current filters.")
    else:
        # Create horizontal bar chart
        fig = px.bar(
            leaderboard_data,
            x="Picks Owned",
            y="franchise_name",
            orientation="h",
            labels={"franchise_name": "Franchise", "Picks Owned": "Total Picks Owned"},
            title="Total Future Draft Picks Owned by Franchise (Filtered)",
            color="Picks Owned",
            color_continuous_scale=px.colors.sequential.Viridis
        )
        fig.update_layout(height=500, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
