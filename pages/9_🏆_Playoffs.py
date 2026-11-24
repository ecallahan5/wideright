import sys
import os

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import functions
import standings_utils

st.set_page_config(layout="wide", page_title="Wide Right - 2026 Playoffs", page_icon="🏆")

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
        border-color: rgba(255, 193, 7, 0.4);
    }
    .metric-val {
        font-size: 2.0rem;
        font-weight: 800;
        color: #FFC107;
        margin-top: 4px;
        margin-bottom: 2px;
    }
    .metric-lbl {
        font-size: 0.88rem;
        opacity: 0.75;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        font-weight: 600;
    }
    .metric-sub {
        font-size: 0.8rem;
        opacity: 0.65;
        margin-top: 3px;
    }
    .matchup-card {
        background: rgba(128, 128, 128, 0.04);
        border-radius: 14px;
        border: 1px solid rgba(128, 128, 128, 0.18);
        padding: 16px 20px;
        margin-bottom: 14px;
    }
    .bracket-slot {
        background: rgba(128, 128, 128, 0.05);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 12px;
        padding: 10px 14px;
        margin-bottom: 8px;
    }
    .bracket-slot-winner {
        border-color: rgba(76, 175, 80, 0.65);
        background: rgba(76, 175, 80, 0.08);
    }
    .bracket-team-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 5px 0;
        gap: 8px;
    }
    .bracket-divider {
        border-top: 1px dashed rgba(128, 128, 128, 0.25);
        margin: 4px 0;
    }
    .seed-pill {
        display: inline-block;
        min-width: 24px;
        text-align: center;
        padding: 1px 6px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 800;
        background: rgba(255, 193, 7, 0.18);
        color: #ffc107;
        border: 1px solid rgba(255, 193, 7, 0.4);
        margin-right: 6px;
    }
    .seed-pill-cons {
        background: rgba(33, 150, 243, 0.18);
        color: #64b5f6;
        border: 1px solid rgba(33, 150, 243, 0.4);
    }
    .badge {
        display: inline-block;
        padding: 3px 9px;
        border-radius: 8px;
        font-size: 0.76rem;
        font-weight: 700;
    }
    .badge-gold {
        background: rgba(255, 193, 7, 0.2);
        color: #ffc107;
        border: 1px solid rgba(255, 193, 7, 0.4);
    }
    .badge-green {
        background: rgba(76, 175, 80, 0.2);
        color: #81c784;
        border: 1px solid rgba(76, 175, 80, 0.4);
    }
    .badge-blue {
        background: rgba(33, 150, 243, 0.2);
        color: #64b5f6;
        border: 1px solid rgba(33, 150, 243, 0.4);
    }
    .badge-purple {
        background: rgba(156, 39, 176, 0.2);
        color: #ce93d8;
        border: 1px solid rgba(156, 39, 176, 0.4);
    }
    .prob-bar-wrap {
        width: 100%;
        height: 10px;
        border-radius: 6px;
        overflow: hidden;
        display: flex;
        background: rgba(128, 128, 128, 0.18);
        margin-top: 8px;
    }
    .prob-bar-left {
        background: linear-gradient(90deg, #4CAF50, #81C784);
        height: 100%;
    }
    .prob-bar-right {
        background: linear-gradient(90deg, #42A5F5, #1E88E5);
        height: 100%;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏆 2026 Playoffs & Championship Odds")
st.caption("Weeks 15–17 Championship Bracket ($470 pool), 3rd Place Game, and Consolation Bracket (Extra Draft Pick) powered by 10,000 Gamma + optimal roster simulations.")
st.divider()


@st.cache_data(ttl=300)
def fetch_playoffs_page_data():
    """Fetches franchises, standings, current week, regular-season model, and postseason sim/matchup tables."""
    franchises = functions.bq_query("""
        SELECT franchise_id, franchise_name, division, icon
        FROM `mfl-374514.dbt_production.dim_franchises`
    """)
    franchises_df = pd.DataFrame(franchises)

    try:
        standings = functions.bq_query("""
            SELECT franchise_id, CAST(wins AS INT64) AS wins, CAST(losses AS INT64) AS losses,
                   CAST(points_for AS FLOAT64) AS points_for
            FROM `mfl-374514.dbt_production.dim_standings`
        """)
        standings_df = pd.DataFrame(standings)
    except Exception:
        standings_df = pd.DataFrame()

    try:
        wk_info = functions.bq_query(
            "SELECT recent_completed_week, current_week FROM `mfl-374514.dbt_production.dim_current_week`"
        )[0]
        recent_completed_wk = int(wk_info.get("recent_completed_week", 0))
        current_wk = int(wk_info.get("current_week", recent_completed_wk + 1))
    except Exception:
        recent_completed_wk = 0
        current_wk = 1

    try:
        reg_rows = functions.bq_query("""
            SELECT franchise_id, after_week,
                   CAST(proj_wins AS FLOAT64) AS proj_wins,
                   CAST(win_division AS FLOAT64) AS win_division,
                   CAST(wild_card AS FLOAT64) AS wild_card,
                   CAST(make_playoffs AS FLOAT64) AS make_playoffs,
                   CAST(one_seed AS FLOAT64) AS one_seed,
                   CAST(bye AS FLOAT64) AS bye,
                   CAST(top_pts AS FLOAT64) AS top_pts,
                   CAST(first_pick AS FLOAT64) AS first_pick
            FROM `mfl-374514.dbt_production.fct_reg_season_model`
            WHERE year = 2026
            ORDER BY after_week DESC, proj_wins DESC
        """)
        reg_df = pd.DataFrame(reg_rows)
    except Exception:
        reg_df = pd.DataFrame()

    try:
        ps_rows = functions.bq_query("""
            SELECT franchise_id, after_week, bracket, seed,
                   CAST(reach_semis AS FLOAT64) AS reach_semis,
                   CAST(reach_finals AS FLOAT64) AS reach_finals,
                   CAST(win_championship AS FLOAT64) AS win_championship,
                   CAST(runner_up AS FLOAT64) AS runner_up,
                   CAST(third_place AS FLOAT64) AS third_place,
                   CAST(extra_pick AS FLOAT64) AS extra_pick
            FROM `mfl-374514.external.postseason_sims`
            WHERE year = 2026
            ORDER BY after_week DESC, win_championship DESC
        """)
        ps_df = pd.DataFrame(ps_rows)
    except Exception:
        ps_df = pd.DataFrame()

    try:
        m_rows = functions.bq_query("""
            SELECT after_week, week, bracket, round_name, game_num,
                   high_seed, high_franchise_id, low_seed, low_franchise_id,
                   CAST(high_win_prob AS FLOAT64) AS high_win_prob,
                   CAST(low_win_prob AS FLOAT64) AS low_win_prob,
                   CAST(high_proj_pts AS FLOAT64) AS high_proj_pts,
                   CAST(low_proj_pts AS FLOAT64) AS low_proj_pts,
                   CAST(high_actual_pts AS FLOAT64) AS high_actual_pts,
                   CAST(low_actual_pts AS FLOAT64) AS low_actual_pts,
                   winner_franchise_id
            FROM `mfl-374514.external.postseason_matchups`
            WHERE year = 2026
            ORDER BY after_week DESC, week ASC, game_num ASC
        """)
        matchups_df = pd.DataFrame(m_rows)
    except Exception:
        matchups_df = pd.DataFrame()

    return {
        "franchises_df": franchises_df,
        "standings_df": standings_df,
        "recent_completed_wk": recent_completed_wk,
        "current_wk": current_wk,
        "reg_df": reg_df,
        "ps_df": ps_df,
        "matchups_df": matchups_df,
    }


def _team_row_html(fid, seed, team_meta, pill_cls="", score_str="", prob_str="", is_winner=False):
    """Renders a single team row inside a bracket card (single-line HTML to avoid Markdown code-block parsing)."""
    if not fid or fid not in team_meta:
        seed_badge = f'<span class="seed-pill {pill_cls}">#{seed}</span>' if seed else ""
        return (
            f'<div class="bracket-team-row" style="opacity: 0.55;">'
            f'<div>{seed_badge}<em>TBD</em></div>'
            f'<div style="font-size: 0.82rem;">—</div>'
            f'</div>'
        )
    meta = team_meta[fid]
    icon_html = f'<img src="{meta["icon"]}" width="24" style="border-radius:50%; vertical-align:middle; margin-right:6px;">' if meta.get("icon") else ""
    seed_badge = f'<span class="seed-pill {pill_cls}">#{int(seed)}</span>' if pd.notna(seed) else ""
    name_weight = "800" if is_winner else "600"
    win_check = " ✓" if is_winner else ""
    right_parts = []
    if score_str:
        right_parts.append(f'<strong>{score_str}</strong>')
    if prob_str:
        right_parts.append(f'<span style="opacity:0.75; font-size:0.8rem;">{prob_str}</span>')
    right_html = " &bull; ".join(right_parts) if right_parts else ""
    return (
        f'<div class="bracket-team-row">'
        f'<div style="display:flex; align-items:center;">'
        f'{seed_badge}{icon_html}<span style="font-weight:{name_weight};">{meta["franchise_name"]}{win_check}</span>'
        f'</div>'
        f'<div style="font-size: 0.85rem; white-space: nowrap;">{right_html}</div>'
        f'</div>'
    )


def render_bracket_card(title, high_id, high_seed, low_id, low_seed, team_meta, is_consolation=False,
                        high_pts=None, low_pts=None, high_prob=None, low_prob=None, winner_id=None, subtitle=""):
    """Renders a sleek matchup card inside the 3-round bracket."""
    pill_cls = "seed-pill-cons" if is_consolation else ""
    h_score = f"{high_pts:.1f}" if pd.notna(high_pts) else ""
    l_score = f"{low_pts:.1f}" if pd.notna(low_pts) else ""
    h_prob = f"{high_prob*100:.0f}%" if (pd.notna(high_prob) and not winner_id) else ""
    l_prob = f"{low_prob*100:.0f}%" if (pd.notna(low_prob) and not winner_id) else ""
    card_cls = "bracket-slot bracket-slot-winner" if winner_id else "bracket-slot"
    sub_html = f'<span style="font-size:0.74rem; opacity:0.65;">{subtitle}</span>' if subtitle else ""
    row_high = _team_row_html(high_id, high_seed, team_meta, pill_cls, h_score, h_prob, is_winner=(winner_id is not None and winner_id == high_id))
    row_low = _team_row_html(low_id, low_seed, team_meta, pill_cls, l_score, l_prob, is_winner=(winner_id is not None and winner_id == low_id))
    html = (
        f'<div class="{card_cls}">'
        f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">'
        f'<span style="font-size:0.74rem; text-transform:uppercase; letter-spacing:0.5px; font-weight:700; opacity:0.75;">{title}</span>'
        f'{sub_html}'
        f'</div>'
        f'{row_high}'
        f'<div class="bracket-divider"></div>'
        f'{row_low}'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_matchup_preview_card(row, team_meta, is_consolation=False):
    """Renders a wide head-to-head preview card for active postseason week games."""
    h_id = row["high_franchise_id"]
    l_id = row["low_franchise_id"]
    if not h_id or not l_id or h_id not in team_meta or l_id not in team_meta:
        return
    h_meta = team_meta[h_id]
    l_meta = team_meta[l_id]
    pill_cls = "seed-pill-cons" if is_consolation else ""

    h_prob = float(row["high_win_prob"]) if pd.notna(row["high_win_prob"]) else 0.5
    l_prob = float(row["low_win_prob"]) if pd.notna(row["low_win_prob"]) else (1.0 - h_prob)
    h_proj = f"Proj: {row['high_proj_pts']:.1f} pts" if pd.notna(row["high_proj_pts"]) else ""
    l_proj = f"Proj: {row['low_proj_pts']:.1f} pts" if pd.notna(row["low_proj_pts"]) else ""

    winner_id = row["winner_franchise_id"] if pd.notna(row["winner_franchise_id"]) else None
    if winner_id and pd.notna(row["high_actual_pts"]) and pd.notna(row["low_actual_pts"]):
        status_badge = '<span class="badge badge-green">FINAL</span>'
        h_proj = f"Final: {row['high_actual_pts']:.2f} pts"
        l_proj = f"Final: {row['low_actual_pts']:.2f} pts"
    else:
        status_badge = f'<span class="badge badge-gold">WEEK {int(row["week"])} &bull; {row["round_name"].upper()}</span>'

    h_icon = f'<img src="{h_meta["icon"]}" width="44" style="border-radius:50%; margin-right:10px;">' if h_meta.get("icon") else ""
    l_icon = f'<img src="{l_meta["icon"]}" width="44" style="border-radius:50%; margin-left:10px;">' if l_meta.get("icon") else ""

    html = (
        f'<div class="matchup-card">'
        f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">'
        f'{status_badge}'
        f'<span style="font-size:0.8rem; opacity:0.7;">10,000 Gamma Roster Simulations</span>'
        f'</div>'
        f'<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">'
        f'<div style="display:flex; align-items:center;">'
        f'{h_icon}'
        f'<div>'
        f'<div><span class="seed-pill {pill_cls}">#{int(row["high_seed"])}</span><strong>{h_meta["franchise_name"]}</strong></div>'
        f'<div style="font-size:0.82rem; opacity:0.75;">{h_proj}</div>'
        f'</div>'
        f'</div>'
        f'<div style="text-align:center;">'
        f'<span style="font-size:1.35rem; font-weight:800; color:#66BB6A;">{h_prob*100:.1f}%</span>'
        f'<span style="margin:0 10px; opacity:0.5; font-weight:700;">vs</span>'
        f'<span style="font-size:1.35rem; font-weight:800; color:#42A5F5;">{l_prob*100:.1f}%</span>'
        f'</div>'
        f'<div style="display:flex; align-items:center; text-align:right;">'
        f'<div>'
        f'<div><strong>{l_meta["franchise_name"]}</strong> <span class="seed-pill {pill_cls}" style="margin-left:6px; margin-right:0;">#{int(row["low_seed"])}</span></div>'
        f'<div style="font-size:0.82rem; opacity:0.75;">{l_proj}</div>'
        f'</div>'
        f'{l_icon}'
        f'</div>'
        f'</div>'
        f'<div class="prob-bar-wrap">'
        f'<div class="prob-bar-left" style="width: {h_prob*100:.1f}%;"></div>'
        f'<div class="prob-bar-right" style="width: {l_prob*100:.1f}%;"></div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def build_projected_seeds(reg_latest_df, franchises_df):
    """Derives projected Seeds #1-#6 (Championship) and Consolation #1-#6 (best-to-worst #7-#12) during regular season."""
    merged = franchises_df.merge(reg_latest_df, on="franchise_id", how="left")
    merged["proj_wins"] = merged["proj_wins"].fillna(0.0)
    merged["win_division"] = merged["win_division"].fillna(0.0)

    div_winners = []
    for div_name in sorted(merged["division"].unique()):
        div_grp = merged[merged["division"] == div_name].sort_values(
            by=["win_division", "proj_wins"], ascending=[False, False]
        )
        if not div_grp.empty:
            div_winners.append(div_grp.iloc[0]["franchise_id"])

    div_win_df = merged[merged["franchise_id"].isin(div_winners)].sort_values(
        by=["proj_wins", "one_seed"], ascending=[False, False]
    )
    non_div_df = merged[~merged["franchise_id"].isin(div_winners)].sort_values(
        by=["proj_wins", "make_playoffs"], ascending=[False, False]
    )

    champ_ids = div_win_df["franchise_id"].tolist() + non_div_df["franchise_id"].head(3).tolist()
    cons_ids = non_div_df["franchise_id"].iloc[3:9].tolist()

    return (
        {i + 1: tid for i, tid in enumerate(champ_ids)},
        {i + 1: tid for i, tid in enumerate(cons_ids)},
    )


data = fetch_playoffs_page_data()
franchises_df = data["franchises_df"]
standings_df = data["standings_df"]
recent_completed_wk = data["recent_completed_wk"]
current_wk = data["current_wk"]
reg_df = data["reg_df"]
ps_df = data["ps_df"]
matchups_df = data["matchups_df"]

if franchises_df.empty:
    st.warning("Unable to load franchise data from BigQuery right now.")
    st.stop()

# Build franchise metadata lookup
team_meta = {}
standings_lookup = standings_df.set_index("franchise_id").to_dict("index") if not standings_df.empty else {}
for _, r in franchises_df.iterrows():
    fid = r["franchise_id"]
    st_row = standings_lookup.get(fid, {})
    team_meta[fid] = {
        "franchise_name": r["franchise_name"],
        "division": r["division"],
        "icon": r.get("icon", ""),
        "wins": int(st_row.get("wins", 0)),
        "losses": int(st_row.get("losses", 0)),
        "points_for": float(st_row.get("points_for", 0.0)),
    }

has_ps_sims = not ps_df.empty
latest_ps_wk = int(ps_df["after_week"].max()) if has_ps_sims else None
latest_reg_wk = int(reg_df["after_week"].max()) if not reg_df.empty else recent_completed_wk
is_live_playoffs = (not matchups_df.empty) and (int(matchups_df["after_week"].max()) >= 14)

# Calibration Week Selector (if postseason sims exist across multiple weeks)
if has_ps_sims:
    avail_ps_wks = sorted(ps_df["after_week"].unique(), reverse=True)
    c_info, c_sel = st.columns([0.72, 0.28])
    with c_info:
        if is_live_playoffs:
            st.markdown(
                '<div style="font-size:0.95rem; opacity:0.85; margin-top:4px;">'
                'Live postseason bracket tracking active! Matchup Win % and Championship odds update automatically as Weeks 15–17 unfold.'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="font-size:0.95rem; opacity:0.85; margin-top:4px;">'
                'Full-season Monte Carlo simulation projecting remaining regular-season games AND the 3-round reseeded Weeks 15–17 brackets.'
                '</div>',
                unsafe_allow_html=True,
            )
    with c_sel:
        selected_ps_wk = st.selectbox(
            "Simulation Week:",
            options=avail_ps_wks,
            format_func=lambda w: f"After Week {w}" + (" (Playoffs)" if w >= 14 else ""),
            key="playoffs_sim_wk_select",
        )
    ps_wk_df = ps_df[ps_df["after_week"] == selected_ps_wk].copy()
    ps_wk_df = ps_wk_df.merge(franchises_df, on="franchise_id", how="left")
    ps_wk_df["playoff_ev"] = (
        ps_wk_df["win_championship"] * standings_utils.CHAMPION_PAYOUT
        + ps_wk_df["runner_up"] * standings_utils.RUNNER_UP_PAYOUT
        + ps_wk_df["third_place"] * standings_utils.THIRD_PLACE_PAYOUT
    )
    active_matchups_df = (
        matchups_df[matchups_df["after_week"] == selected_ps_wk].copy()
        if not matchups_df.empty else pd.DataFrame()
    )
    viewing_live = (not active_matchups_df.empty) and (selected_ps_wk >= 14)
else:
    selected_ps_wk = latest_reg_wk
    ps_wk_df = pd.DataFrame()
    active_matchups_df = pd.DataFrame()
    viewing_live = False

reg_latest_df = reg_df[reg_df["after_week"] == latest_reg_wk].copy() if not reg_df.empty else pd.DataFrame()
proj_champ_seeds, proj_cons_seeds = (
    build_projected_seeds(reg_latest_df, franchises_df)
    if not reg_latest_df.empty else ({}, {})
)

# --- Top KPI Row ---
k1, k2, k3, k4 = st.columns(4)

if has_ps_sims and not ps_wk_df.empty:
    champ_fav = ps_wk_df.sort_values(by="win_championship", ascending=False).iloc[0]
    ev_fav = ps_wk_df.sort_values(by="playoff_ev", ascending=False).iloc[0]
    extra_fav = ps_wk_df.sort_values(by="extra_pick", ascending=False).iloc[0]
    with k1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-lbl">Championship Favorite</div>
            <div class="metric-val" style="color:#FFC107;">{champ_fav['win_championship']*100:.1f}%</div>
            <div class="metric-sub">{champ_fav['franchise_name']} ($275 Title)</div>
        </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-lbl">Top Playoff $EV</div>
            <div class="metric-val" style="color:#4CAF50;">${ev_fav['playoff_ev']:.2f}</div>
            <div class="metric-sub">{ev_fav['franchise_name']} ($470 Podium Pool)</div>
        </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-lbl">Extra Pick Favorite</div>
            <div class="metric-val" style="color:#42A5F5;">{extra_fav['extra_pick']*100:.1f}%</div>
            <div class="metric-sub">{extra_fav['franchise_name']} (Consolation)</div>
        </div>
        """, unsafe_allow_html=True)
else:
    top_one_seed = (
        franchises_df.merge(reg_latest_df, on="franchise_id").sort_values("one_seed", ascending=False).iloc[0]
        if not reg_latest_df.empty else None
    )
    with k1:
        val_txt = f"{top_one_seed['one_seed']*100:.1f}%" if top_one_seed is not None else "—"
        sub_txt = f"{top_one_seed['franchise_name']} (#1 Seed Odds)" if top_one_seed is not None else "Awaiting sim run"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-lbl">Projected #1 Seed</div>
            <div class="metric-val" style="color:#FFC107;">{val_txt}</div>
            <div class="metric-sub">{sub_txt}</div>
        </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-lbl">Playoff Podium Pool</div>
            <div class="metric-val" style="color:#4CAF50;">$470</div>
            <div class="metric-sub">🥇 $275 &bull; 🥈 $135 &bull; 🥉 $60</div>
        </div>
        """, unsafe_allow_html=True)
    with k3:
        cons_1_id = proj_cons_seeds.get(1)
        cons_1_name = team_meta[cons_1_id]["franchise_name"] if cons_1_id in team_meta else "TBD"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-lbl">Consolation #1 Seed</div>
            <div class="metric-val" style="color:#42A5F5; font-size:1.45rem;">{cons_1_name}</div>
            <div class="metric-sub">Projected Top Seed for Extra Pick</div>
        </div>
        """, unsafe_allow_html=True)

if recent_completed_wk >= 17:
    status_val, status_sub = "Complete", "2026 Champion Crowned!"
elif recent_completed_wk == 16:
    status_val, status_sub = "Week 17", "Championship & 3rd Place Finals"
elif recent_completed_wk == 15:
    status_val, status_sub = "Week 16", "Reseeded Semifinals"
elif recent_completed_wk == 14:
    status_val, status_sub = "Week 15", "Wild Card Round (#3v#6, #4v#5)"
else:
    wks_to_go = max(0, 14 - recent_completed_wk)
    status_val = f"{wks_to_go} Wk{'s' if wks_to_go != 1 else ''}"
    status_sub = f"Until Playoffs (Through Wk {recent_completed_wk})"

with k4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-lbl">Postseason Status</div>
        <div class="metric-val" style="color:#ba68c8;">{status_val}</div>
        <div class="metric-sub">{status_sub}</div>
    </div>
    """, unsafe_allow_html=True)

if not has_ps_sims:
    st.write("")
    st.info(
        "Full Weeks 15–17 Championship, 3rd Place, and Extra Pick probabilities will appear automatically "
        "after the next **Run Playoff Odds Simulation** run (every Tuesday or via GitHub Actions `workflow_dispatch`). "
        "Below is the live projected bracket based on current regular-season projections."
    )

st.write("")

# --- Tabs ---
tab_champ, tab_cons = st.tabs([
    "🏆 Championship Bracket ($470)",
    "🎁 Consolation Bracket (Extra Pick)",
])


def render_bracket_section(bracket_key, is_consolation=False):
    """Renders active previews + 3-round visual bracket for Championship or Consolation."""
    if viewing_live:
        b_matchups = active_matchups_df[active_matchups_df["bracket"] == bracket_key].copy()
        if b_matchups.empty:
            st.info("Matchups for this bracket are not populated yet.")
            return

        # Active week matchup previews (games with both teams known for current_wk or latest round)
        target_wk = min(max(int(selected_ps_wk) + 1, 15), 17)
        wk_games = b_matchups[b_matchups["week"] == target_wk]
        wk_games_known = wk_games[wk_games["high_franchise_id"].notna() & wk_games["low_franchise_id"].notna()]
        if not wk_games_known.empty:
            round_label = wk_games_known.iloc[0]["round_name"]
            st.markdown(f"#### ⚡ Week {target_wk} Matchup Previews ({round_label})")
            for _, mrow in wk_games_known.iterrows():
                render_matchup_preview_card(mrow, team_meta, is_consolation=is_consolation)
            st.write("")

        st.markdown("#### 🗓️ Live 3-Round Bracket")
        if not is_consolation:
            st.caption("Reseeded after Wild Card Round: #1 plays the lowest-ranked surviving seed; #2 plays the highest-ranked surviving seed.")

        col_wc, col_sf, col_fin = st.columns(3, gap="large")

        def get_game(rname, gnum):
            sub = b_matchups[(b_matchups["round_name"] == rname) & (b_matchups["game_num"] == gnum)]
            return sub.iloc[0] if not sub.empty else None

        with col_wc:
            st.markdown("**Week 15 — Wild Card**")
            for gnum, lbl in [(1, "Wild Card 1 (#3 vs #6)"), (2, "Wild Card 2 (#4 vs #5)")]:
                g = get_game("Wild Card", gnum)
                if g is not None:
                    render_bracket_card(
                        lbl, g["high_franchise_id"], g["high_seed"], g["low_franchise_id"], g["low_seed"],
                        team_meta, is_consolation=is_consolation,
                        high_pts=g["high_actual_pts"], low_pts=g["low_actual_pts"],
                        high_prob=g["high_win_prob"], low_prob=g["low_win_prob"],
                        winner_id=g["winner_franchise_id"] if pd.notna(g["winner_franchise_id"]) else None,
                    )

        with col_sf:
            st.markdown("**Week 16 — Semifinals**")
            for gnum, lbl in [(1, "Semifinal 1 (#1 Bye)"), (2, "Semifinal 2 (#2 Bye)")]:
                g = get_game("Semifinals", gnum)
                if g is not None:
                    render_bracket_card(
                        lbl, g["high_franchise_id"], g["high_seed"], g["low_franchise_id"], g["low_seed"],
                        team_meta, is_consolation=is_consolation,
                        high_pts=g["high_actual_pts"], low_pts=g["low_actual_pts"],
                        high_prob=g["high_win_prob"], low_prob=g["low_win_prob"],
                        winner_id=g["winner_franchise_id"] if pd.notna(g["winner_franchise_id"]) else None,
                    )

        with col_fin:
            st.markdown("**Week 17 — Championship**")
            g_fin = get_game("Finals", 1)
            if g_fin is not None:
                fin_title = "Extra Pick Final" if is_consolation else "Championship Game ($275 / $135)"
                render_bracket_card(
                    fin_title, g_fin["high_franchise_id"], g_fin["high_seed"], g_fin["low_franchise_id"], g_fin["low_seed"],
                    team_meta, is_consolation=is_consolation,
                    high_pts=g_fin["high_actual_pts"], low_pts=g_fin["low_actual_pts"],
                    high_prob=g_fin["high_win_prob"], low_prob=g_fin["low_win_prob"],
                    winner_id=g_fin["winner_franchise_id"] if pd.notna(g_fin["winner_franchise_id"]) else None,
                )
            if not is_consolation:
                g_tp = get_game("3rd Place", 1)
                if g_tp is not None:
                    render_bracket_card(
                        "3rd Place Game ($60)", g_tp["high_franchise_id"], g_tp["high_seed"],
                        g_tp["low_franchise_id"], g_tp["low_seed"],
                        team_meta, is_consolation=False,
                        high_pts=g_tp["high_actual_pts"], low_pts=g_tp["low_actual_pts"],
                        high_prob=g_tp["high_win_prob"], low_prob=g_tp["low_win_prob"],
                        winner_id=g_tp["winner_franchise_id"] if pd.notna(g_tp["winner_franchise_id"]) else None,
                    )
    else:
        # Regular Season Preview Mode: render projected bracket from projected seeds
        seeds_map = proj_cons_seeds if is_consolation else proj_champ_seeds
        if len(seeds_map) < 6:
            st.info("Projected bracket seeds are generating. Check back shortly!")
            return

        st.markdown("#### 🔮 Projected 3-Round Bracket (If Regular Season Ended as Projected)")
        st.caption("Seeds update automatically every week and lock into official MFL matchups upon completion of Week 14. Semifinals are reseeded (#1 vs lowest surviving seed).")

        col_wc, col_sf, col_fin = st.columns(3, gap="large")
        with col_wc:
            st.markdown("**Week 15 — Wild Card**")
            render_bracket_card("Wild Card 1 (#3 vs #6)", seeds_map[3], 3, seeds_map[6], 6, team_meta, is_consolation=is_consolation, subtitle="Projected")
            render_bracket_card("Wild Card 2 (#4 vs #5)", seeds_map[4], 4, seeds_map[5], 5, team_meta, is_consolation=is_consolation, subtitle="Projected")
        with col_sf:
            st.markdown("**Week 16 — Semifinals**")
            render_bracket_card("Semifinal 1 (#1 Bye)", seeds_map[1], 1, None, None, team_meta, is_consolation=is_consolation, subtitle="vs Lowest Surviving Seed")
            render_bracket_card("Semifinal 2 (#2 Bye)", seeds_map[2], 2, None, None, team_meta, is_consolation=is_consolation, subtitle="vs Highest Surviving Seed")
        with col_fin:
            st.markdown("**Week 17 — Finals**")
            fin_title = "Extra Pick Final" if is_consolation else "Championship Game ($275 / $135)"
            render_bracket_card(fin_title, None, None, None, None, team_meta, is_consolation=is_consolation, subtitle="Semifinal Winners")
            if not is_consolation:
                render_bracket_card("3rd Place Game ($60)", None, None, None, None, team_meta, is_consolation=False, subtitle="Semifinal Losers")


# =========================================================================
# TAB 1: CHAMPIONSHIP BRACKET
# =========================================================================
with tab_champ:
    st.subheader("Championship Bracket & Title Odds", divider="orange")
    render_bracket_section("championship", is_consolation=False)

    if has_ps_sims and not ps_wk_df.empty:
        st.divider()
        st.markdown("#### 📊 Championship, Runner-Up &amp; 3rd Place Probabilities")

        if viewing_live:
            champ_odds_df = ps_wk_df[ps_wk_df["bracket"] == "championship"].copy()
        else:
            champ_odds_df = ps_wk_df[
                (ps_wk_df["win_championship"] > 0) | (ps_wk_df["reach_semis"] > 0)
            ].copy()

        champ_odds_df = champ_odds_df.sort_values(
            by=["win_championship", "runner_up", "third_place"], ascending=[False, False, False]
        ).reset_index(drop=True)

        col_ch_chart, col_ch_tbl = st.columns([1.0, 1.0], gap="large")

        with col_ch_chart:
            chart_src = champ_odds_df.sort_values(by="win_championship", ascending=True)
            bar_rows = []
            for _, r in chart_src.iterrows():
                bar_rows.append({"Franchise": r["franchise_name"], "Finish": "🥇 Champion ($275)", "Probability (%)": round(r["win_championship"] * 100, 1)})
                bar_rows.append({"Franchise": r["franchise_name"], "Finish": "🥈 Runner-Up ($135)", "Probability (%)": round(r["runner_up"] * 100, 1)})
                bar_rows.append({"Franchise": r["franchise_name"], "Finish": "🥉 3rd Place ($60)", "Probability (%)": round(r["third_place"] * 100, 1)})
            fig_champ = px.bar(
                pd.DataFrame(bar_rows),
                x="Probability (%)",
                y="Franchise",
                color="Finish",
                orientation="h",
                color_discrete_map={
                    "🥇 Champion ($275)": "#FFC107",
                    "🥈 Runner-Up ($135)": "#B0BEC5",
                    "🥉 3rd Place ($60)": "#FF8A65",
                },
            )
            fig_champ.update_layout(
                barmode="stack",
                margin=dict(l=0, r=20, t=30, b=10),
                height=380,
                xaxis=dict(title="Podium Finish Odds (%)", ticksuffix="%"),
                yaxis=dict(title=""),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig_champ, use_container_width=True)

        with col_ch_tbl:
            tbl = champ_odds_df[[
                "franchise_name", "reach_semis", "reach_finals",
                "win_championship", "runner_up", "third_place", "playoff_ev"
            ]].copy()
            for c in ["reach_semis", "reach_finals", "win_championship", "runner_up", "third_place"]:
                tbl[c] = tbl[c] * 100.0
            tbl.columns = ["Franchise", "Semis %", "Finals %", "Champ %", "Runner-Up %", "3rd %", "Playoff EV"]
            st.dataframe(
                tbl,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Semis %": st.column_config.NumberColumn("Semis %", format="%.1f%%"),
                    "Finals %": st.column_config.NumberColumn("Finals %", format="%.1f%%"),
                    "Champ %": st.column_config.ProgressColumn("Champ %", format="%.1f%%", min_value=0, max_value=100),
                    "Runner-Up %": st.column_config.NumberColumn("Runner-Up %", format="%.1f%%"),
                    "3rd %": st.column_config.NumberColumn("3rd %", format="%.1f%%"),
                    "Playoff EV": st.column_config.NumberColumn("Playoff EV", format="$%.2f"),
                },
            )

        # Road to the Title Sankey Diagram (top contenders flowing into Semis -> Finals/3rd Place -> Podium)
        sankey_teams = champ_odds_df.head(6)
        if not sankey_teams.empty and sankey_teams["reach_semis"].sum() > 0:
            st.divider()
            st.markdown("#### 🛣️ Road to the Title (Simulated Playoff Flow)")
            st.caption("Tracks how the top 6 contenders advance from Semifinals into the Championship Game, 3rd Place Game, and final cash podium finishes.")

            team_labels = sankey_teams["franchise_name"].tolist()
            n_t = len(team_labels)
            node_labels = team_labels + [
                "Championship Game",
                "3rd Place Game",
                "🥇 Champion ($275)",
                "🥈 Runner-Up ($135)",
                "🥉 3rd Place ($60)",
                "4th Place ($0)",
            ]
            idx_finals = n_t
            idx_third_gm = n_t + 1
            idx_champ = n_t + 2
            idx_ru = n_t + 3
            idx_3rd = n_t + 4
            idx_4th = n_t + 5

            palette = ["#FFC107", "#42A5F5", "#66BB6A", "#AB47BC", "#FF7043", "#26C6DA"]
            node_colors = palette[:n_t] + ["#FFD54F", "#90A4AE", "#FFC107", "#B0BEC5", "#FF8A65", "#78909C"]

            sources, targets, values, link_colors = [], [], [], []
            total_champ = 0.0
            total_ru = 0.0
            total_3rd = 0.0
            total_4th = 0.0

            for idx_i, (_, r) in enumerate(sankey_teams.iterrows()):
                p_fin = max(0.0, float(r["reach_finals"]) * 100.0)
                p_semis_loss = max(0.0, (float(r["reach_semis"]) - float(r["reach_finals"])) * 100.0)
                if p_fin > 0.1:
                    sources.append(idx_i)
                    targets.append(idx_finals)
                    values.append(round(p_fin, 2))
                    link_colors.append("rgba(255, 193, 7, 0.35)")
                if p_semis_loss > 0.1:
                    sources.append(idx_i)
                    targets.append(idx_third_gm)
                    values.append(round(p_semis_loss, 2))
                    link_colors.append("rgba(144, 164, 174, 0.28)")
                total_champ += float(r["win_championship"]) * 100.0
                total_ru += float(r["runner_up"]) * 100.0
                total_3rd += float(r["third_place"]) * 100.0
                total_4th += max(0.0, (float(r["reach_semis"]) - float(r["reach_finals"]) - float(r["third_place"])) * 100.0)

            for src, tgt, val, col in [
                (idx_finals, idx_champ, total_champ, "rgba(255, 193, 7, 0.55)"),
                (idx_finals, idx_ru, total_ru, "rgba(176, 190, 197, 0.45)"),
                (idx_third_gm, idx_3rd, total_3rd, "rgba(255, 138, 101, 0.45)"),
                (idx_third_gm, idx_4th, total_4th, "rgba(120, 144, 156, 0.30)"),
            ]:
                if val > 0.1:
                    sources.append(src)
                    targets.append(tgt)
                    values.append(round(val, 2))
                    link_colors.append(col)

            fig_sankey = go.Figure(data=[go.Sankey(
                node=dict(
                    pad=18,
                    thickness=18,
                    line=dict(color="rgba(255,255,255,0.2)", width=0.5),
                    label=node_labels,
                    color=node_colors,
                ),
                link=dict(
                    source=sources,
                    target=targets,
                    value=values,
                    color=link_colors,
                ),
            )])
            fig_sankey.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_sankey, use_container_width=True)


# =========================================================================
# TAB 2: CONSOLATION BRACKET (EXTRA DRAFT PICK)
# =========================================================================
with tab_cons:
    st.subheader("Consolation Bracket — Battle for the Extra Draft Pick", divider="blue")
    st.caption("The 6 non-playoff franchises are seeded best-to-worst (#7 overall = Consolation #1 with a first-round bye, ..., #12 = Consolation #6). The bracket winner earns the Extra Draft Pick.")

    render_bracket_section("consolation", is_consolation=True)

    if has_ps_sims and not ps_wk_df.empty:
        st.divider()
        st.markdown("#### 🎟️ Extra Draft Pick Probabilities")

        if viewing_live:
            cons_odds_df = ps_wk_df[ps_wk_df["bracket"] == "consolation"].copy()
        else:
            cons_odds_df = ps_wk_df[ps_wk_df["extra_pick"] > 0].copy()

        cons_odds_df = cons_odds_df.sort_values(by="extra_pick", ascending=False).reset_index(drop=True)

        if not cons_odds_df.empty:
            c_chart, c_tbl = st.columns([1.0, 1.0], gap="large")
            with c_chart:
                c_src = cons_odds_df.sort_values(by="extra_pick", ascending=True).copy()
                c_src["extra_pick_pct"] = c_src["extra_pick"] * 100.0
                fig_cons = px.bar(
                    c_src,
                    x="extra_pick_pct",
                    y="franchise_name",
                    orientation="h",
                    text="extra_pick_pct",
                    color="extra_pick_pct",
                    color_continuous_scale="Blues",
                    labels={"extra_pick_pct": "Extra Pick Odds (%)", "franchise_name": "Franchise"},
                )
                fig_cons.update_traces(texttemplate="%{x:.1f}%", textposition="outside", cliponaxis=False)
                fig_cons.update_layout(
                    margin=dict(l=0, r=45, t=10, b=10),
                    height=340,
                    coloraxis_showscale=False,
                    xaxis=dict(visible=False),
                    yaxis=dict(title=""),
                )
                st.plotly_chart(fig_cons, use_container_width=True)

            with c_tbl:
                if viewing_live:
                    ctbl = cons_odds_df[["seed", "franchise_name", "reach_semis", "reach_finals", "extra_pick"]].copy()
                    for col in ["reach_semis", "reach_finals", "extra_pick"]:
                        ctbl[col] = ctbl[col] * 100.0
                    ctbl.columns = ["Cons. Seed", "Franchise", "Semis %", "Finals %", "Extra Pick %"]
                else:
                    ctbl = cons_odds_df[["franchise_name", "division", "extra_pick"]].copy()
                    ctbl["extra_pick"] = ctbl["extra_pick"] * 100.0
                    ctbl.columns = ["Franchise", "Division", "Extra Pick %"]
                st.dataframe(
                    ctbl,
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "Extra Pick %": st.column_config.ProgressColumn("Extra Pick %", format="%.1f%%", min_value=0, max_value=100),
                    },
                )
        else:
            st.info("No Extra Pick odds recorded for this week yet.")
