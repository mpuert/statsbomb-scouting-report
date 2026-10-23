"""Build a one-team scouting report from StatsBomb open data.

Reads every match the team played in one competition/season, extracts the
report data (all spatial values converted to meters), writes it as JSON that
follows the Data Contract in report_spec.md, and inserts it into the approved
template (template/template.html). The template itself is never modified.

Usage:
    python build/build_report.py --team "Manchester United" --competition 2 --season 27
"""
import argparse
import json
import math
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "open-data" / "data"
TEMPLATE = ROOT / "template" / "template.html"
OUT_DIR = ROOT / "reports"

YD = 0.9144                      # 1 StatsBomb unit = 1 yard
L_YD, W_YD = 120.0, 80.0
COLS, ROWS = 6, 4
BUILDUP_PATTERNS = {"Regular Play", "From Goal Kick", "From Keeper", "From Kick Off"}
ON_TARGET = {"Saved", "Saved To Post", "Saved Off Target"}
TECHNIQUES = {"Inswinging", "Outswinging", "Straight"}
ABBR = {
    "Goalkeeper": "GK", "Right Back": "RB", "Right Center Back": "RCB", "Center Back": "CB", "Left Center Back": "LCB",
    "Left Back": "LB", "Right Wing Back": "RWB", "Left Wing Back": "LWB", "Right Defensive Midfield": "RDM",
    "Center Defensive Midfield": "CDM", "Left Defensive Midfield": "LDM", "Right Midfield": "RM",
    "Right Center Midfield": "RCM", "Center Midfield": "CM", "Left Center Midfield": "LCM", "Left Midfield": "LM",
    "Right Wing": "RW", "Right Attacking Midfield": "RAM", "Center Attacking Midfield": "CAM",
    "Left Attacking Midfield": "LAM", "Left Wing": "LW", "Right Center Forward": "RCF", "Center Forward": "CF",
    "Left Center Forward": "LCF", "Secondary Striker": "SS",
}


def m(v):
    return round(v * YD, 1)


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def clock(e):
    return f"{e['minute']:02d}:{e['second']:02d}"


def mmss_to_min(s):
    mm, ss = s.split(":")
    return int(mm) + int(ss) / 60


def ts_seconds(ts):
    h, mi, s = ts.split(":")
    return int(h) * 3600 + int(mi) * 60 + float(s)


def pos_group(position):
    if position == "Goalkeeper":
        return "GK"
    if "Back" in position:
        return "DEF"
    if "Midfield" in position:
        return "MID"
    return "FWD"  # wings, forwards, strikers


def fmt_formation(n):
    return "-".join(str(n))


def player_name(p):
    return p.get("player_nickname") or p["player_name"]


def zone_index(x, y):
    return min(ROWS - 1, int(y / (W_YD / ROWS))), min(COLS - 1, int(x / (L_YD / COLS)))


def delivery_zone(start, end):
    """Near Post / Central / Far Post relative to the taker's side; Short if it ends outside the box."""
    ex, ey = end[0], end[1]
    if ex < 102 or ey < 18 or ey > 62:
        return "Short"
    d = ey if start[1] < W_YD / 2 else W_YD - ey    # distance from the taker's touchline
    return "Near Post" if d < 37 else "Far Post" if d > 43 else "Central"


