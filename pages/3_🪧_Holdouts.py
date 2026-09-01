import streamlit as st
import pandas as pd
import global_vars
import functions
import requests
from datetime import datetime
from google.cloud import bigquery

st.set_page_config(layout="wide")
st.title("🪧 2026 Holdouts")
st.divider()

# --- Custom Styling for candidate profile cards ---
st.markdown("""
<style>
    .candidate-card {
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
    .candidate-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.2);
        border-color: rgba(33, 150, 243, 0.4);
    }
    .candidate-name {
        font-size: 1.1rem;
        font-weight: 700;
        margin-top: 10px;
        margin-bottom: 2px;
    }
    .candidate-meta {
        font-size: 0.85rem;
        opacity: 0.7;
        margin-bottom: 5px;
    }
    .candidate-pts {
        font-size: 1.2rem;
        font-weight: 800;
        background: linear-gradient(45deg, #ff9800, #ff5722);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
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

# --- Fetch Holdout Eligible Players and Franchises from BigQuery ---
with st.spinner("Fetching holdout data..."):
    # Get eligible holdout players joined with dim_players to fetch their player_ids for photos
    query_players = """
        SELECT 
            h.name, 
            h.position, 
            h.franchise_name, 
            h.salary, 
            h.contract_year, 
            h.last_yr_pts,
            h.points_per_dollar,
            p.player_id
        FROM `mfl-374514.dbt_production.dim_holdout_players` h
        LEFT JOIN `mfl-374514.dbt_production.dim_players` p 
            ON h.name = p.player_name
        ORDER BY h.points_per_dollar DESC
    """
    players = run_live_query(query_players)
    players_df = pd.DataFrame(players)
    
    # Ensure numeric types
    if not players_df.empty:
        players_df['last_yr_pts'] = pd.to_numeric(players_df['last_yr_pts'], errors='coerce').fillna(0.0)
        players_df['salary'] = pd.to_numeric(players_df['salary'], errors='coerce').fillna(0.0)
        players_df['contract_year'] = pd.to_numeric(players_df['contract_year'], errors='coerce').fillna(0).astype(int)
        players_df['points_per_dollar'] = pd.to_numeric(players_df['points_per_dollar'], errors='coerce').fillna(0.0)

    # Get franchise list
    franchises = functions.bq_query("SELECT franchise_name FROM `mfl-374514.dbt_production.dim_franchises` ORDER BY franchise_name")
    franchises_df = pd.DataFrame(franchises)

# --- Filters in the Sidebar ---
if not players_df.empty:
    st.sidebar.header("Filter Options")
    all_franchises = sorted([f for f in players_df["franchise_name"].unique() if f is not None])
    selected_franchises = st.sidebar.multiselect(
        "Filter by Franchise",
        options=all_franchises,
        default=all_franchises,
        help="Select franchises to show their eligible holdout players."
    )
    all_positions = sorted([p for p in players_df["position"].unique() if p is not None])
    selected_positions = st.sidebar.multiselect(
        "Filter by Position",
        options=all_positions,
        default=all_positions,
        help="Select positions to show eligible holdout players."
    )
        
    # Filter the dataframe for both components
    filtered_players_df = players_df[
        (players_df["franchise_name"].isin(selected_franchises)) &
        (players_df["position"].isin(selected_positions))
    ]
else:
    filtered_players_df = pd.DataFrame()

# --- 1. Dynamic Top Candidate Profiles Grid ---
st.subheader("🔥 Top Holdout Candidates")
st.write("The leading eligible candidates based on salary efficiency in the 2025 season.")

if not filtered_players_df.empty:
    top_candidates = filtered_players_df.head(4)
    cols = st.columns(4, gap="medium")
    
    for idx, (_, row) in enumerate(top_candidates.iterrows()):
        with cols[idx]:
            display_name = format_display_name(row['name'])
            p_id = row['player_id']
            if p_id and pd.notna(p_id):
                photo_url = f"https://www49.myfantasyleague.com/player_photos_2014/{p_id}_thumb.jpg"
            else:
                photo_url = global_vars.player_icon
                
            pts_val = f"{row['last_yr_pts']:.1f}"
            
            card_html = f"""
            <div class="candidate-card">
                <img src="{photo_url}" style="width: 100px; height: 100px; border-radius: 50%; object-fit: cover; border: 3px solid rgba(255, 255, 255, 0.2);" onerror="this.src='{global_vars.player_icon}'">
                <div class="candidate-name">{display_name}</div>
                <div class="candidate-meta">{row['position']} • {row['franchise_name']}</div>
                <div class="candidate-meta" style="font-weight: 600; margin-top: -2px; margin-bottom: 5px;">Salary: ${row['salary']:.2f}</div>
                <div class="candidate-pts">{pts_val} Pts</div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
else:
    st.info("No candidates match the current filters.")

st.divider()

# --- 2. Interactive Data Table ---
st.subheader("📊 Eligible Players List")
st.write("All franchise players meeting the holdout cutoffs who have not held out in the last two years or had an extension last season.")

if not filtered_players_df.empty:
    st.dataframe(
        filtered_players_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "name": "Player",    
            "franchise_name": "Franchise",
            "position": "Position",
            "contract_year": "Years Remaining",
            "last_yr_pts": st.column_config.NumberColumn(
                "2025 Points",
                format="%.1f"
            ),  
            "salary": st.column_config.NumberColumn(
                "Salary",
                format="$%.2f"
            )
        },
        column_order=("name", "position", "salary", "contract_year", "franchise_name", "last_yr_pts")
    )
