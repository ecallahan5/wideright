"""
Shared mathematical clinch, elimination, and regular-season award utilities
for the Wide Right Fantasy Football League (12 teams, 3 divisions, 14 regular-season weeks,
28-game format: 1 H2H + 1 Top-6 League Median game per week).
"""

from itertools import combinations


REG_SEASON_WEEKS = 14
DIVISION_TITLE_PAYOUT = 50
WILD_CARD_PAYOUT = 30
POINTS_TITLE_PAYOUT = 60
CHAMPION_PAYOUT = 275
RUNNER_UP_PAYOUT = 135
THIRD_PLACE_PAYOUT = 60


def build_h2h_and_standings_from_schedule(team_ids, div_map, sched_rows, up_to_week):
    """
    Processes regular-season schedule rows (week <= 14) up through `up_to_week`.

    Each row in `sched_rows` should contain:
        week, franchise_id, opp_id, team_score, opp_score

    Returns a dict with:
        past_h2h: {t1: {t2: wins}}
        rem_h2h: {t1: {t2: remaining_games}}
        past_div_wins: {t: div_h2h_wins}
        w_rem: int (number of remaining regular-season weeks after `up_to_week`)
        hist_wins: {t: wins} reconstructed from schedule + median through `up_to_week`
        hist_losses: {t: losses} reconstructed through `up_to_week`
        hist_pf: {t: points_for} reconstructed through `up_to_week`
    """
    past_h2h = {t1: {t2: 0 for t2 in team_ids} for t1 in team_ids}
    rem_h2h = {t1: {t2: 0 for t2 in team_ids} for t1 in team_ids}
    past_div_wins = {t: 0 for t in team_ids}
    hist_wins = {t: 0 for t in team_ids}
    hist_losses = {t: 0 for t in team_ids}
    hist_pf = {t: 0.0 for t in team_ids}

    reg_rows = [r for r in (sched_rows or []) if int(r["week"]) <= REG_SEASON_WEEKS]
    if not reg_rows:
        return {
            "past_h2h": past_h2h,
            "rem_h2h": rem_h2h,
            "past_div_wins": past_div_wins,
            "w_rem": max(0, REG_SEASON_WEEKS - int(up_to_week)),
            "hist_wins": hist_wins,
            "hist_losses": hist_losses,
            "hist_pf": hist_pf,
        }

    reg_weeks = sorted({int(r["week"]) for r in reg_rows})
    rem_weeks = [w for w in reg_weeks if w > up_to_week]
    w_rem = len(rem_weeks)

    rows_by_past_week = {}
    for row in reg_rows:
        wk = int(row["week"])
        f_id = row["franchise_id"]
        o_id = row["opp_id"]
        if f_id not in past_h2h or o_id not in past_h2h:
            continue
        t_score = float(row.get("team_score") or 0.0)
        o_score = float(row.get("opp_score") or 0.0)

        if wk <= up_to_week:
            if t_score > o_score:
                past_h2h[f_id][o_id] += 1
                if div_map.get(f_id) == div_map.get(o_id):
                    past_div_wins[f_id] += 1
            rows_by_past_week.setdefault(wk, []).append((f_id, o_id, t_score, o_score))
        else:
            rem_h2h[f_id][o_id] += 1

    # Reconstruct H2H + Top-6 League Median wins/losses/PF for completed weeks <= up_to_week
    for wk in sorted(rows_by_past_week.keys()):
        wk_entries = rows_by_past_week[wk]
        wk_scores = {f_id: t_score for f_id, _, t_score, _ in wk_entries}
        sorted_teams = sorted(wk_scores.keys(), key=lambda tid: wk_scores[tid], reverse=True)
        top6 = set(sorted_teams[:6])
        for f_id, _, sc, osc in wk_entries:
            hist_pf[f_id] += sc
            if sc > osc:
                hist_wins[f_id] += 1
            elif sc < osc:
                hist_losses[f_id] += 1
            if f_id in top6:
                hist_wins[f_id] += 1
            else:
                hist_losses[f_id] += 1

    return {
        "past_h2h": past_h2h,
        "rem_h2h": rem_h2h,
        "past_div_wins": past_div_wins,
        "w_rem": w_rem,
        "hist_wins": hist_wins,
        "hist_losses": hist_losses,
        "hist_pf": hist_pf,
    }


