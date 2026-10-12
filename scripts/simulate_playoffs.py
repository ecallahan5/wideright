"""
Monte Carlo Regular Season & Playoff Odds Simulation for Wide Right Fantasy Football.
Simulates remaining weekly matchups based on historical scoring distributions blended with
MFL optimal roster projected scores (capturing bye weeks, injuries, and talent changes).
Incorporates Head-to-Head and League Median scoring (2 matchups per week),
applies league tiebreakers, and calculates playoff odds, projected wins, and draft pick probabilities.
Writes output directly to BigQuery native table: `mfl-374514.external.reg_season_sims`.
"""

import argparse
import datetime
import os
import time
from functools import cmp_to_key
import numpy as np
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import dlt

from dlt_scripts.common import fetch_mfl_data


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


def get_simulation_inputs(client, target_week=None):
    """Fetch standings, schedule, scores, and franchises from BigQuery."""
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

    # 4. Weekly Scores
    scores_data = bq_query(
        client,
        f"""
        SELECT franchise_id, CAST(score AS FLOAT64) as score, week 
        FROM `mfl-374514.dbt_production.fct_results` 
        WHERE week <= {recent_completed_wk}
        """
    )
    scores_df = pd.DataFrame(scores_data)
    
    # Calculate Mean & Std Dev per team
    team_means = scores_df.groupby("franchise_id")["score"].mean().to_dict()
    team_stds = scores_df.groupby("franchise_id")["score"].std().fillna(15.0).to_dict()
    
    # League fallback
    league_mean = scores_df["score"].mean() if len(scores_df) > 0 else 100.0
    league_std = scores_df["score"].std() if len(scores_df) > 0 else 15.0

    means_arr = np.array([team_means.get(t, league_mean) for t in team_ids])
    stds_arr = np.array([team_stds.get(t, league_std) for t in team_ids])

    # 5. Schedule
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
        WHERE home.is_home = '1' AND away.is_home = '0'
        ORDER BY wk, home.matchup_num
        """
    )

    future_weeks = sorted(list(set(g["wk"] for g in sched_data if g["wk"] >= current_wk)))
    weekly_roster_projs = get_projected_team_scores(client, future_weeks, team_ids)

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
    }


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
        delta_wk = wk - current_wk
        if delta_wk == 0:
            w_proj = 0.70  # Upcoming week: 70% projected starting lineup, 30% history
        elif delta_wk == 1:
            w_proj = 0.60
        elif delta_wk == 2:
            w_proj = 0.50
        else:
            w_proj = 0.40  # Distant weeks: 40% projected starting lineup, 60% history

        wk_projs = weekly_roster_projs.get(wk, {})
        effective_means = means_arr.copy()
        if wk_projs:
            proj_means = np.array([wk_projs.get(t, means_arr[i]) for i, t in enumerate(team_ids)])
            effective_means = (w_proj * proj_means) + ((1.0 - w_proj) * means_arr)

        home_means = effective_means[home_indices]
        home_stds = stds_arr[home_indices]
        away_means = effective_means[away_indices]
        away_stds = stds_arr[away_indices]

        # Simulate scores for all matchups in this week
        home_scores = np.random.normal(home_means, home_stds, size=(num_runs, n_matchups))
        away_scores = np.random.normal(away_means, away_stds, size=(num_runs, n_matchups))

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

    def compare_teams(r, t1, t2):
        """Returns 1 if t1 ranks ahead of t2, -1 if t2 ranks ahead of t1."""
        if sim_wins[r, t1] != sim_wins[r, t2]:
            return 1 if sim_wins[r, t1] > sim_wins[r, t2] else -1
        # Head-to-Head
        if sim_h2h[r, t1, t2] > sim_h2h[r, t2, t1]:
            return 1
        elif sim_h2h[r, t2, t1] > sim_h2h[r, t1, t2]:
            return -1
        # Total Regular Season Points
        if sim_points[r, t1] > sim_points[r, t2]:
            return 1
        elif sim_points[r, t1] < sim_points[r, t2]:
            return -1
        # Division Record
        if sim_div_wins[r, t1] > sim_div_wins[r, t2]:
            return 1
        return -1

    for r in range(num_runs):
        # Points Champion
        best_pts_team = int(np.argmax(sim_points[r]))
        top_pts_cnt[best_pts_team] += 1

        # 1. Division Winners (1 per division)
        div_winners = []
        for div_name, div_teams in div_indices.items():
            div_sorted = sorted(div_teams, key=cmp_to_key(lambda a, b: compare_teams(r, b, a)))
            div_winners.append(div_sorted[0])

        # Rank the 3 division winners
        div_winners_sorted = sorted(div_winners, key=cmp_to_key(lambda a, b: compare_teams(r, b, a)))
        s1 = div_winners_sorted[0]
        s2 = div_winners_sorted[1]
        s3 = div_winners_sorted[2]

        one_seed_cnt[s1] += 1
        two_seed_cnt[s2] += 1
        div_win_cnt[s1] += 1
        div_win_cnt[s2] += 1
        div_win_cnt[s3] += 1

        # 2. Wild Cards (top 3 non-division winners)
        non_div_teams = [t for t in range(n_teams) if t not in div_winners]
        wc_sorted = sorted(non_div_teams, key=cmp_to_key(lambda a, b: compare_teams(r, b, a)))
        wc1, wc2, wc3 = wc_sorted[0], wc_sorted[1], wc_sorted[2]

        wc_cnt[wc1] += 1
        wc_cnt[wc2] += 1
        wc_cnt[wc3] += 1

        for t in [s1, s2, s3, wc1, wc2, wc3]:
            playoff_cnt[t] += 1

        # 3. First Draft Pick (worst overall team)
        worst_team = sorted(range(n_teams), key=cmp_to_key(lambda a, b: compare_teams(r, a, b)))[0]
        pick_cnt[worst_team] += 1

    # 5. Aggregate Probabilities
    proj_wins = sim_wins.mean(axis=0)

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
            "after_week": inputs["recent_completed_wk"],
        })

    df_probs = pd.DataFrame(rows)
    return df_probs


def save_to_bigquery(client, df_probs, table_id="mfl-374514.external.reg_season_sims"):
    """Atomically replaces probabilities for the completed week in BigQuery."""
    week = int(df_probs["after_week"].iloc[0])
    print(f"Saving simulation results for after_week {week} to BigQuery table: {table_id}...")

    # 1. Delete existing rows for this week (idempotent)
    delete_sql = f"DELETE FROM `{table_id}` WHERE after_week = {week}"
    client.query(delete_sql).result()
    print(f"Deleted any existing records for after_week = {week}.")

    # 2. Insert new records
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
        ],
    )
    job = client.load_table_from_dataframe(df_probs, table_id, job_config=job_config)
    job.result()
    print(f"Successfully inserted {len(df_probs)} rows into {table_id} for week {week}!")


def simulate_and_save(num_runs=10000, target_week=None):
    """Main entrypoint to run simulation and save results directly to BigQuery."""
    start_time = time.time()
    print(f"[{datetime.datetime.now()}] Starting Wide Right Playoff Odds Model ({num_runs:,} runs with Roster Projections & Median Scoring)...")

    client = get_bq_client()
    inputs = get_simulation_inputs(client, target_week=target_week)
    print(f"Loaded league data: After Week {inputs['recent_completed_wk']}, Next Week {inputs['current_wk']}.")

    # Display upcoming week's roster projections
    current_wk = inputs["current_wk"]
    wk_projs = inputs.get("weekly_roster_projs", {}).get(current_wk, {})
    if wk_projs:
        team_names = inputs["team_names"]
        print(f"\n--- Week {current_wk} Optimal Roster Projections ---")
        sorted_projs = sorted(wk_projs.items(), key=lambda x: x[1], reverse=True)
        for fid, score in sorted_projs:
            print(f"  {team_names.get(fid, fid):<26} {score:>6.1f} pts")

    df_probs = run_simulation(inputs, num_runs=num_runs)

    # Format summary display
    team_names = inputs["team_names"]
    display_df = df_probs.copy()
    display_df["Team"] = display_df["franchise_id"].map(team_names)
    display_df = display_df.sort_values(by="make_playoffs", ascending=False)
    cols = ["Team", "proj_wins", "make_playoffs", "win_division", "bye", "one_seed", "top_pts", "first_pick"]
    print("\n--- Simulation Summary (28-Game Median Model + Roster Projections) ---")
    print(display_df[cols].to_string(index=False))

    save_to_bigquery(client, df_probs)

    elapsed = round(time.time() - start_time, 2)
    print(f"\nSimulation and BigQuery load completed successfully in {elapsed} seconds!")
    return df_probs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Wide Right Playoff Odds Simulation (Median Scoring + Roster Projections)")
    parser.add_argument("--runs", type=int, default=10000, help="Number of Monte Carlo simulations (default: 10000)")
    parser.add_argument("--week", type=int, default=None, help="Specific completed week to simulate (default: auto)")
    args = parser.parse_args()

    simulate_and_save(num_runs=args.runs, target_week=args.week)