else:
    st.info("No holdout eligible players match the current filters.")

st.divider()

# --- 3. Live Ballot Status Tracker (Gamification) ---
st.subheader("🗳️ Ballot Submission Status")
st.write("See which franchises have submitted their ballot. Your choices are completely secret.")

def get_voted_teams():
    try:
        query = "SELECT DISTINCT voter_team FROM `mfl-374514.external.holdout_ballots_2026`"
        rows = run_live_query(query)
        return [r["voter_team"] for r in rows]
    except Exception as e:
        st.warning(f"Could not load voting status: {e}")
        return []

voted_teams = get_voted_teams()
team_names = [t for t in franchises_df["franchise_name"].tolist() if t is not None] if not franchises_df.empty else []

if team_names:
    cols = st.columns(4)
    for idx, name in enumerate(sorted(team_names)):
        with cols[idx % 4]:
            if name in voted_teams:
                st.markdown(f"🟢 **{name}**")
            else:
                st.markdown(f"⚪ <span style='color:grey;'>{name}</span>", unsafe_allow_html=True)

st.divider()

# --- 4. Secret Voting Form / Ballot ---
st.subheader("✍️ Submit / Edit Ballot")
st.write("Cast your votes for the players most likely to hold out. Your ballot is saved securely in the database.")



def insert_ballot_to_bigquery(team_name, selected_players):
    try:
        # Prepare row details
        row = {
            "voter_team": team_name,
            "vote_1": selected_players[0] if len(selected_players) > 0 else None,
            "vote_2": selected_players[1] if len(selected_players) > 1 else None,
            "vote_3": selected_players[2] if len(selected_players) > 2 else None,
            "vote_4": selected_players[3] if len(selected_players) > 3 else None,
            "vote_5": selected_players[4] if len(selected_players) > 4 else None,
            "submitted_at": datetime.now().isoformat()
        }
        
        # 1. Delete previous entry to avoid duplicates (parameterized to safely handle apostrophes/quotes in team names)
        delete_query = "DELETE FROM `mfl-374514.external.holdout_ballots_2026` WHERE voter_team = @team_name"
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("team_name", "STRING", team_name)
            ]
        )
        delete_job = functions.client.query(delete_query, job_config=job_config)
        delete_job.result() # Wait for deletion to complete
        
        # 2. Insert new row
        table_ref = functions.client.dataset("external").table("holdout_ballots_2026")
        errors = functions.client.insert_rows_json(table_ref, [row])
        if errors:
            st.error(f"BigQuery streaming insert failed: {errors}")
            return False
        return True
    except Exception as e:
        st.error(f"Failed to submit ballot: {e}")
        return False

