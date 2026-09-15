import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import functions
import global_vars

st.set_page_config(layout="wide")

# Helper function to re-format names from "Last, First" to "First Last"
def format_display_name(name):
    if not name or not isinstance(name, str):
        return ""
    if ',' in name:
        parts = name.split(',')
        return f"{parts[1].strip()} {parts[0].strip()}"
    return name

# Helper function to run live BigQuery queries
def run_live_query(query):
    query_job = functions.client.query(query)
    rows_raw = query_job.result()
    return [dict(row) for row in rows_raw]

# --- Custom Styling ---
st.markdown("""
<style>
    .prospect-card {
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
    .prospect-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.2);
        border-color: rgba(255, 193, 7, 0.4);
    }
    .prospect-name {
        font-size: 1.1rem;
        font-weight: 700;
        margin-top: 10px;
        margin-bottom: 2px;
    }
    .prospect-meta {
        font-size: 0.85rem;
        opacity: 0.7;
        margin-bottom: 5px;
    }
    .prospect-pts {
        font-size: 1.2rem;
        font-weight: 800;
        color: #FFC107;
        margin-top: 5px;
    }
    .claim-box {
        background: rgba(255, 193, 7, 0.06);
        border: 1px solid rgba(255, 193, 7, 0.3);
        border-radius: 12px;
        padding: 20px;
        margin-top: 15px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Fetch Current Week
try:
    current_wk_query = "SELECT current_week FROM `mfl-374514.dbt_production.dim_current_week`"
    wk_rows = run_live_query(current_wk_query)
    current_wk = wk_rows[0]["current_week"] if wk_rows else 1
except Exception:
    current_wk = 1

st.title(f"🚕 Taxi Squad Claims — Week {current_wk}")
st.write(
    "Franchises may claim eligible players from opposing taxi squads. "
    "Once submitted, the owning franchise has **7 days** to either promote the player to their active roster or surrender him to the claiming team."
)

# FFP Rule Status Alert
if current_wk >= 8:
    st.info("🔓 **Week 8+:** Future Franchise Players (FFP) are now **open** for claims. Claiming an FFP player requires surrendering future draft pick compensation.")
else:
    st.info(f"🛡️ **Weeks 1–7 (Current: Week {current_wk}):** Designated Future Franchise Players (FFP) are **protected** from claims until Week 8.")

st.divider()

# --- Query Claimable Players ---
query_claimables = """
    SELECT 
        a.player_id,
        a.team,
        a.player_name,
        a.position,
        a.ytd_pts,
        a.pos_rank,
        a.owning_team,
        a.ffp_flag,
        a.comp_pick,
        a.claiming_team_id,
        a.claiming_team_name,
        a.current_team_name,
        b.discord_id as claiming_discord,
        c.discord_id as owning_discord
    FROM `mfl-374514.dbt_production.taxi_claimables` a 
    LEFT JOIN `mfl-374514.external.discord` b 
        ON a.claiming_team_id = b.franchise_id 
    LEFT JOIN `mfl-374514.external.discord` c 
        ON a.owning_team = c.franchise_id
"""

try:
    raw_claimables = run_live_query(query_claimables)
    claimables_df = pd.DataFrame(raw_claimables)
except Exception as e:
    st.error(f"Failed to load taxi claimable players: {e}")
    claimables_df = pd.DataFrame()

if not claimables_df.empty:
    # Ensure numeric types
    claimables_df['ytd_pts'] = pd.to_numeric(claimables_df['ytd_pts'], errors='coerce').fillna(0.0)
    claimables_df['ffp_flag'] = pd.to_numeric(claimables_df['ffp_flag'], errors='coerce').fillna(0).astype(int)
    claimables_df['name_display'] = claimables_df['player_name'].apply(format_display_name)
    
    # Filter FFP if before Week 8
    if current_wk < 8:
        claimables_df = claimables_df[claimables_df['ffp_flag'] == 0]

    # Check session state to see if a franchise is selected in the dropdown beneath the cards
    selected_franchise_val = st.session_state.get("selected_franchise", "— Choose your franchise —")
    
    if selected_franchise_val and selected_franchise_val not in ["— Choose your franchise —", "— All Franchises (League View) —"]:
        active_prospects_df = claimables_df[claimables_df["claiming_team_name"] == selected_franchise_val].copy()
        cards_title = f"🔥 Top Claimable Prospects for {selected_franchise_val}"
        cards_desc = f"Highest-scoring taxi squad players eligible to be claimed by **{selected_franchise_val}** in Week {current_wk}."
    else:
        active_prospects_df = claimables_df.copy()
        cards_title = "🔥 Top Claimable Prospects"
        cards_desc = f"Highest-scoring taxi squad players eligible to be claimed in Week {current_wk}."

    # --- 1. Top Claimable Prospects Grid ---
    st.subheader(cards_title)
    st.write(cards_desc)
    
    # Deduplicate by player_id to show top prospects
    unique_prospects = active_prospects_df.sort_values('ytd_pts', ascending=False).drop_duplicates(subset=['player_id']).head(4)
    
    if not unique_prospects.empty:
        cols = st.columns(min(4, len(unique_prospects)), gap="medium")
        for idx, (_, row) in enumerate(unique_prospects.iterrows()):
            with cols[idx]:
                p_id = row.get('player_id')
                if p_id and pd.notna(p_id):
                    photo_url = f"https://www49.myfantasyleague.com/player_photos_2014/{p_id}_thumb.jpg"
                else:
                    photo_url = global_vars.player_icon
                    
                ffp_badge = f"<div style='color: #FF9800; font-size: 0.8rem; font-weight: 600; margin-bottom: 4px;'>⚠️ FFP (R{int(row['comp_pick']) if pd.notna(row['comp_pick']) else '?'})</div>" if row['ffp_flag'] == 1 else ""
                
                card_html = (
                    f'<div class="prospect-card">'
                    f'<img src="{photo_url}" style="width: 100px; height: 100px; border-radius: 50%; object-fit: cover; border: 3px solid rgba(255, 193, 7, 0.4);" onerror="this.src=\'{global_vars.player_icon}\'">'
                    f'<div class="prospect-name">{row["name_display"]}</div>'
                    f'<div class="prospect-meta">{row["position"]} • Owner: {row["current_team_name"]}</div>'
                    f'{ffp_badge}'
                    f'<div class="prospect-pts">{row["ytd_pts"]:.1f} Pts</div>'
                    f'</div>'
                )
                st.markdown(card_html, unsafe_allow_html=True)
    else:
        st.info("No claimable prospects found for this selection.")
    
    st.divider()

    # --- 2. Franchise Selector & Claim Submission ---
    st.subheader("✍️ Submit a Taxi Claim")
    
    available_claiming_teams = sorted([t for t in claimables_df["claiming_team_name"].unique() if t])
    
    selected_team = st.selectbox(
        "Select Your Franchise",
        ["— Choose your franchise —"] + available_claiming_teams,
        key="selected_franchise"
    )
    
    if selected_team != "— Choose your franchise —":
        team_claimables = claimables_df[claimables_df["claiming_team_name"] == selected_team].copy().sort_values('ytd_pts', ascending=False).reset_index(drop=True)
        
        if not team_claimables.empty:
            # Position & Search filters
            col_filter1, col_filter2 = st.columns([1, 2], gap="medium")
            with col_filter1:
                all_pos = sorted(team_claimables["position"].unique().tolist())
                sel_pos = st.multiselect("Filter by Position", options=all_pos, default=all_pos)
            with col_filter2:
                all_owners = sorted(team_claimables["current_team_name"].unique().tolist())
                sel_owners = st.multiselect("Filter by Owning Franchise", options=all_owners, default=all_owners)
                
            filtered_team_claimables = team_claimables[
                (team_claimables["position"].isin(sel_pos)) & 
                (team_claimables["current_team_name"].isin(sel_owners))
            ]
            
            # Format comp pick text
            filtered_team_claimables["comp_display"] = filtered_team_claimables.apply(
                lambda r: f"Round {int(r['comp_pick'])}" if r['ffp_flag'] == 1 and pd.notna(r['comp_pick']) else "None", 
                axis=1
            )
            
            st.markdown(f"#### Eligible Players for **{selected_team}** ({len(filtered_team_claimables)} available)")
            
            st.dataframe(
                filtered_team_claimables,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "name_display": "Player",
                    "position": "Pos",
                    "current_team_name": "Current Owner",
                    "ytd_pts": st.column_config.NumberColumn(f"{global_vars.league_year} Pts", format="%.2f"),
                    "comp_display": "Draft Compensation Required",
                    "pos_rank": "Pos Rank"
                },
                column_order=("name_display", "position", "current_team_name", "ytd_pts", "comp_display", "pos_rank")
            )
            
            # Claim Submission Form
            st.markdown("---")
            st.markdown(f"### 🎯 Initiate Claim for **{selected_team}**")
            
            player_choices = ["— Select player to claim —"] + [
                f"{r['name_display']} ({r['position']} - {r['current_team_name']})"
                for _, r in filtered_team_claimables.iterrows()
            ]
            
            chosen_player_str = st.selectbox("Choose player to claim", player_choices)
            
            if chosen_player_str != "— Select player to claim —":
                # Find matching row
                chosen_idx = player_choices.index(chosen_player_str) - 1
                target_player = filtered_team_claimables.iloc[chosen_idx]
                
                target_name = target_player['name_display']
                target_raw_name = target_player['player_name']
                target_owner = target_player['current_team_name']
                target_pos = target_player['position']
                target_pts = target_player['ytd_pts']
                target_ffp = target_player['ffp_flag'] == 1
                target_comp = target_player['comp_pick']
                claiming_discord = target_player.get('claiming_discord')
                owning_discord = target_player.get('owning_discord')
                
                # Claim detail card preview
                with st.container():
                    claim_html = (
                        f'<div class="claim-box">'
                        f'<h4 style="margin-top: 0; color: #FFC107;">Claim Details Confirmation</h4>'
                        f'<p><strong>Claiming Franchise:</strong> {selected_team}</p>'
                        f'<p><strong>Target Player:</strong> {target_name} ({target_pos}) • <em>{target_pts:.1f} YTD Pts</em></p>'
                        f'<p><strong>Current Owner:</strong> {target_owner}</p>'
                        f'</div>'
                    )
                    st.markdown(claim_html, unsafe_allow_html=True)
                    
                    if target_ffp:
                        comp_str = f"Round {int(target_comp)}" if pd.notna(target_comp) else "Future Round"
                        st.warning(
                            f"⚠️ **FFP Claim Warning:** **{target_name}** is a designated Future Franchise Player (FFP). "
                            f"If this claim is successful, **{selected_team}** must surrender a future draft pick in **{comp_str}** to **{target_owner}**.",
                            icon="⚠️"
                        )
                
                confirm_claim = st.button(
                    f"🚀 Submit Official Claim on {target_name}", 
                    type="primary",
                    use_container_width=True
                )
                
                if confirm_claim:
                    with st.spinner("Submitting taxi claim..."):
                        try:
                            discord_secrets = st.secrets.get("discord", {})
                            webhook_url = discord_secrets.get("taxi_url")
                            
                            current_time = datetime.now()
                            deadline_str = (current_time + timedelta(weeks=1)).strftime("%A, %B %d, %Y at %I:%M %p")
                            
                            # Build Discord message with user mentions
                            claiming_tag = f"<@{claiming_discord}>" if claiming_discord and pd.notna(claiming_discord) else f"**{selected_team}**"
                            owning_tag = f"<@{owning_discord}>" if owning_discord and pd.notna(owning_discord) else f"**{target_owner}**"
                            
                            if target_ffp:
                                comp_str = f"Round {int(target_comp)}" if pd.notna(target_comp) else "Draft Pick"
                                message = (
                                    f"🚕 **TAXI SQUAD CLAIM (FFP)**\n\n"
                                    f"{claiming_tag} is submitting an official claim on **{target_raw_name}** ({target_pos}) from {owning_tag}.\n"
                                    f"⚠️ **Compensation:** This is an FFP claim requiring **{comp_str}** draft pick compensation.\n"
                                    f"⏳ **Resolution Deadline:** {owning_tag} must promote or surrender by **{deadline_str}**."
                                )
                            else:
                                message = (
                                    f"🚕 **TAXI SQUAD CLAIM**\n\n"
                                    f"{claiming_tag} is submitting an official claim on **{target_raw_name}** ({target_pos}) from {owning_tag}.\n"
                                    f"⏳ **Resolution Deadline:** {owning_tag} must promote or surrender by **{deadline_str}**."
                                )
                                
                            if webhook_url:
                                resp = requests.post(webhook_url, json={"content": message}, timeout=10)
                                resp.raise_for_status()
                                
                            st.balloons()
                            st.toast("Taxi claim successfully submitted!", icon="🎉")
                            st.success(
                                f"🎉 Claim successfully recorded for **{target_name}**! "
                                f"A Discord notification has been dispatched. **{target_owner}** has until **{deadline_str}** to respond."
                            )
                        except Exception as e:
                            st.error(f"Failed to submit claim to Discord: {e}")
        else:
            st.info(f"No eligible taxi players available for **{selected_team}** to claim.")
    else:
        st.subheader("📊 League-Wide Taxi Squad Claimables")
        st.write("Select your franchise from the dropdown above to filter your available claims and submit a claim.")
        
        # Position & Owner filters for league view
        col_f1, col_f2 = st.columns([1, 2], gap="medium")
        with col_f1:
            all_pos = sorted(claimables_df["position"].unique().tolist())
            sel_pos = st.multiselect("Filter by Position", options=all_pos, default=all_pos, key="league_pos_filter")
        with col_f2:
            all_owners = sorted(claimables_df["current_team_name"].unique().tolist())
            sel_owners = st.multiselect("Filter by Owning Franchise", options=all_owners, default=all_owners, key="league_owner_filter")
            
        league_display = claimables_df[
            (claimables_df["position"].isin(sel_pos)) & 
            (claimables_df["current_team_name"].isin(sel_owners))
        ].drop_duplicates(subset=["player_id"]).sort_values('ytd_pts', ascending=False).reset_index(drop=True)
        
        league_display["comp_display"] = league_display.apply(
            lambda r: f"Round {int(r['comp_pick'])}" if r['ffp_flag'] == 1 and pd.notna(r['comp_pick']) else "None", 
            axis=1
        )
        
        st.dataframe(
            league_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "name_display": "Player",
                "position": "Pos",
                "current_team_name": "Current Owner",
                "ytd_pts": st.column_config.NumberColumn(f"{global_vars.league_year} Pts", format="%.2f"),
                "comp_display": "Draft Compensation Required",
                "pos_rank": "Pos Rank"
            },
            column_order=("name_display", "position", "current_team_name", "ytd_pts", "comp_display", "pos_rank")
        )
else:
    st.info("No taxi claimable players found for this week.")
