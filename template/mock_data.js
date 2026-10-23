/* =====================================================================
   MOCK DATA — for previewing template.html only. Every number is made up.
   The real build replaces the __REPORT_DATA__ placeholder in template.html
   with JSON of exactly this shape; this file is then not needed.

   DATA CONTRACT (all spatial values already in METERS)
   ---------------------------------------------------------------------
   Pitch: 109.7 m x 73.2 m. x = distance from the team's OWN goal line
   (team always attacks left -> right). y = distance from the team's LEFT
   touchline (top edge of every diagram). Clock strings are "MM:SS" copied
   from each event's own minute/second — never re-derived.

   meta        { team, competition, season, generated, pitch:{length_m,width_m} }
   record      { played, won, drawn, lost, points, goals_for, goals_against, clean_sheets }
   matches[]   { id, date "YYYY-MM-DD", stage, stadium, home_away "H"|"A",
                 opponent, team_score, opp_score, result "W"|"D"|"L",
                 possession_pct, xg_for, xg_against, formation,
                 timeline[] { clock "MM:SS", period, side "team"|"opp",
                              type "goal"|"own_goal"|"yellow"|"second_yellow"|"red"|"sub",
                              player, detail } }
   squad[]     { name, jersey, group "GK"|"DEF"|"MID"|"FWD", position,
                 apps, starts, minutes, goals, assists, shots, xg,
                 passes_att, passes_cmp, tackles, interceptions,
                 dribbles_att, dribbles_cmp, fouls, yellow, red }
   team_stats  { goals_for, goals_against, shots, shots_on_target, xg_for, xg_against,
                 pass_accuracy_pct, possession_pct, fouls, yellow, red, clean_sheets }
   formation   { primary, matches_used, matches_total, usage[] {formation, matches},
                 in_possession[] / out_of_possession[] { slot, abbr, player, x_m, y_m } }
   style       { possession_pct, avg_pass_length_m, forward_pass_share_pct,
                 pass_accuracy_pct, ppda }
   zones       { cols, rows, cell_length_m, cell_width_m,
                 buildup[rows][cols], pressure[rows][cols], overloads[rows][cols] }
   shots[]     { match_id, clock, player, x_m, y_m, xg, outcome "Goal"|"On Target"|"Off Target" }
   corners[]   { match_id, clock, side "left"|"right", technique, zone,
                 start_x_m, start_y_m, end_x_m, end_y_m, shot, goal }
   free_kicks[]{ match_id, clock, third "Defensive"|"Middle"|"Attacking", completed,
                 technique, zone, start_x_m, start_y_m, end_x_m, end_y_m, shot, goal }
     technique: "Inswinging"|"Outswinging"|"Straight"|"Not recorded"
     zone:      "Near Post"|"Central"|"Far Post"|"Short"|"Direct Shot"
     shot/goal: true if the possession the delivery started produced one
                (includes second balls and rebounds).
   ===================================================================== */
