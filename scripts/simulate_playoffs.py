"""
Monte Carlo Regular Season & Full Postseason Odds Simulation for Wide Right Fantasy Football.
Simulates remaining regular-season matchups (Weeks 1-14) AND the 6-team reseeded
Championship + Consolation Playoff Brackets (Weeks 15-17) based on Empirical Bayes
historical scoring distributions blended with MFL optimal roster projected scores
(capturing bye weeks, injuries, and talent changes) using a right-skewed Gamma distribution.
Incorporates Head-to-Head and League Median scoring (2 matchups per week) and exact
league tiebreakers.

Writes output directly to BigQuery native tables:
  - `mfl-374514.external.reg_season_sims` (Weeks 1-14 regular season odds)
  - `mfl-374514.external.postseason_sims` (Weeks 1-17 Championship/Podium & Extra Pick odds)
  - `mfl-374514.external.postseason_matchups` (Weeks 14-17 live bracket matchups & win %)
"""

import argparse
import datetime
import os
import time
import numpy as np
import pandas as pd
from google.api_core.exceptions import NotFound
from google.cloud import bigquery
from google.oauth2 import service_account
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import dlt

from dlt_scripts.common import fetch_mfl_data
import standings_utils


def get_bq_client():
    """Resolves BigQuery client for local dev, GitHub Actions, or cloud server."""
    # 1. Standard Google Application Credentials (set by GitHub Actions google-github-actions/auth)
    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        return bigquery.Client(project="mfl-374514")

    # 2. DLT secrets from .dlt/secrets.toml (local dev)
    try:
        gcp_creds = dlt.secrets.get("gcp_service_account")
        if gcp_creds:
            scopes = ["https://www.googleapis.com/auth/bigquery"]
            creds = service_account.Credentials.from_service_account_info(gcp_creds, scopes=scopes)
            return bigquery.Client(credentials=creds, project=gcp_creds.get("project_id", "mfl-374514"))
    except Exception:
        pass

    # 3. Environment variables from GitHub Action runner
    private_key = os.getenv("DESTINATION__BIGQUERY__CREDENTIALS__PRIVATE_KEY")
    client_email = os.getenv("DESTINATION__BIGQUERY__CREDENTIALS__CLIENT_EMAIL")
    project_id = os.getenv("DESTINATION__BIGQUERY__CREDENTIALS__PROJECT_ID", "mfl-374514")
    if private_key and client_email:
        creds_info = {
            "type": "service_account",
            "project_id": project_id,
            "private_key": private_key,
            "client_email": client_email,
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        creds = service_account.Credentials.from_service_account_info(creds_info)
        return bigquery.Client(credentials=creds, project=project_id)

    # 4. Default application credentials fallback
    return bigquery.Client(project="mfl-374514")


def bq_query(client, sql):
    """Executes a query and returns a list of dictionaries."""
    query_job = client.query(sql)
    return [dict(row) for row in query_job]


def get_projected_team_scores(client, future_weeks, franchises):
    """
    Fetches MFL player projected scores for each future week and calculates
    each franchise's optimal starting lineup projected score (1 QB, 2 RB, 2 WR, 1 TE, 1 PK, 1 Def, 2 Flex).
    Returns dict: {week: {franchise_id: projected_score}}
    """
    api_key = os.getenv("MFL_API_KEY") or dlt.secrets.get("mfl_api_key", "")
    if not api_key or not future_weeks:
        print("MFL API key not found or no future weeks; skipping live roster projections.")
        return {}

    try:
        rosters = bq_query(
            client,
            "SELECT franchise_id, player_id FROM `mfl-374514.dbt_production.dim_rosters` WHERE status = 'ROSTER'"
        )
        roster_df = pd.DataFrame(rosters)

        players = bq_query(
            client,
            "SELECT player_id, position FROM `mfl-374514.dbt_production.dim_players`"
        )
        players_map = {p["player_id"]: p["position"] for p in players}
        roster_df["pos"] = roster_df["player_id"].map(players_map)

        weekly_projections = {}

        for w in future_weeks:
            try:
                data = fetch_mfl_data("projectedScores", api_key, extra_params=f"&W={w}")
                p_projs = {}
                for p in data.get("projectedScores", {}).get("playerScore", []):
                    val = p.get("score", "")
                    try:
                        p_projs[p["id"]] = float(val) if val else 0.0
                    except ValueError:
                        p_projs[p["id"]] = 0.0

                wk_df = roster_df.copy()
                wk_df["proj"] = wk_df["player_id"].map(p_projs).fillna(0.0)

                team_scores = {}
                for fid in franchises:
                    tr = wk_df[wk_df["franchise_id"] == fid]
                    qbs = tr[tr["pos"] == "QB"].sort_values("proj", ascending=False)
                    qb = qbs["proj"].iloc[0] if len(qbs) > 0 else 0.0

                    pks = tr[tr["pos"] == "PK"].sort_values("proj", ascending=False)
                    pk = pks["proj"].iloc[0] if len(pks) > 0 else 0.0

                    defs = tr[tr["pos"] == "Def"].sort_values("proj", ascending=False)
                    d = defs["proj"].iloc[0] if len(defs) > 0 else 0.0

                    rbs = tr[tr["pos"] == "RB"].sort_values("proj", ascending=False)
                    rb = rbs.head(2)["proj"].sum()
                    remaining_rbs = rbs.iloc[2:]

                    wrs = tr[tr["pos"] == "WR"].sort_values("proj", ascending=False)
                    wr = wrs.head(2)["proj"].sum()
                    remaining_wrs = wrs.iloc[2:]

                    tes = tr[tr["pos"] == "TE"].sort_values("proj", ascending=False)
                    te = tes.head(1)["proj"].sum()
                    remaining_tes = tes.iloc[1:]

                    # 2 Flex spots from remaining RB, WR, TE
                    flex_pool = pd.concat([remaining_rbs, remaining_wrs, remaining_tes]).sort_values("proj", ascending=False)
                    flex = flex_pool.head(2)["proj"].sum()

                    total = round(qb + pk + d + rb + wr + te + flex, 2)
                    team_scores[fid] = total

                weekly_projections[w] = team_scores
            except Exception as e:
                print(f"Warning: could not fetch projected scores for week {w}: {e}")

        print(f"Successfully calculated optimal projected roster scores for {len(weekly_projections)} future weeks.")
        return weekly_projections
    except Exception as e:
        print(f"Warning: error calculating roster projections ({e}); continuing with historical model.")
        return {}


def get_simulation_inputs(client, target_week=None, target_year=None):
    """Fetch standings, schedule, scores, and franchises from BigQuery."""
    # Determine season / year
    if target_year is not None:
        sim_year = int(target_year)
    else:
        now = datetime.datetime.now()
        sim_year = now.year if now.month > 2 else now.year - 1

    # 1. Week Information
    week_info = bq_query(
        client,
        "SELECT recent_completed_week, current_week FROM `mfl-374514.dbt_production.dim_current_week`"
    )[0]
    
    if target_week is not None:
        recent_completed_wk = int(target_week)
        current_wk = recent_completed_wk + 1
    else:
        recent_completed_wk = int(week_info["recent_completed_week"])
        current_wk = int(week_info["current_week"])

    # 2. Franchises and Divisions
    franchises_data = bq_query(
        client,
        "SELECT franchise_id, division, franchise_name FROM `mfl-374514.dbt_production.dim_franchises`"
    )
    team_ids = sorted([f["franchise_id"] for f in franchises_data])
    team_names = {f["franchise_id"]: f["franchise_name"] for f in franchises_data}
    div_map = {f["franchise_id"]: f["division"] for f in franchises_data}
    divisions = sorted(list(set(div_map.values())))
    
    team_idx = {tid: i for i, tid in enumerate(team_ids)}
    n_teams = len(team_ids)
    div_indices = {
        div: [team_idx[t] for t in team_ids if div_map[t] == div]
        for div in divisions
    }

    # 3. Current Standings (reflects actual H2H + Median wins to date)
    standings_data = bq_query(
        client,
        """
        SELECT 
            franchise_id, 
            CAST(wins AS INT64) as wins, 
            CAST(losses AS INT64) as losses, 
            points_for 
        FROM `mfl-374514.dbt_production.dim_standings`
        """
    )
    standings_map = {s["franchise_id"]: s for s in standings_data}

    # 4. Weekly Scores & Empirical Bayes Early-Season Shrinkage
    scores_data = bq_query(
        client,
        f"""
        SELECT franchise_id, CAST(score AS FLOAT64) as score, week 
        FROM `mfl-374514.dbt_production.fct_results` 
        WHERE week <= {recent_completed_wk}
        """
    )
    scores_df = pd.DataFrame(scores_data)

    # League baseline fallback
    league_mean = float(scores_df["score"].mean()) if len(scores_df) > 0 else 100.0
    league_std = float(scores_df["score"].std()) if len(scores_df) > 1 else 15.0
    if pd.isna(league_std) or league_std <= 0:
        league_std = 15.0

    # Raw Mean, Std Dev, and Games Played (N) per team
    if len(scores_df) > 0:
        grouped_scores = scores_df.groupby("franchise_id")["score"]
        team_means = grouped_scores.mean().to_dict()
        team_stds = grouped_scores.std().fillna(league_std).to_dict()
        team_counts = grouped_scores.count().to_dict()
    else:
        team_means, team_stds, team_counts = {}, {}, {}

    # Empirical Bayes Shrinkage:
    # mu_adj = (N / (N + K)) * x_bar_team + (K / (N + K)) * x_bar_league
    # Regresses early-season mean and std dev toward the league baseline (K = 4.0 games)
    shrinkage_k = 4.0
    means_arr = np.zeros(n_teams, dtype=float)
    stds_arr = np.zeros(n_teams, dtype=float)

    for i, t in enumerate(team_ids):
        n_games = float(team_counts.get(t, 0))
        w_team = n_games / (n_games + shrinkage_k)
        w_league = shrinkage_k / (n_games + shrinkage_k)

        raw_mean = float(team_means.get(t, league_mean))
        raw_std = float(team_stds.get(t, league_std))
        if pd.isna(raw_std) or raw_std <= 0:
            raw_std = league_std

        means_arr[i] = (w_team * raw_mean) + (w_league * league_mean)
        stds_arr[i] = (w_team * raw_std) + (w_league * league_std)

    # 5. Schedule (Regular Season Weeks 1-14)
    sched_data = bq_query(
        client,
        """
        SELECT 
            home.week_num as wk,
            home.franchise_id as home_id,
            away.franchise_id as away_id,
            COALESCE(CAST(home_res.score AS FLOAT64), 0.0) as home_score,
            COALESCE(CAST(away_res.score AS FLOAT64), 0.0) as away_score
        FROM `mfl-374514.dbt_production.dim_schedules` home
        JOIN `mfl-374514.dbt_production.dim_schedules` away 
            ON home.week_num = away.week_num 
            AND home.matchup_num = away.matchup_num 
            AND home.franchise_id != away.franchise_id
        LEFT JOIN `mfl-374514.dbt_production.fct_results` home_res 
            ON home.franchise_id = home_res.franchise_id AND home.week_num = home_res.week
        LEFT JOIN `mfl-374514.dbt_production.fct_results` away_res 
            ON away.franchise_id = away_res.franchise_id AND away.week_num = away_res.week
        WHERE home.is_home = '1' AND away.is_home = '0' AND home.week_num <= 14
        ORDER BY wk, home.matchup_num
        """
    )

    # Extract completed postseason scores (Weeks 15-17) from scores_df
    postseason_scores_by_wk = {}
    if len(scores_df) > 0:
        ps_df = scores_df[scores_df["week"].isin([15, 16, 17])]
        for _, r in ps_df.iterrows():
            wk_int = int(r["week"])
            postseason_scores_by_wk.setdefault(wk_int, {})[r["franchise_id"]] = float(r["score"])

    # Fetch MFL optimal lineup projections for all remaining regular-season + playoff weeks (through Week 17)
    reg_future_weeks = {int(g["wk"]) for g in sched_data if int(g["wk"]) >= current_wk}
    postseason_future_weeks = {w for w in (15, 16, 17) if w >= current_wk}
    future_weeks = sorted(reg_future_weeks | postseason_future_weeks)
    weekly_roster_projs = get_projected_team_scores(client, future_weeks, team_ids)

    # Fetch official live playoff brackets directly from MFL API once Week 14 is complete
    live_brackets = fetch_mfl_playoff_brackets() if recent_completed_wk >= 14 else None

    # Merge any official playoff game scores directly from MFL playoffBracket payload
    if live_brackets:
        for b in live_brackets.get("brackets", []):
            for g in b.get("games", []):
                wk_g = g.get("week")
                if wk_g and wk_g <= recent_completed_wk:
                    for side_id_k, side_pts_k in [("home_franchise_id", "home_points"), ("away_franchise_id", "away_points")]:
                        fid = g.get(side_id_k)
                        pts = g.get(side_pts_k)
                        if fid and pts is not None:
                            postseason_scores_by_wk.setdefault(int(wk_g), {}).setdefault(fid, float(pts))

    return {
        "recent_completed_wk": recent_completed_wk,
        "current_wk": current_wk,
        "team_ids": team_ids,
        "team_names": team_names,
        "team_idx": team_idx,
        "n_teams": n_teams,
        "div_map": div_map,
        "divisions": divisions,
        "div_indices": div_indices,
        "standings_map": standings_map,
        "means_arr": means_arr,
        "stds_arr": stds_arr,
        "sched_data": sched_data,
        "weekly_roster_projs": weekly_roster_projs,
        "postseason_scores_by_wk": postseason_scores_by_wk,
        "live_brackets": live_brackets,
        "year": sim_year,
    }


def _parse_mfl_bracket_payload(raw_payload):
    """
    Normalizes an MFL `TYPE=playoffBracket` response into a flat ordered list of games:
      [{"game_id": int, "week": int, "home_franchise_id": str|None, "away_franchise_id": str|None,
        "home_seed": int|None, "away_seed": int|None, "home_points": float|None, "away_points": float|None}, ...]
    """
    pb = (raw_payload or {}).get("playoffBracket", {})
    rounds = pb.get("playoffRound", [])
    if isinstance(rounds, dict):
        rounds = [rounds]

    games = []
    for rd in rounds:
        wk = int(rd["week"]) if rd.get("week") else None
        rd_games = rd.get("playoffGame", [])
        if isinstance(rd_games, dict):
            rd_games = [rd_games]
        for g in rd_games:
            home = g.get("home", {}) or {}
            away = g.get("away", {}) or {}

            def _to_float(v):
                try:
                    return float(v) if v not in (None, "") else None
                except (ValueError, TypeError):
                    return None

            def _to_int(v):
                try:
                    return int(v) if v not in (None, "") else None
                except (ValueError, TypeError):
                    return None

            games.append({
                "game_id": _to_int(g.get("game_id")) or len(games) + 1,
                "week": wk,
                "home_franchise_id": home.get("franchise_id"),
                "away_franchise_id": away.get("franchise_id"),
                "home_seed": _to_int(home.get("seed")),
                "away_seed": _to_int(away.get("seed")),
                "home_points": _to_float(home.get("points")),
                "away_points": _to_float(away.get("points")),
            })

    games.sort(key=lambda x: (x["week"] or 99, x["game_id"]))
    return {"bracket_id": str(pb.get("bracket_id", "")), "games": games}


def fetch_mfl_playoff_brackets():
    """
    Fetches official live playoff brackets directly from MFL (`TYPE=playoffBracket`):
      - BRACKET_ID=1: Championship Bracket
      - BRACKET_ID=2: 3rd Place Game
      - BRACKET_ID=3: Consolation Bracket
    """
    try:
        api_key = os.getenv("MFL_API_KEY") or dlt.secrets.get("mfl_api_key", "")
    except Exception:
        api_key = os.getenv("MFL_API_KEY", "")

    brackets = []
    try:
        for bid in ("1", "2", "3"):
            raw = fetch_mfl_data("playoffBracket", api_key, extra_params=f"&BRACKET_ID={bid}")
            brackets.append(_parse_mfl_bracket_payload(raw))
        print(f"Loaded {len(brackets)} live playoff brackets directly from MFL API (BRACKET_ID 1, 2, 3).")
        return {"brackets": brackets}
    except Exception as e:
        print(f"Warning: could not fetch MFL playoffBracket API ({e}); will derive bracket from BigQuery standings/results.")
    return None


def compute_effective_means(wk, current_wk, means_arr, weekly_roster_projs, team_ids):
    """Blends optimal MFL roster projection for `wk` with Empirical Bayes historical mean."""
    delta_wk = max(0, int(wk) - int(current_wk))
    if delta_wk == 0:
        w_proj = 0.70
    elif delta_wk == 1:
        w_proj = 0.60
    elif delta_wk == 2:
        w_proj = 0.50
    else:
        w_proj = 0.40

    wk_projs = (weekly_roster_projs or {}).get(int(wk), {})
    effective_means = means_arr.copy()
    if wk_projs:
        for i, tid in enumerate(team_ids):
            val = float(wk_projs.get(tid, 0.0) or 0.0)
            # Only blend when MFL has published realistic lineup projections for this week
            if val > 20.0:
                effective_means[i] = (w_proj * val) + ((1.0 - w_proj) * means_arr[i])
    return np.maximum(effective_means, 1.0)


def sample_gamma_scores(num_runs, effective_means, stds_arr):
    """Samples (num_runs, n_teams) fantasy scores from a right-skewed Gamma distribution."""
    safe_means = np.maximum(effective_means, 1.0)
    safe_stds = np.maximum(stds_arr, 1.0)
    shape = (safe_means / safe_stds) ** 2
    scale = (safe_stds ** 2) / safe_means
    return np.random.gamma(shape, scale, size=(num_runs, len(safe_means)))


def simulate_six_team_bracket_vectorized(seeds_arr, wk15_scores, wk16_scores, wk17_scores, n_teams):
    """
    Vectorized simulation of a 6-team reseeded 3-week playoff bracket across `num_runs`:
      - Week 15 (Wild Card): #3 vs #6, #4 vs #5 (#1 & #2 on Bye)
      - Week 16 (Semifinals): Reseeded by true seed (#1 vs lowest surviving seed, #2 vs highest)
      - Week 17 (Finals + 3rd Place): Semis winners for 1st/2nd; Semis losers for 3rd/4th
    """
    num_runs = seeds_arr.shape[0]
    r_idx = np.arange(num_runs)

    s1 = seeds_arr[:, 0]
    s2 = seeds_arr[:, 1]
    s3 = seeds_arr[:, 2]
    s4 = seeds_arr[:, 3]
    s5 = seeds_arr[:, 4]
    s6 = seeds_arr[:, 5]

    # Week 15: Wild Card
    wc1_s3_wins = wk15_scores[r_idx, s3] >= wk15_scores[r_idx, s6]
    wc1_w = np.where(wc1_s3_wins, s3, s6)
    wc1_seed = np.where(wc1_s3_wins, 3, 6)

    wc2_s4_wins = wk15_scores[r_idx, s4] >= wk15_scores[r_idx, s5]
    wc2_w = np.where(wc2_s4_wins, s4, s5)
    wc2_seed = np.where(wc2_s4_wins, 4, 5)

    # Week 16: Semifinals (True seed-based reseeding)
    wc1_lower_ranked = wc1_seed > wc2_seed
    sf1_opp = np.where(wc1_lower_ranked, wc1_w, wc2_w)
    sf2_opp = np.where(wc1_lower_ranked, wc2_w, wc1_w)

    sf1_s1_wins = wk16_scores[r_idx, s1] >= wk16_scores[r_idx, sf1_opp]
    sf1_w = np.where(sf1_s1_wins, s1, sf1_opp)
    sf1_l = np.where(sf1_s1_wins, sf1_opp, s1)

    sf2_s2_wins = wk16_scores[r_idx, s2] >= wk16_scores[r_idx, sf2_opp]
    sf2_w = np.where(sf2_s2_wins, s2, sf2_opp)
    sf2_l = np.where(sf2_s2_wins, sf2_opp, s2)

    # Week 17: Championship Final & 3rd Place Game
    fin_sf1_wins = wk17_scores[r_idx, sf1_w] >= wk17_scores[r_idx, sf2_w]
    champ = np.where(fin_sf1_wins, sf1_w, sf2_w)
    runner_up = np.where(fin_sf1_wins, sf2_w, sf1_w)

    tp_sf1_wins = wk17_scores[r_idx, sf1_l] >= wk17_scores[r_idx, sf2_l]
    third = np.where(tp_sf1_wins, sf1_l, sf2_l)

    semis_cnt = (
        np.bincount(s1, minlength=n_teams)
        + np.bincount(s2, minlength=n_teams)
        + np.bincount(wc1_w, minlength=n_teams)
        + np.bincount(wc2_w, minlength=n_teams)
    )
    finals_cnt = np.bincount(sf1_w, minlength=n_teams) + np.bincount(sf2_w, minlength=n_teams)

    return {
        "reach_semis": semis_cnt,
        "reach_finals": finals_cnt,
        "champ": np.bincount(champ, minlength=n_teams),
        "runner_up": np.bincount(runner_up, minlength=n_teams),
        "third": np.bincount(third, minlength=n_teams),
    }


def simulate_live_bracket(bracket_state, bracket_name, include_third_place, inputs, wk_scores_map, wk_means_map, num_runs):
    """
    Simulates remaining rounds of a live postseason bracket (Weeks 15-17), honoring all
    completed matchups deterministically and computing per-team probabilities + per-matchup win %.
    """
    team_idx = inputs["team_idx"]
    n_teams = inputs["n_teams"]
    r_idx = np.arange(num_runs)
    games = bracket_state["games"]
    seed_by_tid = bracket_state["seed_by_tid"]

    def idx_arr(tid):
        return np.full(num_runs, team_idx[tid], dtype=int)

    def sim_or_lock_game(g, wk_scores):
        h_id = g["high_franchise_id"]
        l_id = g["low_franchise_id"]
        h_idx = idx_arr(h_id)
        l_idx = idx_arr(l_id)
        if g["is_complete"]:
            w_id = g["winner_franchise_id"]
            lo_id = g["loser_franchise_id"]
            h_prob = 1.0 if w_id == h_id else 0.0
            return idx_arr(w_id), idx_arr(lo_id), h_prob, 1.0 - h_prob
        h_wins = wk_scores[r_idx, h_idx] >= wk_scores[r_idx, l_idx]
        w_arr = np.where(h_wins, h_idx, l_idx)
        lo_arr = np.where(h_wins, l_idx, h_idx)
        h_prob = float(h_wins.mean())
        return w_arr, lo_arr, h_prob, 1.0 - h_prob

    # Seed array lookup by team index for true seed-based reseeding
    idx_to_seed = np.full(n_teams, 99, dtype=int)
    for tid, sd in seed_by_tid.items():
        if tid in team_idx:
            idx_to_seed[team_idx[tid]] = int(sd)

    # Week 15: Wild Card
    g_wc1 = games[("Wild Card", 1)]
    g_wc2 = games[("Wild Card", 2)]
    wc1_w, _, wc1_hp, wc1_lp = sim_or_lock_game(g_wc1, wk_scores_map[15])
    wc2_w, _, wc2_hp, wc2_lp = sim_or_lock_game(g_wc2, wk_scores_map[15])

    # Week 16: Semifinals
    g_sf1 = games[("Semifinals", 1)]
    g_sf2 = games[("Semifinals", 2)]
    s1_idx = idx_arr(g_sf1["high_franchise_id"])
    s2_idx = idx_arr(g_sf2["high_franchise_id"])

    if g_sf1["low_franchise_id"] and g_sf2["low_franchise_id"]:
        sf1_w, sf1_l, sf1_hp, sf1_lp = sim_or_lock_game(g_sf1, wk_scores_map[16])
        sf2_w, sf2_l, sf2_hp, sf2_lp = sim_or_lock_game(g_sf2, wk_scores_map[16])
    else:
        # Wild Card not yet finished: reseed dynamically per simulation run by true seed number
        wc1_seed_arr = idx_to_seed[wc1_w]
        wc2_seed_arr = idx_to_seed[wc2_w]
        wc1_lower_ranked = wc1_seed_arr > wc2_seed_arr
        sf1_opp = np.where(wc1_lower_ranked, wc1_w, wc2_w)
        sf2_opp = np.where(wc1_lower_ranked, wc2_w, wc1_w)

        sf1_h_wins = wk_scores_map[16][r_idx, s1_idx] >= wk_scores_map[16][r_idx, sf1_opp]
        sf1_w = np.where(sf1_h_wins, s1_idx, sf1_opp)
        sf1_l = np.where(sf1_h_wins, sf1_opp, s1_idx)
        sf1_hp = float(sf1_h_wins.mean())
        sf1_lp = 1.0 - sf1_hp

        sf2_h_wins = wk_scores_map[16][r_idx, s2_idx] >= wk_scores_map[16][r_idx, sf2_opp]
        sf2_w = np.where(sf2_h_wins, s2_idx, sf2_opp)
        sf2_l = np.where(sf2_h_wins, sf2_opp, s2_idx)
        sf2_hp = float(sf2_h_wins.mean())
        sf2_lp = 1.0 - sf2_hp

    # Week 17: Finals & optional 3rd Place
    g_fin = games[("Finals", 1)]
    if g_fin["high_franchise_id"] and g_fin["low_franchise_id"]:
        champ, runner_up, fin_hp, fin_lp = sim_or_lock_game(g_fin, wk_scores_map[17])
    else:
        fin_sf1_wins = wk_scores_map[17][r_idx, sf1_w] >= wk_scores_map[17][r_idx, sf2_w]
        champ = np.where(fin_sf1_wins, sf1_w, sf2_w)
        runner_up = np.where(fin_sf1_wins, sf2_w, sf1_w)
        fin_hp, fin_lp = None, None

    tp_hp, tp_lp = None, None
    if include_third_place:
        g_tp = games[("3rd Place", 1)]
        if g_tp["high_franchise_id"] and g_tp["low_franchise_id"]:
            third, _, tp_hp, tp_lp = sim_or_lock_game(g_tp, wk_scores_map[17])
        else:
            tp_sf1_wins = wk_scores_map[17][r_idx, sf1_l] >= wk_scores_map[17][r_idx, sf2_l]
            third = np.where(tp_sf1_wins, sf1_l, sf2_l)
    else:
        third = None

    semis_cnt = (
        np.bincount(s1_idx, minlength=n_teams)
        + np.bincount(s2_idx, minlength=n_teams)
        + np.bincount(wc1_w, minlength=n_teams)
        + np.bincount(wc2_w, minlength=n_teams)
    )
    finals_cnt = np.bincount(sf1_w, minlength=n_teams) + np.bincount(sf2_w, minlength=n_teams)
    champ_cnt = np.bincount(champ, minlength=n_teams)
    runner_up_cnt = np.bincount(runner_up, minlength=n_teams)
    third_cnt = np.bincount(third, minlength=n_teams) if third is not None else np.zeros(n_teams, dtype=int)

    # Assemble per-matchup rows for BigQuery
    matchup_rows = []
    game_probs = {
        ("Wild Card", 1): (wc1_hp, wc1_lp),
        ("Wild Card", 2): (wc2_hp, wc2_lp),
        ("Semifinals", 1): (sf1_hp, sf1_lp) if (g_sf1["high_franchise_id"] and g_sf1["low_franchise_id"]) else (None, None),
        ("Semifinals", 2): (sf2_hp, sf2_lp) if (g_sf2["high_franchise_id"] and g_sf2["low_franchise_id"]) else (None, None),
        ("Finals", 1): (fin_hp, fin_lp),
    }
    if include_third_place:
        game_probs[("3rd Place", 1)] = (tp_hp, tp_lp)

    for key, g in games.items():
        hp, lp = game_probs.get(key, (None, None))
        wk = g["week"]
        h_id = g["high_franchise_id"]
        l_id = g["low_franchise_id"]
        h_proj = round(float(wk_means_map[wk][team_idx[h_id]]), 2) if (h_id and h_id in team_idx) else None
        l_proj = round(float(wk_means_map[wk][team_idx[l_id]]), 2) if (l_id and l_id in team_idx) else None
        matchup_rows.append({
            "year": inputs["year"],
            "after_week": inputs["recent_completed_wk"],
            "week": wk,
            "bracket": bracket_name,
            "round_name": g["round_name"],
            "game_num": g["game_num"],
            "high_seed": g["high_seed"],
            "high_franchise_id": h_id,
            "low_seed": g["low_seed"],
            "low_franchise_id": l_id,
            "high_win_prob": round(float(hp), 4) if hp is not None else None,
            "low_win_prob": round(float(lp), 4) if lp is not None else None,
            "high_proj_pts": h_proj,
            "low_proj_pts": l_proj,
            "high_actual_pts": g["high_actual_pts"],
            "low_actual_pts": g["low_actual_pts"],
            "winner_franchise_id": g["winner_franchise_id"],
        })

    team_rows = []
    for sd, tid in sorted(bracket_state["seeds"].items()):
        i = team_idx[tid]
        is_champ_bracket = (bracket_name == "championship")
        team_rows.append({
            "franchise_id": tid,
            "year": inputs["year"],
            "after_week": inputs["recent_completed_wk"],
            "bracket": bracket_name,
            "seed": int(sd),
            "reach_semis": round(float(semis_cnt[i] / num_runs), 4),
            "reach_finals": round(float(finals_cnt[i] / num_runs), 4),
            "win_championship": round(float(champ_cnt[i] / num_runs), 4) if is_champ_bracket else 0.0,
            "runner_up": round(float(runner_up_cnt[i] / num_runs), 4) if is_champ_bracket else 0.0,
            "third_place": round(float(third_cnt[i] / num_runs), 4) if is_champ_bracket else 0.0,
            "extra_pick": round(float(champ_cnt[i] / num_runs), 4) if not is_champ_bracket else 0.0,
        })

    return team_rows, matchup_rows


def run_simulation(inputs, num_runs=10000):
    """Run vectorized Monte Carlo simulations with H2H, League Median, and blended roster projections."""
    current_wk = inputs["current_wk"]
    n_teams = inputs["n_teams"]
    team_idx = inputs["team_idx"]
    div_map = inputs["div_map"]
    div_indices = inputs["div_indices"]
    standings_map = inputs["standings_map"]
    sched_data = inputs["sched_data"]
    means_arr = inputs["means_arr"]
    stds_arr = inputs["stds_arr"]
    team_ids = inputs["team_ids"]
    weekly_roster_projs = inputs.get("weekly_roster_projs", {})

    # 1. Past Stats Setup
    past_wins = np.array([standings_map[t]["wins"] for t in team_ids], dtype=int)
    past_points = np.array([standings_map[t]["points_for"] for t in team_ids], dtype=float)

    past_div_wins = np.zeros(n_teams, dtype=int)
    past_h2h = np.zeros((n_teams, n_teams), dtype=int)

    future_by_week = {}
    for g in sched_data:
        h_idx, a_idx = team_idx[g["home_id"]], team_idx[g["away_id"]]
        is_div = int(div_map[g["home_id"]] == div_map[g["away_id"]])
        wk = g["wk"]
        if wk < current_wk:
            if g["home_score"] > g["away_score"]:
                past_h2h[h_idx, a_idx] += 1
                if is_div:
                    past_div_wins[h_idx] += 1
            elif g["away_score"] > g["home_score"]:
                past_h2h[a_idx, h_idx] += 1
                if is_div:
                    past_div_wins[a_idx] += 1
        else:
            if wk not in future_by_week:
                future_by_week[wk] = []
            future_by_week[wk].append({
                "home_idx": h_idx,
                "away_idx": a_idx,
                "is_div": is_div,
            })

    # 2. Simulation State Initialization
    sim_wins = np.zeros((num_runs, n_teams), dtype=int)
    sim_div_wins = np.zeros((num_runs, n_teams), dtype=int)
    sim_points = np.zeros((num_runs, n_teams), dtype=float)
    sim_h2h = np.zeros((num_runs, n_teams, n_teams), dtype=int)

    sim_wins[:] = past_wins
    sim_div_wins[:] = past_div_wins
    sim_points[:] = past_points
    sim_h2h[:] = past_h2h

    # 3. Simulate Remaining Regular Season Weeks
    for wk in sorted(future_by_week.keys()):
        matchups = future_by_week[wk]
        n_matchups = len(matchups)

        home_indices = np.array([m["home_idx"] for m in matchups])
        away_indices = np.array([m["away_idx"] for m in matchups])
        is_div_arr = np.array([m["is_div"] for m in matchups])

        # Compute effective mean for each team this week (blending roster projections with historical averages)
        effective_means = compute_effective_means(wk, current_wk, means_arr, weekly_roster_projs, team_ids)

        home_means = effective_means[home_indices]
        home_stds = stds_arr[home_indices]
        away_means = effective_means[away_indices]
        away_stds = stds_arr[away_indices]

        # Simulate scores for all matchups in this week using a right-skewed Gamma distribution
        # Parameterized by exact mean (mu) and std dev (sigma): shape k = (mu/sigma)^2, scale theta = sigma^2/mu
        home_shape = (home_means / home_stds) ** 2
        home_scale = (home_stds ** 2) / home_means
        away_shape = (away_means / away_stds) ** 2
        away_scale = (away_stds ** 2) / away_means

        home_scores = np.random.gamma(home_shape, home_scale, size=(num_runs, n_matchups))
        away_scores = np.random.gamma(away_shape, away_scale, size=(num_runs, n_matchups))

        # A. Head-to-Head Outcomes
        home_win = home_scores > away_scores

        for m_idx in range(n_matchups):
            h, a = home_indices[m_idx], away_indices[m_idx]
            div_flag = is_div_arr[m_idx]
            hw = home_win[:, m_idx]

            sim_wins[hw, h] += 1
            sim_wins[~hw, a] += 1

            if div_flag:
                sim_div_wins[hw, h] += 1
                sim_div_wins[~hw, a] += 1

            sim_h2h[hw, h, a] += 1
            sim_h2h[~hw, a, h] += 1

            sim_points[:, h] += home_scores[:, m_idx]
            sim_points[:, a] += away_scores[:, m_idx]

        # B. Weekly League Median Scoring (Matchup 2)
        week_scores = np.zeros((num_runs, n_teams), dtype=float)
        for m_idx in range(n_matchups):
            h, a = home_indices[m_idx], away_indices[m_idx]
            week_scores[:, h] = home_scores[:, m_idx]
            week_scores[:, a] = away_scores[:, m_idx]

        # Top 6 scores receive an extra win against the weekly median
        ranks = np.argsort(np.argsort(-week_scores, axis=1), axis=1)
        sim_wins += (ranks < 6).astype(int)

    # 4. Postseason Seeding & Tiebreakers
    one_seed_cnt = np.zeros(n_teams, dtype=int)
    two_seed_cnt = np.zeros(n_teams, dtype=int)
    div_win_cnt = np.zeros(n_teams, dtype=int)
    wc_cnt = np.zeros(n_teams, dtype=int)
    playoff_cnt = np.zeros(n_teams, dtype=int)
    pick_cnt = np.zeros(n_teams, dtype=int)
    top_pts_cnt = np.zeros(n_teams, dtype=int)
    champ_seeds_arr = np.zeros((num_runs, 6), dtype=int)
    cons_seeds_arr = np.zeros((num_runs, 6), dtype=int)

    def resolve_tie_group(r, tied_teams):
        """Resolves a group of teams tied on overall wins using H2H (sweep/round-robin %) -> Points -> Div Wins."""
        if len(tied_teams) <= 1:
            return list(tied_teams)

        # 2-team tie: direct Head-to-Head -> Total Points -> Division Wins
        if len(tied_teams) == 2:
            t1, t2 = tied_teams[0], tied_teams[1]
            if sim_h2h[r, t1, t2] != sim_h2h[r, t2, t1]:
                return [t1, t2] if sim_h2h[r, t1, t2] > sim_h2h[r, t2, t1] else [t2, t1]
            return sorted(tied_teams, key=lambda t: (sim_points[r, t], sim_div_wins[r, t]), reverse=True)

        # Multi-team tie (3+): check round-robin H2H win percentage among the tied group
        h2h_pct = {}
        valid_round_robin = True
        for t1 in tied_teams:
            w = sum(int(sim_h2h[r, t1, t2]) for t2 in tied_teams if t2 != t1)
            l = sum(int(sim_h2h[r, t2, t1]) for t2 in tied_teams if t2 != t1)
            if w + l == 0:
                valid_round_robin = False
                break
            h2h_pct[t1] = round(w / (w + l), 6)

        if valid_round_robin and len(set(h2h_pct.values())) > 1:
            ordered = []
            for pct in sorted(set(h2h_pct.values()), reverse=True):
                sub_group = [t for t in tied_teams if h2h_pct[t] == pct]
                if len(sub_group) == 1:
                    ordered.extend(sub_group)
                else:
                    ordered.extend(resolve_tie_group(r, sub_group))
            return ordered

        # Circular or identical H2H tie: fall back directly to Total Regular Season Points -> Division Wins
        return sorted(tied_teams, key=lambda t: (sim_points[r, t], sim_div_wins[r, t]), reverse=True)

    def rank_teams(r, teams):
        """Ranks teams from best to worst: Wins -> H2H (2-way or multi-team round-robin) -> Points -> Div Wins."""
        win_buckets = {}
        for t in teams:
            w = int(sim_wins[r, t])
            win_buckets.setdefault(w, []).append(t)

        ranked = []
        for w in sorted(win_buckets.keys(), reverse=True):
            ranked.extend(resolve_tie_group(r, win_buckets[w]))
        return ranked

    for r in range(num_runs):
        # Points Champion
        best_pts_team = int(np.argmax(sim_points[r]))
        top_pts_cnt[best_pts_team] += 1

        # 1. Division Winners (1 per division)
        div_winners = []
        for div_name, div_teams in div_indices.items():
            div_sorted = rank_teams(r, div_teams)
            div_winners.append(div_sorted[0])

        # Rank the 3 division winners
        div_winners_sorted = rank_teams(r, div_winners)
        s1 = div_winners_sorted[0]
        s2 = div_winners_sorted[1]
        s3 = div_winners_sorted[2]

        one_seed_cnt[s1] += 1
        two_seed_cnt[s2] += 1
        div_win_cnt[s1] += 1
        div_win_cnt[s2] += 1
        div_win_cnt[s3] += 1

        # 2. Wild Cards (top 3 non-division winners) & Consolation Seeds (best-to-worst #7..#12)
        non_div_teams = [t for t in range(n_teams) if t not in div_winners]
        wc_sorted = rank_teams(r, non_div_teams)
        wc1, wc2, wc3 = wc_sorted[0], wc_sorted[1], wc_sorted[2]

        wc_cnt[wc1] += 1
        wc_cnt[wc2] += 1
        wc_cnt[wc3] += 1

        for t in [s1, s2, s3, wc1, wc2, wc3]:
            playoff_cnt[t] += 1

        champ_seeds_arr[r] = [s1, s2, s3, wc1, wc2, wc3]
        if len(wc_sorted) >= 9:
            cons_seeds_arr[r] = wc_sorted[3:9]

        # 3. First Draft Pick (worst overall team)
        worst_team = rank_teams(r, range(n_teams))[-1]
        pick_cnt[worst_team] += 1

    # 5. Aggregate Regular Season Probabilities
    proj_wins = sim_wins.mean(axis=0)
    recent_completed_wk = inputs["recent_completed_wk"]

    rows = []
    for i, tid in enumerate(team_ids):
        rows.append({
            "franchise_id": tid,
            "one_seed": round(float(one_seed_cnt[i] / num_runs), 4),
            "bye": round(float((one_seed_cnt[i] + two_seed_cnt[i]) / num_runs), 4),
            "win_division": round(float(div_win_cnt[i] / num_runs), 4),
            "wild_card": round(float(wc_cnt[i] / num_runs), 4),
            "make_playoffs": round(float(playoff_cnt[i] / num_runs), 4),
            "first_pick": round(float(pick_cnt[i] / num_runs), 4),
            "proj_wins": round(float(proj_wins[i]), 4),
            "top_pts": round(float(top_pts_cnt[i] / num_runs), 4),
            "after_week": recent_completed_wk,
            "year": inputs["year"],
        })
    df_probs = pd.DataFrame(rows)

    # 6. Full Postseason Simulation (Weeks 15-17: Championship + 3rd Place + Consolation Brackets)
    wk_means_map = {
        wk: compute_effective_means(wk, current_wk, means_arr, weekly_roster_projs, team_ids)
        for wk in (15, 16, 17)
    }
    wk_scores_map = {
        wk: sample_gamma_scores(num_runs, wk_means_map[wk], stds_arr)
        for wk in (15, 16, 17)
    }

    if recent_completed_wk < 14:
        # Regular Season Mode: simulate Weeks 15-17 directly off each simulated regular season's seeds
        champ_res = simulate_six_team_bracket_vectorized(
            champ_seeds_arr, wk_scores_map[15], wk_scores_map[16], wk_scores_map[17], n_teams
        )
        cons_res = simulate_six_team_bracket_vectorized(
            cons_seeds_arr, wk_scores_map[15], wk_scores_map[16], wk_scores_map[17], n_teams
        )

        ps_rows = []
        for i, tid in enumerate(team_ids):
            ps_rows.append({
                "franchise_id": tid,
                "year": inputs["year"],
                "after_week": recent_completed_wk,
                "bracket": "projected",
                "seed": None,
                "reach_semis": round(float(champ_res["reach_semis"][i] / num_runs), 4),
                "reach_finals": round(float(champ_res["reach_finals"][i] / num_runs), 4),
                "win_championship": round(float(champ_res["champ"][i] / num_runs), 4),
                "runner_up": round(float(champ_res["runner_up"][i] / num_runs), 4),
                "third_place": round(float(champ_res["third"][i] / num_runs), 4),
                "extra_pick": round(float(cons_res["champ"][i] / num_runs), 4),
            })
        df_postseason = pd.DataFrame(ps_rows)
        df_matchups = pd.DataFrame()
    else:
        # Live Postseason Mode (after_week >= 14): lock actual seeds & completed playoff games
        sched_rows_flat = []
        for g in sched_data:
            sched_rows_flat.append({
                "week": int(g["wk"]),
                "franchise_id": g["home_id"],
                "opp_id": g["away_id"],
                "team_score": float(g["home_score"]),
                "opp_score": float(g["away_score"]),
            })
            sched_rows_flat.append({
                "week": int(g["wk"]),
                "franchise_id": g["away_id"],
                "opp_id": g["home_id"],
                "team_score": float(g["away_score"]),
                "opp_score": float(g["home_score"]),
            })

        reg_state = standings_utils.build_h2h_and_standings_from_schedule(
            team_ids, div_map, sched_rows_flat, up_to_week=14
        )
        # Use authoritative dim_standings if exactly after Week 14; else 14-week reconstructed standings
        if recent_completed_wk == 14:
            reg_wins = {t: int(standings_map[t]["wins"]) for t in team_ids}
            reg_pf = {t: float(standings_map[t]["points_for"]) for t in team_ids}
        else:
            reg_wins = reg_state["hist_wins"] if any(reg_state["hist_wins"].values()) else {t: int(standings_map[t]["wins"]) for t in team_ids}
            reg_pf = reg_state["hist_pf"] if any(reg_state["hist_pf"].values()) else {t: float(standings_map[t]["points_for"]) for t in team_ids}

        derived_seeds = standings_utils.rank_regular_season_seeds(
            team_ids=team_ids,
            div_map=div_map,
            wins_map=reg_wins,
            pf_map=reg_pf,
            past_h2h=reg_state["past_h2h"],
            past_div_wins=reg_state["past_div_wins"],
        )

        api_brackets_list = (inputs.get("live_brackets") or {}).get("brackets", [])
        api_champ = api_brackets_list[0] if len(api_brackets_list) > 0 else None
        api_third = api_brackets_list[1] if len(api_brackets_list) > 1 else None
        api_cons = api_brackets_list[2] if len(api_brackets_list) > 2 else None

        ps_scores = inputs.get("postseason_scores_by_wk", {})
        champ_state = standings_utils.resolve_live_bracket_state(
            seeds_map=derived_seeds["championship_seeds"],
            week_scores_by_wk=ps_scores,
            recent_completed_wk=recent_completed_wk,
            api_bracket=api_champ,
            third_place_api_bracket=api_third,
            include_third_place=True,
        )
        cons_state = standings_utils.resolve_live_bracket_state(
            seeds_map=derived_seeds["consolation_seeds"],
            week_scores_by_wk=ps_scores,
            recent_completed_wk=recent_completed_wk,
            api_bracket=api_cons,
            third_place_api_bracket=None,
            include_third_place=False,
        )

        champ_team_rows, champ_matchup_rows = simulate_live_bracket(
            champ_state, "championship", True, inputs, wk_scores_map, wk_means_map, num_runs
        )
        cons_team_rows, cons_matchup_rows = simulate_live_bracket(
            cons_state, "consolation", False, inputs, wk_scores_map, wk_means_map, num_runs
        )

        df_postseason = pd.DataFrame(champ_team_rows + cons_team_rows)
        df_matchups = pd.DataFrame(champ_matchup_rows + cons_matchup_rows)

    return df_probs, df_postseason, df_matchups


def _delete_existing_week_rows(client, table_id, year, week):
    """Idempotently deletes existing rows for (year, after_week), ignoring NotFound on first run."""
    delete_sql = f"DELETE FROM `{table_id}` WHERE year = {year} AND after_week = {week}"
    try:
        client.query(delete_sql).result()
        print(f"Deleted any existing records in {table_id} for year = {year}, after_week = {week}.")
    except NotFound:
        print(f"Table {table_id} does not exist yet; it will be created automatically.")


def save_to_bigquery(client, df_probs, table_id="mfl-374514.external.reg_season_sims"):
    """Atomically replaces regular-season probabilities for the completed week and year in BigQuery."""
    week = int(df_probs["after_week"].iloc[0])
    year = int(df_probs["year"].iloc[0])
    print(f"Saving regular-season simulation results for Year {year}, after_week {week} to BigQuery table: {table_id}...")

    _delete_existing_week_rows(client, table_id, year, week)

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        schema=[
            bigquery.SchemaField("franchise_id", "STRING"),
            bigquery.SchemaField("one_seed", "FLOAT64"),
            bigquery.SchemaField("bye", "FLOAT64"),
            bigquery.SchemaField("win_division", "FLOAT64"),
            bigquery.SchemaField("wild_card", "FLOAT64"),
            bigquery.SchemaField("make_playoffs", "FLOAT64"),
            bigquery.SchemaField("first_pick", "FLOAT64"),
            bigquery.SchemaField("proj_wins", "FLOAT64"),
            bigquery.SchemaField("top_pts", "FLOAT64"),
            bigquery.SchemaField("after_week", "INT64"),
            bigquery.SchemaField("year", "INT64"),
        ],
    )
    job = client.load_table_from_dataframe(df_probs, table_id, job_config=job_config)
    job.result()
    print(f"Successfully inserted {len(df_probs)} rows into {table_id} for year {year}, week {week}!")


