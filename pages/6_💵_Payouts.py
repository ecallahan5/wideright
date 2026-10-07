import sys
import os

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import streamlit as st
import pandas as pd
import plotly.express as px
from google.cloud import bigquery
import functions
import global_vars

st.set_page_config(layout="wide", page_title="Wide Right - 2026 Payouts", page_icon="💵")

# --- Custom Styling ---
st.markdown("""
<style>
    .metric-card {
        background: rgba(128, 128, 128, 0.05);
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        border: 1px solid rgba(128, 128, 128, 0.18);
        padding: 18px 22px;
        text-align: center;
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        border-color: rgba(76, 175, 80, 0.35);
    }
    .metric-val {
        font-size: 2.1rem;
        font-weight: 800;
        color: #4CAF50;
        margin-top: 4px;
        margin-bottom: 2px;
    }
    .metric-lbl {
        font-size: 0.9rem;
        opacity: 0.75;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        font-weight: 600;
    }
    .metric-sub {
        font-size: 0.8rem;
        opacity: 0.6;
        margin-top: 3px;
    }
    .podium-card {
        background: rgba(128, 128, 128, 0.05);
        border-radius: 16px;
        border: 1px solid rgba(128, 128, 128, 0.2);
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        transition: transform 0.25s ease;
    }
    .podium-card:hover {
        transform: translateY(-4px);
    }
    .gold-border {
        border-color: rgba(255, 215, 0, 0.5);
        background: linear-gradient(180deg, rgba(255, 215, 0, 0.08) 0%, rgba(128, 128, 128, 0.03) 100%);
    }
    .silver-border {
        border-color: rgba(192, 192, 192, 0.5);
        background: linear-gradient(180deg, rgba(192, 192, 192, 0.08) 0%, rgba(128, 128, 128, 0.03) 100%);
    }
    .bronze-border {
        border-color: rgba(205, 127, 50, 0.5);
        background: linear-gradient(180deg, rgba(205, 127, 50, 0.08) 0%, rgba(128, 128, 128, 0.03) 100%);
    }
    .week-card {
        background: rgba(128, 128, 128, 0.04);
        border-radius: 14px;
        border: 1px solid rgba(128, 128, 128, 0.18);
        padding: 16px 20px;
        margin-bottom: 14px;
    }
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 0.8rem;
        font-weight: 700;
        margin-right: 6px;
    }
    .badge-gold {
        background: rgba(255, 193, 7, 0.2);
        color: #ffc107;
        border: 1px solid rgba(255, 193, 7, 0.4);
    }
    .badge-silver {
        background: rgba(158, 158, 158, 0.25);
        color: #616161;
        border: 1px solid rgba(158, 158, 158, 0.5);
    }
    .badge-bronze {
        background: rgba(205, 127, 50, 0.2);
        color: #ffaa66;
        border: 1px solid rgba(205, 127, 50, 0.4);
    }
    .badge-bigwin {
        background: rgba(76, 175, 80, 0.2);
        color: #81c784;
        border: 1px solid rgba(76, 175, 80, 0.4);
    }
    .badge-rollover {
        background: rgba(33, 150, 243, 0.2);
        color: #64b5f6;
        border: 1px solid rgba(33, 150, 243, 0.4);
    }
</style>
""", unsafe_allow_html=True)

st.title("💵 2026 Payouts")
st.caption("Live season winnings, weekly high scores & rolling Big Win pot, regular season probables, and prize pool structure.")
st.divider()