# Dropdown to select Franchise
voter_team = st.selectbox("Select Your Franchise", [""] + team_names)

has_voted = False
prev_votes = {}
if voter_team:
    has_voted = voter_team in voted_teams
    if has_voted:
        st.warning(f"⚠️ **{voter_team}** has already submitted a ballot. Submitting a new ballot will overwrite your previous choices.")
        try:
            prev_query = "SELECT vote_1, vote_2, vote_3, vote_4, vote_5 FROM `mfl-374514.external.holdout_ballots_2026` WHERE voter_team = @team_name LIMIT 1"
            job_config = bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("team_name", "STRING", voter_team)]
            )
            prev_rows = [dict(r) for r in functions.client.query(prev_query, job_config=job_config).result()]
            if prev_rows:
                prev_votes = prev_rows[0]
        except Exception:
            prev_votes = {}

with st.form("ballot_form"):
    player_names = sorted([n for n in players_df["name"].tolist() if n is not None]) if not players_df.empty else []
    player_options = [""] + player_names
    
    st.write("Distribute up to 5 votes among eligible holdout candidates. You may select different players or vote for the same player multiple times.")
    
    def get_index(vote_key):
        val = prev_votes.get(vote_key)
        if val and val in player_options:
            return player_options.index(val)
        return 0

    col_a, col_b = st.columns(2, gap="medium")
    with col_a:
        v1 = st.selectbox("Vote 1 (Choice 1)", options=player_options, index=get_index("vote_1"), format_func=lambda x: format_display_name(x) if x else "— Select player (Required) —")
        v2 = st.selectbox("Vote 2 (Choice 2)", options=player_options, index=get_index("vote_2"), format_func=lambda x: format_display_name(x) if x else "— Select player (Optional) —")
        v3 = st.selectbox("Vote 3 (Choice 3)", options=player_options, index=get_index("vote_3"), format_func=lambda x: format_display_name(x) if x else "— Select player (Optional) —")
    with col_b:
        v4 = st.selectbox("Vote 4 (Choice 4)", options=player_options, index=get_index("vote_4"), format_func=lambda x: format_display_name(x) if x else "— Select player (Optional) —")
        v5 = st.selectbox("Vote 5 (Choice 5)", options=player_options, index=get_index("vote_5"), format_func=lambda x: format_display_name(x) if x else "— Select player (Optional) —")
    
    submit_button = st.form_submit_button(
        "Overwrite Ballot" if has_voted else "Submit Ballot", 
        use_container_width=True
    )

if submit_button:
    selected_players = [v for v in [v1, v2, v3, v4, v5] if v and v != ""]
    if not voter_team:
        st.error("Please select your Franchise first.")
    elif not selected_players:
        st.error("Please select at least one player choice.")
    else:
        with st.spinner("Saving ballot..."):
            if insert_ballot_to_bigquery(voter_team, selected_players):
                # 1. Visual celebration
                st.balloons()
                
                # 2. Discord notification (secret)
                try:
                    discord_secrets = st.secrets.get("discord", {})
                    webhook_url = discord_secrets.get("contracts_url")
                    if webhook_url:
                        action = "updated" if has_voted else "submitted"
                        message = f"🗳️ **{voter_team}** has {action} their 2026 Holdouts ballot!"
                        
                        # Calculate remaining teams to vote (excluding current team since they just voted)
                        remaining_teams = [t for t in team_names if t not in voted_teams and t != voter_team]
                        if remaining_teams:
                            remaining_str = ", ".join(sorted(remaining_teams))
                            message += f"\n⏳ **Teams left to vote:** {remaining_str}"
                        else:
                            message += "\n🎉 **All franchises have successfully submitted their ballots!**"
                            
                        requests.post(webhook_url, json={"content": message}, timeout=10)
                except Exception as e:
                    # Log silently - don't fail user experience
                    pass
                
                st.success(f"Success! Your ballot has been recorded for **{voter_team}**!")
                # Rerun to update the status grid
                st.rerun()