def save_postseason_to_bigquery(client, df_postseason, table_id="mfl-374514.external.postseason_sims"):
    """Atomically replaces postseason championship/podium/extra-pick probabilities in BigQuery."""
    if df_postseason is None or df_postseason.empty:
        return
    week = int(df_postseason["after_week"].iloc[0])
    year = int(df_postseason["year"].iloc[0])
    print(f"Saving postseason simulation results for Year {year}, after_week {week} to BigQuery table: {table_id}...")

    _delete_existing_week_rows(client, table_id, year, week)

    df_upload = df_postseason.copy()
    df_upload["seed"] = pd.array(df_upload["seed"], dtype="Int64")

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        schema=[
            bigquery.SchemaField("franchise_id", "STRING"),
            bigquery.SchemaField("year", "INT64"),
            bigquery.SchemaField("after_week", "INT64"),
            bigquery.SchemaField("bracket", "STRING"),
            bigquery.SchemaField("seed", "INT64"),
            bigquery.SchemaField("reach_semis", "FLOAT64"),
            bigquery.SchemaField("reach_finals", "FLOAT64"),
            bigquery.SchemaField("win_championship", "FLOAT64"),
            bigquery.SchemaField("runner_up", "FLOAT64"),
            bigquery.SchemaField("third_place", "FLOAT64"),
            bigquery.SchemaField("extra_pick", "FLOAT64"),
        ],
    )
    job = client.load_table_from_dataframe(df_upload, table_id, job_config=job_config)
    job.result()
    print(f"Successfully inserted {len(df_upload)} rows into {table_id} for year {year}, week {week}!")


