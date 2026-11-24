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
