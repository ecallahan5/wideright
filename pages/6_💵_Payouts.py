import sys
import os

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google.cloud import bigquery
import functions
import global_vars
import standings_utils

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
    .prob-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.78rem;
        font-weight: 700;
    }
    .prob-card {
        background: rgba(128, 128, 128, 0.04);
        border: 1px solid rgba(128, 128, 128, 0.16);
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 10px;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .prob-card:hover {
        transform: translateY(-2px);
        border-color: rgba(33, 150, 243, 0.4);
    }
</style>
""", unsafe_allow_html=True)

st.title("💵 2026 Payouts")
st.caption("Live season winnings, weekly high scores & rolling Big Win pot, regular season probables, and prize pool structure.")
st.divider()

# --- Data Fetching & Calculation ---
def _format_cash(val):
    """Formats dollar amount as whole dollars when exact, else 2 decimal places."""
    if float(val).is_integer():
        return f"${int(round(val)):,}"
    return f"${val:,.2f}"


@st.cache_data(ttl=300)
def fetch_payouts_data():
    """
    Fetches franchises, current week info, standings, and schedule, and calculates:
      1. Weekly High Scores ($10 / $6 / $4) & rolling Big Win pot ($5/wk) from Weeks 1-14.
      2. Mathematically clinched Regular Season awards (Division Titles $50 ea, locked Wild Cards $30 ea,
         and Points Title $60 upon Week 14 completion).
      3. Any postseason/manual ledger rows in `mfl-374514.external.payouts_2026` (if present).
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

    # 4. Fetch Regular Season Game Results (Weeks 1-14) for Weekly Payouts Calculation
    results_query = """
        SELECT franchise_id, week, CAST(score AS FLOAT64) as score, result 
        FROM `mfl-374514.dbt_production.fct_results` 
        WHERE score IS NOT NULL AND week <= 14
        ORDER BY week ASC, score DESC
    """
    results = functions.bq_query(results_query)
    results_df = pd.DataFrame(results)

    if recent_completed_wk == 0 and not results_df.empty:
        recent_completed_wk = int(results_df["week"].max())
        current_wk = recent_completed_wk + 1

    # 4b. Fetch Standings & Schedule for Mathematical Clinch Detection
    try:
        standings_rows = functions.bq_query("""
            SELECT
                franchise_id,
                CAST(wins AS INT64) AS wins,
                CAST(losses AS INT64) AS losses,
                CAST(points_for AS FLOAT64) AS points_for
            FROM `mfl-374514.dbt_production.dim_standings`
        """)
    except Exception:
        standings_rows = []

    try:
        sched_rows = functions.bq_query("""
            SELECT 
                CAST(s1.week_num AS INT64) AS week,
                s1.franchise_id AS franchise_id,
                s2.franchise_id AS opp_id,
                s1.is_home AS is_home,
                COALESCE(CAST(r1.score AS FLOAT64), 0.0) AS team_score,
                COALESCE(CAST(r2.score AS FLOAT64), 0.0) AS opp_score
            FROM `mfl-374514.dbt_production.dim_schedules` s1
            JOIN `mfl-374514.dbt_production.dim_schedules` s2
                ON s1.week_num = s2.week_num
                AND s1.matchup_num = s2.matchup_num
                AND s1.franchise_id != s2.franchise_id
            LEFT JOIN `mfl-374514.dbt_production.fct_results` r1
                ON s1.franchise_id = r1.franchise_id AND s1.week_num = r1.week
            LEFT JOIN `mfl-374514.dbt_production.fct_results` r2
                ON s2.franchise_id = r2.franchise_id AND s2.week_num = r2.week
            ORDER BY week, s1.matchup_num
        """)
    except Exception:
        sched_rows = []

    # Calculate weekly awards
    events = []
    current_pot = 5
    weeks_analyzed = sorted(results_df["week"].unique()) if not results_df.empty else []

    # Map franchise details
    id_to_name = dict(zip(franchises_df["franchise_id"], franchises_df["franchise_name"]))
    id_to_icon = dict(zip(franchises_df["franchise_id"], franchises_df["icon"]))

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
                "category": "weekly",
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
                "category": "weekly",
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
                "category": "weekly",
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
                    "category": "weekly",
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
                    "category": "weekly",
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

    # 4c. Calculate Mathematically Clinched Regular Season Awards (Division Titles, Locked Wild Cards, Points Title)
    reg_awards = standings_utils.compute_clinched_reg_season_awards(
        franchises_records=franchises,
        standings_records=standings_rows,
        sched_records=sched_rows,
        recent_completed_wk=recent_completed_wk,
    )
    events.extend(reg_awards["events"])

    # 4d. Merge any non-overlapping postseason payouts from external.payouts_2026 (if populated)
    if has_official_table and official_payouts is not None:
        auto_keywords = ("high score", "big win", "division", "wild card", "points")
        for _, r in official_payouts.iterrows():
            ev_type = str(r.get("event_type") or "").strip()
            ev_lower = ev_type.lower()
            if not ev_type or any(kw in ev_lower for kw in auto_keywords):
                continue
            fid = r.get("franchise_id")
            amt = float(r.get("payout") or 0)
            if fid and amt > 0:
                ev_wk = int(r["event_week"]) if pd.notna(r.get("event_week")) else max(recent_completed_wk, 14)
                events.append({
                    "week": ev_wk,
                    "event_type": ev_type,
                    "category": "season",
                    "franchise_id": fid,
                    "franchise_name": id_to_name.get(fid, fid),
                    "icon": id_to_icon.get(fid, ""),
                    "score": None,
                    "payout": int(amt) if amt.is_integer() else round(amt, 2),
                    "description": f"{ev_type} ({_format_cash(amt)})"
                })

    events_df = pd.DataFrame(events)

    # 5. Build Aggregated Leaderboard
    leaderboard = franchises_df.copy()
    weekly_paid_out = 0
    season_paid_out = 0
    season_labels_map = {}
    season_podium_map = {}

    if not events_df.empty:
        won_events = events_df[events_df["payout"] > 0]
        weekly_won = won_events[won_events["category"] == "weekly"]
        season_won = won_events[won_events["category"] == "season"]

        weekly_sum_raw = float(weekly_won["payout"].sum()) if not weekly_won.empty else 0.0
        season_sum_raw = float(season_won["payout"].sum()) if not season_won.empty else 0.0
        weekly_paid_out = int(round(weekly_sum_raw)) if weekly_sum_raw.is_integer() else round(weekly_sum_raw, 2)
        season_paid_out = int(round(season_sum_raw)) if season_sum_raw.is_integer() else round(season_sum_raw, 2)

        payouts_by_team = won_events.groupby("franchise_id")["payout"].sum().reset_index()
        weekly_by_team = weekly_won.groupby("franchise_id")["payout"].sum().reset_index().rename(columns={"payout": "weekly_payout"})
        season_by_team = season_won.groupby("franchise_id")["payout"].sum().reset_index().rename(columns={"payout": "season_payout"})
        h1_by_team = weekly_won[weekly_won["event_type"] == "High Score 1"].groupby("franchise_id")["payout"].count().reset_index().rename(columns={"payout": "h1_count"})
        h2_by_team = weekly_won[weekly_won["event_type"] == "High Score 2"].groupby("franchise_id")["payout"].count().reset_index().rename(columns={"payout": "h2_count"})
        h3_by_team = weekly_won[weekly_won["event_type"] == "High Score 3"].groupby("franchise_id")["payout"].count().reset_index().rename(columns={"payout": "h3_count"})
        bw_by_team = weekly_won[weekly_won["event_type"] == "Big Win"].groupby("franchise_id")["payout"].count().reset_index().rename(columns={"payout": "bw_count"})

        for fid, grp in season_won.groupby("franchise_id"):
            tbl_parts = []
            pod_parts = []
            for _, sr in grp.iterrows():
                et = sr["event_type"]
                amt_str = _format_cash(sr["payout"])
                if et == "Division Title":
                    tbl_parts.append(f"🛡️ Div ({amt_str})")
                    pod_parts.append(f"🛡️ Div Title (+{amt_str})")
                elif et == "Wild Card":
                    tbl_parts.append(f"🃏 WC ({amt_str})")
                    pod_parts.append(f"🃏 Wild Card (+{amt_str})")
                elif et == "Points Title":
                    tbl_parts.append(f"🏅 Pts ({amt_str})")
                    pod_parts.append(f"🏅 Points Title (+{amt_str})")
                else:
                    tbl_parts.append(f"🏆 {et} ({amt_str})")
                    pod_parts.append(f"🏆 {et} (+{amt_str})")
            season_labels_map[fid] = ", ".join(tbl_parts)
            season_podium_map[fid] = " &bull; ".join(pod_parts)

        leaderboard = leaderboard.merge(payouts_by_team, on="franchise_id", how="left")
        leaderboard = leaderboard.merge(weekly_by_team, on="franchise_id", how="left")
        leaderboard = leaderboard.merge(season_by_team, on="franchise_id", how="left")
        leaderboard = leaderboard.merge(h1_by_team, on="franchise_id", how="left")
        leaderboard = leaderboard.merge(h2_by_team, on="franchise_id", how="left")
        leaderboard = leaderboard.merge(h3_by_team, on="franchise_id", how="left")
        leaderboard = leaderboard.merge(bw_by_team, on="franchise_id", how="left")
    else:
        leaderboard["payout"] = 0
        leaderboard["weekly_payout"] = 0
        leaderboard["season_payout"] = 0
        leaderboard["h1_count"] = 0
        leaderboard["h2_count"] = 0
        leaderboard["h3_count"] = 0
        leaderboard["bw_count"] = 0

    leaderboard["payout"] = leaderboard["payout"].fillna(0.0)
    leaderboard["weekly_payout"] = leaderboard["weekly_payout"].fillna(0.0)
    leaderboard["season_payout"] = leaderboard["season_payout"].fillna(0.0)
    leaderboard["h1_count"] = leaderboard["h1_count"].fillna(0).astype(int)
    leaderboard["h2_count"] = leaderboard["h2_count"].fillna(0).astype(int)
    leaderboard["h3_count"] = leaderboard["h3_count"].fillna(0).astype(int)
    leaderboard["bw_count"] = leaderboard["bw_count"].fillna(0).astype(int)
    leaderboard["season_awards_label"] = leaderboard["franchise_id"].map(season_labels_map).fillna("—")
    leaderboard["season_awards_podium"] = leaderboard["franchise_id"].map(season_podium_map).fillna("")

    leaderboard = leaderboard.sort_values(
        by=["payout", "season_payout", "h1_count", "bw_count", "franchise_name"],
        ascending=[False, False, False, False, True],
    ).reset_index(drop=True)
    leaderboard["Rank"] = leaderboard.index + 1

    return {
        "leaderboard": leaderboard,
        "events_df": events_df,
        "weekly_summary": weekly_summary,
        "current_pot": current_pot,
        "recent_completed_wk": recent_completed_wk,
        "current_wk": current_wk,
        "has_official_table": has_official_table,
        "franchises_df": franchises_df,
        "weekly_paid_out": weekly_paid_out,
        "season_paid_out": season_paid_out,
        "clinched_divisions": reg_awards["clinched_divisions"],
        "clinched_wild_cards": reg_awards["clinched_wild_cards"],
        "clinched_points_title": reg_awards["clinched_points_title"],
        "w_rem": reg_awards["w_rem"],
    }

@st.cache_data(ttl=300)
def fetch_payout_projections_data():
    """
    Fetches the latest Monte Carlo simulation model projections for 2026 joined with franchise standings.
    """
    query = """
        SELECT 
            f.franchise_id,
            f.franchise_name,
            f.division,
            f.icon,
            CAST(s.wins AS INT64) as wins,
            CAST(s.losses AS INT64) as losses,
            CAST(s.points_for AS FLOAT64) as points_for,
            m.after_week,
            CAST(m.proj_wins AS FLOAT64) as proj_wins,
            CAST(m.win_division AS FLOAT64) as win_division,
            CAST(m.wild_card AS FLOAT64) as wild_card,
            CAST(m.make_playoffs AS FLOAT64) as make_playoffs,
            CAST(m.one_seed AS FLOAT64) as one_seed,
            CAST(m.bye AS FLOAT64) as bye,
            CAST(m.top_pts AS FLOAT64) as top_pts,
            CAST(m.first_pick AS FLOAT64) as first_pick
        FROM `mfl-374514.dbt_production.dim_franchises` f
        LEFT JOIN `mfl-374514.dbt_production.dim_standings` s ON f.franchise_id = s.franchise_id
        JOIN `mfl-374514.dbt_production.fct_reg_season_model` m ON f.franchise_id = m.franchise_id AND m.year = 2026
        ORDER BY m.after_week DESC, m.proj_wins DESC
    """
    try:
        rows = functions.bq_query(query)
        df = pd.DataFrame(rows)
        if not df.empty:
            df["expected_reg_payout"] = (df["win_division"] * 50.0) + (df["wild_card"] * 30.0) + (df["top_pts"] * 60.0)
            df["ev_division"] = df["win_division"] * 50.0
            df["ev_wild_card"] = df["wild_card"] * 30.0
            df["ev_top_pts"] = df["top_pts"] * 60.0
        return df
    except Exception:
        return pd.DataFrame()

data = fetch_payouts_data()
leaderboard_df = data["leaderboard"]
events_df = data["events_df"]
weekly_summary = data["weekly_summary"]
current_pot = data["current_pot"]
recent_completed_wk = data["recent_completed_wk"]
current_wk = data["current_wk"]
has_official_table = data["has_official_table"]
weekly_paid_out = data["weekly_paid_out"]
season_paid_out = data["season_paid_out"]
clinched_divisions = data["clinched_divisions"]
clinched_wild_cards = data["clinched_wild_cards"]
clinched_points_title = data["clinched_points_title"]
w_rem = data["w_rem"]

# --- Global Metrics ---
TOTAL_LEAGUE_POT = 1120
WEEKLY_POOL = 350
SEASON_PLAYOFF_POOL = 770
total_paid_out = weekly_paid_out + season_paid_out
total_remaining = TOTAL_LEAGUE_POT - total_paid_out
weekly_prizes_left = WEEKLY_POOL - weekly_paid_out
season_prizes_left = SEASON_PLAYOFF_POOL - season_paid_out

paid_out_sub = (
    f"{_format_cash(weekly_paid_out)} Weekly &bull; {_format_cash(season_paid_out)} Season Clinched"
    if season_paid_out > 0
    else f"Weeks 1 – {recent_completed_wk} High Scores &amp; Big Wins"
)
big_win_lbl = f"Week {current_wk} Big Win Pot" if recent_completed_wk < 14 else "Final Big Win Pot"

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
        <div class="metric-val" style="color: #4CAF50;">{_format_cash(total_paid_out)}</div>
        <div class="metric-sub">{paid_out_sub}</div>
    </div>
    """, unsafe_allow_html=True)
with m3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-lbl">{big_win_lbl}</div>
        <div class="metric-val" style="color: #FFC107;">${current_pot:,}</div>
        <div class="metric-sub">Rolling Pot &bull; Margin ≥ 12.0 pts</div>
    </div>
    """, unsafe_allow_html=True)
