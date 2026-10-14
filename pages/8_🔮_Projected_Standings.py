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

model_df = fetch_projected_standings_data()

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

sim_data = model_df[model_df["after_week"] == selected_wk].copy()
sim_data = sim_data.sort_values(by="proj_wins", ascending=False).reset_index(drop=True)

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
        <div class="metric-sub">{one_seed_fav['franchise_name']} ({one_seed_fav['proj_wins']:.1f} Proj W)</div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-lbl">Most Projected Wins</div>
        <div class="metric-val" style="color: #2196F3; font-size: 1.8rem;">{top_team['proj_wins']:.1f}W</div>
        <div class="metric-sub">{top_team['franchise_name']} ({top_team['wins']}-{top_team['losses']} Current)</div>
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
        <div class="metric-sub">{first_pick_fav['franchise_name']} (Favored for Pick 1.01)</div>
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
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <h4 style="margin: 0;">{div_name} Division</h4>
                <span class="badge badge-purple">4 Franchises</span>
            </div>
        """, unsafe_allow_html=True)

        for _, team_row in div_df.iterrows():
            icon_tag = f'<img src="{team_row["icon"]}" width="32" style="vertical-align: middle; border-radius: 50%; margin-right: 10px;">' if team_row["icon"] else '🏈 '
            rk = team_row["div_rank"]
            rk_ordinal = "1st" if rk == 1 else ("2nd" if rk == 2 else ("3rd" if rk == 3 else "4th"))
            rk_badge = "badge-gold" if rk == 1 else ("badge-silver" if rk == 2 else "badge-bronze")
            
            st.markdown(f"""
            <div class="prob-card" style="margin-bottom: 10px; padding: 12px 14px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="display: flex; align-items: center;">
                        <span class="badge {rk_badge}" style="margin-right: 8px;">{rk_ordinal}</span>
                        {icon_tag}
                        <div>
                            <strong style="font-size: 0.95rem;">{team_row['franchise_name']}</strong>
                            <div style="font-size: 0.8rem; opacity: 0.7;">{team_row['wins']}-{team_row['losses']} &bull; {team_row['points_for']:.1f} PF</div>
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 1.15rem; font-weight: 800; color: #ba68c8;">{team_row['proj_wins']:.1f}W</div>
                        <div style="font-size: 0.75rem; opacity: 0.75;">Div Champ: <strong>{team_row['win_division']*100:.1f}%</strong></div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

places_lookup = pd.DataFrame(places_df)

st.write("")
st.write("")

# --- Section 2: Complete League Standings & Playoff Probability Grid ---
st.subheader("📊 League-Wide Projections & Postseason Probabilities", divider="blue")

col_grid, col_chart = st.columns([1.1, 0.9], gap="large")

with col_grid:
    st.markdown("#### Projected Regular Season Table")
    
    tbl_df = sim_data[[
        "franchise_name", "division", "wins", "losses", "points_for", "proj_wins",
        "make_playoffs", "win_division", "wild_card", "bye", "one_seed", "first_pick"
    ]].copy()
    
    tbl_df["Record"] = tbl_df["wins"].astype(str) + "-" + tbl_df["losses"].astype(str)
    tbl_df["make_playoffs"] = tbl_df["make_playoffs"] * 100
    tbl_df["win_division"] = tbl_df["win_division"] * 100
    tbl_df["wild_card"] = tbl_df["wild_card"] * 100
    tbl_df["bye"] = tbl_df["bye"] * 100
    tbl_df["one_seed"] = tbl_df["one_seed"] * 100
    tbl_df["first_pick"] = tbl_df["first_pick"] * 100

    tbl_df = tbl_df[[
        "franchise_name", "division", "Record", "points_for", "proj_wins",
        "make_playoffs", "win_division", "wild_card", "bye", "one_seed", "first_pick"
    ]]
    tbl_df.columns = [
        "Franchise", "Division", "Record", "Current PF", "Proj Wins",
        "Playoff %", "Div Champ %", "Wild Card %", "Bye %", "#1 Seed %", "#1 Pick %"
    ]

    st.dataframe(
        tbl_df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Franchise": "Franchise",
            "Division": "Division",
            "Record": "Record",
            "Current PF": st.column_config.NumberColumn("Points For", format="%.1f"),
            "Proj Wins": st.column_config.NumberColumn("Proj Wins", format="%.1f"),
            "Playoff %": st.column_config.ProgressColumn("Playoffs %", format="%.1f%%", min_value=0, max_value=100),
            "Div Champ %": st.column_config.ProgressColumn("Div %", format="%.1f%%", min_value=0, max_value=100),
            "Wild Card %": st.column_config.ProgressColumn("WC %", format="%.1f%%", min_value=0, max_value=100),
            "Bye %": st.column_config.ProgressColumn("Bye %", format="%.1f%%", min_value=0, max_value=100),
            "#1 Seed %": st.column_config.ProgressColumn("Top Seed %", format="%.1f%%", min_value=0, max_value=100),
            "#1 Pick %": st.column_config.ProgressColumn("#1 Pick %", format="%.1f%%", min_value=0, max_value=100),
        }
    )

