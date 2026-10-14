import sys
import os

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import functions
import global_vars

st.set_page_config(layout="wide", page_title="Wide Right - 2026 Points Race", page_icon="🏅")

# --- Custom Styling ---
st.markdown("""
<style>
    .metric-card {
        background: rgba(128, 128, 128, 0.05);
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        border: 1px solid rgba(128, 128, 128, 0.18);
        padding: 18px 20px;
        text-align: center;
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        border-color: rgba(255, 193, 7, 0.35);
    }
    .metric-val {
        font-size: 2.1rem;
        font-weight: 800;
        color: #ffc107;
        margin-top: 4px;
        margin-bottom: 2px;
    }
    .metric-lbl {
        font-size: 0.85rem;
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
    .podium-card {
        background: rgba(128, 128, 128, 0.05);
        border-radius: 16px;
        border: 1px solid rgba(128, 128, 128, 0.2);
        padding: 22px 18px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        transition: transform 0.25s ease;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .podium-card:hover {
        transform: translateY(-4px);
    }
    .gold-border {
        border-color: rgba(255, 215, 0, 0.6);
        background: linear-gradient(180deg, rgba(255, 215, 0, 0.12) 0%, rgba(128, 128, 128, 0.03) 100%);
    }
    .silver-border {
        border-color: rgba(192, 192, 192, 0.6);
        background: linear-gradient(180deg, rgba(192, 192, 192, 0.12) 0%, rgba(128, 128, 128, 0.03) 100%);
    }
    .bronze-border {
        border-color: rgba(205, 127, 50, 0.6);
        background: linear-gradient(180deg, rgba(205, 127, 50, 0.12) 0%, rgba(128, 128, 128, 0.03) 100%);
    }
    .honor-card {
        background: rgba(128, 128, 128, 0.04);
        border-radius: 14px;
        border: 1px solid rgba(128, 128, 128, 0.18);
        padding: 16px;
        margin-bottom: 12px;
        transition: transform 0.2s ease;
    }
    .honor-card:hover {
        transform: translateY(-2px);
        border-color: rgba(255, 193, 7, 0.3);
    }
    .delta-pos {
        color: #4caf50;
        font-weight: 700;
    }
    .delta-neg {
        color: #f44336;
        font-weight: 700;
    }
    .delta-neutral {
        color: #9e9e9e;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# --- Data Fetching ---
@st.cache_data(ttl=300)
def fetch_points_race_data():
    """Fetches all necessary datasets for the Points Race dashboard."""
    # 1. Week Information
    week_info = functions.bq_query("SELECT recent_completed_week, current_week FROM `mfl-374514.dbt_production.dim_current_week`")[0]
    recent_wk = int(week_info.get("recent_completed_week", 1))
    last_wk = max(1, recent_wk - 1)

    # 2. Franchises
    franchises = functions.bq_query("SELECT franchise_id, franchise_name, division, icon FROM `mfl-374514.dbt_production.dim_franchises`")
    franchises_df = pd.DataFrame(franchises)

    # 3. Standings (Official Total Points)
    standings = functions.bq_query("SELECT franchise_id, points_for, points_against, wins, losses FROM `mfl-374514.dbt_production.dim_standings`")
    standings_df = pd.DataFrame(standings)

    # 4. Weekly Game Results (Actual Score & Optimal Score)
    results_query = f"""
        SELECT 
            franchise_id,
            week,
            cast(score as float64) as score,
            result,
            cast(optimal_score as float64) as optimal_score
        FROM `mfl-374514.dbt_production.fct_results`
        WHERE week <= {recent_wk}
        ORDER BY week, score DESC
    """
    results = functions.bq_query(results_query)
    results_df = pd.DataFrame(results)

    # Determine Current Season Year
    cur_year = int(global_vars.league_year)

    # 5. Model Projections & Probability (Current & Previous Week for Current Year)
    model_query = f"""
        SELECT 
            curr.franchise_id,
            curr.top_pts as top_pts_prob,
            curr.proj_wins,
            prev.top_pts as prev_top_pts_prob
        FROM `mfl-374514.dbt_production.fct_reg_season_model` curr
        LEFT JOIN `mfl-374514.dbt_production.fct_reg_season_model` prev
          ON curr.franchise_id = prev.franchise_id 
          AND prev.year = curr.year
          AND prev.after_week = {last_wk}
        WHERE curr.year = {cur_year} AND curr.after_week = {recent_wk}
    """
    model = functions.bq_query(model_query)
    model_df = pd.DataFrame(model)

    # 6. Historical Simulation Weeks (for trends - only up to current completed week for Current Year)
    hist_model_query = f"""
        SELECT 
            m.after_week,
            m.franchise_id,
            m.top_pts as top_pts_prob,
            m.proj_wins
        FROM `mfl-374514.dbt_production.fct_reg_season_model` m
        WHERE m.year = {cur_year} AND m.after_week <= {recent_wk}
        ORDER BY m.after_week, m.top_pts DESC
    """
    hist_model = functions.bq_query(hist_model_query)
    hist_model_df = pd.DataFrame(hist_model)

    return recent_wk, last_wk, franchises_df, standings_df, results_df, model_df, hist_model_df


recent_wk, last_wk, franchises_df, standings_df, results_df, model_df, hist_model_df = fetch_points_race_data()

# --- Data Processing & Joins ---
# Merge Leaderboard DataFrame
leaderboard = standings_df.merge(franchises_df, on="franchise_id", how="left")
if not model_df.empty:
    leaderboard = leaderboard.merge(model_df, on="franchise_id", how="left")
else:
    leaderboard["top_pts_prob"] = 0.0
    leaderboard["prev_top_pts_prob"] = 0.0
    leaderboard["proj_wins"] = 0.0

leaderboard["top_pts_prob"] = leaderboard["top_pts_prob"].fillna(0.0)
leaderboard["prev_top_pts_prob"] = leaderboard["prev_top_pts_prob"].fillna(0.0)
leaderboard["points_for"] = pd.to_numeric(leaderboard["points_for"], errors="coerce").fillna(0.0)

# Calculate PPG, Points Behind Leader, and Probability Delta
max_pts = leaderboard["points_for"].max()
leaderboard["ppg"] = leaderboard["points_for"] / recent_wk
leaderboard["pts_back"] = max_pts - leaderboard["points_for"]
leaderboard["top_pts_pct"] = leaderboard["top_pts_prob"] * 100
leaderboard["prev_top_pts_pct"] = leaderboard["prev_top_pts_prob"] * 100
leaderboard["wow_delta"] = leaderboard["top_pts_pct"] - leaderboard["prev_top_pts_pct"]

# Efficiency Metrics from results_df
if not results_df.empty:
    results_df["score"] = pd.to_numeric(results_df["score"], errors="coerce").fillna(0.0)
    results_df["optimal_score"] = pd.to_numeric(results_df["optimal_score"], errors="coerce").fillna(results_df["score"])
    
    eff_agg = results_df.groupby("franchise_id").agg(
        total_actual=("score", "sum"),
        total_optimal=("optimal_score", "sum"),
        max_week_score=("score", "max"),
        min_week_score=("score", "min"),
        score_std=("score", "std")
    ).reset_index()
    
    eff_agg["efficiency_pct"] = (eff_agg["total_actual"] / eff_agg["total_optimal"].replace(0, np.nan)) * 100
    eff_agg["efficiency_pct"] = eff_agg["efficiency_pct"].fillna(100.0)
    eff_agg["bench_lost"] = eff_agg["total_optimal"] - eff_agg["total_actual"]
    
    leaderboard = leaderboard.merge(eff_agg, on="franchise_id", how="left")
else:
    leaderboard["efficiency_pct"] = 100.0
    leaderboard["bench_lost"] = 0.0
    leaderboard["max_week_score"] = leaderboard["points_for"]
    leaderboard["min_week_score"] = leaderboard["points_for"]
    leaderboard["score_std"] = 0.0

leaderboard = leaderboard.sort_values(by="points_for", ascending=False).reset_index(drop=True)
leaderboard["rank"] = leaderboard.index + 1


# --- Page Header ---
st.title("🏅 2026 Regular Season Points Race")
st.caption(f"Live total points standings, Monte Carlo Points Title probability model, weekly scoring breakdown, and lineup efficiency through Week {recent_wk}.")
st.divider()

# --- KPI Metric Ribbon ---
leader_row = leaderboard.iloc[0]
best_odds_row = leaderboard.sort_values(by="top_pts_pct", ascending=False).iloc[0]

# Single highest week score in league
if not results_df.empty:
    high_single_row = results_df.merge(franchises_df, on="franchise_id").sort_values(by="score", ascending=False).iloc[0]
    high_score_val = high_single_row["score"]
    high_score_team = high_single_row["franchise_name"]
    high_score_wk = int(high_single_row["week"])
else:
    high_score_val = 0.0
    high_score_team = "N/A"
    high_score_wk = 0

# Best Lineup Manager
best_eff_row = leaderboard.sort_values(by="efficiency_pct", ascending=False).iloc[0]

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-lbl">🏆 Current Points Leader</div>
        <div class="metric-val">{leader_row['points_for']:.2f}</div>
        <div class="metric-sub"><strong>{leader_row['franchise_name']}</strong> ({leader_row['ppg']:.1f} PPG)</div>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    wow_sym = "+" if best_odds_row['wow_delta'] > 0 else ""
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-lbl">🎯 Top Title Odds</div>
        <div class="metric-val">{best_odds_row['top_pts_pct']:.1f}%</div>
        <div class="metric-sub"><strong>{best_odds_row['franchise_name']}</strong> ({wow_sym}{best_odds_row['wow_delta']:.1f}% WoW)</div>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-lbl">🔥 Season-High Single Week</div>
        <div class="metric-val">{high_score_val:.2f}</div>
        <div class="metric-sub"><strong>{high_score_team}</strong> (Week {high_score_wk})</div>
    </div>
    """, unsafe_allow_html=True)

