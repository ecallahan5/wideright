import streamlit as st
import pandas as pd
import requests
import datetime
import functions
import global_vars

st.set_page_config(layout="wide")
st.title("🆓 Annual Free Extensions")
st.divider()

# --- Custom Styling for candidate profile cards ---
st.markdown("""
<style>
    .player-card {
        background: rgba(128, 128, 128, 0.05);
        border-radius: 16px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(5px);
        -webkit-backdrop-filter: blur(5px);
        border: 1px solid rgba(128, 128, 128, 0.2);
        padding: 20px;
        text-align: center;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .player-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.2);
        border-color: rgba(76, 175, 80, 0.4);
    }
    .player-name {
        font-size: 1.1rem;
        font-weight: 700;
        margin-top: 10px;
        margin-bottom: 2px;
    }
    .player-meta {
        font-size: 0.85rem;
        opacity: 0.7;
        margin-bottom: 5px;
    }
    .player-salary {
        font-size: 1.2rem;
        font-weight: 800;
        color: #4CAF50;
        margin-top: 5px;
    }
    
    /* Option Metric Styles */
    .metric-container {
        background: rgba(128, 128, 128, 0.05);
        padding: 15px;
        border-radius: 12px;
        border: 1px solid rgba(128, 128, 128, 0.15);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to re-format names from "Last, First" to "First Last"
def format_display_name(name):
    if ',' in name:
        parts = name.split(',')
        return f"{parts[1].strip()} {parts[0].strip()}"
    return name

# Helper function to run live, non-cached BigQuery queries
def run_live_query(query):
    query_job = functions.client.query(query)
    rows_raw = query_job.result()
    return [dict(row) for row in rows_raw]

# --- Info Header ---
st.info("""
💡 **Rules of the Annual Free Extension:**
* Each franchise receives **one free extension** per season to extend a player in the final year of their contract.
* The player is extended at a premium multiplier based on the length:
  * **1 Year Extension:** **15% Raise** (Minimum **$5.00**)
  * **2 Year Extension:** **30% Raise** (Minimum **$12.00**)
  * **3 Year Extension:** **45% Raise** (Minimum **$24.00**)
* If the player's current salary is below the minimum required for the chosen term, their current year's salary will be immediately adjusted upward to the minimum.
""", icon="ℹ️")

# --- Fetch Data from BigQuery ---
with st.spinner("Loading extension eligibility data..."):
    try:
        # Get current season
        current_season = global_vars.league_year
        
        # Pull eligible players
        elig_query = "SELECT * FROM `mfl-374514.dbt_production.dim_free_ext_elig`"
        elig_data = functions.bq_query(elig_query)
        ext_eligible_df = pd.DataFrame(elig_data)
        
        if not ext_eligible_df.empty:
            # Map position order and sort
            ext_eligible_df['position_order'] = ext_eligible_df['position'].map(global_vars.sort_mapping['index'])
            ext_eligible_df = ext_eligible_df.rename(columns={
                "player_name": "Name",
                "position": "Position", 
                "salary": "Salary"
            }).sort_values('position_order')
            
            # Keep numeric salary for calculations
            ext_eligible_df["Salary_Numeric"] = pd.to_numeric(ext_eligible_df["Salary"], errors='coerce').fillna(0.0)
            ext_eligible_df["Salary_Display"] = ext_eligible_df["Salary_Numeric"].apply(lambda x: f"${x:,.2f}")
            
        # Get exclusion list of teams that already used their free extension this season
        exclusion_query = f"""
            SELECT DISTINCT franchise 
            FROM `mfl-374514.external.extensions` 
            WHERE Ext__Season = {current_season}
              AND method = 'Allotted Extension'
        """
        exclusion_data = functions.bq_query(exclusion_query)
        exclusion_list = [item['franchise'] for item in exclusion_data]
        
    except Exception as e:
        st.error(f"Error fetching data from database: {e}")
        ext_eligible_df = pd.DataFrame()
        exclusion_list = []

# --- Sidebar Filters ---
if not ext_eligible_df.empty:
    st.sidebar.header("Filter Options")
    
    # Get all teams
    all_teams = sorted([t for t in ext_eligible_df["franchise_name"].unique() if t is not None])
    # Filter out teams that already used their extension
    available_teams = [team for team in all_teams if team not in exclusion_list]
    
    selected_team = st.sidebar.selectbox(
        "Choose a Team",
        options=available_teams,
        index=None,
        placeholder="Select Franchise",
        help="Only includes franchises that have not used their annual free extension this season."
    )
else:
    selected_team = None

# --- Session State Management ---
if "selected_player_str" not in st.session_state:
    st.session_state.selected_player_str = None
if "prev_selected_team" not in st.session_state:
    st.session_state.prev_selected_team = None

# Reset player selection if team changes
if selected_team != st.session_state.prev_selected_team:
    st.session_state.selected_player_str = None
    st.session_state.prev_selected_team = selected_team

# --- Main UI Flow ---
if selected_team:
    team_elig = ext_eligible_df[ext_eligible_df["franchise_name"] == selected_team]
    
    if not team_elig.empty:
        # Multi-select positions
        unique_positions = sorted(team_elig["Position"].dropna().unique())
        pos_order = team_elig["Position"].map(global_vars.sort_mapping['index'])
        unique_positions = team_elig.loc[pos_order.sort_values().index, "Position"].unique().tolist()
        
        selected_positions = st.sidebar.multiselect(
            "Filter Roster by Position",
            options=unique_positions,
            default=unique_positions
        )
        
        # Filter eligible players
        filtered_team_elig = team_elig[team_elig["Position"].isin(selected_positions)]
        
        if not filtered_team_elig.empty:
            # Display summary grid of eligible players as cards
            st.markdown("### 📋 Eligible Roster Summary")
            st.write("These players are in the final year of their contracts and are eligible for a free extension:")
            
            # Render grid of player cards (4 columns per row)
            cols_per_row = 4
            num_players = len(filtered_team_elig)
            for i in range(0, num_players, cols_per_row):
                row_players = filtered_team_elig.iloc[i : i + cols_per_row]
                cols = st.columns(cols_per_row, gap="medium")
                for idx, (_, row) in enumerate(row_players.iterrows()):
                    with cols[idx]:
                        p_display_name = format_display_name(row["Name"])
                        p_id = row["player_id"]
                        if p_id and pd.notna(p_id):
                            photo_url = f"https://www49.myfantasyleague.com/player_photos_2014/{p_id}_thumb.jpg"
                        else:
                            photo_url = global_vars.player_icon
                            
                        card_html = f"""
                        <div class="player-card">
                            <img src="{photo_url}" style="width: 100px; height: 100px; border-radius: 50%; object-fit: cover; border: 3px solid rgba(255, 255, 255, 0.2);" onerror="this.src='{global_vars.player_icon}'">
                            <div class="player-name">{p_display_name}</div>
                            <div class="player-meta">{row['Position']} • {selected_team}</div>
                            <div class="player-salary">${row['Salary_Numeric']:.2f}</div>
                        </div>
                        """
                        st.markdown(card_html, unsafe_allow_html=True)
                        
                        # Interactive Select button below card
                        if st.button("Select Player", key=f"btn_{p_id}_{i}_{idx}", use_container_width=True):
                            st.session_state.selected_player_str = f"{row['Name']} - {row['Position']}"
            
            st.write("")
            
            # Dropdown to select player
            player_list = (filtered_team_elig["Name"] + " - " + filtered_team_elig["Position"]).tolist()
            
            # Reset selection if it's no longer in the filtered list
            if st.session_state.selected_player_str and st.session_state.selected_player_str not in player_list:
                st.session_state.selected_player_str = None
                
            selected_player_str = st.selectbox(
                "Select Player to Extend",
                options=player_list,
                key="selected_player_str",
                placeholder="Choose a player..."
            )
            
            if selected_player_str:
                # Find selected player record
                player_row = filtered_team_elig[
                    (filtered_team_elig["Name"] + " - " + filtered_team_elig["Position"]) == selected_player_str
                ].iloc[0]
                
                player_name = player_row["Name"]
                player_pos = player_row["Position"]
                player_id = player_row["player_id"]
                raw_salary = player_row["Salary_Numeric"]
                
                # Show Player Profile Card
                photo_url = f"https://www49.myfantasyleague.com/player_photos_2014/{player_id}_thumb.jpg"
                
                st.divider()
                
                # Use st.columns to display player profile side-by-side with calculations
                col_profile, col_calc = st.columns([1, 2], gap="large")
                
                with col_profile:
                    st.markdown("#### Player Profile")
                    card_html = f"""
                    <div class="player-card">
                        <img src="{photo_url}" style="width: 120px; height: 120px; border-radius: 50%; object-fit: cover; border: 3px solid rgba(255, 255, 255, 0.2);" onerror="this.src='{global_vars.player_icon}'">
                        <div class="player-name">{format_display_name(player_name)}</div>
                        <div class="player-meta">{player_pos} • {selected_team}</div>
                        <div class="player-salary">${raw_salary:.2f} (Current)</div>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)
                
                with col_calc:
                    st.markdown("#### Extension Salary Options")
                    
                    # Calculate values
                    ext_1_min, ext_2_min, ext_3_min = 5.0, 12.0, 24.0
                    
                    ext_1_calc = raw_salary * 1.15
                    ext_2_calc = raw_salary * 1.30
                    ext_3_calc = raw_salary * 1.45
                    
                    ext_1_salary = max(ext_1_calc, ext_1_min)
                    ext_2_salary = max(ext_2_calc, ext_2_min)
                    ext_3_salary = max(ext_3_calc, ext_3_min)
                    
                    # Display metrics
                    metric_1, metric_2, metric_3 = st.columns(3)
                    with metric_1:
                        st.markdown(
                            f'<div class="metric-container">'
                            f'<div style="font-size: 0.9rem; opacity: 0.8;">1 Year Option</div>'
                            f'<div style="font-size: 1.6rem; font-weight: 800; color: #2196F3; margin-top: 5px;">${ext_1_salary:.2f}</div>'
                            f'<div style="font-size: 0.75rem; opacity: 0.6; margin-top: 2px;">(15% premium)</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                    with metric_2:
                        st.markdown(
                            f'<div class="metric-container">'
                            f'<div style="font-size: 0.9rem; opacity: 0.8;">2 Year Option</div>'
                            f'<div style="font-size: 1.6rem; font-weight: 800; color: #2196F3; margin-top: 5px;">${ext_2_salary:.2f}</div>'
                            f'<div style="font-size: 0.75rem; opacity: 0.6; margin-top: 2px;">(30% premium)</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                    with metric_3:
                        st.markdown(
                            f'<div class="metric-container">'
                            f'<div style="font-size: 0.9rem; opacity: 0.8;">3 Year Option</div>'
                            f'<div style="font-size: 1.6rem; font-weight: 800; color: #2196F3; margin-top: 5px;">${ext_3_salary:.2f}</div>'
                            f'<div style="font-size: 0.75rem; opacity: 0.6; margin-top: 2px;">(45% premium)</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                        
                    st.write("")
                    
                    # Norwood Chatbot Interactive Interface
                    with st.chat_message("Norwood", avatar=global_vars.norwood_avatar):
                        st.write(f"Do you want to extend **{format_display_name(player_name)}**?")
                        extend_choice = st.checkbox("Yes, let's extend him!")
                        
                        if extend_choice:
                            ext_length = st.radio(
                                f"Select extension term for {format_display_name(player_name)}:",
                                options=[1, 2, 3],
                                format_func=lambda x: f"{x} Year{'s' if x > 1 else ''}",
                                horizontal=True
                            )
                            
                            # Determine salary and warning triggers
                            if ext_length == 1:
                                target_salary = ext_1_salary
                                adj_needed = ext_1_calc < ext_1_min
                            elif ext_length == 2:
                                target_salary = ext_2_salary
                                adj_needed = ext_2_calc < ext_2_min
                            else:
                                target_salary = ext_3_salary
                                adj_needed = ext_3_calc < ext_3_min
                                
                            if adj_needed:
                                st.warning(
                                    f"⚠️ **Salary Adjustment Alert:** The calculated extension salary (${raw_salary * (1 + (ext_length*0.15 - 0.15 + 0.15)):.2f}) is below the positional minimum of **${target_salary:.2f}**. "
                                    f"Proceeding will immediately adjust {format_display_name(player_name)}'s current contract salary upward to **${target_salary:.2f}**.",
                                    icon="⚠️"
                                )
                                
                            st.write(f"Confirm extension of **{format_display_name(player_name)}** for **{ext_length} Year{'s' if ext_length > 1 else ''}** at a salary of **${target_salary:.2f}/yr**.")
                            
                            extend_button = st.button("Extend him!")
                            
                            if extend_button:
                                with st.spinner("Submitting extension claim..."):
                                    try:
                                        webhook_url = st.secrets["discord"]["contracts_url"]
                                        
                                        if adj_needed:
                                            content = (
                                                f"🚨 **ANNUAL FREE EXTENSION ALERT!** 🚨\n\n"
                                                f"**{selected_team}** has extended **{format_display_name(player_name)} ({player_pos})** for **{ext_length} years** at a salary of **${target_salary:.2f}**.\n\n"
                                                f"⚠️ *The current contract is below the minimum required. <@197385905638604800> will need to adjust the current year's salary.*"
                                            )
                                        else:
                                            content = (
                                                f"🚨 **ANNUAL FREE EXTENSION ALERT!** 🚨\n\n"
                                                f"**{selected_team}** has extended **{format_display_name(player_name)} ({player_pos})** for **{ext_length} years** at a salary of **${target_salary:.2f}**."
                                            )
                                            
                                        # Post to discord
                                        r = requests.post(webhook_url, json={"content": content}, timeout=10)
                                        if r.status_code in [200, 204]:
                                            st.cache_data.clear()  # Clear cache so dropdown list refreshes immediately
                                            st.balloons()
                                            st.success(f"Success! Extension submitted for **{format_display_name(player_name)}**! The Discord announcement has been sent.")
                                            st.toast(f"Extension claim submitted!", icon='🎉')
                                        else:
                                            st.error(f"Failed to send Discord alert: {r.status_code} {r.text}")
                                    except Exception as e:
                                        st.error(f"Failed to submit extension claim: {e}")
        else:
            st.info("No players match the selected positions.")
    else:
        st.info("This team has no eligible final-year players for a free extension.")
else:
    st.info("👈 Please select a franchise from the left sidebar to begin.")