# --- Data Fetching & Calculation ---
@st.cache_data(ttl=300)
def fetch_payouts_data():
    """
    Fetches franchises, current week info, and calculates weekly payouts automatically from live 2026 game results.
    Also checks if an official external.payouts_2026 table exists with ledger rows.
    """
    # 1. Franchises
    franchises_query = """
        SELECT franchise_id, franchise_name, division, icon 
        FROM `mfl-374514.dbt_production.dim_franchises`
    """
    franchises = functions.bq_query(franchises_query)
    franchises_df = pd.DataFrame(franchises)

    # 2. Current Week
    try:
        current_wk_info = functions.bq_query("SELECT recent_completed_week, current_week, next_week FROM `mfl-374514.dbt_production.dim_current_week`")[0]
        recent_completed_wk = int(current_wk_info.get("recent_completed_week", 0))
        current_wk = int(current_wk_info.get("current_week", recent_completed_wk + 1))
    except Exception:
        recent_completed_wk = 0
        current_wk = 1

    # 3. Check for official BigQuery table mfl-374514.external.payouts_2026
    official_payouts = None
    has_official_table = False
    try:
        official_rows = functions.bq_query("SELECT event_type, event_week, franchise_id, payout FROM `mfl-374514.external.payouts_2026` WHERE franchise_id IS NOT NULL")
        if official_rows and len(official_rows) > 0:
            official_payouts = pd.DataFrame(official_rows)
            has_official_table = True
    except Exception:
        has_official_table = False

    # 4. Fetch Game Results for Weekly Payouts Calculation
    results_query = """
        SELECT franchise_id, week, CAST(score AS FLOAT64) as score, result 
        FROM `mfl-374514.dbt_production.fct_results` 
        WHERE score IS NOT NULL 
        ORDER BY week ASC, score DESC
    """
    results = functions.bq_query(results_query)
    results_df = pd.DataFrame(results)

    # Calculate weekly awards
    events = []
    current_pot = 5
    weeks_analyzed = sorted(results_df["week"].unique()) if not results_df.empty else []

    # Map franchise details
    id_to_name = dict(zip(franchises_df["franchise_id"], franchises_df["franchise_name"]))
    id_to_icon = dict(zip(franchises_df["franchise_id"], franchises_df["icon"]))
    id_to_div = dict(zip(franchises_df["franchise_id"], franchises_df["division"]))

    weekly_summary = {}

    for wk in weeks_analyzed:
        wk_int = int(wk)
        wk_df = results_df[results_df["week"] == wk_int].sort_values(by="score", ascending=False).reset_index(drop=True)
        if len(wk_df) >= 3:
            s1 = wk_df.loc[0, "score"]
            s2 = wk_df.loc[1, "score"]
            s3 = wk_df.loc[2, "score"]
            f1 = wk_df.loc[0, "franchise_id"]
            f2 = wk_df.loc[1, "franchise_id"]
            f3 = wk_df.loc[2, "franchise_id"]

            # High Score 1: $10
            events.append({
                "week": wk_int,
                "event_type": "High Score 1",
                "franchise_id": f1,
                "franchise_name": id_to_name.get(f1, f1),
                "icon": id_to_icon.get(f1, ""),
                "score": s1,
                "payout": 10,
                "description": f"1st place score: {s1:.2f} pts ($10)"
            })

            # High Score 2: $6
            events.append({
                "week": wk_int,
                "event_type": "High Score 2",
                "franchise_id": f2,
                "franchise_name": id_to_name.get(f2, f2),
                "icon": id_to_icon.get(f2, ""),
                "score": s2,
                "payout": 6,
                "description": f"2nd place score: {s2:.2f} pts ($6)"
            })

            # High Score 3: $4
            events.append({
                "week": wk_int,
                "event_type": "High Score 3",
                "franchise_id": f3,
                "franchise_name": id_to_name.get(f3, f3),
                "icon": id_to_icon.get(f3, ""),
                "score": s3,
                "payout": 4,
                "description": f"3rd place score: {s3:.2f} pts ($4)"
            })

            # Big Win: spread >= 12.0
            spread = s1 - s2
            pot_for_week = current_pot
            if spread >= 12.0:
                events.append({
                    "week": wk_int,
                    "event_type": "Big Win",
                    "franchise_id": f1,
                    "franchise_name": id_to_name.get(f1, f1),
                    "icon": id_to_icon.get(f1, ""),
                    "score": s1,
                    "payout": pot_for_week,
                    "description": f"Won Big Win pot of ${pot_for_week} (Spread: +{spread:.2f} pts ≥ 12.0)"
                })
                weekly_summary[wk_int] = {
                    "high_1": (id_to_name.get(f1, f1), s1, 10, id_to_icon.get(f1, "")),
                    "high_2": (id_to_name.get(f2, f2), s2, 6, id_to_icon.get(f2, "")),
                    "high_3": (id_to_name.get(f3, f3), s3, 4, id_to_icon.get(f3, "")),
                    "big_win_winner": id_to_name.get(f1, f1),
                    "big_win_pot": pot_for_week,
                    "big_win_spread": spread,
                    "big_win_won": True
                }
                # Reset pot
                current_pot = 5
            else:
                events.append({
                    "week": wk_int,
                    "event_type": "Big Win (Rollover)",
                    "franchise_id": None,
                    "franchise_name": "No Winner (Rollover)",
                    "icon": "",
                    "score": None,
                    "payout": 0,
                    "description": f"Spread of +{spread:.2f} pts fell short of 12.0. Pot of ${pot_for_week} carries over."
                })
                weekly_summary[wk_int] = {
                    "high_1": (id_to_name.get(f1, f1), s1, 10, id_to_icon.get(f1, "")),
                    "high_2": (id_to_name.get(f2, f2), s2, 6, id_to_icon.get(f2, "")),
                    "high_3": (id_to_name.get(f3, f3), s3, 4, id_to_icon.get(f3, "")),
                    "big_win_winner": None,
                    "big_win_pot": pot_for_week,
                    "big_win_spread": spread,
                    "big_win_won": False
                }
                # Pot rolls over +$5
                current_pot += 5

    events_df = pd.DataFrame(events)

    # 5. Build Aggregated Leaderboard
    leaderboard = franchises_df.copy()
    if not events_df.empty:
        won_events = events_df[events_df["payout"] > 0]
        payouts_by_team = won_events.groupby("franchise_id")["payout"].sum().reset_index()
        h1_by_team = won_events[won_events["event_type"] == "High Score 1"].groupby("franchise_id")["payout"].count().reset_index().rename(columns={"payout": "h1_count"})
        h2_by_team = won_events[won_events["event_type"] == "High Score 2"].groupby("franchise_id")["payout"].count().reset_index().rename(columns={"payout": "h2_count"})
        h3_by_team = won_events[won_events["event_type"] == "High Score 3"].groupby("franchise_id")["payout"].count().reset_index().rename(columns={"payout": "h3_count"})
        bw_by_team = won_events[won_events["event_type"] == "Big Win"].groupby("franchise_id")["payout"].count().reset_index().rename(columns={"payout": "bw_count"})

        leaderboard = leaderboard.merge(payouts_by_team, on="franchise_id", how="left")
        leaderboard = leaderboard.merge(h1_by_team, on="franchise_id", how="left")
        leaderboard = leaderboard.merge(h2_by_team, on="franchise_id", how="left")
        leaderboard = leaderboard.merge(h3_by_team, on="franchise_id", how="left")
        leaderboard = leaderboard.merge(bw_by_team, on="franchise_id", how="left")
    else:
        leaderboard["payout"] = 0
        leaderboard["h1_count"] = 0
        leaderboard["h2_count"] = 0
        leaderboard["h3_count"] = 0
        leaderboard["bw_count"] = 0

    leaderboard["payout"] = leaderboard["payout"].fillna(0).astype(int)
    leaderboard["h1_count"] = leaderboard["h1_count"].fillna(0).astype(int)
    leaderboard["h2_count"] = leaderboard["h2_count"].fillna(0).astype(int)
    leaderboard["h3_count"] = leaderboard["h3_count"].fillna(0).astype(int)
    leaderboard["bw_count"] = leaderboard["bw_count"].fillna(0).astype(int)

    leaderboard = leaderboard.sort_values(by=["payout", "h1_count", "bw_count", "franchise_name"], ascending=[False, False, False, True]).reset_index(drop=True)
    leaderboard["Rank"] = leaderboard.index + 1

    return {
        "leaderboard": leaderboard,
        "events_df": events_df,
        "weekly_summary": weekly_summary,
        "current_pot": current_pot,
        "recent_completed_wk": recent_completed_wk,
        "current_wk": current_wk,
        "has_official_table": has_official_table,
        "franchises_df": franchises_df
    }