def save_matchups_to_bigquery(client, df_matchups, table_id="mfl-374514.external.postseason_matchups"):
    """Atomically replaces live postseason bracket matchup probabilities & scores in BigQuery."""
    if df_matchups is None or df_matchups.empty:
        return
    week = int(df_matchups["after_week"].iloc[0])
    year = int(df_matchups["year"].iloc[0])
    print(f"Saving postseason matchups for Year {year}, after_week {week} to BigQuery table: {table_id}...")

    _delete_existing_week_rows(client, table_id, year, week)

    df_upload = df_matchups.copy()
    df_upload["high_seed"] = pd.array(df_upload["high_seed"], dtype="Int64")
    df_upload["low_seed"] = pd.array(df_upload["low_seed"], dtype="Int64")

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        schema=[
            bigquery.SchemaField("year", "INT64"),
            bigquery.SchemaField("after_week", "INT64"),
            bigquery.SchemaField("week", "INT64"),
            bigquery.SchemaField("bracket", "STRING"),
            bigquery.SchemaField("round_name", "STRING"),
            bigquery.SchemaField("game_num", "INT64"),
            bigquery.SchemaField("high_seed", "INT64"),
            bigquery.SchemaField("high_franchise_id", "STRING"),
            bigquery.SchemaField("low_seed", "INT64"),
            bigquery.SchemaField("low_franchise_id", "STRING"),
            bigquery.SchemaField("high_win_prob", "FLOAT64"),
            bigquery.SchemaField("low_win_prob", "FLOAT64"),
            bigquery.SchemaField("high_proj_pts", "FLOAT64"),
            bigquery.SchemaField("low_proj_pts", "FLOAT64"),
            bigquery.SchemaField("high_actual_pts", "FLOAT64"),
            bigquery.SchemaField("low_actual_pts", "FLOAT64"),
            bigquery.SchemaField("winner_franchise_id", "STRING"),
        ],
    )
    job = client.load_table_from_dataframe(df_upload, table_id, job_config=job_config)
    job.result()
    print(f"Successfully inserted {len(df_upload)} rows into {table_id} for year {year}, week {week}!")