with col_chart:
    st.markdown("#### Projected Wins by Franchise")
    chart_df = sim_data.sort_values(by="proj_wins", ascending=True).copy()
    
    fig_wins = px.bar(
        chart_df,
        x="proj_wins",
        y="franchise_name",
        color="division",
        orientation="h",
        labels={"proj_wins": "Projected Wins", "franchise_name": "Franchise", "division": "Division"},
        color_discrete_map={
            "Left Upright": "#42A5F5",
            "Crossbar": "#FFB74D",
            "Right Upright": "#66BB6A"
        },
        text="proj_wins"
    )
    fig_wins.update_traces(texttemplate="%{x:.1f}W", textposition="outside", cliponaxis=False)
    fig_wins.update_layout(
        margin=dict(l=0, r=40, t=10, b=10),
        height=400,
        xaxis=dict(title="Projected Regular Season Wins", range=[0, 24]),
        yaxis=dict(title=""),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_wins, use_container_width=True)

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
    
    # Retrieve projected division rank
    team_rank_row = places_lookup[places_lookup["franchise_name"] == selected_team]
    if not team_rank_row.empty:
        p_rank = team_rank_row.iloc[0]["div_rank"]
        p_rank_ord = "1st" if p_rank == 1 else ("2nd" if p_rank == 2 else ("3rd" if p_rank == 3 else "4th"))
    else:
        p_rank_ord = "-"

    t_col1, t_col2 = st.columns([0.3, 0.7], gap="large")
    
    with t_col1:
        icon_html = f'<img src="{team_data["icon"]}" width="85" style="margin-bottom: 8px;">' if team_data["icon"] else '🏈'
        st.markdown(f"""
        <div class="podium-card" style="text-align: center; padding: 22px;">
            <div>{icon_html}</div>
            <h3 style="margin: 6px 0 2px 0;">{team_data['franchise_name']}</h3>
            <div style="font-size: 0.9rem; opacity: 0.75;">{team_data['division']} Division</div>
            <div style="font-size: 0.88rem; margin-top: 8px;">Current Record: <strong>{team_data['wins']}-{team_data['losses']}</strong> ({team_data['points_for']:.2f} PF)</div>
            <hr style="margin: 12px 0; border: none; border-top: 1px solid rgba(128,128,128,0.2);" />
            <div style="font-size: 0.85rem; opacity: 0.8;">Projected Division Finish:</div>
            <div class="metric-val" style="font-size: 2.2rem; margin: 4px 0;">{p_rank_ord} Place</div>
            <div style="font-size: 0.85rem; opacity: 0.75;">Projected: <strong>{team_data['proj_wins']:.1f} Wins</strong></div>
        </div>
        """, unsafe_allow_html=True)

    with t_col2:
        st.markdown("#### Monte Carlo Probability Matrix")
        
        r1_1, r1_2, r1_3, r1_4 = st.columns(4)
        with r1_1:
            st.metric("Make Playoffs", f"{team_data['make_playoffs']*100:.1f}%")
        with r1_2:
            st.metric("Win Division", f"{team_data['win_division']*100:.1f}%")
        with r1_3:
            st.metric("Wild Card Seed", f"{team_data['wild_card']*100:.1f}%")
        with r1_4:
            st.metric("Points Title", f"{team_data['top_pts']*100:.1f}%")

        st.write("")
        r2_1, r2_2, r2_3, r2_4 = st.columns(4)
        with r2_1:
            st.metric("#1 Overall Seed", f"{team_data['one_seed']*100:.1f}%")
        with r2_2:
            st.metric("First-Round Bye", f"{team_data['bye']*100:.1f}%")
        with r2_3:
            st.metric("Projected Wins", f"{team_data['proj_wins']:.1f}")
        with r2_4:
            st.metric("#1 Overall Pick", f"{team_data['first_pick']*100:.1f}%")

        st.write("")
        # Contextual summary banner
        playoff_pct = team_data['make_playoffs'] * 100
        if playoff_pct >= 90:
            status_text = f"🔥 <strong>Playoff Lock / Heavy Contender:</strong> {team_data['franchise_name']} is virtually guaranteed a playoff spot ({playoff_pct:.1f}%). Primary battle is for a first-round bye ({team_data['bye']*100:.1f}%) and the #1 seed."
            status_color = "rgba(76, 175, 80, 0.15)"
            status_border = "#4CAF50"
        elif playoff_pct >= 40:
            status_text = f"⚔️ <strong>Playoff Bubble Battle:</strong> {team_data['franchise_name']} has a {playoff_pct:.1f}% probability of securing a postseason ticket, primarily contending for a Wild Card spot ({team_data['wild_card']*100:.1f}%)."
            status_color = "rgba(255, 193, 7, 0.15)"
            status_border = "#FFC107"
        else:
            status_text = f"🎯 <strong>Uphill Climb / Draft Focus:</strong> {team_data['franchise_name']} sits at {playoff_pct:.1f}% playoff odds and holds a {team_data['first_pick']*100:.1f}% chance at the #1 overall pick in the next rookie draft."
            status_color = "rgba(233, 30, 99, 0.15)"
            status_border = "#e91e63"

        st.markdown(f"""
        <div style="background: {status_color}; border-left: 4px solid {status_border}; padding: 12px 16px; border-radius: 8px; margin-top: 14px; font-size: 0.9rem;">
            {status_text}
        </div>
        """, unsafe_allow_html=True)