def compute_clinch_status(
    team_ids,
    div_map,
    wins_map,
    pf_map,
    past_h2h,
    rem_h2h,
    past_div_wins,
    w_rem,
):
    """
    Computes exact mathematical clinch & elimination tags ([Z], [Y], [X], [E]) and
    regular-season prize lock flags accounting for 28-game H2H + Top-6 League Median rules.

    Returns a dict keyed by franchise_id with:
        tag: 'Z' | 'Y' | 'X' | 'E' | ''
        label: str
        clinched_bye: bool
        clinched_div: bool
        clinched_playoffs: bool
        clinched_wc: bool
        can_win_div: bool
        is_points_title: bool
    """
    team_ids = sorted(team_ids)
    all_divs = sorted({div_map[t] for t in team_ids})
    div_teams_map = {d: [t for t in team_ids if div_map[t] == d] for d in all_divs}

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
        min_med = max(0, k - 6) * w_rem
        return internal_games + min_med

    def can_subset_all_reach(target_team, subset_ids):
        """Returns True if every team in subset_ids can simultaneously finish ahead of or tied with target_team's floor."""
        target_floor = wins_map[target_team]
        needs = {}
        for j in subset_ids:
            max_j = wins_map[j] + 2 * w_rem
            if max_j < target_floor:
                return False
            if len(subset_ids) == 1 and max_j == target_floor:
                if past_h2h[target_team][j] > past_h2h[j][target_team] + rem_h2h[target_team][j]:
                    return False
            needs[j] = max(0, target_floor - wins_map[j])

        sub_list = list(subset_ids)
        for r_len in range(1, len(sub_list) + 1):
            for comb in combinations(sub_list, r_len):
                if sum(needs[x] for x in comb) > max_group_wins_possible(comb):
                    return False
        return True

    def resolve_final_tie_group(tied_teams):
        """Resolves a group of teams tied on final wins: H2H (sweep/round-robin %) -> Points For -> Division Wins."""
        if len(tied_teams) <= 1:
            return list(tied_teams)

        if len(tied_teams) == 2:
            a, b = tied_teams[0], tied_teams[1]
            if past_h2h[a][b] != past_h2h[b][a]:
                return [a, b] if past_h2h[a][b] > past_h2h[b][a] else [b, a]
            return sorted(tied_teams, key=lambda t: (pf_map[t], past_div_wins[t]), reverse=True)

        h2h_pct = {}
        valid_round_robin = True
        for a in tied_teams:
            w = sum(past_h2h[a][b] for b in tied_teams if b != a)
            l = sum(past_h2h[b][a] for b in tied_teams if b != a)
            if w + l == 0:
                valid_round_robin = False
                break
            h2h_pct[a] = round(w / (w + l), 6)

        if valid_round_robin and len(set(h2h_pct.values())) > 1:
            ordered = []
            for pct in sorted(set(h2h_pct.values()), reverse=True):
                sub_group = [t for t in tied_teams if h2h_pct[t] == pct]
                if len(sub_group) == 1:
                    ordered.extend(sub_group)
                else:
                    ordered.extend(resolve_final_tie_group(sub_group))
            return ordered

        return sorted(tied_teams, key=lambda t: (pf_map[t], past_div_wins[t]), reverse=True)

    def rank_final_teams(teams):
        """Exact league tiebreaker when w_rem == 0: Wins -> H2H -> Points For -> Division Wins."""
        win_buckets = {}
        for t in teams:
            win_buckets.setdefault(wins_map[t], []).append(t)

        ranked = []
        for w in sorted(win_buckets.keys(), reverse=True):
            ranked.extend(resolve_final_tie_group(win_buckets[w]))
        return ranked

    status = {}

    if w_rem == 0:
        div_winners = []
        for d, d_teams in div_teams_map.items():
            d_sorted = rank_final_teams(d_teams)
            div_winners.append(d_sorted[0])
        div_winners_sorted = rank_final_teams(div_winners)
        bye_ids = set(div_winners_sorted[:2])
        div_win_ids = set(div_winners_sorted)
        non_div = [t for t in team_ids if t not in div_win_ids]
        wc_sorted = rank_final_teams(non_div)
        wc_ids = set(wc_sorted[:3])

        max_pf = max((pf_map[t] for t in team_ids), default=0.0)
        pts_win_ids = {t for t in team_ids if abs(pf_map[t] - max_pf) < 1e-6 and max_pf > 0}

        for tid in team_ids:
            is_bye = tid in bye_ids
            is_div = tid in div_win_ids
            is_wc = tid in wc_ids
            is_pts = tid in pts_win_ids
            if is_bye:
                tag, label = "Z", "Clinched First-Round Bye"
            elif is_div:
                tag, label = "Y", "Clinched Division Title"
            elif is_wc:
                tag, label = "X", "Clinched Playoff Berth"
            else:
                tag, label = "E", "Eliminated from Playoffs"
            status[tid] = {
                "tag": tag,
                "label": label,
                "clinched_bye": is_bye,
                "clinched_div": is_div,
                "clinched_playoffs": is_div or is_wc,
                "clinched_wc": is_wc,
                "can_win_div": is_div,
                "is_points_title": is_pts,
            }
        return status

    # Pass 1: Compute clinched_div for all teams first (needed for airtight Wild Card lock checks)
    clinched_div_map = {}
    for tid in team_ids:
        my_div = div_map[tid]
        own_rivals = [t for t in div_teams_map[my_div] if t != tid]
        clinched_div_map[tid] = not any(can_subset_all_reach(tid, [r]) for r in own_rivals)

    # Pass 2: Compute Bye, Playoff Berth, Wild Card Lock, and Elimination
    for tid in team_ids:
        my_div = div_map[tid]
        own_rivals = [t for t in div_teams_map[my_div] if t != tid]
        other_divs = [d for d in all_divs if d != my_div]

        clinched_div = clinched_div_map[tid]

        # Clinched First-Round Bye [Z]
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

        # Clinched Playoffs [X]: either clinched division OR no valid scenario allows
        # 1 own-division winner + 3 non-division-winner Wild Cards (requiring a division winner
        # ahead of any Wild Card from another division) to simultaneously reach tid's win floor.
        clinched_playoffs = clinched_div
        if not clinched_playoffs:
            can_miss_playoffs = False
            reachable = [t for t in team_ids if t != tid and can_subset_all_reach(tid, [t])]
            reachable_by_div = {d: [t for t in div_teams_map[d] if t in reachable] for d in all_divs}
            reachable_own = reachable_by_div[my_div]

            # A team from another division can only be a Wild Card ahead of tid if at least 2 teams
            # from that division can reach tid's floor (1 to win the division + 1+ as Wild Card).
            wc_eligible = [
                t for t in reachable
                if div_map[t] == my_div or len(reachable_by_div[div_map[t]]) >= 2
            ]

            for own_w in reachable_own:
                wc_pool = [t for t in wc_eligible if t != own_w]
                if len(wc_pool) < 3:
                    continue
                for wc_comb in combinations(wc_pool, 3):
                    extra_div_choices = []
                    feasible_divs = True
                    for od in other_divs:
                        wc_in_od = [t for t in wc_comb if div_map[t] == od]
                        if wc_in_od:
                            cands = [t for t in reachable_by_div[od] if t not in wc_in_od]
                            if not cands:
                                feasible_divs = False
                                break
                            extra_div_choices.append(cands)
                    if not feasible_divs:
                        continue

                    if not extra_div_choices:
                        if can_subset_all_reach(tid, [own_w, *wc_comb]):
                            can_miss_playoffs = True
                            break
                    elif len(extra_div_choices) == 1:
                        for dw1 in extra_div_choices[0]:
                            if can_subset_all_reach(tid, [own_w, *wc_comb, dw1]):
                                can_miss_playoffs = True
                                break
                        if can_miss_playoffs:
                            break
                    else:
                        for dw1 in extra_div_choices[0]:
                            for dw2 in extra_div_choices[1]:
                                if can_subset_all_reach(tid, [own_w, *wc_comb, dw1, dw2]):
                                    can_miss_playoffs = True
                                    break
                            if can_miss_playoffs:
                                break
                        if can_miss_playoffs:
                            break
                if can_miss_playoffs:
                    break
            clinched_playoffs = not can_miss_playoffs

        # Elimination checks
        max_tid_wins = wins_map[tid] + 2 * w_rem

        # Strict division-elimination check (never false-negatives on 3-way circular H2H ties)
        rival_clinched_div = any(clinched_div_map[r] for r in own_rivals)
        can_win_div_strict = not rival_clinched_div
        if can_win_div_strict:
            for r in own_rivals:
                if wins_map[r] > max_tid_wins:
                    can_win_div_strict = False
                    break
        if can_win_div_strict:
            for r_len in range(2, len(own_rivals) + 1):
                for comb in combinations(own_rivals, r_len):
                    if all(max_tid_wins >= wins_map[x] for x in comb):
                        max_allowed = sum(max_tid_wins - wins_map[x] for x in comb)
                        if min_group_wins_guaranteed(comb) > max_allowed:
                            can_win_div_strict = False
                            break
                if not can_win_div_strict:
                    break

        # Standard division check (includes 1-on-1 H2H check for [E] tag display)
        can_win_div = can_win_div_strict
        if can_win_div:
            for r in own_rivals:
                if wins_map[r] == max_tid_wins and past_h2h[r][tid] > past_h2h[tid][r] + rem_h2h[tid][r]:
                    can_win_div = False
                    break

        # Wild Card elimination check
        can_win_wc = True
        non_leaders_above = 0
        for d, d_teams in div_teams_map.items():
            rivals_in_d = [t for t in d_teams if t != tid]
            above_in_d = [
                t for t in rivals_in_d
                if wins_map[t] > max_tid_wins
                or (wins_map[t] == max_tid_wins and past_h2h[t][tid] > past_h2h[tid][t] + rem_h2h[tid][t])
            ]
            non_leaders_above += max(0, len(above_in_d) - 1)
        if non_leaders_above >= 3:
            can_win_wc = False

        # Mathematically locked into a Wild Card spot (cannot miss playoffs AND cannot win division)
        clinched_wc = clinched_playoffs and (not clinched_div) and (not can_win_div_strict)

        if clinched_bye:
            tag, label = "Z", "Clinched First-Round Bye"
        elif clinched_div:
            tag, label = "Y", "Clinched Division Title"
        elif clinched_playoffs:
            tag, label = "X", "Clinched Playoff Berth"
        elif not can_win_div and not can_win_wc:
            tag, label = "E", "Eliminated from Playoffs"
        else:
            tag, label = "", ""

        status[tid] = {
            "tag": tag,
            "label": label,
            "clinched_bye": clinched_bye,
            "clinched_div": clinched_div,
            "clinched_playoffs": clinched_playoffs,
            "clinched_wc": clinched_wc,
            "can_win_div": can_win_div,
            "is_points_title": False,
        }

    return status