data = fetch_payouts_data()
leaderboard_df = data["leaderboard"]
events_df = data["events_df"]
weekly_summary = data["weekly_summary"]
current_pot = data["current_pot"]
recent_completed_wk = data["recent_completed_wk"]
current_wk = data["current_wk"]
has_official_table = data["has_official_table"]

# --- Global Metrics ---
TOTAL_LEAGUE_POT = 1120
total_paid_out = int(leaderboard_df["payout"].sum())
total_remaining = TOTAL_LEAGUE_POT - total_paid_out
weekly_prizes_left = 350 - total_paid_out

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-lbl">Total Prize Pool</div>
        <div class="metric-val">${TOTAL_LEAGUE_POT:,}</div>
        <div class="metric-sub">12 Teams &bull; $1,200 ($80 MFL fee)</div>
    </div>
    """, unsafe_allow_html=True)
with m2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-lbl">Paid Out to Date</div>
        <div class="metric-val" style="color: #4CAF50;">${total_paid_out:,}</div>
        <div class="metric-sub">Weeks 1 – {recent_completed_wk} High Scores &amp; Big Wins</div>
    </div>
    """, unsafe_allow_html=True)
with m3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-lbl">Week {current_wk} Big Win Pot</div>
        <div class="metric-val" style="color: #FFC107;">${current_pot:,}</div>
        <div class="metric-sub">Rolling Pot &bull; Margin ≥ 12.0 pts</div>
    </div>
    """, unsafe_allow_html=True)
with m4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-lbl">Prize Money Remaining</div>
        <div class="metric-val" style="color: #2196F3;">${total_remaining:,}</div>
        <div class="metric-sub">${weekly_prizes_left:,} Weekly &bull; $770 Season/Playoffs</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")
st.write("")

# --- Tabs Navigation ---
tab_leaders, tab_weekly, tab_projections, tab_rules = st.tabs([
    "🏆 Season Leaderboard",
    "📅 Weekly High Scores & Big Win",
    "🔮 Up for Grabs & Probables",
    "📋 Rules & Payout Structure"
])

# =========================================================================
# TAB 1: SEASON LEADERBOARD
# =========================================================================
with tab_leaders:
    st.subheader("Season to Date Winnings Leaderboard", divider="green")

    # Top 3 Podium
    if len(leaderboard_df) >= 3 and leaderboard_df.loc[0, "payout"] > 0:
        p1, p2, p3 = st.columns(3)
        top1 = leaderboard_df.iloc[0]
        top2 = leaderboard_df.iloc[1]
        top3 = leaderboard_df.iloc[2]

        with p1:
            icon_html = f'<img src="{top1["icon"]}" width="54" style="border-radius:50%; margin-bottom:8px;">' if top1["icon"] else '🥇'
            st.markdown(f"""
            <div class="podium-card gold-border">
                <div>{icon_html}</div>
                <span class="badge badge-gold">1ST PLACE</span>
                <h3 style="margin: 6px 0 2px 0;">{top1['franchise_name']}</h3>
                <div style="font-size: 0.85rem; opacity: 0.7;">{top1['division']} Division</div>
                <div class="metric-val" style="color: #FFD700; font-size: 2rem;">${top1['payout']:.2f}</div>
                <div style="font-size: 0.8rem; opacity: 0.8;">{top1['h1_count']}x 1st &bull; {top1['h2_count']}x 2nd &bull; {top1['bw_count']}x Big Win</div>
            </div>
            """, unsafe_allow_html=True)

        with p2:
            icon_html = f'<img src="{top2["icon"]}" width="54" style="border-radius:50%; margin-bottom:8px;">' if top2["icon"] else '🥈'
            st.markdown(f"""
            <div class="podium-card silver-border">
                <div>{icon_html}</div>
                <span class="badge badge-silver">2ND PLACE</span>
                <h3 style="margin: 6px 0 2px 0;">{top2['franchise_name']}</h3>
                <div style="font-size: 0.85rem; opacity: 0.7;">{top2['division']} Division</div>
                <div class="metric-val" style="color: #757575; font-size: 2rem;">${top2['payout']:.2f}</div>
                <div style="font-size: 0.8rem; opacity: 0.8;">{top2['h1_count']}x 1st &bull; {top2['h2_count']}x 2nd &bull; {top2['bw_count']}x Big Win</div>
            </div>
            """, unsafe_allow_html=True)

        with p3:
            icon_html = f'<img src="{top3["icon"]}" width="54" style="border-radius:50%; margin-bottom:8px;">' if top3["icon"] else '🥉'
            st.markdown(f"""
            <div class="podium-card bronze-border">
                <div>{icon_html}</div>
                <span class="badge badge-bronze">3RD PLACE</span>
                <h3 style="margin: 6px 0 2px 0;">{top3['franchise_name']}</h3>
                <div style="font-size: 0.85rem; opacity: 0.7;">{top3['division']} Division</div>
                <div class="metric-val" style="color: #CD7F32; font-size: 2rem;">${top3['payout']:.2f}</div>
                <div style="font-size: 0.8rem; opacity: 0.8;">{top3['h1_count']}x 1st &bull; {top3['h2_count']}x 2nd &bull; {top3['bw_count']}x Big Win</div>
            </div>
            """, unsafe_allow_html=True)

    st.write("")

    # Full Leaderboard Table & Earnings Chart
    col_table, col_chart = st.columns([1.1, 0.9], gap="large")

    with col_table:
        st.markdown("#### Complete Earnings Standings")
        display_df = leaderboard_df[["Rank", "franchise_name", "division", "payout", "h1_count", "h2_count", "h3_count", "bw_count"]].copy()
        display_df["payout"] = display_df["payout"].apply(lambda x: f"${x:,.2f}")
        display_df.columns = ["Rank", "Franchise", "Division", "Total Winnings", "1st High ($10)", "2nd High ($6)", "3rd High ($4)", "Big Wins"]
        st.dataframe(display_df, hide_index=True, use_container_width=True)

    with col_chart:
        st.markdown("#### Cash Won by Franchise")
        chart_df = leaderboard_df.sort_values(by="payout", ascending=True)
        fig = px.bar(
            chart_df,
            x="payout",
            y="franchise_name",
            orientation="h",
            labels={"payout": "Winnings ($)", "franchise_name": "Franchise"},
            color="payout",
            color_continuous_scale="Viridis",
            text="payout"
        )
        fig.update_traces(texttemplate="$%{x:.0f}", textposition="outside", cliponaxis=False)
        fig.update_layout(
            margin=dict(l=0, r=40, t=10, b=10),
            height=380,
            coloraxis_showscale=False,
            xaxis=dict(visible=False),
            yaxis=dict(title="")
        )
        st.plotly_chart(fig, use_container_width=True)

    # Franchise Detail Breakdown Expander
    st.divider()
    st.markdown("#### 🔍 Franchise Earnings Detail")
    selected_franchise = st.selectbox(
        "Select a franchise to view itemized winnings:",
        options=leaderboard_df["franchise_name"].tolist()
    )

    if selected_franchise and not events_df.empty:
        f_events = events_df[events_df["franchise_name"] == selected_franchise]
        if not f_events.empty:
            f_display = f_events[["week", "event_type", "payout", "description"]].copy()
            f_display["payout"] = f_display["payout"].apply(lambda x: f"${x:,.2f}")
            f_display.columns = ["Week", "Award / Event", "Amount", "Details"]
            st.dataframe(f_display, hide_index=True, use_container_width=True)
        else:
            st.info(f"{selected_franchise} has not won any cash payouts yet this season. Keep fighting!")

# =========================================================================
# TAB 2: WEEKLY RESULTS TRACKER
# =========================================================================
with tab_weekly:
    st.subheader("Weekly High Scores & Big Win Tracker", divider="blue")
    st.write(
        "Each week features **\\$25** in guaranteed prizes: **\\$10** (1st high score), "
        "**\\$6** (2nd high score), **\\$4** (3rd high score), plus a **\\$5 rolling pot** for a **Big Win** "
        "(awarded when the 1st place score beats 2nd place by **12.0+ points**)."
    )

    # Next Week Preview Card
    st.markdown(f"""
    <div class="week-card" style="border-left: 5px solid #FFC107; background: rgba(255, 193, 7, 0.06); padding: 14px 22px;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span class="badge badge-bigwin">UPCOMING</span>
                <strong style="font-size: 1.15rem;">Week {current_wk} Side Games Preview</strong>
            </div>
            <div style="display: flex; align-items: center; background: rgba(255, 193, 7, 0.16); border: 1.5px solid rgba(255, 193, 7, 0.45); border-radius: 12px; padding: 6px 18px; gap: 12px;">
                <span style="font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.6px; opacity: 0.85;">Big Win Rolling Pot</span>
                <span style="font-size: 1.9rem; font-weight: 800; color: #FFB300; line-height: 1;">${current_pot:,}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.write("")

    # Completed Weeks Cards
    if weekly_summary:
        for wk in sorted(weekly_summary.keys(), reverse=True):
            info = weekly_summary[wk]
            h1 = info["high_1"]
            h2 = info["high_2"]
            h3 = info["high_3"]
            bw_won = info["big_win_won"]
            bw_winner = info["big_win_winner"]
            bw_pot = info["big_win_pot"]
            bw_spread = info["big_win_spread"]

            bw_badge = f'<span class="badge badge-bigwin">🏆 BIG WIN: {bw_winner} (${bw_pot}) &bull; +{bw_spread:.2f} pts</span>' if bw_won else f'<span class="badge badge-rollover">🔄 BIG WIN ROLLED OVER (${bw_pot}) &bull; Spread +{bw_spread:.2f} &lt; 12.0</span>'

            st.markdown(f"""
            <div class="week-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <h4 style="margin: 0;">Week {wk} Results</h4>
                    <div>{bw_badge}</div>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 14px;">
                    <div style="background: rgba(128, 128, 128, 0.05); padding: 12px 16px; border-radius: 10px; border-left: 4px solid #FFD700;">
                        <span class="badge badge-gold">1ST PLACE ($10)</span>
                        <div style="font-weight: 700; font-size: 1.05rem; margin-top: 4px;">{h1[0]}</div>
                        <div style="font-size: 0.85rem; opacity: 0.75;">Score: <strong>{h1[1]:.2f} pts</strong></div>
                    </div>
                    <div style="background: rgba(128, 128, 128, 0.05); padding: 12px 16px; border-radius: 10px; border-left: 4px solid #C0C0C0;">
                        <span class="badge badge-silver">2ND PLACE ($6)</span>
                        <div style="font-weight: 700; font-size: 1.05rem; margin-top: 4px;">{h2[0]}</div>
                        <div style="font-size: 0.85rem; opacity: 0.75;">Score: <strong>{h2[1]:.2f} pts</strong></div>
                    </div>
                    <div style="background: rgba(128, 128, 128, 0.05); padding: 12px 16px; border-radius: 10px; border-left: 4px solid #CD7F32;">
                        <span class="badge badge-bronze">3RD PLACE ($4)</span>
                        <div style="font-weight: 700; font-size: 1.05rem; margin-top: 4px;">{h3[0]}</div>
                        <div style="font-size: 0.85rem; opacity: 0.75;">Score: <strong>{h3[1]:.2f} pts</strong></div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No completed weeks recorded yet for 2026. Check back after Week 1 concludes!")

# =========================================================================
# TAB 3: UP FOR GRABS & PROBABLES
# =========================================================================
with tab_projections:
    st.subheader("Regular Season & Playoff Prizes Up for Grabs", divider="orange")

    # Coming Soon Placeholder Banner
    st.markdown("""
    <div class="week-card" style="border-left: 5px solid #2196F3; background: rgba(33, 150, 243, 0.05); padding: 22px 24px; border-radius: 16px; margin-bottom: 24px;">
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
            <span class="badge" style="background: rgba(33, 150, 243, 0.2); color: #2196F3; font-weight: 800; border: 1px solid rgba(33, 150, 243, 0.4);">COMING SOON</span>
            <span style="font-weight: 700; font-size: 1.15rem;">🔮 2026 Playoff &amp; Regular Season Simulation Model</span>
        </div>
        <p style="margin: 0; opacity: 0.85; font-size: 0.95rem; line-height: 1.5;">
            Weekly Monte Carlo playoff simulations and division odds are currently being calibrated for 2026 and will launch once mid-season simulation batches begin. Check back soon for live division title chances, wild card race probabilities, and projected win totals!
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### 🎁 End of Season &amp; Playoff Prize Allocation")
    st.write("A total of **\\$770** will be awarded at the conclusion of the regular season and playoffs:")

    p1, p2, p3 = st.columns(3, gap="large")

    with p1:
        st.markdown("""
        <div class="metric-card" style="text-align: left; padding: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="badge badge-gold">REGULAR SEASON</span>
                <strong style="color: #FFC107; font-size: 1.25rem;">$150 Total</strong>
            </div>
            <h4 style="margin: 10px 0 6px 0;">🛡️ 3x Division Titles</h4>
            <div style="font-size: 0.9rem; opacity: 0.8; margin-bottom: 12px;"><strong>$50.00</strong> awarded to the 1st place finisher in each division:</div>
            <ul style="font-size: 0.88rem; opacity: 0.85; margin: 0; padding-left: 20px;">
                <li>Left Upright Champion: <strong>$50.00</strong></li>
                <li>Crossbar Champion: <strong>$50.00</strong></li>
                <li>Right Upright Champion: <strong>$50.00</strong></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with p2:
        st.markdown("""
        <div class="metric-card" style="text-align: left; padding: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="badge badge-silver">REGULAR SEASON</span>
                <strong style="color: #64b5f6; font-size: 1.25rem;">$150 Total</strong>
            </div>
            <h4 style="margin: 10px 0 6px 0;">🃏 Wild Cards &amp; Points Title</h4>
            <div style="font-size: 0.9rem; opacity: 0.8; margin-bottom: 12px;">Non-division playoff qualifiers and total scoring leader:</div>
            <ul style="font-size: 0.88rem; opacity: 0.85; margin: 0; padding-left: 20px;">
                <li>Wild Card Seed #1: <strong>$30.00</strong></li>
                <li>Wild Card Seed #2: <strong>$30.00</strong></li>
                <li>Wild Card Seed #3: <strong>$30.00</strong></li>
                <li>Points Title (Top PF): <strong>$60.00</strong></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with p3:
        st.markdown("""
        <div class="metric-card" style="text-align: left; padding: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="badge badge-bigwin">POSTSEASON</span>
                <strong style="color: #4CAF50; font-size: 1.25rem;">$470 Total</strong>
            </div>
            <h4 style="margin: 10px 0 6px 0;">🏆 Playoff Podium</h4>
            <div style="font-size: 0.9rem; opacity: 0.8; margin-bottom: 12px;">Awarded to the top finishers in the playoff tournament:</div>
            <ul style="font-size: 0.88rem; opacity: 0.85; margin: 0; padding-left: 20px;">
                <li>🥇 League Champion: <strong>$275.00</strong></li>
                <li>🥈 League Runner-Up: <strong>$135.00</strong></li>
                <li>🥉 3rd Place Match: <strong>$60.00</strong></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    # Current Live Division Leaders
    st.write("")
    st.divider()
    st.markdown("#### 📊 Current Division Leaders (Through Week 3)")
    standings_query = """
        SELECT a.division, a.franchise_name, b.wins, b.losses, b.points_for
        FROM `mfl-374514.dbt_production.dim_franchises` a
        LEFT JOIN `mfl-374514.dbt_production.dim_standings` b ON a.franchise_id = b.franchise_id
        ORDER BY a.division, CAST(b.wins AS INT64) DESC, b.points_for DESC
    """
    try:
        std_df = pd.DataFrame(functions.bq_query(standings_query))
        if not std_df.empty:
            l_col1, l_col2, l_col3 = st.columns(3, gap="large")
            div_cols = [l_col1, l_col2, l_col3]
            for col_idx, div_name in enumerate(sorted(std_df["division"].unique())):
                sub_df = std_df[std_df["division"] == div_name].reset_index(drop=True)
                top_team = sub_df.iloc[0]
                with div_cols[col_idx % 3]:
                    st.metric(
                        label=f"{div_name} Leader",
                        value=top_team["franchise_name"],
                        delta=f"{top_team['wins']}-{top_team['losses']} ({top_team['points_for']:.2f} PF)"
                    )
    except Exception:
        pass

# =========================================================================
# TAB 4: RULES & PAYOUT STRUCTURE
# =========================================================================
with tab_rules:
    st.subheader("Wide Right League Payout Rules & Structure", divider="gray")

    st.markdown("""
    The Wide Right Fantasy Football League operates with 12 franchises at **\\$100** buy-in each, producing a total pot of **\\$1,200**.
    From this total, **\\$80** covers the MyFantasyLeague (MFL) league management platform hosting fee, leaving an active prize pool of **\\$1,120**.
    """)

    rule_col1, rule_col2 = st.columns(2, gap="large")

    with rule_col1:
        st.markdown("#### 💰 Full Prize Allocation Breakdown")
        breakdown_data = {
            "Category": [
                "Weekly High Score 1 (x14 weeks)",
                "Weekly High Score 2 (x14 weeks)",
                "Weekly High Score 3 (x14 weeks)",
                "Weekly Big Win Rolling Pot (x14 weeks)",
                "Division Winners (3 Divisions)",
                "Wild Card Teams (3 Teams)",
                "Regular Season Points Title",
                "League Champion (1st Place)",
                "League Runner-Up (2nd Place)",
                "League 3rd Place",
                "MFL Platform Hosting Fee",
                "TOTAL"
            ],
            "Award Amount": [
                "$10.00 / week",
                "$6.00 / week",
                "$4.00 / week",
                "$5.00 / week (Rolling)",
                "$50.00 each",
                "$30.00 each",
                "$60.00",
                "$275.00",
                "$135.00",
                "$60.00",
                "$80.00",
                "$1,200.00"
            ],
            "Total Pool": [
                "$140.00",
                "$84.00",
                "$56.00",
                "$70.00",
                "$150.00",
                "$90.00",
                "$60.00",
                "$275.00",
                "$135.00",
                "$60.00",
                "$80.00",
                "$1,200.00"
            ]
        }
        st.dataframe(pd.DataFrame(breakdown_data), hide_index=True, use_container_width=True)

    with rule_col2:
        st.markdown("#### 📜 Rules & Edge Cases")
        with st.expander("🎯 Weekly High Scores (\\$10 / \\$6 / \\$4)", expanded=True):
            st.write("""
            - The three highest-scoring teams across the entire league in Weeks 1 through 14 earn \\$10, \\$6, and \\$4 respectively.
            - **Ties**: If teams tie for an award, the prize money for the tied positions is split equally (e.g., a tie for 1st place splits \\$10 + \\$6 = \\$8.00 each).
            """)

        with st.expander("💥 Weekly Big Win Rolling Pot (\\$5 rolling)", expanded=True):
            st.write("""
            - \\$5 is added to the Big Win pot each regular season week.
            - To win the pot, the **#1 highest-scoring team** of that week must beat the **#2 highest-scoring team** by **12.00 or more points**.
            - If the margin is less than 12.00 points, **no one wins** the Big Win that week and the entire accumulated pot rolls over into the next week (+ $5).
            - Any pot remaining after Week 14 is handled per commissioner agreement / final week payout.
            """)

        with st.expander("🛡️ Division & Points Titles", expanded=False):
            st.write("""
            - **Division Titles**: Awarded to the regular season winner of each of the 3 divisions (Left Upright, Crossbar, Right Upright).
            - **Wild Cards**: Awarded to the top 3 non-division-winning teams qualifying for the playoffs.
            - **Points Title**: Awarded to the franchise that scores the highest cumulative points for across Weeks 1 through 14.
            """)