with kpi4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-lbl">⚡ Best Lineup Efficiency</div>
        <div class="metric-val">{best_eff_row['efficiency_pct']:.1f}%</div>
        <div class="metric-sub"><strong>{best_eff_row['franchise_name']}</strong> ({best_eff_row['bench_lost']:.1f} pts benched)</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")
st.write("")

# --- Section 1: Top 3 Points Title Contenders (Podium) ---
st.subheader("🏁 Points Title Contenders Podium", divider="rainbow")
st.write("Top 3 franchises with the highest simulated probability of winning the regular season Total Points title.")

odds_sorted = leaderboard.sort_values(by="top_pts_pct", ascending=False).reset_index(drop=True)
top3 = odds_sorted.head(3)

pod_col1, pod_col2, pod_col3 = st.columns(3)
borders = ["gold-border", "silver-border", "bronze-border"]
places = ["🥇 Favorite", "🥈 Contender", "🥉 Challenger"]

for idx, col in enumerate([pod_col1, pod_col2, pod_col3]):
    if idx < len(top3):
        team = top3.iloc[idx]
        delta_val = team['wow_delta']
        if delta_val > 0.05:
            delta_class = "delta-pos"
            delta_str = f"+{delta_val:.2f}% WoW"
        elif delta_val < -0.05:
            delta_class = "delta-neg"
            delta_str = f"{delta_val:.2f}% WoW"
        else:
            delta_class = "delta-neutral"
            delta_str = "Even WoW"

        behind_str = "Leader" if team['pts_back'] == 0 else f"-{team['pts_back']:.2f} pts"

        with col:
            st.markdown(f"""
            <div class="podium-card {borders[idx]}">
                <div>
                    <span style="font-size: 0.9rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px;">{places[idx]}</span>
                    <h3 style="margin-top: 6px; margin-bottom: 8px;">{team['franchise_name']}</h3>
                    <div style="font-size: 0.85rem; opacity: 0.7; margin-bottom: 12px;">Division: {team['division']}</div>
                    <img src="{team['icon']}" width="90" style="margin-bottom: 12px; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.2));" />
                </div>
                <div>
                    <div style="font-size: 0.8rem; text-transform: uppercase; opacity: 0.75; font-weight: 600;">Points Title Probability</div>
                    <div style="font-size: 2.2rem; font-weight: 800; color: #ffc107; line-height: 1.1;">{team['top_pts_pct']:.1f}%</div>
                    <div class="{delta_class}" style="font-size: 0.85rem; margin-top: 3px; margin-bottom: 12px;">{delta_str}</div>
                    <hr style="border: none; border-top: 1px solid rgba(128,128,128,0.2); margin: 10px 0;" />
                    <div style="display: flex; justify-content: space-around; font-size: 0.85rem;">
                        <div>
                            <div style="opacity: 0.7;">Current Total</div>
                            <div style="font-weight: 700; font-size: 1.05rem;">{team['points_for']:.2f}</div>
                        </div>
                        <div>
                            <div style="opacity: 0.7;">Points Behind</div>
                            <div style="font-weight: 700; font-size: 1.05rem;">{behind_str}</div>
                        </div>
                        <div>
                            <div style="opacity: 0.7;">Efficiency</div>
                            <div style="font-weight: 700; font-size: 1.05rem;">{team['efficiency_pct']:.1f}%</div>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

st.write("")
st.write("")

# --- Section 2: Full Leaderboard & Interactive Grid ---
st.subheader(f"📊 Complete Points Leaderboard (After Week {recent_wk})", divider=True)

display_df = leaderboard[[
    "rank", "franchise_name", "top_pts_pct", "wow_delta", "points_for", "ppg", "pts_back",
    "efficiency_pct", "bench_lost", "max_week_score"
]].copy()

display_df.columns = [
    "Rank", "Franchise", "Title Odds %", "WoW Delta %", "Total Points", "PPG", "Pts Behind",
    "Efficiency %", "Bench Lost", "Season High"
]

st.dataframe(
    display_df,
    hide_index=True,
    use_container_width=True,
    column_config={
        "Rank": st.column_config.NumberColumn("Rank", format="%d"),
        "Franchise": "Franchise",
        "Title Odds %": st.column_config.ProgressColumn(
            "Title Odds %",
            help="Probability of finishing #1 in total points",
            format="%.2f%%",
            min_value=0,
            max_value=100,
        ),
        "WoW Delta %": st.column_config.NumberColumn("WoW Delta %", format="%+.2f%%"),
        "Total Points": st.column_config.NumberColumn("Total Points", format="%.2f"),
        "PPG": st.column_config.NumberColumn("PPG", format="%.2f"),
        "Pts Behind": st.column_config.NumberColumn("Pts Behind", format="%.2f"),
        "Efficiency %": st.column_config.NumberColumn("Efficiency %", format="%.1f%%"),
        "Bench Lost": st.column_config.NumberColumn("Bench Lost", format="%.2f"),
        "Season High": st.column_config.NumberColumn("Season High", format="%.2f"),
    }
)

st.write("")
st.write("")

# --- Section 3: Interactive Visualizations ---
st.subheader("📈 Points Trajectory & Scoring Analytics", divider=True)

tab_traj, tab_dist, tab_hist_odds, tab_honor = st.tabs([
    "📈 Cumulative Trajectory", 
    "📊 Weekly Scoring & Median", 
    "🔮 Model Probability Momentum",
    "🏆 Weekly High Score Honor Roll"
])

# TAB 1: Cumulative Trajectory
with tab_traj:
    st.write("Track how the points margin has evolved week-by-week across all 12 franchises:")
    if not results_df.empty:
        # Build cumulative dataframe
        cum_df = results_df.merge(franchises_df[["franchise_id", "franchise_name"]], on="franchise_id")
        cum_df = cum_df.sort_values(by=["franchise_name", "week"])
        cum_df["cum_points"] = cum_df.groupby("franchise_name")["score"].cumsum()

        fig_traj = px.line(
            cum_df,
            x="week",
            y="cum_points",
            color="franchise_name",
            markers=True,
            title="Cumulative Points Race (Weeks 1 to Present)",
            labels={"week": "Week Number", "cum_points": "Total Points For", "franchise_name": "Franchise"}
        )
        fig_traj.update_layout(
            hovermode="x unified",
            xaxis=dict(dtick=1, title="NFL Week"),
            yaxis=dict(title="Cumulative Points"),
            legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5),
            margin=dict(l=20, r=20, t=40, b=110),
            height=520
        )
        st.plotly_chart(fig_traj, use_container_width=True)

# TAB 2: Weekly Scoring Breakdown & League Median Line
with tab_dist:
    st.write("Weekly scores for each team against the weekly league median & league average:")
    if not results_df.empty:
        merged_res = results_df.merge(franchises_df[["franchise_id", "franchise_name"]], on="franchise_id")
        
        # Calculate weekly average and median
        weekly_summary = merged_res.groupby("week")["score"].agg(["mean", "median"]).reset_index()

        fig_bar = px.bar(
            merged_res,
            x="week",
            y="score",
            color="franchise_name",
            barmode="group",
            title="Weekly Scores by Team with League Median Line",
            labels={"week": "NFL Week", "score": "Points Scored", "franchise_name": "Franchise"}
        )
        # Add Median line
        fig_bar.add_trace(
            go.Scatter(
                x=weekly_summary["week"],
                y=weekly_summary["median"],
                mode="lines+markers",
                name="League Median",
                line=dict(color="#ff9800", width=3, dash="dash"),
                marker=dict(size=8)
            )
        )
        # Add Average line
        fig_bar.add_trace(
            go.Scatter(
                x=weekly_summary["week"],
                y=weekly_summary["mean"],
                mode="lines+markers",
                name="League Average",
                line=dict(color="#03a9f4", width=3, dash="dot"),
                marker=dict(size=8)
            )
        )
        fig_bar.update_layout(
            xaxis=dict(dtick=1, title="NFL Week"),
            yaxis=dict(title="Weekly Score"),
            legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5),
            margin=dict(l=20, r=20, t=40, b=110),
            height=540
        )
        st.plotly_chart(fig_bar, use_container_width=True)

# TAB 3: Model Probability Momentum
with tab_hist_odds:
    st.write("Compare simulated Points Title probability shifts across model weeks:")
    if not hist_model_df.empty and len(hist_model_df["after_week"].unique()) > 1:
        merged_hist = hist_model_df.merge(franchises_df[["franchise_id", "franchise_name"]], on="franchise_id")
        merged_hist["top_pts_pct"] = merged_hist["top_pts_prob"] * 100

        fig_odds_trend = px.line(
            merged_hist,
            x="after_week",
            y="top_pts_pct",
            color="franchise_name",
            markers=True,
            title="Simulated Points Title Probability Evolution",
            labels={"after_week": "Completed Week", "top_pts_pct": "Title Probability (%)", "franchise_name": "Franchise"}
        )
        fig_odds_trend.update_layout(
            xaxis=dict(dtick=1, title="Simulation After Completed Week"),
            yaxis=dict(title="Probability (%)", range=[0, 100]),
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5),
            margin=dict(l=20, r=20, t=40, b=100),
            height=500
        )
        st.plotly_chart(fig_odds_trend, use_container_width=True)
    else:
        st.info("Historical probability tracking will populate across multiple weeks as simulations are run each Tuesday.")

# TAB 4: Weekly High Score Honor Roll
with tab_honor:
    st.write("Weekly high scorers and top performances for every completed week:")
    if not results_df.empty:
        honor_df = results_df.merge(franchises_df, on="franchise_id")
        weeks_list = sorted(honor_df["week"].unique(), reverse=True)
        
        h_cols = st.columns(min(len(weeks_list), 5))
        for i, wk in enumerate(weeks_list[:5]):
            wk_data = honor_df[honor_df["week"] == wk].sort_values(by="score", ascending=False)
            top_scorer = wk_data.iloc[0]
            runner_up = wk_data.iloc[1]
            diff = top_scorer["score"] - runner_up["score"]
            
            with h_cols[i]:
                st.markdown(f"""
                <div class="honor-card">
                    <div style="font-size: 0.8rem; text-transform: uppercase; font-weight: 700; color: #ffc107;">Week {wk} Champion</div>
                    <img src="{top_scorer['icon']}" width="65" style="margin: 8px 0;" />
                    <div style="font-weight: 700; font-size: 1rem;">{top_scorer['franchise_name']}</div>
                    <div style="font-size: 1.6rem; font-weight: 800; color: #4caf50; margin: 4px 0;">{top_scorer['score']:.2f}</div>
                    <div style="font-size: 0.75rem; opacity: 0.7;">Optimal: {top_scorer['optimal_score']:.2f}</div>
                    <div style="font-size: 0.75rem; opacity: 0.7; margin-top: 4px;">+{diff:.2f} pts over {runner_up['franchise_name']}</div>
                </div>
                """, unsafe_allow_html=True)

st.write("")
st.write("")

# --- Section 4: Lineup Efficiency & Coach's Report ---
st.subheader("⚡ Lineup Efficiency & Coach's Report", divider=True)
st.write("Measures how effectively each manager started their optimal possible lineup versus leaving points on the bench.")

eff_sorted = leaderboard.sort_values(by="efficiency_pct", ascending=True)

# Custom labels displaying team and coaching efficiency %
y_labels = [f"<b>{name}</b>  ({eff:.1f}%)" for name, eff in zip(eff_sorted["franchise_name"], eff_sorted["efficiency_pct"])]
outside_labels = [f"  {eff:.1f}% Eff  (-{bench:.1f} benched)" for eff, bench in zip(eff_sorted["efficiency_pct"], eff_sorted["bench_lost"])]

fig_eff = go.Figure()
fig_eff.add_trace(go.Bar(
    y=y_labels,
    x=eff_sorted["points_for"],
    name="Actual Points Started",
    orientation="h",
    marker=dict(color="#4caf50"),
    text=[f"{pts:.1f}" for pts in eff_sorted["points_for"]],
    textposition="inside",
    textfont=dict(color="white", size=11),
    insidetextanchor="middle",
    hovertemplate="<b>%{y}</b><br>Actual Started: <b>%{x:.2f} pts</b><extra></extra>"
))
fig_eff.add_trace(go.Bar(
    y=y_labels,
    x=eff_sorted["bench_lost"],
    name="Points Left on Bench",
    orientation="h",
    marker=dict(color="rgba(244, 67, 54, 0.75)"),
    text=outside_labels,
    textposition="outside",
    textfont=dict(size=11),
    cliponaxis=False,
    hovertemplate="<b>%{y}</b><br>Points on Bench: <b>+%{x:.2f} pts</b><extra></extra>"
))

max_potential = (eff_sorted["points_for"] + eff_sorted["bench_lost"]).max()
fig_eff.update_layout(
    barmode="stack",
    title="Lineup Efficiency: Actual Points Started vs. Benched Potential (Ranked by Coaching Rating %)",
    xaxis=dict(title="Fantasy Points", range=[0, max_potential * 1.2]),
    yaxis=dict(title=""),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=20, r=40, t=50, b=50),
    height=540
)
st.plotly_chart(fig_eff, use_container_width=True)

st.write("")
st.write("")

# --- Section 5: Team Deep-Dive Drilldown ---
st.subheader("🔍 Franchise Deep-Dive Profile", divider=True)
st.write("Inspect detailed weekly score progression, consistency, and lineup efficiency for any team:")

team_names = sorted(leaderboard["franchise_name"].unique())
selected_team_name = st.selectbox("Select Franchise to Analyze:", team_names, index=0)

if selected_team_name:
    team_data = leaderboard[leaderboard["franchise_name"] == selected_team_name].iloc[0]
    team_id = team_data["franchise_id"]
    
    # Header Banner
    banner_c1, banner_c2, banner_c3, banner_c4, banner_c5 = st.columns([1, 2, 1, 1, 1])
    with banner_c1:
        st.image(team_data["icon"], width=100)
    with banner_c2:
        st.markdown(f"### {team_data['franchise_name']}")
        st.caption(f"Division: **{team_data['division']}** | Current Points Rank: **#{team_data['rank']}**")
    with banner_c3:
        st.metric("Total Points", f"{team_data['points_for']:.2f}", f"#{team_data['rank']} in League")
    with banner_c4:
        st.metric("Title Odds", f"{team_data['top_pts_pct']:.2f}%", f"{'+' if team_data['wow_delta'] > 0 else ''}{team_data['wow_delta']:.2f}% WoW")
    with banner_c5:
        st.metric("Efficiency", f"{team_data['efficiency_pct']:.1f}%", f"{team_data['bench_lost']:.1f} benched")
    
    # Weekly breakdown for selected team
    if not results_df.empty:
        team_weekly = results_df[results_df["franchise_id"] == team_id].sort_values(by="week")
        
        tw_col1, tw_col2 = st.columns([3, 2], gap="large")
        
        with tw_col1:
            fig_team = go.Figure()
            fig_team.add_trace(go.Bar(
                x=team_weekly["week"],
                y=team_weekly["score"],
                name="Actual Score",
                marker=dict(color="#2196f3")
            ))
            fig_team.add_trace(go.Bar(
                x=team_weekly["week"],
                y=team_weekly["optimal_score"],
                name="Optimal Possible",
                marker=dict(color="#ff9800", opacity=0.6)
            ))
            fig_team.update_layout(
                barmode="group",
                title=f"{selected_team_name} - Actual vs Optimal Score by Week",
                xaxis=dict(dtick=1, title="NFL Week"),
                yaxis=dict(title="Points"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=20, r=20, t=50, b=50),
                height=390
            )
            st.plotly_chart(fig_team, use_container_width=True)
            
        with tw_col2:
            st.markdown("#### 📋 Performance Consistency")
            tw_summary = pd.DataFrame({
                "Metric": ["Average Weekly Score", "Season High Score", "Season Low Score", "Score Volatility (Std Dev)", "Avg Bench Pts Lost/Wk"],
                "Value": [
                    f"{team_data['ppg']:.2f} pts",
                    f"{team_data['max_week_score']:.2f} pts",
                    f"{team_data['min_week_score']:.2f} pts",
                    f"{team_data['score_std']:.2f} pts",
                    f"{team_data['bench_lost'] / recent_wk:.2f} pts"
                ]
            })
            st.dataframe(tw_summary, hide_index=True, use_container_width=True, height=230)