def compute_clinched_reg_season_awards(
    franchises_records,
    standings_records,
    sched_records,
    recent_completed_wk,
):
    """
    Determines all mathematically clinched regular-season cash awards as of `recent_completed_wk`:
      - Division Titles ($50 each, up to 3)
      - Locked Wild Card Berths ($30 each, up to 3) — awarded once a team has clinched playoffs
        AND is mathematically eliminated from winning its division (or at Week 14 conclusion)
      - Regular Season Points Title ($60) — awarded upon completion of Week 14

    Also walks back completed weeks to identify the exact week each division/WC clinch occurred.
    """
    reg_completed_wk = min(int(recent_completed_wk or 0), REG_SEASON_WEEKS)
    empty_result = {
        "events": [],
        "clinch_status": {},
        "clinched_divisions": {},
        "clinched_wild_cards": [],
        "clinched_points_title": [],
        "w_rem": max(0, REG_SEASON_WEEKS - reg_completed_wk),
        "reg_completed_wk": reg_completed_wk,
    }

    if reg_completed_wk <= 0 or not franchises_records or not standings_records:
        return empty_result

    team_ids = sorted([f["franchise_id"] for f in franchises_records])
    name_map = {f["franchise_id"]: f["franchise_name"] for f in franchises_records}
    div_map = {f["franchise_id"]: f["division"] for f in franchises_records}
    icon_map = {f["franchise_id"]: f.get("icon", "") for f in franchises_records}

    wins_map = {t: 0 for t in team_ids}
    pf_map = {t: 0.0 for t in team_ids}
    for s in standings_records:
        tid = s["franchise_id"]
        if tid in wins_map:
            wins_map[tid] = int(s.get("wins") or 0)
            pf_map[tid] = float(s.get("points_for") or 0.0)

    sched_state = build_h2h_and_standings_from_schedule(
        team_ids, div_map, sched_records, reg_completed_wk
    )
    w_rem = sched_state["w_rem"]

    # If past Week 14 (playoffs underway) and standings include anything beyond Week 14,
    # fall back to reconstructed 14-week regular-season standings when available.
    if int(recent_completed_wk or 0) > REG_SEASON_WEEKS and sched_records:
        if any(sched_state["hist_wins"].values()):
            wins_map = sched_state["hist_wins"]
            pf_map = sched_state["hist_pf"]

    current_status = compute_clinch_status(
        team_ids=team_ids,
        div_map=div_map,
        wins_map=wins_map,
        pf_map=pf_map,
        past_h2h=sched_state["past_h2h"],
        rem_h2h=sched_state["rem_h2h"],
        past_div_wins=sched_state["past_div_wins"],
        w_rem=w_rem,
    )

    # Cache historical clinch statuses on demand when walking back to find clinch week
    hist_status_cache = {}

    def get_hist_status(wk):
        if wk not in hist_status_cache:
            st_wk = build_h2h_and_standings_from_schedule(team_ids, div_map, sched_records, wk)
            hist_status_cache[wk] = compute_clinch_status(
                team_ids=team_ids,
                div_map=div_map,
                wins_map=st_wk["hist_wins"],
                pf_map=st_wk["hist_pf"],
                past_h2h=st_wk["past_h2h"],
                rem_h2h=st_wk["rem_h2h"],
                past_div_wins=st_wk["past_div_wins"],
                w_rem=st_wk["w_rem"],
            )
        return hist_status_cache[wk]

    def find_clinch_week(tid, field):
        if not sched_records:
            return reg_completed_wk
        clinch_wk = reg_completed_wk
        for wk in range(reg_completed_wk - 1, 0, -1):
            wk_status = get_hist_status(wk)
            if wk_status.get(tid, {}).get(field, False):
                clinch_wk = wk
            else:
                break
        return clinch_wk

    events = []
    clinched_divisions = {}
    clinched_wild_cards = []
    clinched_points_title = []

    # 1. Clinched Division Titles ($50 each)
    for tid in team_ids:
        if current_status[tid]["clinched_div"]:
            clinch_wk = find_clinch_week(tid, "clinched_div")
            div_name = div_map[tid]
            if w_rem == 0 and clinch_wk == REG_SEASON_WEEKS:
                desc = f"Won {div_name} Division Title (${DIVISION_TITLE_PAYOUT})"
            else:
                desc = f"Clinched {div_name} Division Title in Week {clinch_wk} (${DIVISION_TITLE_PAYOUT})"
            clinched_divisions[div_name] = {
                "franchise_id": tid,
                "franchise_name": name_map[tid],
                "clinch_wk": clinch_wk,
                "payout": DIVISION_TITLE_PAYOUT,
            }
            events.append({
                "week": clinch_wk,
                "event_type": "Division Title",
                "category": "season",
                "franchise_id": tid,
                "franchise_name": name_map[tid],
                "icon": icon_map[tid],
                "score": None,
                "payout": DIVISION_TITLE_PAYOUT,
                "description": desc,
            })

    # 2. Clinched Wild Card Berths ($30 each)
    for tid in team_ids:
        if current_status[tid]["clinched_wc"]:
            clinch_wk = find_clinch_week(tid, "clinched_wc")
            if w_rem == 0 and clinch_wk == REG_SEASON_WEEKS:
                desc = f"Won Wild Card Playoff Berth (${WILD_CARD_PAYOUT})"
            else:
                desc = f"Clinched Wild Card Playoff Berth in Week {clinch_wk} (${WILD_CARD_PAYOUT})"
            clinched_wild_cards.append({
                "franchise_id": tid,
                "franchise_name": name_map[tid],
                "clinch_wk": clinch_wk,
                "payout": WILD_CARD_PAYOUT,
            })
            events.append({
                "week": clinch_wk,
                "event_type": "Wild Card",
                "category": "season",
                "franchise_id": tid,
                "franchise_name": name_map[tid],
                "icon": icon_map[tid],
                "score": None,
                "payout": WILD_CARD_PAYOUT,
                "description": desc,
            })

    # 3. Regular Season Points Title ($60, only finalized when Week 14 is complete)
    if w_rem == 0:
        pts_winners = [tid for tid in team_ids if current_status[tid]["is_points_title"]]
        if pts_winners:
            share = POINTS_TITLE_PAYOUT / len(pts_winners)
            payout_val = int(share) if share == int(share) else round(share, 2)
            for tid in pts_winners:
                tie_note = " (Split Tie)" if len(pts_winners) > 1 else ""
                clinched_points_title.append({
                    "franchise_id": tid,
                    "franchise_name": name_map[tid],
                    "points_for": pf_map[tid],
                    "payout": payout_val,
                })
                events.append({
                    "week": REG_SEASON_WEEKS,
                    "event_type": "Points Title",
                    "category": "season",
                    "franchise_id": tid,
                    "franchise_name": name_map[tid],
                    "icon": icon_map[tid],
                    "score": pf_map[tid],
                    "payout": payout_val,
                    "description": f"Regular Season Points Champion{tie_note}: {pf_map[tid]:.2f} pts (${payout_val})",
                })

    return {
        "events": events,
        "clinch_status": current_status,
        "clinched_divisions": clinched_divisions,
        "clinched_wild_cards": clinched_wild_cards,
        "clinched_points_title": clinched_points_title,
        "w_rem": w_rem,
        "reg_completed_wk": reg_completed_wk,
    }