def simulate_and_save(num_runs=10000, target_week=None, target_year=None):
    """Main entrypoint to run regular-season + postseason simulation and save results to BigQuery."""
    start_time = time.time()
    print(f"[{datetime.datetime.now()}] Starting Wide Right Full Season & Playoff Odds Model ({num_runs:,} runs)...")

    client = get_bq_client()
    inputs = get_simulation_inputs(client, target_week=target_week, target_year=target_year)
    recent_completed_wk = inputs["recent_completed_wk"]
    current_wk = inputs["current_wk"]
    print(f"Loaded league data: Year {inputs['year']}, After Week {recent_completed_wk}, Next Week {current_wk}.")

    # Display upcoming week's roster projections
    wk_projs = inputs.get("weekly_roster_projs", {}).get(current_wk, {})
    if wk_projs:
        team_names = inputs["team_names"]
        print(f"\n--- Week {current_wk} Optimal Roster Projections ---")
        sorted_projs = sorted(wk_projs.items(), key=lambda x: x[1], reverse=True)
        for fid, score in sorted_projs:
            print(f"  {team_names.get(fid, fid):<26} {score:>6.1f} pts")

    df_probs, df_postseason, df_matchups = run_simulation(inputs, num_runs=num_runs)

    # Format summary display
    team_names = inputs["team_names"]
    if recent_completed_wk <= 14:
        display_df = df_probs.copy()
        display_df["Team"] = display_df["franchise_id"].map(team_names)
        display_df = display_df.sort_values(by="make_playoffs", ascending=False)
        cols = ["Team", "proj_wins", "make_playoffs", "win_division", "bye", "one_seed", "top_pts", "first_pick"]
        print("\n--- Regular Season Simulation Summary (28-Game Median Model + Roster Projections) ---")
        print(display_df[cols].to_string(index=False))

    ps_display = df_postseason.copy()
    ps_display["Team"] = ps_display["franchise_id"].map(team_names)
    ps_display["Playoff_EV"] = (
        ps_display["win_championship"] * 275.0
        + ps_display["runner_up"] * 135.0
        + ps_display["third_place"] * 60.0
    ).round(2)
    ps_display = ps_display.sort_values(by=["win_championship", "extra_pick"], ascending=[False, False])
    ps_cols = ["Team", "bracket", "seed", "reach_semis", "reach_finals", "win_championship", "runner_up", "third_place", "extra_pick", "Playoff_EV"]
    print("\n--- Postseason Simulation Summary (Weeks 15-17 Championship & Consolation) ---")
    print(ps_display[ps_cols].to_string(index=False))

    if recent_completed_wk <= 14:
        save_to_bigquery(client, df_probs)
    save_postseason_to_bigquery(client, df_postseason)
    if not df_matchups.empty:
        save_matchups_to_bigquery(client, df_matchups)

    elapsed = round(time.time() - start_time, 2)
    print(f"\nSimulation and BigQuery load completed successfully in {elapsed} seconds!")
    return df_probs, df_postseason, df_matchups


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Wide Right Regular Season & Full Postseason Simulation")
    parser.add_argument("--runs", type=int, default=10000, help="Number of Monte Carlo simulations (default: 10000)")
    parser.add_argument("--week", type=int, default=None, help="Specific completed week to simulate (default: auto)")
    parser.add_argument("--year", type=int, default=None, help="Specific season/year to simulate (default: current league year)")
    args = parser.parse_args()

    simulate_and_save(num_runs=args.runs, target_week=args.week, target_year=args.year)
