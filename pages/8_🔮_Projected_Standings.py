import sys
import os

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import streamlit as st
import pandas as pd
import numpy as np
from itertools import combinations
from functools import cmp_to_key
import plotly.express as px
import plotly.graph_objects as go
import functions
import global_vars

st.set_page_config(layout="wide", page_title="Wide Right - Projected Standings", page_icon="🔮")

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
        border-color: rgba(156, 39, 176, 0.35);
    }
    .metric-val {
        font-size: 2.1rem;
        font-weight: 800;
        color: #9c27b0;
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
    .week-card {
        background: rgba(128, 128, 128, 0.04);
        border-radius: 14px;
        border: 1px solid rgba(128, 128, 128, 0.18);
        padding: 16px 20px;
        margin-bottom: 14px;
    }
    .badge {
        display: inline-block;
        padding: 3px 9px;
        border-radius: 8px;
        font-size: 0.8rem;
        font-weight: 700;
    }
    .badge-gold {
        background: rgba(255, 193, 7, 0.2);
        color: #ffc107;
        border: 1px solid rgba(255, 193, 7, 0.4);
    }
    .badge-silver {
        background: rgba(158, 158, 158, 0.25);
        color: #9e9e9e;
        border: 1px solid rgba(158, 158, 158, 0.5);
    }
    .badge-bronze {
        background: rgba(205, 127, 50, 0.2);
        color: #ffaa66;
        border: 1px solid rgba(205, 127, 50, 0.4);
    }
    .badge-purple {
        background: rgba(156, 39, 176, 0.2);
        color: #ba68c8;
        border: 1px solid rgba(156, 39, 176, 0.4);
    }
    .badge-blue {
        background: rgba(33, 150, 243, 0.2);
        color: #64b5f6;
        border: 1px solid rgba(33, 150, 243, 0.4);
    }
    .clinch-tag {
        display: inline-block;
        padding: 1px 7px;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 800;
        margin-left: 6px;
        vertical-align: middle;
        letter-spacing: 0.4px;
    }
    .clinch-z {
        background: rgba(255, 215, 0, 0.22);
        color: #ffd54f;
        border: 1px solid rgba(255, 215, 0, 0.55);
    }
    .clinch-y {
        background: rgba(156, 39, 176, 0.22);
        color: #ce93d8;
        border: 1px solid rgba(156, 39, 176, 0.55);
    }
    .clinch-x {
        background: rgba(76, 175, 80, 0.22);
        color: #81c784;
        border: 1px solid rgba(76, 175, 80, 0.55);
    }
    .clinch-e {
        background: rgba(244, 67, 54, 0.18);
        color: #e57373;
        border: 1px solid rgba(244, 67, 54, 0.45);
    }
    .mover-card {
        background: rgba(128, 128, 128, 0.04);
        border: 1px solid rgba(128, 128, 128, 0.18);
        border-radius: 14px;
        padding: 14px 18px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .mover-card:hover {
        transform: translateY(-2px);
    }
    .delta-pill-pos {
        display: inline-block;
        padding: 1px 6px;
        border-radius: 5px;
        font-size: 0.72rem;
        font-weight: 700;
        background: rgba(76, 175, 80, 0.16);
        color: #66bb6a;
    }
    .delta-pill-neg {
        display: inline-block;
        padding: 1px 6px;
        border-radius: 5px;
        font-size: 0.72rem;
        font-weight: 700;
        background: rgba(244, 67, 54, 0.16);
        color: #ef5350;
    }
    .delta-pill-flat {
        display: inline-block;
        padding: 1px 6px;
        border-radius: 5px;
        font-size: 0.72rem;
        font-weight: 600;
        background: rgba(158, 158, 158, 0.14);
        color: #9e9e9e;
    }
    .prob-card {
        background: rgba(128, 128, 128, 0.04);
        border: 1px solid rgba(128, 128, 128, 0.16);
        border-radius: 12px;
        padding: 12px 14px;
        margin-bottom: 10px;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .prob-card:hover {
        transform: translateY(-2px);
        border-color: rgba(156, 39, 176, 0.4);
    }
</style>
""", unsafe_allow_html=True)

st.title("🔮 Projected Standings & Playoff Picture")
st.caption("Monte Carlo regular season simulations (10,000 iterations), projected win totals, division title odds, playoff seeds, and draft pick probabilities.")
st.divider()

# --- Data Fetching ---
@st.cache_data(ttl=300)
def fetch_projected_standings_data():
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
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def fetch_schedule_and_results_data():
    """Fetches full season schedule paired with weekly scores for Remaining SoS and exact Clinch/Elimination bounds."""
    query = """
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
    """
    try:
        rows = functions.bq_query(query)
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()


def enrich_standings_data(sim_data, model_df, sched_df, selected_wk, available_weeks):
    """
    Enriches sim_data with:
      1. Week-over-Week Deltas (playoff_delta, div_delta, bye_delta, one_seed_delta, first_pick_delta, top_pts_delta, proj_wins_delta)
      2. Remaining Strength of Schedule (rem_sos_proj_wins, rem_sos_win_pct, rem_sos_ppg, rem_sos_rank, rem_games_count, rem_opponents_detail)
      3. Mathematical Clinch & Elimination Tags ([Z], [Y], [X], [E]) accounting for 28-game H2H + Median rules
    """
    df = sim_data.copy()
    max_avail_wk = max(available_weeks) if available_weeks else selected_wk

    # --- 1. Historical Standings Calibration (if viewing an earlier week) ---
    team_ids = sorted(df["franchise_id"].unique())
    div_map = dict(zip(df["franchise_id"], df["division"]))
    name_map = dict(zip(df["franchise_id"], df["franchise_name"]))

    past_h2h = {t1: {t2: 0 for t2 in team_ids} for t1 in team_ids}
    rem_h2h = {t1: {t2: 0 for t2 in team_ids} for t1 in team_ids}
    past_div_wins = {t: 0 for t in team_ids}

    if not sched_df.empty:
        reg_sched = sched_df[sched_df["week"] <= 14].copy()
        reg_weeks = sorted(reg_sched["week"].unique())
        rem_weeks = [w for w in reg_weeks if w > selected_wk]
        w_rem = len(rem_weeks)

        # Populate past H2H, division wins, and remaining H2H counts
        for _, row in reg_sched.iterrows():
            wk = int(row["week"])
            f_id = row["franchise_id"]
            o_id = row["opp_id"]
            if f_id not in past_h2h or o_id not in past_h2h:
                continue
            if wk <= selected_wk:
                if row["team_score"] > row["opp_score"]:
                    past_h2h[f_id][o_id] += 1
                    if div_map.get(f_id) == div_map.get(o_id):
                        past_div_wins[f_id] += 1
            else:
                rem_h2h[f_id][o_id] += 1

        # Reconstruct exact wins/losses/PF if user selected a historical week < max_avail_wk
        if selected_wk < max_avail_wk:
            hist_wins = {t: 0 for t in team_ids}
            hist_losses = {t: 0 for t in team_ids}
            hist_pf = {t: 0.0 for t in team_ids}
            past_sched = reg_sched[reg_sched["week"] <= selected_wk]
            for wk, wk_group in past_sched.groupby("week"):
                wk_scores = wk_group.set_index("franchise_id")["team_score"].to_dict()
                sorted_teams = sorted(wk_scores.keys(), key=lambda tid: wk_scores[tid], reverse=True)
                top6 = set(sorted_teams[:6])
                for _, r in wk_group.iterrows():
                    tid = r["franchise_id"]
                    oid = r["opp_id"]
                    sc = float(r["team_score"])
                    osc = float(r["opp_score"])
                    hist_pf[tid] += sc
                    # H2H outcome
                    if sc > osc:
                        hist_wins[tid] += 1
                    elif sc < osc:
                        hist_losses[tid] += 1
                    # Median outcome
                    if tid in top6:
                        hist_wins[tid] += 1
                    else:
                        hist_losses[tid] += 1
            df["wins"] = df["franchise_id"].map(hist_wins)
            df["losses"] = df["franchise_id"].map(hist_losses)
            df["points_for"] = df["franchise_id"].map(hist_pf)
    else:
        w_rem = max(0, 14 - int(selected_wk))
        reg_sched = pd.DataFrame()

    # --- 2. Week-over-Week Deltas ---
    prev_candidates = [w for w in available_weeks if w < selected_wk]
    prev_wk = max(prev_candidates) if prev_candidates else None

    if prev_wk is not None:
        prev_df = model_df[model_df["after_week"] == prev_wk].set_index("franchise_id")
        df["playoff_delta"] = (df["make_playoffs"] - df["franchise_id"].map(prev_df["make_playoffs"]).fillna(df["make_playoffs"])) * 100.0
        df["div_delta"] = (df["win_division"] - df["franchise_id"].map(prev_df["win_division"]).fillna(df["win_division"])) * 100.0
        df["wc_delta"] = (df["wild_card"] - df["franchise_id"].map(prev_df["wild_card"]).fillna(df["wild_card"])) * 100.0
        df["bye_delta"] = (df["bye"] - df["franchise_id"].map(prev_df["bye"]).fillna(df["bye"])) * 100.0
        df["one_seed_delta"] = (df["one_seed"] - df["franchise_id"].map(prev_df["one_seed"]).fillna(df["one_seed"])) * 100.0
        df["first_pick_delta"] = (df["first_pick"] - df["franchise_id"].map(prev_df["first_pick"]).fillna(df["first_pick"])) * 100.0
        df["top_pts_delta"] = (df["top_pts"] - df["franchise_id"].map(prev_df["top_pts"]).fillna(df["top_pts"])) * 100.0
        df["proj_wins_delta"] = df["proj_wins"] - df["franchise_id"].map(prev_df["proj_wins"]).fillna(df["proj_wins"])
    else:
        df["playoff_delta"] = 0.0
        df["div_delta"] = 0.0
        df["wc_delta"] = 0.0
        df["bye_delta"] = 0.0
        df["one_seed_delta"] = 0.0
        df["first_pick_delta"] = 0.0
        df["top_pts_delta"] = 0.0
        df["proj_wins_delta"] = 0.0

    # --- 3. Remaining Strength of Schedule (Remaining SoS) ---
    wins_map = dict(zip(df["franchise_id"], df["wins"]))
    losses_map = dict(zip(df["franchise_id"], df["losses"]))
    pf_map = dict(zip(df["franchise_id"], df["points_for"]))
    proj_wins_map = dict(zip(df["franchise_id"], df["proj_wins"]))
    playoff_map = dict(zip(df["franchise_id"], df["make_playoffs"]))

    sos_proj_wins = {}
    sos_win_pct = {}
    sos_ppg = {}
    rem_opponents_detail = {}

    if not reg_sched.empty and w_rem > 0:
        future_sched = reg_sched[reg_sched["week"] > selected_wk].sort_values(by="week")
        for tid in team_ids:
            t_games = future_sched[future_sched["franchise_id"] == tid]
            opp_ids = t_games["opp_id"].tolist()
            if opp_ids:
                avg_pw = float(np.mean([proj_wins_map.get(oid, 14.0) for oid in opp_ids]))
                tot_w = sum(wins_map.get(oid, 0) for oid in opp_ids)
                tot_g = sum(wins_map.get(oid, 0) + losses_map.get(oid, 0) for oid in opp_ids)
                win_pct = float(tot_w / tot_g) if tot_g > 0 else 0.500
                avg_ppg = float(np.mean([pf_map.get(oid, 0.0) / max(1, selected_wk) for oid in opp_ids]))
                details = []
                for _, grow in t_games.iterrows():
                    oid = grow["opp_id"]
                    wk_num = int(grow["week"])
                    loc = "vs" if str(grow["is_home"]) == "1" else "@"
                    is_div_game = div_map.get(tid) == div_map.get(oid)
                    details.append({
                        "Week": f"Wk {wk_num}",
                        "Matchup": f"{loc} {name_map.get(oid, oid)}",
                        "Opp Record": f"{wins_map.get(oid, 0)}-{losses_map.get(oid, 0)}",
                        "Opp Proj Wins": round(proj_wins_map.get(oid, 0.0), 1),
                        "Opp Playoff %": f"{playoff_map.get(oid, 0.0)*100:.1f}%",
                        "Type": "Division" if is_div_game else "Non-Div"
                    })
                sos_proj_wins[tid] = avg_pw
                sos_win_pct[tid] = win_pct
                sos_ppg[tid] = avg_ppg
                rem_opponents_detail[tid] = details
            else:
                sos_proj_wins[tid] = 0.0
                sos_win_pct[tid] = 0.0
                sos_ppg[tid] = 0.0
                rem_opponents_detail[tid] = []
    else:
        for tid in team_ids:
            sos_proj_wins[tid] = 0.0
            sos_win_pct[tid] = 0.0
            sos_ppg[tid] = 0.0
            rem_opponents_detail[tid] = []

    df["rem_sos_proj_wins"] = df["franchise_id"].map(sos_proj_wins)
    df["rem_sos_win_pct"] = df["franchise_id"].map(sos_win_pct)
    df["rem_sos_ppg"] = df["franchise_id"].map(sos_ppg)
    # Rank 1 = Hardest remaining schedule (highest opponent projected wins), 12 = Easiest
    if w_rem > 0:
        df["rem_sos_rank"] = df["rem_sos_proj_wins"].rank(ascending=False, method="min").astype(int)
    else:
        df["rem_sos_rank"] = 0

    # --- 4. Mathematical Clinch & Elimination Tags ([Z], [Y], [X], [E]) ---
    # Each remaining week offers at most 2 wins per team (1 H2H + 1 Top-6 League Median).
    # For any subset U of chasing teams, internal H2H games force 1 loss per game, and at most min(|U|, 6) teams can win the median each week.
    def max_group_wins_possible(subset_ids):
        k = len(subset_ids)
        if k == 0 or w_rem == 0:
            return 0
        internal_games = 0
        sub_list = list(subset_ids)
        for idx_a in range(k):
            for idx_b in range(idx_a + 1, k):
                internal_games += rem_h2h[sub_list[idx_a]][sub_list[idx_b]]
        max_h2h = (k * w_rem) - internal_games
        max_med = min(k, 6) * w_rem
        return max_h2h + max_med

    def min_group_wins_guaranteed(subset_ids):
        k = len(subset_ids)
        if k == 0 or w_rem == 0:
            return 0
        internal_games = 0
        sub_list = list(subset_ids)
        for idx_a in range(k):
            for idx_b in range(idx_a + 1, k):
                internal_games += rem_h2h[sub_list[idx_a]][sub_list[idx_b]]
        # Every internal H2H game guarantees 1 win to someone in subset_ids; if k > 6, at least (k - 6) teams in subset_ids win median each week
        min_med = max(0, k - 6) * w_rem
        return internal_games + min_med

    def can_subset_all_reach(target_team, subset_ids):
        """Returns True if every team in subset_ids can simultaneously finish ahead of or tied with target_team's floor."""
        target_floor = wins_map[target_team]
        needs = {}
        for j in subset_ids:
            # If j cannot even reach target_floor individually
            max_j = wins_map[j] + 2 * w_rem
            if max_j < target_floor:
                return False
            # If j can only tie target_floor, check if target_team already clinched H2H over j (in a 1-on-1 comparison)
            if len(subset_ids) == 1 and max_j == target_floor:
                if past_h2h[target_team][j] > past_h2h[j][target_team] + rem_h2h[target_team][j]:
                    return False
            needs[j] = max(0, target_floor - wins_map[j])

        # Check Hall's capacity condition across all non-empty sub-cliques of subset_ids
        sub_list = list(subset_ids)
        for r_len in range(1, len(sub_list) + 1):
            for comb in combinations(sub_list, r_len):
                if sum(needs[x] for x in comb) > max_group_wins_possible(comb):
                    return False
        return True

    def compare_final_teams(a, b):
        """Exact league tiebreaker when w_rem == 0: Wins -> H2H -> Points For -> Division Wins."""
        if wins_map[a] != wins_map[b]:
            return 1 if wins_map[a] > wins_map[b] else -1
        if past_h2h[a][b] != past_h2h[b][a]:
            return 1 if past_h2h[a][b] > past_h2h[b][a] else -1
        if pf_map[a] != pf_map[b]:
            return 1 if pf_map[a] > pf_map[b] else -1
        if past_div_wins[a] != past_div_wins[b]:
            return 1 if past_div_wins[a] > past_div_wins[b] else -1
        return 0

    clinch_tags = {}
    clinch_labels = {}
    all_divs = sorted(df["division"].unique())
    div_teams_map = {d: [t for t in team_ids if div_map[t] == d] for d in all_divs}

    if w_rem == 0:
        # Season complete: use exact tiebreakers
        div_winners = []
        for d, d_teams in div_teams_map.items():
            d_sorted = sorted(d_teams, key=cmp_to_key(lambda x, y: compare_final_teams(y, x)))
            div_winners.append(d_sorted[0])
        div_winners_sorted = sorted(div_winners, key=cmp_to_key(lambda x, y: compare_final_teams(y, x)))
        bye_Ids = set(div_winners_sorted[:2])
        div_win_Ids = set(div_winners_sorted)
        non_div = [t for t in team_ids if t not in div_win_Ids]
        wc_sorted = sorted(non_div, key=cmp_to_key(lambda x, y: compare_final_teams(y, x)))
        wc_Ids = set(wc_sorted[:3])
        for tid in team_ids:
            if tid in bye_Ids:
                clinch_tags[tid] = "Z"
                clinch_labels[tid] = "Clinched First-Round Bye"
            elif tid in div_win_Ids:
                clinch_tags[tid] = "Y"
                clinch_labels[tid] = "Clinched Division Title"
            elif tid in wc_Ids:
                clinch_tags[tid] = "X"
                clinch_labels[tid] = "Clinched Playoff Berth"
            else:
                clinch_tags[tid] = "E"
                clinch_labels[tid] = "Eliminated from Playoffs"
    else:
        for tid in team_ids:
            my_div = div_map[tid]
            own_rivals = [t for t in div_teams_map[my_div] if t != tid]
            other_divs = [d for d in all_divs if d != my_div]

            # 1. Check Clinched Division [Y]: no division rival can catch tid
            clinched_div = not any(can_subset_all_reach(tid, [r]) for r in own_rivals)

            # 2. Check Clinched First-Round Bye [Z]: clinched own division AND no pair of winners from the other 2 divisions can both catch tid
            clinched_bye = False
            if clinched_div and len(other_divs) == 2:
                pair_can_catch = False
                for d1_t in div_teams_map[other_divs[0]]:
                    for d2_t in div_teams_map[other_divs[1]]:
                        if can_subset_all_reach(tid, [d1_t, d2_t]):
                            pair_can_catch = True
                            break
                    if pair_can_catch:
                        break
                clinched_bye = not pair_can_catch

            # 3. Check Clinched Playoffs [X]: either clinched division OR no valid (1 own-div winner + 3 wild cards) combination can simultaneously catch tid
            clinched_playoffs = clinched_div
            if not clinched_playoffs:
                can_miss_playoffs = False
                other_teams = [t for t in team_ids if t != tid]
                # To miss the playoffs, at least 1 own-division rival must beat tid AND at least 3 other non-division-winner teams must beat tid
                for own_w in own_rivals:
                    if not can_subset_all_reach(tid, [own_w]):
                        continue
                    wc_pool = [t for t in other_teams if t != own_w]
                    for wc_comb in combinations(wc_pool, 3):
                        if can_subset_all_reach(tid, [own_w, *wc_comb]):
                            can_miss_playoffs = True
                            break
                    if can_miss_playoffs:
                        break
                clinched_playoffs = not can_miss_playoffs

            # 4. Check Mathematical Elimination [E]
            max_tid_wins = wins_map[tid] + 2 * w_rem
            # Can tid win its division?
            can_win_div = True
            for r in own_rivals:
                if wins_map[r] > max_tid_wins:
                    can_win_div = False
                    break
                if wins_map[r] == max_tid_wins and past_h2h[r][tid] > past_h2h[tid][r] + rem_h2h[tid][r]:
                    can_win_div = False
                    break
            if can_win_div:
                # Also check if any pair/triplet of own-division rivals is guaranteed to produce someone > max_tid_wins via H2H games
                for r_len in range(2, len(own_rivals) + 1):
                    for comb in combinations(own_rivals, r_len):
                        # If all teams in comb stay <= max_tid_wins, their combined additional wins are at most sum(max_tid_wins - wins[x])
                        if all(max_tid_wins >= wins_map[x] for x in comb):
                            max_allowed = sum(max_tid_wins - wins_map[x] for x in comb)
                            if min_group_wins_guaranteed(comb) > max_allowed:
                                can_win_div = False
                                break

            # Can tid win a Wild Card spot? (Needs fewer than 3 non-division-leading teams guaranteed above max_tid_wins)
            can_win_wc = True
            # In each division, at least 1 team wins the division; remove 1 leader per division and count remaining teams already strictly above max_tid_wins
            non_leaders_above = 0
            for d, d_teams in div_teams_map.items():
                rivals_in_d = [t for t in d_teams if t != tid]
                above_in_d = [t for t in rivals_in_d if wins_map[t] > max_tid_wins or (wins_map[t] == max_tid_wins and past_h2h[t][tid] > past_h2h[tid][t] + rem_h2h[tid][t])]
                # At most 1 of them is the division winner; any additional ones are guaranteed Wild Card finishers ahead of tid
                if d == my_div:
                    non_leaders_above += max(0, len(above_in_d) - 1)
                else:
                    non_leaders_above += max(0, len(above_in_d) - 1)
            if non_leaders_above >= 3:
                can_win_wc = False

            if clinched_bye:
                clinch_tags[tid] = "Z"
                clinch_labels[tid] = "Clinched First-Round Bye"
            elif clinched_div:
                clinch_tags[tid] = "Y"
                clinch_labels[tid] = "Clinched Division Title"
            elif clinched_playoffs:
                clinch_tags[tid] = "X"
                clinch_labels[tid] = "Clinched Playoff Berth"
            elif not can_win_div and not can_win_wc:
                clinch_tags[tid] = "E"
                clinch_labels[tid] = "Eliminated from Playoffs"
            else:
                clinch_tags[tid] = ""
                clinch_labels[tid] = ""

    df["clinch_tag"] = df["franchise_id"].map(clinch_tags)
    df["clinch_label"] = df["franchise_id"].map(clinch_labels)
    df["franchise_display"] = df.apply(
        lambda r: f"{r['franchise_name']} [{r['clinch_tag']}]" if r["clinch_tag"] else r["franchise_name"],
        axis=1
    )

    return df, prev_wk, w_rem, rem_opponents_detail


def format_clinch_badge_html(tag, label=""):
    """Returns styled HTML badge for a clinch/elimination tag ([Z], [Y], [X], [E])."""
    if not tag:
        return ""
    cls_map = {"Z": "clinch-z", "Y": "clinch-y", "X": "clinch-x", "E": "clinch-e"}
    cls = cls_map.get(tag, "clinch-x")
    title_attr = f' title="{label}"' if label else ""
    return f'<span class="clinch-tag {cls}"{title_attr}>[{tag}]</span>'


def format_delta_pill_html(val, suffix="%", decimals=1):
    """Returns compact HTML pill for Week-over-Week probability or win changes."""
    if abs(val) < 0.05:
        return '<span class="delta-pill-flat">0.0% WoW</span>'
    elif val > 0:
        return f'<span class="delta-pill-pos">+{val:.{decimals}f}{suffix} ▲</span>'
    else:
        return f'<span class="delta-pill-neg">{val:.{decimals}f}{suffix} ▼</span>'


model_df = fetch_projected_standings_data()
sched_df = fetch_schedule_and_results_data()

if model_df.empty:
    st.info("Simulation model data for 2026 is currently updating. Please check back shortly!")
    st.stop()

available_weeks = sorted(model_df["after_week"].unique(), reverse=True)

# --- Header Controls & Calibration Selector ---
ctrl_col1, ctrl_col2 = st.columns([0.7, 0.3])
with ctrl_col1:
    st.markdown("""
    <div style="font-size: 0.95rem; opacity: 0.85; margin-top: 4px;">
        Projections generated by simulating the remaining schedule <strong>10,000 times</strong> using historical team scoring variance, player projection distributions, and head-to-head tiebreakers.
    </div>
    """, unsafe_allow_html=True)
with ctrl_col2:
    selected_wk = st.selectbox(
        "Simulation Calibration Week:",
        options=available_weeks,
        format_func=lambda w: f"Through Week {w}",
        key="proj_sim_week_select"
    )

raw_sim_data = model_df[model_df["after_week"] == selected_wk].copy()
raw_sim_data = raw_sim_data.sort_values(by="proj_wins", ascending=False).reset_index(drop=True)

sim_data, prev_wk, w_rem, rem_opponents_detail = enrich_standings_data(
    raw_sim_data, model_df, sched_df, selected_wk, available_weeks
)
sim_data = sim_data.sort_values(by="proj_wins", ascending=False).reset_index(drop=True)
sim_data["overall_proj_rank"] = sim_data.index + 1

# Top KPIs
top_team = sim_data.iloc[0]
one_seed_fav = sim_data.sort_values(by="one_seed", ascending=False).iloc[0]
first_pick_fav = sim_data.sort_values(by="first_pick", ascending=False).iloc[0]
bubble_cutoff = sim_data.iloc[5]["proj_wins"] # 6th seed

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-lbl">Projected #1 Seed</div>
        <div class="metric-val" style="color: #4CAF50; font-size: 1.8rem;">{one_seed_fav['one_seed']*100:.1f}%</div>
        <div class="metric-sub">{one_seed_fav['franchise_display']} ({one_seed_fav['proj_wins']:.1f} Proj W)</div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-lbl">Most Projected Wins</div>
        <div class="metric-val" style="color: #2196F3; font-size: 1.8rem;">{top_team['proj_wins']:.1f}W</div>
        <div class="metric-sub">{top_team['franchise_display']} ({top_team['wins']}-{top_team['losses']} Current)</div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-lbl">Playoff Cutoff Line (#6)</div>
        <div class="metric-val" style="color: #FFC107; font-size: 1.8rem;">~{bubble_cutoff:.1f}W</div>
        <div class="metric-sub">Est. wins required to make postseason</div>
    </div>
    """, unsafe_allow_html=True)

with k4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-lbl">#1 Draft Pick Odds</div>
        <div class="metric-val" style="color: #e91e63; font-size: 1.8rem;">{first_pick_fav['first_pick']*100:.1f}%</div>
        <div class="metric-sub">{first_pick_fav['franchise_display']} (Favored for Pick 1.01)</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# --- Week-over-Week Movers & Remaining SoS Spotlight Ribbon ---
riser_row = sim_data.sort_values(by=["playoff_delta", "proj_wins_delta"], ascending=[False, False]).iloc[0]
tumbler_row = sim_data.sort_values(by=["playoff_delta", "proj_wins_delta"], ascending=[True, True]).iloc[0]

if w_rem > 0 and sim_data["rem_sos_proj_wins"].max() > 0:
    easiest_sos_row = sim_data.sort_values(by="rem_sos_proj_wins", ascending=True).iloc[0]
    hardest_sos_row = sim_data.sort_values(by="rem_sos_proj_wins", ascending=False).iloc[0]
else:
    easiest_sos_row = None
    hardest_sos_row = None

mv1, mv2, mv3 = st.columns(3, gap="medium")

with mv1:
    if prev_wk is not None and (abs(riser_row["playoff_delta"]) >= 0.05 or abs(riser_row["proj_wins_delta"]) >= 0.05):
        r_icon = f'<img src="{riser_row["icon"]}" width="38" style="border-radius: 50%; margin-right: 12px;">' if riser_row["icon"] else "📈 "
        r_val = f"{riser_row['playoff_delta']:+.1f}%" if abs(riser_row["playoff_delta"]) >= 0.1 else f"{riser_row['proj_wins_delta']:+.1f}W"
        r_sub = f"Now {riser_row['make_playoffs']*100:.1f}% Playoffs ({riser_row['proj_wins_delta']:+.1f} Proj W vs Wk {prev_wk})"
    else:
        r_icon = "📈 "
        r_val = "Baseline"
        r_sub = f"Week {selected_wk} serves as initial baseline"
    st.markdown(f"""
    <div class="mover-card" style="border-left: 4px solid #4CAF50;">
        <div style="display: flex; align-items: center;">
            {r_icon}
            <div>
                <div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.6px; opacity: 0.75; font-weight: 700;">📈 Biggest Playoff Riser</div>
                <div style="font-size: 1.0rem; font-weight: 800; margin-top: 2px;">{riser_row['franchise_name'] if prev_wk is not None else 'No Prior Week'}</div>
                <div style="font-size: 0.78rem; opacity: 0.75;">{r_sub}</div>
            </div>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 1.35rem; font-weight: 800; color: #66bb6a;">{r_val}</div>
            <div style="font-size: 0.72rem; opacity: 0.65;">WoW Playoff Δ</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with mv2:
    if prev_wk is not None and (abs(tumbler_row["playoff_delta"]) >= 0.05 or abs(tumbler_row["proj_wins_delta"]) >= 0.05):
        t_icon = f'<img src="{tumbler_row["icon"]}" width="38" style="border-radius: 50%; margin-right: 12px;">' if tumbler_row["icon"] else "📉 "
        t_val = f"{tumbler_row['playoff_delta']:+.1f}%" if abs(tumbler_row["playoff_delta"]) >= 0.1 else f"{tumbler_row['proj_wins_delta']:+.1f}W"
        t_sub = f"Now {tumbler_row['make_playoffs']*100:.1f}% Playoffs ({tumbler_row['proj_wins_delta']:+.1f} Proj W vs Wk {prev_wk})"
    else:
        t_icon = "📉 "
        t_val = "Baseline"
        t_sub = f"Week {selected_wk} serves as initial baseline"
    st.markdown(f"""
    <div class="mover-card" style="border-left: 4px solid #ef5350;">
        <div style="display: flex; align-items: center;">
            {t_icon}
            <div>
                <div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.6px; opacity: 0.75; font-weight: 700;">📉 Biggest Playoff Tumbler</div>
                <div style="font-size: 1.0rem; font-weight: 800; margin-top: 2px;">{tumbler_row['franchise_name'] if prev_wk is not None else 'No Prior Week'}</div>
                <div style="font-size: 0.78rem; opacity: 0.75;">{t_sub}</div>
            </div>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 1.35rem; font-weight: 800; color: #ef5350;">{t_val}</div>
            <div style="font-size: 0.72rem; opacity: 0.65;">WoW Playoff Δ</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with mv3:
    if easiest_sos_row is not None and hardest_sos_row is not None:
        s_icon = f'<img src="{easiest_sos_row["icon"]}" width="38" style="border-radius: 50%; margin-right: 12px;">' if easiest_sos_row["icon"] else "🗓️ "
        s_name = easiest_sos_row["franchise_name"]
        s_val = f"{easiest_sos_row['rem_sos_proj_wins']:.1f}W"
        s_sub = f"Toughest: {hardest_sos_row['franchise_name']} ({hardest_sos_row['rem_sos_proj_wins']:.1f}W opp avg)"
    else:
        s_icon = "🗓️ "
        s_name = "Regular Season Complete"
        s_val = "0 Wks"
        s_sub = "All 14 regular season weeks completed"
    st.markdown(f"""
    <div class="mover-card" style="border-left: 4px solid #42A5F5;">
        <div style="display: flex; align-items: center;">
            {s_icon}
            <div>
                <div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.6px; opacity: 0.75; font-weight: 700;">🗓️ Easiest Remaining SoS ({w_rem} Wks)</div>
                <div style="font-size: 1.0rem; font-weight: 800; margin-top: 2px;">{s_name}</div>
                <div style="font-size: 0.78rem; opacity: 0.75;">{s_sub}</div>
            </div>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 1.35rem; font-weight: 800; color: #64b5f6;">{s_val}</div>
            <div style="font-size: 0.72rem; opacity: 0.65;">Opp Proj Wins</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.write("")
st.write("")

# --- Section 1: Projected Divisional Standings ---
st.subheader("🛡️ Projected Divisional Standings", divider="rainbow")
st.caption("Division winners automatically secure playoff seeds #1 through #3, with the top 2 earning first-round byes.")

div_cols = st.columns(3, gap="large")
divisions = ["Left Upright", "Crossbar", "Right Upright"]

# Store places for deep dive lookup
places_df = []

for idx, div_name in enumerate(divisions):
    div_df = sim_data[sim_data["division"] == div_name].sort_values(by="proj_wins", ascending=False).reset_index(drop=True)
    div_df["div_rank"] = div_df.index + 1
    
    for _, r in div_df.iterrows():
        places_df.append({
            "franchise_name": r["franchise_name"],
            "division": r["division"],
            "div_rank": r["div_rank"]
        })
        
    with div_cols[idx]:
        st.markdown(f"""
        <div class="week-card" style="padding: 16px;">
            <div style="margin-bottom: 12px;">
                <h4 style="margin: 0;">{div_name} Division</h4>
            </div>
        """, unsafe_allow_html=True)

        for _, team_row in div_df.iterrows():
            icon_tag = f'<img src="{team_row["icon"]}" width="32" style="vertical-align: middle; border-radius: 50%; margin-right: 10px;">' if team_row["icon"] else '🏈 '
            rk = team_row["div_rank"]
            rk_ordinal = "1st" if rk == 1 else ("2nd" if rk == 2 else ("3rd" if rk == 3 else "4th"))
            rk_badge = "badge-gold" if rk == 1 else ("badge-silver" if rk == 2 else "badge-bronze")
            clinch_html = format_clinch_badge_html(team_row["clinch_tag"], team_row["clinch_label"])
            delta_html = format_delta_pill_html(team_row["playoff_delta"]) if prev_wk is not None else ""
            sos_str = f" &bull; SoS #{int(team_row['rem_sos_rank'])}" if w_rem > 0 and team_row["rem_sos_rank"] > 0 else ""
            
            st.markdown(f"""
            <div class="prob-card" style="margin-bottom: 10px; padding: 12px 14px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="display: flex; align-items: center;">
                        <span class="badge {rk_badge}" style="margin-right: 8px;">{rk_ordinal}</span>
                        {icon_tag}
                        <div>
                            <div><strong style="font-size: 0.95rem;">{team_row['franchise_name']}</strong>{clinch_html}</div>
                            <div style="font-size: 0.78rem; opacity: 0.72;">{team_row['wins']}-{team_row['losses']} &bull; {team_row['points_for']:.1f} PF{sos_str}</div>
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 1.15rem; font-weight: 800; color: #ba68c8;">{team_row['proj_wins']:.1f}W</div>
                        <div style="font-size: 0.75rem; opacity: 0.8;">Playoffs: <strong>{team_row['make_playoffs']*100:.1f}%</strong> {delta_html}</div>
                        <div style="font-size: 0.72rem; opacity: 0.68;">Div Champ: <strong>{team_row['win_division']*100:.1f}%</strong></div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

# Clinch & Elimination Legend Bar
st.markdown("""
<div style="display: flex; flex-wrap: wrap; gap: 16px; align-items: center; font-size: 0.8rem; opacity: 0.85; padding: 6px 12px; background: rgba(128,128,128,0.04); border-radius: 10px; border: 1px solid rgba(128,128,128,0.14);">
    <strong style="opacity: 0.9;">Official Clinch &amp; Elimination Key (Mathematical Guarantees):</strong>
    <span><span class="clinch-tag clinch-z" style="margin-left: 0; margin-right: 4px;">[Z]</span> Clinched First-Round Bye (Top 2 Seed)</span>
    <span><span class="clinch-tag clinch-y" style="margin-left: 0; margin-right: 4px;">[Y]</span> Clinched Division Title</span>
    <span><span class="clinch-tag clinch-x" style="margin-left: 0; margin-right: 4px;">[X]</span> Clinched Playoff Berth (Top 6 Seed)</span>
    <span><span class="clinch-tag clinch-e" style="margin-left: 0; margin-right: 4px;">[E]</span> Eliminated from Playoffs</span>
    <span style="opacity: 0.7;">&bull; <em>SoS #1 = Toughest Remaining Schedule, #12 = Easiest</em></span>
</div>
""", unsafe_allow_html=True)

places_lookup = pd.DataFrame(places_df)

st.write("")
st.write("")

# --- Section 2: Complete League Standings & Playoff Probability Grid ---
st.subheader("📊 League-Wide Projections & Postseason Probabilities", divider="blue")

col_grid, col_chart = st.columns([1.15, 0.85], gap="large")

with col_grid:
    st.markdown("#### Projected Regular Season Table")
    
    tbl_df = sim_data[[
        "franchise_display", "division", "wins", "losses", "points_for", "proj_wins",
        "make_playoffs", "playoff_delta", "win_division", "wild_card", "bye", "one_seed",
        "first_pick", "rem_sos_proj_wins", "rem_sos_rank"
    ]].copy()
    
    tbl_df["Record"] = tbl_df["wins"].astype(str) + "-" + tbl_df["losses"].astype(str)
    tbl_df["make_playoffs"] = tbl_df["make_playoffs"] * 100
    tbl_df["win_division"] = tbl_df["win_division"] * 100
    tbl_df["wild_card"] = tbl_df["wild_card"] * 100
    tbl_df["bye"] = tbl_df["bye"] * 100
    tbl_df["one_seed"] = tbl_df["one_seed"] * 100
    tbl_df["first_pick"] = tbl_df["first_pick"] * 100
    tbl_df["Rem SoS"] = tbl_df.apply(
        lambda r: f"{r['rem_sos_proj_wins']:.1f}W (#{int(r['rem_sos_rank'])})" if w_rem > 0 and r["rem_sos_rank"] > 0 else "Done",
        axis=1
    )

    tbl_df = tbl_df[[
        "franchise_display", "division", "Record", "points_for", "proj_wins",
        "make_playoffs", "playoff_delta", "win_division", "wild_card", "bye", "one_seed", "first_pick", "Rem SoS"
    ]]
    tbl_df.columns = [
        "Franchise", "Division", "Record", "Current PF", "Proj Wins",
        "Playoff %", "WoW Δ %", "Div Champ %", "Wild Card %", "Bye %", "#1 Seed %", "#1 Pick %", "Rem SoS"
    ]

    st.dataframe(
        tbl_df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Franchise": st.column_config.TextColumn("Franchise", help="Includes [Z], [Y], [X], [E] mathematical clinch/elimination tags"),
            "Division": "Division",
            "Record": "Record",
            "Current PF": st.column_config.NumberColumn("Points For", format="%.1f"),
            "Proj Wins": st.column_config.NumberColumn("Proj Wins", format="%.1f"),
            "Playoff %": st.column_config.ProgressColumn("Playoffs %", format="%.1f%%", min_value=0, max_value=100),
            "WoW Δ %": st.column_config.NumberColumn("WoW Δ %", help="Week-over-Week Playoff Probability Change", format="%+.1f%%"),
            "Div Champ %": st.column_config.ProgressColumn("Div %", format="%.1f%%", min_value=0, max_value=100),
            "Wild Card %": st.column_config.ProgressColumn("WC %", format="%.1f%%", min_value=0, max_value=100),
            "Bye %": st.column_config.ProgressColumn("Bye %", format="%.1f%%", min_value=0, max_value=100),
            "#1 Seed %": st.column_config.ProgressColumn("Top Seed %", format="%.1f%%", min_value=0, max_value=100),
            "#1 Pick %": st.column_config.ProgressColumn("#1 Pick %", format="%.1f%%", min_value=0, max_value=100),
            "Rem SoS": st.column_config.TextColumn("Rem SoS", help="Average Projected Wins of Remaining Opponents (#1 = Hardest, #12 = Easiest)"),
        }
    )

with col_chart:
    chart_tab1, chart_tab2, chart_tab3 = st.tabs([
        "📊 Projected Wins",
        "📈 WoW Playoff Movers",
        "🗓️ Remaining SoS"
    ])

    with chart_tab1:
        chart_df = sim_data.sort_values(by="proj_wins", ascending=True).copy()
        fig_wins = px.bar(
            chart_df,
            x="proj_wins",
            y="franchise_display",
            color="division",
            orientation="h",
            labels={"proj_wins": "Projected Wins", "franchise_display": "Franchise", "division": "Division"},
            color_discrete_map={
                "Left Upright": "#42A5F5",
                "Crossbar": "#FFB74D",
                "Right Upright": "#66BB6A"
            },
            text="proj_wins"
        )
        fig_wins.update_traces(texttemplate="%{x:.1f}W", textposition="outside", cliponaxis=False)
        fig_wins.update_layout(
            margin=dict(l=0, r=45, t=10, b=10),
            height=400,
            xaxis=dict(title="Projected Regular Season Wins (28-Game Slate)", range=[0, 28]),
            yaxis=dict(title=""),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_wins, use_container_width=True)

    with chart_tab2:
        if prev_wk is not None:
            delta_chart_df = sim_data.sort_values(by="playoff_delta", ascending=True).copy()
            delta_colors = ["#66BB6A" if v >= 0 else "#EF5350" for v in delta_chart_df["playoff_delta"]]
            fig_delta = go.Figure(go.Bar(
                x=delta_chart_df["playoff_delta"],
                y=delta_chart_df["franchise_display"],
                orientation="h",
                marker_color=delta_colors,
                text=[f"{v:+.1f}%" for v in delta_chart_df["playoff_delta"]],
                textposition="outside",
                cliponaxis=False,
                hovertemplate="<b>%{y}</b><br>Playoff Odds Shift: <b>%{x:+.1f}%</b><extra></extra>"
            ))
            max_abs_d = max(10.0, float(delta_chart_df["playoff_delta"].abs().max()) * 1.28)
            fig_delta.update_layout(
                margin=dict(l=0, r=45, t=25, b=10),
                height=400,
                title=f"Playoff Odds Shift (Week {prev_wk} ➔ Week {selected_wk})",
                xaxis=dict(title="Week-over-Week Playoff Odds Δ (%)", range=[-max_abs_d, max_abs_d], zeroline=True, zerolinewidth=2, zerolinecolor="rgba(128,128,128,0.4)"),
                yaxis=dict(title="")
            )
            st.plotly_chart(fig_delta, use_container_width=True)
        else:
            st.info(f"Week {selected_wk} is the earliest simulation snapshot in 2026. Select a later week to view Week-over-Week movers.")

    with chart_tab3:
        if w_rem > 0 and sim_data["rem_sos_proj_wins"].max() > 0:
            sos_chart_df = sim_data.sort_values(by="rem_sos_proj_wins", ascending=True).copy()
            fig_sos = px.bar(
                sos_chart_df,
                x="rem_sos_proj_wins",
                y="franchise_display",
                color="rem_sos_proj_wins",
                orientation="h",
                color_continuous_scale="RdYlGn_r",
                labels={"rem_sos_proj_wins": "Avg Opp Proj Wins", "franchise_display": "Franchise"},
                text=[f"{pw:.1f}W ({wp*100:.0f}%)" for pw, wp in zip(sos_chart_df["rem_sos_proj_wins"], sos_chart_df["rem_sos_win_pct"])]
            )
            fig_sos.update_traces(textposition="outside", cliponaxis=False)
            fig_sos.update_layout(
                margin=dict(l=0, r=65, t=25, b=10),
                height=400,
                coloraxis_showscale=False,
                title=f"Remaining Opponent Avg Projected Wins ({w_rem} Wks Left)",
                xaxis=dict(title="Remaining Opponents Avg Proj Wins (Curr Win %)", range=[0, max(22.0, float(sos_chart_df["rem_sos_proj_wins"].max()) * 1.25)]),
                yaxis=dict(title="")
            )
            st.plotly_chart(fig_sos, use_container_width=True)
        else:
            st.info("Regular season schedule is complete — no remaining regular season opponents.")

st.write("")
st.divider()

# --- Section 3: Interactive Team Profile Deep-Dive ---
st.subheader("🔍 Franchise Simulation Profile", divider="violet")

team_options = sorted(sim_data["franchise_name"].unique())
selected_team = st.selectbox(
    "Select a franchise to view in-depth simulation breakdown:",
    options=team_options,
    index=0
)

if selected_team:
    team_data = sim_data[sim_data["franchise_name"] == selected_team].iloc[0]
    team_id = team_data["franchise_id"]
    
    # Retrieve projected division rank
    team_rank_row = places_lookup[places_lookup["franchise_name"] == selected_team]
    if not team_rank_row.empty:
        p_rank = team_rank_row.iloc[0]["div_rank"]
        p_rank_ord = "1st" if p_rank == 1 else ("2nd" if p_rank == 2 else ("3rd" if p_rank == 3 else "4th"))
    else:
        p_rank_ord = "-"

    clinch_badge_profile = format_clinch_badge_html(team_data["clinch_tag"], team_data["clinch_label"])
    clinch_sub_html = f'<div style="margin-top: 6px; font-size: 0.8rem; font-weight: 700; opacity: 0.9;">{clinch_badge_profile} {team_data["clinch_label"]}</div>' if team_data["clinch_tag"] else ""

    if w_rem > 0 and team_data["rem_sos_rank"] > 0:
        sos_rank_int = int(team_data["rem_sos_rank"])
        sos_diff_lbl = "Toughest" if sos_rank_int <= 4 else ("Easiest" if sos_rank_int >= 9 else "Middle")
        sos_profile_html = (
            '<hr style="margin: 12px 0; border: none; border-top: 1px solid rgba(128,128,128,0.2);" />'
            f'<div style="font-size: 0.82rem; opacity: 0.8;">Remaining SoS ({w_rem} Wks):</div>'
            f'<div style="font-size: 1.05rem; font-weight: 800; color: #64b5f6; margin-top: 2px;">#{sos_rank_int} in League ({sos_diff_lbl})</div>'
            f'<div style="font-size: 0.8rem; opacity: 0.75;">Opp Avg: <strong>{team_data["rem_sos_proj_wins"]:.1f} Proj W</strong> ({team_data["rem_sos_win_pct"]*100:.1f}% Win)</div>'
        )
    else:
        sos_profile_html = ""

    t_col1, t_col2 = st.columns([0.3, 0.7], gap="large")
    
    with t_col1:
        icon_html = f'<img src="{team_data["icon"]}" width="85" style="margin-bottom: 8px;">' if team_data["icon"] else '🏈'
        st.markdown(f"""
<div class="podium-card" style="text-align: center; padding: 22px;">
<div>{icon_html}</div>
<h3 style="margin: 6px 0 2px 0;">{team_data['franchise_name']}</h3>
<div style="font-size: 0.9rem; opacity: 0.75;">{team_data['division']} Division</div>{clinch_sub_html}
<div style="font-size: 0.88rem; margin-top: 8px;">Current Record: <strong>{team_data['wins']}-{team_data['losses']}</strong> ({team_data['points_for']:.2f} PF)</div>
<hr style="margin: 12px 0; border: none; border-top: 1px solid rgba(128,128,128,0.2);" />
<div style="font-size: 0.85rem; opacity: 0.8;">Projected Division Finish:</div>
<div class="metric-val" style="font-size: 2.2rem; margin: 4px 0;">{p_rank_ord} Place</div>
<div style="font-size: 0.85rem; opacity: 0.75;">Projected: <strong>{team_data['proj_wins']:.1f} Wins</strong></div>{sos_profile_html}
</div>
""", unsafe_allow_html=True)

    with t_col2:
        st.markdown("#### Monte Carlo Probability Matrix")
        
        r1_1, r1_2, r1_3, r1_4 = st.columns(4)
        with r1_1:
            st.metric(
                "Make Playoffs",
                f"{team_data['make_playoffs']*100:.1f}%",
                delta=f"{team_data['playoff_delta']:+.1f}% WoW" if prev_wk is not None else None
            )
        with r1_2:
            st.metric(
                "Win Division",
                f"{team_data['win_division']*100:.1f}%",
                delta=f"{team_data['div_delta']:+.1f}% WoW" if prev_wk is not None else None
            )
        with r1_3:
            st.metric(
                "Wild Card Seed",
                f"{team_data['wild_card']*100:.1f}%",
                delta=f"{team_data['wc_delta']:+.1f}% WoW" if prev_wk is not None else None
            )
        with r1_4:
            st.metric(
                "Points Title",
                f"{team_data['top_pts']*100:.1f}%",
                delta=f"{team_data['top_pts_delta']:+.1f}% WoW" if prev_wk is not None else None
            )

        st.write("")
        r2_1, r2_2, r2_3, r2_4 = st.columns(4)
        with r2_1:
            st.metric(
                "#1 Overall Seed",
                f"{team_data['one_seed']*100:.1f}%",
                delta=f"{team_data['one_seed_delta']:+.1f}% WoW" if prev_wk is not None else None
            )
        with r2_2:
            st.metric(
                "First-Round Bye",
                f"{team_data['bye']*100:.1f}%",
                delta=f"{team_data['bye_delta']:+.1f}% WoW" if prev_wk is not None else None
            )
        with r2_3:
            st.metric(
                "Projected Wins",
                f"{team_data['proj_wins']:.1f}",
                delta=f"{team_data['proj_wins_delta']:+.1f}W WoW" if prev_wk is not None else None
            )
        with r2_4:
            st.metric(
                "#1 Overall Pick",
                f"{team_data['first_pick']*100:.1f}%",
                delta=f"{team_data['first_pick_delta']:+.1f}% WoW" if prev_wk is not None else None
            )

        st.write("")
        # Contextual summary banner with Clinch & Remaining SoS context
        playoff_pct = team_data['make_playoffs'] * 100
        overall_rk = int(team_data["overall_proj_rank"])
        overall_ord = f"{overall_rk}{'st' if overall_rk == 1 else ('nd' if overall_rk == 2 else ('rd' if overall_rk == 3 else 'th'))}"

        if w_rem > 0 and team_data["rem_sos_rank"] > 0:
            s_rk = int(team_data["rem_sos_rank"])
            if s_rk == 12:
                sos_clause = f" and has the <strong>easiest remaining schedule</strong> in the league (opponents average {team_data['rem_sos_proj_wins']:.1f} projected wins)"
            elif s_rk == 1:
                sos_clause = f" and faces the <strong>toughest remaining schedule</strong> in the league (opponents average {team_data['rem_sos_proj_wins']:.1f} projected wins)"
            elif s_rk >= 9:
                sos_clause = f" with a favorable <strong>#{s_rk} remaining schedule</strong> (opponents average {team_data['rem_sos_proj_wins']:.1f} projected wins)"
            elif s_rk <= 4:
                sos_clause = f" against a challenging <strong>#{s_rk} remaining schedule</strong> (opponents average {team_data['rem_sos_proj_wins']:.1f} projected wins)"
            else:
                sos_clause = f" with a balanced <strong>#{s_rk} remaining schedule</strong> (opponents average {team_data['rem_sos_proj_wins']:.1f} projected wins)"
        else:
            sos_clause = ""

        if team_data["clinch_tag"] in ("Z", "Y", "X"):
            status_text = f"🏆 <strong>[{team_data['clinch_tag']}] {team_data['clinch_label']}:</strong> {team_data['franchise_name']} has mathematically locked in a postseason spot ({playoff_pct:.1f}%){sos_clause}. Primary focus is securing a first-round bye ({team_data['bye']*100:.1f}%) and the #1 seed ({team_data['one_seed']*100:.1f}%)."
            status_color = "rgba(76, 175, 80, 0.15)"
            status_border = "#4CAF50"
        elif team_data["clinch_tag"] == "E":
            status_text = f"❌ <strong>[E] Mathematically Eliminated:</strong> {team_data['franchise_name']} is mathematically eliminated from the postseason{sos_clause} and holds a {team_data['first_pick']*100:.1f}% chance at the #1 overall rookie draft pick."
            status_color = "rgba(233, 30, 99, 0.15)"
            status_border = "#e91e63"
        elif playoff_pct >= 90:
            status_text = f"🔥 <strong>Playoff Lock / Heavy Contender:</strong> {team_data['franchise_name']} ranks {overall_ord} in projected wins ({playoff_pct:.1f}% playoff odds){sos_clause}. Primary battle is for a first-round bye ({team_data['bye']*100:.1f}%) and the #1 seed."
            status_color = "rgba(76, 175, 80, 0.15)"
            status_border = "#4CAF50"
        elif playoff_pct >= 40:
            status_text = f"⚔️ <strong>Playoff Bubble Battle:</strong> {team_data['franchise_name']} is currently {overall_ord} in projected wins ({playoff_pct:.1f}% playoff odds){sos_clause}, contending for a Wild Card berth ({team_data['wild_card']*100:.1f}%) or division crown ({team_data['win_division']*100:.1f}%)."
            status_color = "rgba(255, 193, 7, 0.15)"
            status_border = "#FFC107"
        else:
            status_text = f"🎯 <strong>Uphill Climb / Draft Focus:</strong> {team_data['franchise_name']} sits {overall_ord} in projected wins ({playoff_pct:.1f}% playoff odds){sos_clause} and holds a {team_data['first_pick']*100:.1f}% chance at the #1 overall pick in the next rookie draft."
            status_color = "rgba(233, 30, 99, 0.15)"
            status_border = "#e91e63"

        st.markdown(f"""
        <div style="background: {status_color}; border-left: 4px solid {status_border}; padding: 12px 16px; border-radius: 8px; margin-top: 14px; font-size: 0.9rem;">
            {status_text}
        </div>
        """, unsafe_allow_html=True)

        # Remaining Opponents Slate for Selected Team
        rem_slate = rem_opponents_detail.get(team_id, [])
        if rem_slate:
            st.write("")
            st.markdown(f"##### 🗓️ {team_data['franchise_name']} — Remaining Regular Season Slate ({len(rem_slate)} Weeks)")
            st.dataframe(
                pd.DataFrame(rem_slate),
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Week": "Week",
                    "Matchup": "Opponent",
                    "Opp Record": "Opp Record",
                    "Opp Proj Wins": st.column_config.NumberColumn("Opp Proj Wins", format="%.1fW"),
                    "Opp Playoff %": "Opp Playoff %",
                    "Type": "Matchup Type",
                }
            )