def rank_regular_season_seeds(team_ids, div_map, wins_map, pf_map, past_h2h, past_div_wins):
    """
    Computes exact 12-team regular-season final seeding using league tiebreakers:
      Wins -> H2H (2-way or multi-team round-robin) -> Points For -> Division Wins.

    Returns:
      championship_seeds: {1: tid, 2: tid, ..., 6: tid}
        (#1-#3 are the 3 division winners ranked best-to-worst; #4-#6 are top 3 Wild Cards)
      consolation_seeds: {1: tid, 2: tid, ..., 6: tid}
        (the 6 non-playoff teams ranked best-to-worst: #7 overall = Consolation #1, ..., #12 = #6)
    """
    team_ids = sorted(team_ids)
    all_divs = sorted({div_map[t] for t in team_ids})
    div_teams_map = {d: [t for t in team_ids if div_map[t] == d] for d in all_divs}

    def resolve_tie(tied_teams):
        if len(tied_teams) <= 1:
            return list(tied_teams)
        if len(tied_teams) == 2:
            a, b = tied_teams[0], tied_teams[1]
            if past_h2h[a][b] != past_h2h[b][a]:
                return [a, b] if past_h2h[a][b] > past_h2h[b][a] else [b, a]
            return sorted(tied_teams, key=lambda t: (pf_map[t], past_div_wins[t]), reverse=True)

        h2h_pct = {}
        valid_rr = True
        for a in tied_teams:
            w = sum(past_h2h[a][b] for b in tied_teams if b != a)
            l = sum(past_h2h[b][a] for b in tied_teams if b != a)
            if w + l == 0:
                valid_rr = False
                break
            h2h_pct[a] = round(w / (w + l), 6)

        if valid_rr and len(set(h2h_pct.values())) > 1:
            ordered = []
            for pct in sorted(set(h2h_pct.values()), reverse=True):
                sub = [t for t in tied_teams if h2h_pct[t] == pct]
                ordered.extend(sub if len(sub) == 1 else resolve_tie(sub))
            return ordered

        return sorted(tied_teams, key=lambda t: (pf_map[t], past_div_wins[t]), reverse=True)

    def rank_group(teams):
        buckets = {}
        for t in teams:
            buckets.setdefault(wins_map[t], []).append(t)
        ranked = []
        for w in sorted(buckets.keys(), reverse=True):
            ranked.extend(resolve_tie(buckets[w]))
        return ranked

    div_winners = [rank_group(div_teams_map[d])[0] for d in all_divs]
    div_winners_sorted = rank_group(div_winners)
    div_win_set = set(div_winners_sorted)

    non_div_sorted = rank_group([t for t in team_ids if t not in div_win_set])
    wc_teams = non_div_sorted[:3]
    cons_teams = non_div_sorted[3:9]

    champ_ordered = div_winners_sorted + wc_teams
    return {
        "championship_seeds": {idx + 1: tid for idx, tid in enumerate(champ_ordered)},
        "consolation_seeds": {idx + 1: tid for idx, tid in enumerate(cons_teams)},
    }