with m4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-lbl">Prize Money Remaining</div>
        <div class="metric-val" style="color: #2196F3;">{_format_cash(total_remaining)}</div>
        <div class="metric-sub">{_format_cash(weekly_prizes_left)} Weekly &bull; {_format_cash(season_prizes_left)} Season/Playoffs</div>
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

        def _podium_season_html(row):
            if row["season_awards_podium"]:
                return f'<div style="margin-top: 6px;"><span class="badge badge-gold">{row["season_awards_podium"]}</span></div>'
            return ""

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
                {_podium_season_html(top1)}
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
                {_podium_season_html(top2)}
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
                {_podium_season_html(top3)}
            </div>
            """, unsafe_allow_html=True)

    # Clinched Regular Season Awards Banner (shown once any division/WC/points award is locked in)
    if clinched_divisions or clinched_wild_cards or clinched_points_title:
        st.write("")
        award_pills = []
        for div_name in ["Left Upright", "Crossbar", "Right Upright"]:
            if div_name in clinched_divisions:
                info = clinched_divisions[div_name]
                award_pills.append(
                    f'<span class="badge badge-gold">🛡️ {div_name} ($50): {info["franchise_name"]} (Wk {info["clinch_wk"]})</span>'
                )
        for wc in clinched_wild_cards:
            award_pills.append(
                f'<span class="badge badge-rollover">🃏 Wild Card ($30): {wc["franchise_name"]} (Wk {wc["clinch_wk"]})</span>'
            )
        for pt in clinched_points_title:
            award_pills.append(
                f'<span class="badge badge-bigwin">🏅 Points Title ({_format_cash(pt["payout"])}): {pt["franchise_name"]}</span>'
            )
        st.markdown(f"""
        <div class="week-card" style="border-left: 5px solid #FFC107; background: rgba(255, 193, 7, 0.06); padding: 12px 18px; margin-bottom: 6px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 8px;">
                <strong style="font-size: 1.0rem;">🏅 Clinched Regular Season Awards Credited</strong>
                <strong style="color: #FFC107;">{_format_cash(season_paid_out)} Assigned</strong>
            </div>
            <div style="display: flex; flex-wrap: wrap; gap: 6px;">
                {''.join(award_pills)}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # Full Leaderboard Table & Earnings Chart
    col_table, col_chart = st.columns([1.15, 0.85], gap="large")

    with col_table:
        st.markdown("#### Complete Earnings Standings")
        display_df = leaderboard_df[[
            "Rank", "franchise_name", "division", "payout", "season_awards_label",
            "h1_count", "h2_count", "h3_count", "bw_count"
        ]].copy()
        display_df["payout"] = display_df["payout"].apply(lambda x: f"${x:,.2f}")
        display_df.columns = [
            "Rank", "Franchise", "Division", "Total Winnings", "Season Awards",
            "1st High ($10)", "2nd High ($6)", "3rd High ($4)", "Big Wins"
        ]
        st.dataframe(display_df, hide_index=True, use_container_width=True)

    with col_chart:
        st.markdown("#### Cash Won by Franchise")
        chart_df = leaderboard_df.sort_values(by=["payout", "franchise_name"], ascending=[True, False])
        if season_paid_out > 0:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                y=chart_df["franchise_name"],
                x=chart_df["weekly_payout"],
                name="Weekly Prizes",
                orientation="h",
                marker_color="#4CAF50",
                hovertemplate="<b>%{y}</b><br>Weekly Prizes: $%{x:,.2f}<extra></extra>",
            ))
            fig.add_trace(go.Bar(
                y=chart_df["franchise_name"],
                x=chart_df["season_payout"],
                name="Clinched Season Awards",
                orientation="h",
                marker_color="#FFC107",
                hovertemplate="<b>%{y}</b><br>Season Awards: $%{x:,.2f}<extra></extra>",
            ))
            fig.add_trace(go.Scatter(
                y=chart_df["franchise_name"],
                x=chart_df["payout"],
                text=[_format_cash(v) for v in chart_df["payout"]],
                mode="text",
                textposition="middle right",
                showlegend=False,
                hoverinfo="skip",
            ))
            max_payout = float(chart_df["payout"].max()) if not chart_df.empty else 0.0
            fig.update_layout(
                barmode="stack",
                margin=dict(l=0, r=48, t=30, b=10),
                height=390,
                xaxis=dict(visible=False, range=[0, max(max_payout * 1.18, 10)]),
                yaxis=dict(title=""),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
        else:
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
        f_events = events_df[(events_df["franchise_name"] == selected_franchise) & (events_df["payout"] > 0)].copy()
        if not f_events.empty:
            f_events["cat_order"] = f_events["category"].map({"weekly": 0, "season": 1}).fillna(2)
            f_events = f_events.sort_values(by=["week", "cat_order"], ascending=[True, True])
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

    proj_model_df = fetch_payout_projections_data()

    if not proj_model_df.empty:
        available_model_weeks = sorted(proj_model_df["after_week"].unique(), reverse=True)
        
        # Header controls
        ctrl_col1, ctrl_col2 = st.columns([0.7, 0.3])
        with ctrl_col1:
            st.markdown("""
            <div style="font-size: 0.95rem; opacity: 0.85; margin-top: 4px;">
                Probabilities and expected prize values generated from <strong>10,000 Monte Carlo regular season simulations</strong>, incorporating actual scores, player projections, and remaining schedules.
            </div>
            """, unsafe_allow_html=True)
        with ctrl_col2:
            selected_model_wk = st.selectbox(
                "Simulation Calibration Week:",
                options=available_model_weeks,
                format_func=lambda w: f"Through Week {w}",
                key="payout_sim_week_select"
            )

        sim_df = proj_model_df[proj_model_df["after_week"] == selected_model_wk].copy()
        sim_df = sim_df.sort_values(by="expected_reg_payout", ascending=False).reset_index(drop=True)

        top_ev_franchise = sim_df.iloc[0]

        # Top Model Metrics Bar
        eos_sub = (
            f"{_format_cash(season_paid_out)} Clinched &bull; {_format_cash(season_prizes_left)} Up for Grabs"
            if season_paid_out > 0
            else "$300 Reg Season &bull; $470 Postseason"
        )
        sm1, sm2, sm3, sm4 = st.columns(4)
        with sm1:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-lbl">Total League Pot</div>
                <div class="metric-val" style="color: #4CAF50;">$1,120</div>
                <div class="metric-sub">$770 Season/Playoffs &bull; $350 Weekly</div>
            </div>
            """, unsafe_allow_html=True)
        with sm2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-lbl">End of Season Purse</div>
                <div class="metric-val" style="color: #FFC107;">$770</div>
                <div class="metric-sub">{eos_sub}</div>
            </div>
            """, unsafe_allow_html=True)
        with sm3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-lbl">Prize Money Remaining</div>
                <div class="metric-val" style="color: #2196F3;">{_format_cash(total_remaining)}</div>
                <div class="metric-sub">{_format_cash(weekly_prizes_left)} Weekly &bull; {_format_cash(season_prizes_left)} Season/Playoffs</div>
            </div>
            """, unsafe_allow_html=True)
        with sm4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-lbl">Top Expected Earner</div>
                <div class="metric-val" style="color: #9C27B0; font-size: 1.8rem;">${top_ev_franchise['expected_reg_payout']:.2f}</div>
                <div class="metric-sub">{top_ev_franchise['franchise_name']} (Reg Season EV)</div>
            </div>
            """, unsafe_allow_html=True)

        st.write("")
        st.write("")

        # 3 Prize Category Summary Cards with Model Favorites
        st.markdown("#### 🎁 End of Season Prize Pool &amp; Live Projected Favorites")
        
        p1, p2, p3 = st.columns(3, gap="large")
        is_latest_model_wk = (selected_model_wk == available_model_weeks[0])

        # Division Favorites
        lu_top = sim_df[sim_df["division"] == "Left Upright"].sort_values(by="win_division", ascending=False).iloc[0]
        cb_top = sim_df[sim_df["division"] == "Crossbar"].sort_values(by="win_division", ascending=False).iloc[0]
        ru_top = sim_df[sim_df["division"] == "Right Upright"].sort_values(by="win_division", ascending=False).iloc[0]

        # Wild Card & Points Favorites
        wc_contenders = sim_df.sort_values(by="wild_card", ascending=False).head(3)
        pts_favorite = sim_df.sort_values(by="top_pts", ascending=False).iloc[0]

        # Postseason Favorites
        one_seed_fav = sim_df.sort_values(by="one_seed", ascending=False).iloc[0]
        bye_favs = sim_df.sort_values(by="bye", ascending=False).head(2)

        def _div_line_html(div_name, top_row):
            if is_latest_model_wk and div_name in clinched_divisions:
                winner_name = clinched_divisions[div_name]["franchise_name"]
                return f'<div>&bull; <strong>{div_name} ($50):</strong> {winner_name} <span class="badge badge-bigwin">CLINCHED ✓</span></div>'
            return f'<div>&bull; <strong>{div_name} ($50):</strong> {top_row["franchise_name"]} <span class="badge badge-gold">{top_row["win_division"]*100:.1f}%</span></div>'

        clinched_div_cnt = len(clinched_divisions) if is_latest_model_wk else 0
        div_rem_amt = 150 - (clinched_div_cnt * 50)
        if clinched_div_cnt == 3:
            div_header_amt = "All Clinched ($150)"
        elif clinched_div_cnt > 0:
            div_header_amt = f"${div_rem_amt} Left"
        else:
            div_header_amt = "$150 Total"
        div_sub_note = (
            f"<strong>$50.00</strong> per division &bull; <strong>${clinched_div_cnt * 50}</strong> already credited on Leaderboard:"
            if clinched_div_cnt > 0
            else "<strong>$50.00</strong> to 1st place in each division. Current favorites:"
        )

        with p1:
            st.markdown(f"""
            <div class="metric-card" style="text-align: left; padding: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span class="badge badge-gold">REGULAR SEASON</span>
                    <strong style="color: #FFC107; font-size: 1.2rem;">{div_header_amt}</strong>
                </div>
                <h4 style="margin: 10px 0 6px 0;">🛡️ 3x Division Titles</h4>
                <div style="font-size: 0.88rem; opacity: 0.8; margin-bottom: 12px;">{div_sub_note}</div>
                <div style="font-size: 0.88rem; line-height: 1.6;">
                    {_div_line_html("Left Upright", lu_top)}
                    {_div_line_html("Crossbar", cb_top)}
                    {_div_line_html("Right Upright", ru_top)}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with p2:
            clinched_wc_id_set = {w["franchise_id"] for w in clinched_wild_cards} if is_latest_model_wk else set()
            wc_parts = []
            for _, r in wc_contenders.iterrows():
                if r["franchise_id"] in clinched_wc_id_set:
                    wc_parts.append(f'{r["franchise_name"]} <span class="badge badge-bigwin">CLINCHED ✓</span>')
                else:
                    wc_parts.append(f'{r["franchise_name"]} ({r["wild_card"]*100:.1f}%)')
            wc_list_html = ", ".join(wc_parts)

            if is_latest_model_wk and clinched_points_title:
                pts_names = " / ".join(p["franchise_name"] for p in clinched_points_title)
                pts_line_html = f'{pts_names} <span class="badge badge-bigwin">WON ✓</span>'
            else:
                pts_line_html = f'{pts_favorite["franchise_name"]} <span class="badge badge-bigwin">{pts_favorite["top_pts"]*100:.1f}%</span>'

            wc_pts_awarded = (len(clinched_wc_id_set) * 30) + (60 if (is_latest_model_wk and clinched_points_title) else 0)
            wc_pts_rem = 150 - wc_pts_awarded
            wc_pts_header = (
                "All Clinched ($150)" if wc_pts_rem == 0
                else (f"${wc_pts_rem} Left" if wc_pts_awarded > 0 else "$150 Total")
            )

            st.markdown(f"""
            <div class="metric-card" style="text-align: left; padding: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span class="badge badge-silver">REGULAR SEASON</span>
                    <strong style="color: #64b5f6; font-size: 1.2rem;">{wc_pts_header}</strong>
                </div>
                <h4 style="margin: 10px 0 6px 0;">🃏 Wild Cards &amp; Points Title</h4>
                <div style="font-size: 0.88rem; opacity: 0.8; margin-bottom: 12px;">Non-division playoff seeds ($90) &amp; Total Scoring Leader ($60):</div>
                <div style="font-size: 0.88rem; line-height: 1.6;">
                    <div>&bull; <strong>Wild Card Contenders ($30 ea):</strong> {wc_list_html}</div>
                    <div style="margin-top: 4px;">&bull; <strong>Points Title ($60):</strong> {pts_line_html}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with p3:
            bye_list_html = " &bull; ".join([f"{r['franchise_name']} ({r['bye']*100:.1f}%)" for _, r in bye_favs.iterrows()])
            st.markdown(f"""
            <div class="metric-card" style="text-align: left; padding: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span class="badge badge-bigwin">POSTSEASON</span>
                    <strong style="color: #4CAF50; font-size: 1.25rem;">$470 Total</strong>
                </div>
                <h4 style="margin: 10px 0 6px 0;">🏆 Playoff Podium</h4>
                <div style="font-size: 0.88rem; opacity: 0.8; margin-bottom: 12px;">Tournament Finishers: 🥇 $275 &bull; 🥈 $135 &bull; 🥉 $60</div>
                <div style="font-size: 0.88rem; line-height: 1.6;">
                    <div>&bull; <strong>#1 Seed Favorite:</strong> {one_seed_fav['franchise_name']} <span class="badge badge-bigwin">{one_seed_fav['one_seed']*100:.1f}%</span></div>
                    <div style="margin-top: 4px;">&bull; <strong>Bye Favorites:</strong> {bye_list_html}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.write("")
        st.write("")
        st.divider()

        # Expected Value Breakdown Chart & Full Leaderboard Table
        st.markdown("#### 💰 Regular Season Expected Prize Money &amp; Probabilities")
        st.caption("Expected Value (EV) combines each franchise's modeled probability of winning their Division ($50), a Wild Card spot ($30), and the Points Title ($60).")

        # Plotly Stacked Bar Chart for EV
        ev_chart_df = sim_df.sort_values(by="expected_reg_payout", ascending=True).copy()
        plot_data = []
        for _, r in ev_chart_df.iterrows():
            plot_data.append({"franchise": r["franchise_name"], "Prize Category": "Division Title ($50)", "Expected Cash ($)": round(r["ev_division"], 2)})
            plot_data.append({"franchise": r["franchise_name"], "Prize Category": "Wild Card ($30)", "Expected Cash ($)": round(r["ev_wild_card"], 2)})
            plot_data.append({"franchise": r["franchise_name"], "Prize Category": "Points Title ($60)", "Expected Cash ($)": round(r["ev_top_pts"], 2)})
        
        plot_df = pd.DataFrame(plot_data)
        fig_ev = px.bar(
            plot_df,
            x="Expected Cash ($)",
            y="franchise",
            color="Prize Category",
            orientation="h",
            color_discrete_map={
                "Division Title ($50)": "#FFC107",
                "Wild Card ($30)": "#42A5F5",
                "Points Title ($60)": "#66BB6A"
            }
        )
        fig_ev.update_layout(
            barmode="stack",
            margin=dict(l=0, r=20, t=10, b=10),
            height=370,
            xaxis=dict(title="Expected Regular Season Payout ($)", tickprefix="$"),
            yaxis=dict(title=""),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_ev, use_container_width=True)

        st.write("")

        # Interactive Table
        tbl_df = sim_df[[
            "franchise_name", "division", "wins", "losses", "proj_wins",
            "expected_reg_payout", "win_division", "wild_card", "make_playoffs", "top_pts", "bye"
        ]].copy()
        
        tbl_df["Record"] = tbl_df["wins"].astype(str) + "-" + tbl_df["losses"].astype(str)
        tbl_df["win_division"] = tbl_df["win_division"] * 100
        tbl_df["wild_card"] = tbl_df["wild_card"] * 100
        tbl_df["make_playoffs"] = tbl_df["make_playoffs"] * 100
        tbl_df["top_pts"] = tbl_df["top_pts"] * 100
        tbl_df["bye"] = tbl_df["bye"] * 100

        tbl_df = tbl_df[[
            "franchise_name", "division", "Record", "proj_wins",
            "expected_reg_payout", "win_division", "wild_card", "make_playoffs", "top_pts", "bye"
        ]]
        tbl_df.columns = [
            "Franchise", "Division", "Record", "Proj Wins",
            "Expected Reg. Cash", "Win Division %", "Wild Card %", "Make Playoffs %", "Points Title %", "Bye %"
        ]

        st.dataframe(
            tbl_df,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Franchise": "Franchise",
                "Division": "Division",
                "Record": "Record",
                "Proj Wins": st.column_config.NumberColumn("Proj Wins", format="%.1f"),
                "Expected Reg. Cash": st.column_config.NumberColumn("Expected Cash", help="Calculated as (Div Title % × $50) + (Wild Card % × $30) + (Points Title % × $60)", format="$%.2f"),
                "Win Division %": st.column_config.ProgressColumn("Division %", format="%.1f%%", min_value=0, max_value=100),
                "Wild Card %": st.column_config.ProgressColumn("Wild Card %", format="%.1f%%", min_value=0, max_value=100),
                "Make Playoffs %": st.column_config.ProgressColumn("Playoff Odds %", format="%.1f%%", min_value=0, max_value=100),
                "Points Title %": st.column_config.ProgressColumn("Points Title %", format="%.1f%%", min_value=0, max_value=100),
                "Bye %": st.column_config.ProgressColumn("Bye %", format="%.1f%%", min_value=0, max_value=100),
            }
        )

        st.write("")
        # Callout card linking to Projected Standings page
        st.markdown("""
        <div class="week-card" style="border-left: 4px solid #ba68c8; background: rgba(156, 39, 176, 0.05); padding: 14px 20px; border-radius: 12px; margin-top: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
                <div>
                    <strong style="font-size: 1.05rem;">🔮 Looking for Projected Standings &amp; Playoff Seeds?</strong>
                    <div style="font-size: 0.88rem; opacity: 0.8; margin-top: 2px;">
                        Explore full 3-division projected tables, playoff qualification cutoffs, first-round bye odds, and #1 draft pick probabilities on the dedicated page.
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    else:
        st.info("Simulation model data for 2026 is currently generating. Check back shortly!")

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
            - **Division Titles (\\$50 each)**: Awarded to the regular season winner of each of the 3 divisions (Left Upright, Crossbar, Right Upright). Credited automatically to the Season Leaderboard as soon as a franchise mathematically clinches its division.
            - **Wild Cards (\\$30 each)**: Awarded to the top 3 non-division-winning teams qualifying for the playoffs. Credited automatically once a team is mathematically locked into a Wild Card spot or upon completion of Week 14.
            - **Points Title (\\$60)**: Awarded to the franchise that scores the highest cumulative points for across Weeks 1 through 14.
            """)