(function () {
  let seed = 7;
  const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  const pick = a => a[Math.floor(rnd() * a.length)];
  const r1 = v => Math.round(v * 10) / 10;
  const r2 = v => Math.round(v * 100) / 100;
  const L = 109.7, W = 73.2;
  const clock = (m, s) => String(m).padStart(2, "0") + ":" + String(s).padStart(2, "0");

  const squadDef = [
    ["Lukáš Hrádecký", 1, "GK", "Goalkeeper"], ["Matěj Kovář", 17, "GK", "Goalkeeper"],
    ["Jonathan Tah", 4, "DEF", "Center Back"], ["Edmond Tapsoba", 12, "DEF", "Right Center Back"],
    ["Piero Hincapié", 3, "DEF", "Left Center Back"], ["Odilon Kossounou", 6, "DEF", "Right Center Back"],
    ["Jeremie Frimpong", 30, "DEF", "Right Wing Back"], ["Alejandro Grimaldo", 20, "DEF", "Left Wing Back"],
    ["Josip Stanišić", 2, "DEF", "Right Wing Back"], ["Arthur", 13, "DEF", "Left Wing Back"],
    ["Granit Xhaka", 34, "MID", "Left Defensive Midfield"], ["Exequiel Palacios", 25, "MID", "Right Defensive Midfield"],
    ["Robert Andrich", 8, "MID", "Right Defensive Midfield"], ["Florian Wirtz", 10, "MID", "Left Attacking Midfield"],
    ["Jonas Hofmann", 7, "MID", "Right Attacking Midfield"], ["Nadiem Amiri", 11, "MID", "Right Attacking Midfield"],
    ["Amine Adli", 21, "MID", "Left Attacking Midfield"], ["Noah Mbamba", 26, "MID", "Center Defensive Midfield"],
    ["Victor Boniface", 22, "FWD", "Center Forward"], ["Patrik Schick", 14, "FWD", "Center Forward"],
    ["Borja Iglesias", 9, "FWD", "Center Forward"], ["Adam Hložek", 23, "FWD", "Center Forward"],
  ];
  const starters = [0, 4, 2, 3, 7, 10, 11, 6, 13, 14, 18];
  const scorers = [18, 13, 7, 6, 19, 14, 15, 16, 10, 3];

  const opps = ["RB Leipzig", "Borussia Mönchengladbach", "Darmstadt 98", "Bayern Munich", "Heidenheim",
    "Mainz 05", "Wolfsburg", "Augsburg", "Eintracht Frankfurt", "Borussia Dortmund", "Werder Bremen",
    "Union Berlin", "Hoffenheim", "Köln", "Stuttgart", "Freiburg", "Bochum"];
  const matches = [];
  const start = new Date("2023-08-19");
  for (let i = 0; i < 34; i++) {
    const d = new Date(start.getTime() + i * 7 * 86400000 + (i > 16 ? 21 * 86400000 : 0));
    const home = i % 2 === 0;
    const gf = pick([0, 1, 1, 2, 2, 2, 3, 3, 4, 5]);
    let ga = pick([0, 0, 0, 1, 1, 1, 2]);
    if (i % 11 === 5) ga = gf; // a few draws
    if (ga > gf && rnd() < 0.8) ga = gf;
    const res = gf > ga ? "W" : gf === ga ? "D" : "L";
    const tl = [];
    for (let g = 0; g < gf; g++) {
      const m = Math.floor(rnd() * 92) + 1;
      tl.push({ clock: clock(m, Math.floor(rnd() * 60)), period: m > 45 ? 2 : 1, side: "team", type: "goal",
        player: squadDef[pick(scorers)][0], detail: pick(["Open play", "Open play", "Header", "From corner", "Penalty"]) });
    }
    for (let g = 0; g < ga; g++) {
      const m = Math.floor(rnd() * 92) + 1;
      tl.push({ clock: clock(m, Math.floor(rnd() * 60)), period: m > 45 ? 2 : 1, side: "opp", type: "goal",
        player: "Opponent #" + (Math.floor(rnd() * 30) + 1), detail: "Open play" });
    }
    for (let c = 0; c < Math.floor(rnd() * 4); c++) {
      const m = Math.floor(rnd() * 90) + 1, own = rnd() < 0.5;
      tl.push({ clock: clock(m, Math.floor(rnd() * 60)), period: m > 45 ? 2 : 1, side: own ? "team" : "opp", type: "yellow",
        player: own ? squadDef[pick(starters)][0] : "Opponent #" + (Math.floor(rnd() * 30) + 1), detail: "Foul" });
    }
    for (let s = 0; s < 5; s++) {
      const m = 55 + Math.floor(rnd() * 35);
      tl.push({ clock: clock(m, Math.floor(rnd() * 60)), period: 2, side: s < 3 ? "team" : "opp", type: "sub",
        player: s < 3 ? squadDef[pick([12, 15, 16, 19, 8])][0] : "Opponent #" + (Math.floor(rnd() * 30) + 1),
        detail: s < 3 ? "replaces " + squadDef[pick([13, 14, 18, 7])][0] : "Substitution" });
    }
    tl.sort((a, b) => a.clock.localeCompare(b.clock));
    matches.push({
      id: 3895000 + i, date: d.toISOString().slice(0, 10), stage: "Matchweek " + (i + 1),
      stadium: home ? "BayArena" : opps[i % 17] + " Stadium", home_away: home ? "H" : "A",
      opponent: opps[i % 17], team_score: gf, opp_score: ga, result: res,
      possession_pct: r1(48 + rnd() * 22), xg_for: r2(0.8 + rnd() * 2.6), xg_against: r2(0.3 + rnd() * 1.4),
      formation: i % 7 === 3 ? "4-2-3-1" : "3-4-2-1", timeline: tl,
    });
  }
  const sum = f => matches.reduce((a, m) => a + f(m), 0);
  const won = matches.filter(m => m.result === "W").length, drawn = matches.filter(m => m.result === "D").length;

  const squad = squadDef.map(([name, jersey, group, position], i) => {
    const isStarter = starters.includes(i);
    const apps = isStarter ? 28 + Math.floor(rnd() * 6) : 6 + Math.floor(rnd() * 18);
    const starts = isStarter ? apps - Math.floor(rnd() * 4) : Math.floor(apps * rnd() * 0.5);
    const minutes = starts * (78 + Math.floor(rnd() * 12)) + (apps - starts) * 22;
    const att = group === "GK" ? 28 * apps : group === "FWD" ? 22 * apps : 55 * apps;
    const fwd = group === "FWD" ? 3 : group === "MID" ? 1.6 : group === "DEF" ? 0.6 : 0;
    const shots = Math.round(fwd * apps * (0.5 + rnd()));
    return {
      name, jersey, group, position, apps, starts, minutes,
      goals: Math.round(shots * (0.08 + rnd() * 0.1)), assists: group === "GK" ? 0 : Math.round(rnd() * (group === "DEF" ? 8 : 11)),
      shots, xg: r2(shots * (0.09 + rnd() * 0.06)),
      passes_att: att, passes_cmp: Math.round(att * (0.78 + rnd() * 0.14)),
      tackles: group === "GK" ? 0 : Math.round(apps * (0.4 + rnd() * 1.6)), interceptions: group === "GK" ? 1 : Math.round(apps * rnd() * 1.2),
      dribbles_att: group === "GK" ? 0 : Math.round(apps * rnd() * (group === "DEF" ? 1.5 : 3)),
      dribbles_cmp: 0, fouls: Math.round(apps * rnd() * 1.4), yellow: Math.floor(rnd() * 7), red: rnd() < 0.08 ? 1 : 0,
    };
  });
  squad.forEach(p => (p.dribbles_cmp = Math.round(p.dribbles_att * (0.45 + rnd() * 0.25))));

  const posIn = [["GK", "Goalkeeper", 0, 9, 36.6], ["LCB", "Left Center Back", 4, 30, 15], ["CB", "Center Back", 2, 25, 36.6],
    ["RCB", "Right Center Back", 3, 30, 58], ["LWB", "Left Wing Back", 7, 70, 6], ["LDM", "Left Defensive Midfield", 10, 47, 28],
    ["RDM", "Right Defensive Midfield", 11, 49, 45], ["RWB", "Right Wing Back", 6, 74, 67], ["LAM", "Left Attacking Midfield", 13, 80, 25],
    ["RAM", "Right Attacking Midfield", 14, 79, 48], ["CF", "Center Forward", 18, 90, 36]];
  const posOut = { GK: [6, 36.6], LCB: [21, 22], CB: [17, 36.6], RCB: [21, 51], LWB: [28, 9], LDM: [37, 30], RDM: [38, 43],
    RWB: [30, 64], LAM: [53, 25], RAM: [52, 48], CF: [61, 36.6] };

  const grid = fn => Array.from({ length: 4 }, (_, r) => Array.from({ length: 6 }, (_, c) => Math.round(fn(r, c) * (0.85 + rnd() * 0.3))));

  const shots = [];
  for (let i = 0; i < 560; i++) {
    const inBox = rnd() < 0.68;
    const x = inBox ? L - 2 - rnd() * 15 : L - 17 - rnd() * 16;
    const y = W / 2 + (rnd() - 0.5) * (inBox ? 32 : 46);
    const dist = Math.hypot(L - x, W / 2 - y);
    const xg = r2(Math.min(0.85, Math.max(0.01, 0.7 * Math.exp(-dist / 5.5) + rnd() * 0.03)));
    const u = rnd();
    const outcome = u < xg ? "Goal" : u < xg + 0.3 ? "On Target" : "Off Target";
    const m = pick(matches);
    shots.push({ match_id: m.id, clock: clock(Math.floor(rnd() * 93), Math.floor(rnd() * 60)),
      player: squadDef[pick([18, 18, 18, 13, 13, 19, 7, 6, 14, 15, 16, 10, 3, 2])][0], x_m: r1(x), y_m: r1(y), xg, outcome });
  }

  const techniques = ["Inswinging", "Inswinging", "Outswinging", "Straight"];
  const zoneEnd = (zone, left) => {
    const nearY = left ? 31 : 42, farY = left ? 44 : 29;
    if (zone === "Short") return [L - 6 - rnd() * 12, left ? 4 + rnd() * 10 : W - 4 - rnd() * 10];
    if (zone === "Near Post") return [L - 2 - rnd() * 5, nearY + (rnd() - 0.5) * 6];
    if (zone === "Far Post") return [L - 2 - rnd() * 7, farY + (rnd() - 0.5) * 7];
    return [L - 6 - rnd() * 7, W / 2 + (rnd() - 0.5) * 8];
  };
  const corners = [];
  for (let i = 0; i < 196; i++) {
    const left = rnd() < 0.5, zone = pick(["Near Post", "Near Post", "Central", "Far Post", "Far Post", "Short"]);
    const [ex, ey] = zoneEnd(zone, left), shot = rnd() < 0.3;
    corners.push({ match_id: pick(matches).id, clock: clock(Math.floor(rnd() * 93), Math.floor(rnd() * 60)),
      side: left ? "left" : "right", technique: zone === "Short" ? "Not recorded" : pick(techniques), zone,
      start_x_m: L - 0.5, start_y_m: left ? 0.5 : W - 0.5, end_x_m: r1(ex), end_y_m: r1(ey), shot, goal: shot && rnd() < 0.14 });
  }
  const free_kicks = [];
  for (let i = 0; i < 430; i++) {
    const u = rnd(), third = u < 0.38 ? "Defensive" : u < 0.78 ? "Middle" : "Attacking";
    const sx = third === "Defensive" ? rnd() * 36.5 : third === "Middle" ? 36.6 + rnd() * 36.5 : 73.2 + rnd() * 30;
    const sy = 4 + rnd() * (W - 8);
    let zone = "Short", technique = "Not recorded", ex, ey;
    if (third === "Attacking") {
      zone = pick(["Near Post", "Central", "Far Post", "Short", "Short", "Direct Shot"]);
      const left = sy < W / 2;
      if (zone === "Direct Shot") { ex = L; ey = W / 2 + (rnd() - 0.5) * 7; }
      else if (zone === "Short") { ex = sx + (rnd() - 0.3) * 12; ey = sy + (rnd() - 0.5) * 14; }
      else { [ex, ey] = zoneEnd(zone, left); technique = pick(techniques); }
    } else {
      const long = rnd() < (third === "Middle" ? 0.45 : 0.25);
      ex = Math.min(L - 3, sx + (long ? 25 + rnd() * 25 : (rnd() - 0.4) * 14));
      ey = Math.max(2, Math.min(W - 2, sy + (rnd() - 0.5) * (long ? 40 : 18)));
    }
    const shot = third === "Attacking" ? rnd() < 0.33 : rnd() < 0.04;
    free_kicks.push({ match_id: pick(matches).id, clock: clock(Math.floor(rnd() * 93), Math.floor(rnd() * 60)),
      third, completed: rnd() < (third === "Defensive" ? 0.9 : third === "Middle" ? 0.8 : 0.62), technique, zone,
      start_x_m: r1(sx), start_y_m: r1(sy), end_x_m: r1(ex), end_y_m: r1(ey), shot, goal: shot && rnd() < 0.1 });
  }

  window.MOCK_DATA = {
    meta: { team: "Bayer Leverkusen", competition: "1. Bundesliga", season: "2023/2024", generated: "2026-09-29",
      pitch: { length_m: 109.7, width_m: 73.2 }, mock: true },
    record: { played: 34, won, drawn, lost: 34 - won - drawn, points: won * 3 + drawn,
      goals_for: sum(m => m.team_score), goals_against: sum(m => m.opp_score),
      clean_sheets: matches.filter(m => m.opp_score === 0).length },
    matches,
    squad,
    team_stats: { goals_for: sum(m => m.team_score), goals_against: sum(m => m.opp_score), shots: shots.length,
      shots_on_target: shots.filter(s => s.outcome !== "Off Target").length, xg_for: r2(sum(m => m.xg_for)),
      xg_against: r2(sum(m => m.xg_against)), pass_accuracy_pct: 88.4, possession_pct: r1(sum(m => m.possession_pct) / 34),
      fouls: 312, yellow: 58, red: 2, clean_sheets: matches.filter(m => m.opp_score === 0).length },
    formation: {
      primary: "3-4-2-1", matches_used: matches.filter(m => m.formation === "3-4-2-1").length, matches_total: 34,
      usage: [{ formation: "3-4-2-1", matches: matches.filter(m => m.formation === "3-4-2-1").length },
        { formation: "4-2-3-1", matches: matches.filter(m => m.formation === "4-2-3-1").length }],
      in_possession: posIn.map(([abbr, slot, pi, x, y]) => ({ slot, abbr, player: squadDef[pi][0], x_m: x, y_m: y })),
      out_of_possession: posIn.map(([abbr, slot, pi]) => ({ slot, abbr, player: squadDef[pi][0], x_m: posOut[abbr][0], y_m: posOut[abbr][1] })),
    },
    style: { possession_pct: r1(sum(m => m.possession_pct) / 34), avg_pass_length_m: 17.6, forward_pass_share_pct: 31.8,
      pass_accuracy_pct: 88.4, ppda: 8.7 },
    zones: {
      cols: 6, rows: 4, cell_length_m: 18.28, cell_width_m: 18.3,
      buildup: grid((r, c) => [900, 1500, 1300, 800, 350, 120][c] * [0.7, 1.2, 1.0, 0.8][r]),
      pressure: grid((r, c) => [120, 260, 520, 700, 610, 380][c] * [0.8, 1.1, 1.1, 1.0][r]),
      overloads: grid((r, c) => [700, 1900, 3000, 3300, 2700, 1400][c] * [0.9, 1.1, 1.0, 1.05][r]),
    },
    shots, corners, free_kicks,
  };
})();