def reseed_semifinals(seed1_id, seed2_id, wc1_winner_id, wc1_winner_seed, wc2_winner_id, wc2_winner_seed):
    """
    Reseeds Wild Card winners by actual playoff seed number (not franchise_id):
      - #1 plays the higher seed number (lowest-ranked survivor)
      - #2 plays the lower seed number (highest-ranked survivor)
    Returns [(1, seed1_id, sf1_opp_seed, sf1_opp_id), (2, seed2_id, sf2_opp_seed, sf2_opp_id)].
    """
    if wc1_winner_seed > wc2_winner_seed:
        sf1_opp_seed, sf1_opp_id = wc1_winner_seed, wc1_winner_id
        sf2_opp_seed, sf2_opp_id = wc2_winner_seed, wc2_winner_id
    else:
        sf1_opp_seed, sf1_opp_id = wc2_winner_seed, wc2_winner_id
        sf2_opp_seed, sf2_opp_id = wc1_winner_seed, wc1_winner_id

    return [
        (1, seed1_id, sf1_opp_seed, sf1_opp_id),
        (2, seed2_id, sf2_opp_seed, sf2_opp_id),
    ]


def _extract_valid_fid(val):
    """Returns normalized franchise_id string if valid (non-empty, not placeholder), else None."""
    if val is None:
        return None
    s = str(val).strip()
    if not s or s.lower() in ("none", "null", "tbd", "0000"):
        return None
    return s


