import streamlit as st

st.set_page_config(layout="wide", page_title="Wide Right 2026", page_icon="🏈")

# --- Custom Styling ---
st.markdown("""
<style>
    .toc-card {
        background: rgba(128, 128, 128, 0.05);
        border: 1px solid rgba(128, 128, 128, 0.18);
        border-radius: 14px;
        padding: 18px 20px;
        margin-bottom: 16px;
        transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
    }
    .toc-card:hover {
        transform: translateY(-2px);
        border-color: rgba(33, 150, 243, 0.45);
        box-shadow: 0 6px 20px rgba(0,0,0,0.12);
    }
    .toc-title {
        font-size: 1.15rem;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .toc-desc {
        font-size: 0.88rem;
        opacity: 0.82;
        line-height: 1.5;
        margin-bottom: 12px;
    }
    .badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        margin-bottom: 8px;
    }
    .badge-blue {
        background: rgba(33, 150, 243, 0.15);
        color: #64b5f6;
        border: 1px solid rgba(33, 150, 243, 0.35);
    }
    .badge-green {
        background: rgba(76, 175, 80, 0.15);
        color: #81c784;
        border: 1px solid rgba(76, 175, 80, 0.35);
    }
    .badge-gold {
        background: rgba(255, 193, 7, 0.15);
        color: #ffc107;
        border: 1px solid rgba(255, 193, 7, 0.35);
    }
    .badge-purple {
        background: rgba(156, 39, 176, 0.15);
        color: #ba68c8;
        border: 1px solid rgba(156, 39, 176, 0.35);
    }
</style>
""", unsafe_allow_html=True)

st.title("Welcome to Wide Right 2026!")
st.image(
    "https://s.yimg.com/ny/api/res/1.2/QJcrvuxEPZLQX4n3kjaa2g--/YXBwaWQ9aGlnaGxhbmRlcjt3PTI0MDA7aD0xNjI4O2NmPXdlYnA-/https://s.yimg.com/os/creatr-images/2019-02/9c91c250-2653-11e9-bfee-96db584edaa1",
    use_column_width=True
)
st.divider()

st.subheader("📖 League Hub & Table of Contents")
st.write("Navigate all league dashboards, simulation models, prize trackers, and roster management tools below:")

st.write("")

# --- Section 1: Season Race & Analytics ---
st.markdown("### 🏆 Season Race &amp; Performance Analytics")

c1, c2, c3 = st.columns(3, gap="medium")

with c1:
    st.markdown("""
    <div class="toc-card">
        <span class="badge badge-purple">MONTE CARLO MODEL</span>
        <div class="toc-title">🔮 Projected Standings</div>
        <div class="toc-desc">
            10,000 Monte Carlo schedule simulations, projected division finishes, playoff qualification odds, first-round bye favorites, and #1 draft pick odds.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/8_🔮_Projected_Standings.py", label="Open Projected Standings ➔", icon="🔮")

with c2:
    st.markdown("""
    <div class="toc-card">
        <span class="badge badge-gold">SCORING ANALYTICS</span>
        <div class="toc-title">🏅 Points Race</div>
        <div class="toc-desc">
            Cumulative regular season points leaderboard, weekly scoring distributions, median benchmark tracking, lineup efficiency coaches report, and honor roll.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/7_🏅_Points_Race.py", label="Open Points Race ➔", icon="🏅")

with c3:
    st.markdown("""
    <div class="toc-card">
        <span class="badge badge-green">PRIZE POOL &amp; CASH</span>
        <div class="toc-title">💵 Payouts</div>
        <div class="toc-desc">
            Season earnings leaderboard, weekly high score awards ($10 / $6 / $4), rolling Big Win pot tracker, regular season expected cash ($ EV), and prize rules.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/6_💵_Payouts.py", label="Open Payouts ➔", icon="💵")

st.write("")
st.divider()

# --- Section 2: Franchise & Contract Management ---
st.markdown("### 📋 Franchise &amp; Roster Management")

r1, r2, r3 = st.columns(3, gap="medium")

with r1:
    st.markdown("""
    <div class="toc-card">
        <span class="badge badge-blue">SALARY CAP</span>
        <div class="toc-title">🖊️ Active Roster Management</div>
        <div class="toc-desc">
            Live salary cap compliance tracker, contract years remaining, positional salary allocations, cap penalty projections, and cut simulator.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/2_🖊️_Active Roster Management.py", label="Open Roster Management ➔", icon="🖊️")

with r2:
    st.markdown("""
    <div class="toc-card">
        <span class="badge badge-green">CONTRACTS</span>
        <div class="toc-title">🆓 Free Extensions</div>
        <div class="toc-desc">
            Identify expiring contracts eligible for penalty-free multi-year extensions, evaluate extension candidates, and check submission deadlines.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/4_🆓_Free Extensions.py", label="Open Free Extensions ➔", icon="🆓")

with r3:
    st.markdown("""
    <div class="toc-card">
        <span class="badge badge-gold">DEVELOPMENT</span>
        <div class="toc-title">🚕 Taxi Claims</div>
        <div class="toc-desc">
            Taxi squad roster tracking, active poaching claim windows, player eligibility requirements, and draft pick compensation management.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/5_🚕_Taxi Claims.py", label="Open Taxi Claims ➔", icon="🚕")

st.write("")

r4, r5, _ = st.columns(3, gap="medium")

with r4:
    st.markdown("""
    <div class="toc-card">
        <span class="badge badge-purple">RULES &amp; VOTING</span>
        <div class="toc-title">🪧 Holdouts</div>
        <div class="toc-desc">
            Annual holdout candidate pool, voting status, contractual market adjustments, and league compliance requirements.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/3_🪧_Holdouts.py", label="Open Holdouts ➔", icon="🪧")

with r5:
    st.markdown("""
    <div class="toc-card">
        <span class="badge badge-blue">ASSET CAPITAL</span>
        <div class="toc-title">👶 Draft Picks</div>
        <div class="toc-desc">
            Full inventory of current and future rookie draft picks across all 12 franchises, draft board capital, and pick trade tracking.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/1_👶_Draft Picks.py", label="Open Draft Picks ➔", icon="👶")