def build(team, competition_id, season_id):
    matches_meta = [mt for mt in load(DATA / "matches" / str(competition_id) / f"{season_id}.json")
                    if team in (mt["home_team"]["home_team_name"], mt["away_team"]["away_team_name"])]
    matches_meta.sort(key=lambda mt: (mt["match_date"], mt.get("kick_off") or ""))
    if not matches_meta:
        raise SystemExit(f"No matches found for {team}")

    names = {}                    # player_id -> display name (nickname if present)
    squad = defaultdict(lambda: Counter())
    squad_pos_minutes = defaultdict(Counter)
    squad_info = {}
    matches, shots, corners, free_kicks = [], [], [], []
    zones = {k: [[0] * COLS for _ in range(ROWS)] for k in ("buildup", "pressure", "overloads")}
    tot = Counter()
    pass_len_sum = 0.0
    form_counter = Counter()
    # formation average positions: slot -> phase -> [sum_x, sum_y, n], slot -> player counter
    slot_pos = defaultdict(lambda: {"in": [0.0, 0.0, 0], "out": [0.0, 0.0, 0]})
    slot_players = defaultdict(Counter)
    slot_matches = Counter()
    formation_by_match = {}

    for mt in matches_meta:
        mid = mt["match_id"]
        home = mt["home_team"]["home_team_name"] == team
        opp = mt["away_team"]["away_team_name"] if home else mt["home_team"]["home_team_name"]
        gf, ga = (mt["home_score"], mt["away_score"]) if home else (mt["away_score"], mt["home_score"])
        events = load(DATA / "events" / f"{mid}.json")
        lineups = load(DATA / "lineups" / f"{mid}.json")
        for t in lineups:
            for p in t["lineup"]:
                names[p["player_id"]] = player_name(p)
        nm = lambda e: names.get(e["player"]["id"], e["player"]["name"]) if "player" in e else ""

        mine = lambda e: e["team"]["name"] == team
        match_end = max(e["minute"] + e["second"] / 60 for e in events if e["period"] <= 4)

        # ---- formation (starting XI)
        xi = next(e for e in events if e["type"]["name"] == "Starting XI" and mine(e))
        formation = fmt_formation(xi["tactics"]["formation"])
        formation_by_match[mid] = formation
        form_counter[formation] += 1

        # ---- possession (time-based: each possession phase spans from its first event to the next phase's first event)
        poss_time = Counter()
        by_period = defaultdict(list)
        for e in events:
            if e["period"] <= 4:
                by_period[e["period"]].append(e)
        for evs in by_period.values():
            phases = []
            for e in evs:
                if not phases or phases[-1][0] != e["possession"]:
                    phases.append((e["possession"], e["possession_team"]["name"], ts_seconds(e["timestamp"])))
            end = max(ts_seconds(e["timestamp"]) for e in evs)
            for i, (_, pteam, start) in enumerate(phases):
                stop = phases[i + 1][2] if i + 1 < len(phases) else end
                poss_time[pteam == team] += max(0.0, stop - start)
        possession_pct = round(100 * poss_time[True] / max(1e-9, poss_time[True] + poss_time[False]), 1)

        # ---- per-event extraction
        timeline = []
        xg_for = xg_against = 0.0
        m_pass_att = m_pass_cmp = 0
        possession_shot, possession_goal = set(), set()
        for e in events:
            if e["period"] > 4:
                continue  # ignore penalty shootouts
            typ = e["type"]["name"]
            if typ == "Shot" and mine(e):
                possession_shot.add(e["possession"])
                if e["shot"]["outcome"]["name"] == "Goal":
                    possession_goal.add(e["possession"])

        for e in events:
            if e["period"] > 4:
                continue
            typ = e["type"]["name"]
            is_mine = mine(e)
            side = "team" if is_mine else "opp"
            pid = e.get("player", {}).get("id")
            loc = e.get("location")
            in_poss = e["possession_team"]["name"] == team

            if typ == "Shot":
                sh = e["shot"]
                xg = sh.get("statsbomb_xg", 0.0)
                outcome = sh["outcome"]["name"]
                if is_mine:
                    xg_for += xg
                    out = "Goal" if outcome == "Goal" else "On Target" if outcome in ON_TARGET else "Off Target"
                    shots.append({"match_id": mid, "clock": clock(e), "player": nm(e), "x_m": m(loc[0]), "y_m": m(loc[1]),
                                  "xg": round(xg, 3), "outcome": out})
                    squad[pid]["shots"] += 1
                    squad[pid]["xg"] += xg
                    tot["shots"] += 1
                    if out != "Off Target":
                        tot["shots_on_target"] += 1
                    if outcome == "Goal":
                        squad[pid]["goals"] += 1
                else:
                    xg_against += xg
                if outcome == "Goal":
                    detail = {"Penalty": "Penalty", "Free Kick": "Direct free kick"}.get(sh["type"]["name"],
                             "Header" if sh.get("body_part", {}).get("name") == "Head" else "Open play")
                    timeline.append({"clock": clock(e), "period": e["period"], "side": side, "type": "goal",
                                     "player": nm(e), "detail": detail})
                if is_mine and sh["type"]["name"] == "Free Kick":
                    end = sh.get("end_location", [L_YD, W_YD / 2])
                    free_kicks.append({"match_id": mid, "clock": clock(e), "third": third(loc[0]),
                                       "completed": outcome in ON_TARGET or outcome == "Goal", "technique": "Not recorded",
                                       "zone": "Direct Shot", "start_x_m": m(loc[0]), "start_y_m": m(loc[1]),
                                       "end_x_m": m(end[0]), "end_y_m": m(end[1]),
                                       "shot": True, "goal": outcome == "Goal"})

            elif typ == "Own Goal Against":
                timeline.append({"clock": clock(e), "period": e["period"], "side": "opp" if is_mine else "team",
                                 "type": "own_goal", "player": nm(e), "detail": "Own goal"})

            elif typ in ("Foul Committed", "Bad Behaviour"):
                key = "foul_committed" if typ == "Foul Committed" else "bad_behaviour"
                card = e.get(key, {}).get("card", {}).get("name")
                if is_mine and typ == "Foul Committed":
                    squad[pid]["fouls"] += 1
                    tot["fouls"] += 1
                if card:
                    ctype = {"Yellow Card": "yellow", "Second Yellow": "second_yellow", "Red Card": "red"}[card]
                    timeline.append({"clock": clock(e), "period": e["period"], "side": side, "type": ctype,
                                     "player": nm(e), "detail": "Foul" if typ == "Foul Committed" else "Behaviour"})
                    if is_mine:
                        if ctype in ("yellow", "second_yellow"):
                            squad[pid]["yellow"] += 1
                            tot["yellow"] += 1
                        if ctype in ("red", "second_yellow"):
                            squad[pid]["red"] += 1
                            tot["red"] += 1

            elif typ == "Substitution":
                on = e["substitution"]["replacement"]
                timeline.append({"clock": clock(e), "period": e["period"], "side": side, "type": "sub",
                                 "player": names.get(on["id"], on["name"]), "detail": "replaces " + nm(e)})

            if not is_mine:
                if typ == "Pass" and loc and loc[0] < 80:
                    tot["ppda_opp_passes"] += 1  # attempted; opponent's own 2/3 = our attacking 2/3
                continue

            # ---------------- scouted team's events only ----------------
            if typ == "Pass":
                p = e["pass"]
                outcome = p.get("outcome", {}).get("name")
                if outcome not in ("Injury Clearance", "Unknown"):
                    m_pass_att += 1
                    squad[pid]["passes_att"] += 1
                    tot["passes_att"] += 1
                    pass_len_sum += p["length"]
                    if abs(p["angle"]) < math.pi / 4:
                        tot["forward_passes"] += 1
                    if outcome is None:
                        m_pass_cmp += 1
                        squad[pid]["passes_cmp"] += 1
                        tot["passes_cmp"] += 1
                if p.get("goal_assist"):
                    squad[pid]["assists"] += 1
                ptype = p.get("type", {}).get("name")
                if ptype in ("Corner", "Free Kick"):
                    end = p["end_location"]
                    tech = p.get("technique", {}).get("name")
                    item = {"match_id": mid, "clock": clock(e),
                            "technique": tech if tech in TECHNIQUES else "Not recorded",
                            "zone": delivery_zone(loc, end), "start_x_m": m(loc[0]), "start_y_m": m(loc[1]),
                            "end_x_m": m(end[0]), "end_y_m": m(end[1]),
                            "shot": e["possession"] in possession_shot, "goal": e["possession"] in possession_goal}
                    if ptype == "Corner":
                        corners.append({**item, "side": "left" if loc[1] < W_YD / 2 else "right"})
                    else:
                        free_kicks.append({**item, "third": third(loc[0]), "completed": outcome is None})
            elif typ == "Duel" and e["duel"].get("type", {}).get("name") == "Tackle":
                squad[pid]["tackles"] += 1
            elif typ == "Interception":
                squad[pid]["interceptions"] += 1
            elif typ == "Dribble":
                squad[pid]["dribbles_att"] += 1
                if e["dribble"]["outcome"]["name"] == "Complete":
                    squad[pid]["dribbles_cmp"] += 1

            # PPDA defensive actions: tackles, interceptions, fouls, and challenges (Dribbled Past)
            if typ in ("Duel", "Interception", "Foul Committed", "Dribbled Past") and loc and loc[0] > 40:
                if typ != "Duel" or e["duel"].get("type", {}).get("name") == "Tackle":
                    tot["ppda_def_actions"] += 1

            if loc:
                r, c = zone_index(loc[0], loc[1])
                if typ in ("Pass", "Carry") and e["play_pattern"]["name"] in BUILDUP_PATTERNS:
                    zones["buildup"][r][c] += 1
                if typ == "Pressure":
                    zones["pressure"][r][c] += 1
                if typ in ("Pass", "Carry", "Ball Receipt*", "Dribble", "Shot"):
                    zones["overloads"][r][c] += 1

        # ---- squad appearances / minutes from lineup position spells
        team_lineup = next(t for t in lineups if t["team_name"] == team)["lineup"]
        for p in team_lineup:
            if not p["positions"]:
                continue
            pid = p["player_id"]
            squad_info[pid] = {"name": player_name(p), "jersey": p["jersey_number"]}
            squad[pid]["apps"] += 1
            if p["positions"][0]["start_reason"] == "Starting XI":
                squad[pid]["starts"] += 1
            for sp in p["positions"]:
                end = mmss_to_min(sp["to"]) if sp["to"] else match_end
                mins = max(0.0, end - mmss_to_min(sp["from"]))
                squad[pid]["minutes"] += mins
                squad_pos_minutes[pid][sp["position"]] += mins

        # ---- average positions for the formation view (starters, first positional spell only)
        spells = {}
        for p in team_lineup:
            if p["positions"] and p["positions"][0]["start_reason"] == "Starting XI":
                sp = p["positions"][0]
                end = (sp["to_period"] or 99, mmss_to_min(sp["to"]) if sp["to"] else 999)
                spells[p["player_id"]] = (sp["position"], end)
        for pid, (slot, _) in spells.items():
            slot_matches[(formation, slot)] += 1
            slot_players[(formation, slot)][names[pid]] += 1
        for e in events:
            pid = e.get("player", {}).get("id")
            if not mine(e) or pid not in spells or not e.get("location") or e["period"] > 4:
                continue
            slot, (end_period, end_min) = spells[pid]
            if (e["period"], e["minute"] + e["second"] / 60) >= (end_period, end_min):
                continue
            acc = slot_pos[(formation, slot)]["in" if e["possession_team"]["name"] == team else "out"]
            acc[0] += e["location"][0]
            acc[1] += e["location"][1]
            acc[2] += 1

        timeline.sort(key=lambda t: (t["period"], mmss_to_min(t["clock"])))
        tot["pass_acc_sum"] += 100 * m_pass_cmp / max(1, m_pass_att)
        stadium = (mt.get("stadium") or {}).get("name", "—")
        stage = mt["competition_stage"]["name"]
        matches.append({
            "id": mid, "date": mt["match_date"],
            "stage": f"Matchweek {mt['match_week']}" if stage == "Regular Season" and mt.get("match_week") else stage,
            "stadium": stadium, "home_away": "H" if home else "A", "opponent": opp,
            "team_score": gf, "opp_score": ga, "result": "W" if gf > ga else "D" if gf == ga else "L",
            "possession_pct": possession_pct, "xg_for": round(xg_for, 2), "xg_against": round(xg_against, 2),
            "formation": formation, "timeline": timeline,
        })

    n = len(matches)
    won = sum(mt["result"] == "W" for mt in matches)
    drawn = sum(mt["result"] == "D" for mt in matches)
    gf = sum(mt["team_score"] for mt in matches)
    ga = sum(mt["opp_score"] for mt in matches)
    cs = sum(mt["opp_score"] == 0 for mt in matches)
    avg_poss = round(sum(mt["possession_pct"] for mt in matches) / n, 1)
    pass_acc = round(tot["pass_acc_sum"] / n, 1)

    squad_out = []
    for pid, info in squad_info.items():
        s = squad[pid]
        position = squad_pos_minutes[pid].most_common(1)[0][0]
        squad_out.append({
            "name": info["name"], "jersey": info["jersey"], "group": pos_group(position), "position": position,
            "apps": s["apps"], "starts": s["starts"], "minutes": round(s["minutes"]),
            "goals": s["goals"], "assists": s["assists"], "shots": s["shots"], "xg": round(s["xg"], 2),
            "passes_att": s["passes_att"], "passes_cmp": s["passes_cmp"], "tackles": s["tackles"],
            "interceptions": s["interceptions"], "dribbles_att": s["dribbles_att"], "dribbles_cmp": s["dribbles_cmp"],
            "fouls": s["fouls"], "yellow": s["yellow"], "red": s["red"],
        })

    primary = form_counter.most_common(1)[0][0]
    slots = sorted([sl for (f, sl) in slot_matches if f == primary], key=lambda sl: -slot_matches[(primary, sl)])[:11]

    def avg_positions(phase):
        out = []
        for sl in slots:
            sx, sy, k = slot_pos[(primary, sl)][phase]
            if k:
                out.append({"slot": sl, "abbr": ABBR.get(sl, sl), "player": slot_players[(primary, sl)].most_common(1)[0][0],
                            "x_m": m(sx / k), "y_m": m(sy / k)})
        return out

    first = matches_meta[0]
    return {
        "meta": {"team": team, "competition": first["competition"]["competition_name"],
                 "season": first["season"]["season_name"], "generated": date.today().isoformat(),
                 "pitch": {"length_m": round(L_YD * YD, 1), "width_m": round(W_YD * YD, 1)}},
        "record": {"played": n, "won": won, "drawn": drawn, "lost": n - won - drawn, "points": 3 * won + drawn,
                   "goals_for": gf, "goals_against": ga, "clean_sheets": cs},
        "matches": matches,
        "squad": squad_out,
        "team_stats": {"goals_for": gf, "goals_against": ga, "shots": tot["shots"],
                       "shots_on_target": tot["shots_on_target"],
                       "xg_for": round(sum(mt["xg_for"] for mt in matches), 2),
                       "xg_against": round(sum(mt["xg_against"] for mt in matches), 2),
                       "pass_accuracy_pct": pass_acc, "possession_pct": avg_poss, "fouls": tot["fouls"],
                       "yellow": tot["yellow"], "red": tot["red"], "clean_sheets": cs},
        "formation": {"primary": primary, "matches_used": form_counter[primary], "matches_total": n,
                      "usage": [{"formation": f, "matches": c} for f, c in form_counter.most_common()],
                      "in_possession": avg_positions("in"), "out_of_possession": avg_positions("out")},
        "style": {"possession_pct": avg_poss, "avg_pass_length_m": round(pass_len_sum / max(1, tot["passes_att"]) * YD, 1),
                  "forward_pass_share_pct": round(100 * tot["forward_passes"] / max(1, tot["passes_att"]), 1),
                  "pass_accuracy_pct": pass_acc,
                  "ppda": round(tot["ppda_opp_passes"] / max(1, tot["ppda_def_actions"]), 1)},
        "zones": {"cols": COLS, "rows": ROWS, "cell_length_m": round(L_YD / COLS * YD, 2),
                  "cell_width_m": round(W_YD / ROWS * YD, 2), **zones},
        "shots": shots, "corners": corners, "free_kicks": free_kicks,
    }


def third(x):
    return "Defensive" if x < L_YD / 3 else "Middle" if x < 2 * L_YD / 3 else "Attacking"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--team", required=True)
    ap.add_argument("--competition", type=int, required=True)
    ap.add_argument("--season", type=int, required=True)
    args = ap.parse_args()

    data = build(args.team, args.competition, args.season)
    OUT_DIR.mkdir(exist_ok=True)
    slug = re.sub(r"\W+", "_", args.team).strip("_")
    (OUT_DIR / f"{slug}_report_data.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

    html = TEMPLATE.read_text(encoding="utf-8")
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    tag = '<script id="report-data" type="application/json">__REPORT_DATA__</script>'
    assert html.count(tag) == 1, "template placeholder missing"
    html = html.replace(tag, tag.replace("__REPORT_DATA__", payload))
    html = html.replace('<script src="mock_data.js"></script>\n', "")
    out = OUT_DIR / f"{slug}_Scouting_Report.html"
    out.write_text(html, encoding="utf-8")
    print(f"Wrote {out} ({len(data['matches'])} matches, {len(data['shots'])} shots)")


if __name__ == "__main__":
    main()