def resolve_live_bracket_state(
    seeds_map,
    week_scores_by_wk,
    recent_completed_wk,
    api_bracket=None,
    third_place_api_bracket=None,
    include_third_place=True,
):
    """
    Resolves the live 6-team reseeded playoff bracket state (Weeks 15, 16, 17).
    Prefers official team assignments from `api_bracket` (e.g. wideright.app/api/v1/playoffs)
    when present, and fills/advances from `seeds_map` + `week_scores_by_wk` as fallback.

    Returns a dict with:
      seeds: {1: tid, ..., 6: tid}
      seed_by_tid: {tid: seed}
      games: dict keyed by ('Wild Card', 1), ('Wild Card', 2), ('Semifinals', 1),
             ('Semifinals', 2), ('Finals', 1), and optionally ('3rd Place', 1).
             Each game has: week, round_name, game_num, high_seed, high_franchise_id,
             low_seed, low_franchise_id, high_actual_pts, low_actual_pts,
             winner_franchise_id, loser_franchise_id, is_complete.
    """
    api_games = (api_bracket or {}).get("games", []) if isinstance(api_bracket, dict) else []
    tp_api_games = (third_place_api_bracket or {}).get("games", []) if isinstance(third_place_api_bracket, dict) else []

    # Build authoritative 1..6 seed mapping (prefer explicit MFL playoffBracket seeds when populated)
    resolved_seeds = dict(seeds_map or {})
    explicit_mfl_seeds = {}
    for g in api_games:
        for fid_k, sd_k in [("home_franchise_id", "home_seed"), ("away_franchise_id", "away_seed")]:
            fid = _extract_valid_fid(g.get(fid_k))
            sd = g.get(sd_k)
            if fid and sd is not None:
                explicit_mfl_seeds[int(sd)] = fid
    if len(explicit_mfl_seeds) == 6:
        resolved_seeds = explicit_mfl_seeds
    elif len(api_games) >= 4:
        api_s1 = _extract_valid_fid(api_games[2].get("home_franchise_id"))
        api_s2 = _extract_valid_fid(api_games[3].get("home_franchise_id"))
        api_wc1_h = _extract_valid_fid(api_games[0].get("home_franchise_id"))
        api_wc1_a = _extract_valid_fid(api_games[0].get("away_franchise_id"))
        api_wc2_h = _extract_valid_fid(api_games[1].get("home_franchise_id"))
        api_wc2_a = _extract_valid_fid(api_games[1].get("away_franchise_id"))
        if all([api_s1, api_s2, api_wc1_h, api_wc1_a, api_wc2_h, api_wc2_a]):
            existing_seed_of = {tid: sd for sd, tid in resolved_seeds.items()}
            wc1_pair = sorted([api_wc1_h, api_wc1_a], key=lambda t: existing_seed_of.get(t, 99))
            wc2_pair = sorted([api_wc2_h, api_wc2_a], key=lambda t: existing_seed_of.get(t, 99))
            resolved_seeds = {
                1: api_s1,
                2: api_s2,
                3: api_wc1_h if existing_seed_of.get(api_wc1_h, 3) <= existing_seed_of.get(api_wc1_a, 6) else wc1_pair[0],
                6: api_wc1_a if existing_seed_of.get(api_wc1_h, 3) <= existing_seed_of.get(api_wc1_a, 6) else wc1_pair[1],
                4: api_wc2_h if existing_seed_of.get(api_wc2_h, 4) <= existing_seed_of.get(api_wc2_a, 5) else wc2_pair[0],
                5: api_wc2_a if existing_seed_of.get(api_wc2_h, 4) <= existing_seed_of.get(api_wc2_a, 5) else wc2_pair[1],
            }

    seed_by_tid = {tid: sd for sd, tid in resolved_seeds.items() if tid}

    def build_game(week, round_name, game_num, high_id, low_id):
        h_id = _extract_valid_fid(high_id)
        l_id = _extract_valid_fid(low_id)
        h_seed = seed_by_tid.get(h_id)
        l_seed = seed_by_tid.get(l_id)
        # Ensure high_seed is the better (smaller) seed number when both known
        if h_id and l_id and h_seed is not None and l_seed is not None and h_seed > l_seed:
            h_id, l_id = l_id, h_id
            h_seed, l_seed = l_seed, h_seed

        wk_scores = week_scores_by_wk.get(week, {})
        h_pts = wk_scores.get(h_id) if h_id else None
        l_pts = wk_scores.get(l_id) if l_id else None
        is_complete = (
            recent_completed_wk >= week
            and h_id is not None
            and l_id is not None
            and h_pts is not None
            and l_pts is not None
        )
        winner_id = None
        loser_id = None
        if is_complete:
            # Higher seed wins exact tiebreaker if scores ever tie
            if float(h_pts) >= float(l_pts):
                winner_id, loser_id = h_id, l_id
            else:
                winner_id, loser_id = l_id, h_id

        return {
            "week": week,
            "round_name": round_name,
            "game_num": game_num,
            "high_seed": h_seed,
            "high_franchise_id": h_id,
            "low_seed": l_seed,
            "low_franchise_id": l_id,
            "high_actual_pts": float(h_pts) if is_complete else None,
            "low_actual_pts": float(l_pts) if is_complete else None,
            "winner_franchise_id": winner_id,
            "loser_franchise_id": loser_id,
            "is_complete": is_complete,
        }

    games = {}

    # Week 15: Wild Card (#3 vs #6, #4 vs #5)
    wc1_h = _extract_valid_fid(api_games[0].get("home_franchise_id")) if len(api_games) > 0 else resolved_seeds.get(3)
    wc1_a = _extract_valid_fid(api_games[0].get("away_franchise_id")) if len(api_games) > 0 else resolved_seeds.get(6)
    wc2_h = _extract_valid_fid(api_games[1].get("home_franchise_id")) if len(api_games) > 1 else resolved_seeds.get(4)
    wc2_a = _extract_valid_fid(api_games[1].get("away_franchise_id")) if len(api_games) > 1 else resolved_seeds.get(5)

    games[("Wild Card", 1)] = build_game(15, "Wild Card", 1, wc1_h or resolved_seeds.get(3), wc1_a or resolved_seeds.get(6))
    games[("Wild Card", 2)] = build_game(15, "Wild Card", 2, wc2_h or resolved_seeds.get(4), wc2_a or resolved_seeds.get(5))

    # Week 16: Semifinals (Reseeded after Wild Card)
    sf1_h = (_extract_valid_fid(api_games[2].get("home_franchise_id")) if len(api_games) > 2 else None) or resolved_seeds.get(1)
    sf2_h = (_extract_valid_fid(api_games[3].get("home_franchise_id")) if len(api_games) > 3 else None) or resolved_seeds.get(2)
    sf1_a = _extract_valid_fid(api_games[2].get("away_franchise_id")) if len(api_games) > 2 else None
    sf2_a = _extract_valid_fid(api_games[3].get("away_franchise_id")) if len(api_games) > 3 else None

    if (not sf1_a or not sf2_a) and games[("Wild Card", 1)]["is_complete"] and games[("Wild Card", 2)]["is_complete"]:
        w1 = games[("Wild Card", 1)]["winner_franchise_id"]
        w2 = games[("Wild Card", 2)]["winner_franchise_id"]
        reseeded = reseed_semifinals(sf1_h, sf2_h, w1, seed_by_tid.get(w1, 3), w2, seed_by_tid.get(w2, 4))
        sf1_a = sf1_a or reseeded[0][3]
        sf2_a = sf2_a or reseeded[1][3]

    games[("Semifinals", 1)] = build_game(16, "Semifinals", 1, sf1_h, sf1_a)
    games[("Semifinals", 2)] = build_game(16, "Semifinals", 2, sf2_h, sf2_a)

    # Week 17: Finals & 3rd Place
    fin_h = _extract_valid_fid(api_games[4].get("home_franchise_id")) if len(api_games) > 4 else None
    fin_a = _extract_valid_fid(api_games[4].get("away_franchise_id")) if len(api_games) > 4 else None
    if (not fin_h or not fin_a) and games[("Semifinals", 1)]["is_complete"] and games[("Semifinals", 2)]["is_complete"]:
        fin_h = fin_h or games[("Semifinals", 1)]["winner_franchise_id"]
        fin_a = fin_a or games[("Semifinals", 2)]["winner_franchise_id"]

    games[("Finals", 1)] = build_game(17, "Finals", 1, fin_h, fin_a)

    if include_third_place:
        tp_h = _extract_valid_fid(tp_api_games[0].get("home_franchise_id")) if len(tp_api_games) > 0 else None
        tp_a = _extract_valid_fid(tp_api_games[0].get("away_franchise_id")) if len(tp_api_games) > 0 else None
        if (not tp_h or not tp_a) and games[("Semifinals", 1)]["is_complete"] and games[("Semifinals", 2)]["is_complete"]:
            tp_h = tp_h or games[("Semifinals", 1)]["loser_franchise_id"]
            tp_a = tp_a or games[("Semifinals", 2)]["loser_franchise_id"]
        games[("3rd Place", 1)] = build_game(17, "3rd Place", 1, tp_h, tp_a)

    return {
        "seeds": resolved_seeds,
        "seed_by_tid": seed_by_tid,
        "games": games,
    }
