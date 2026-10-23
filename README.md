# StatsBomb Team Scouting Report

**Live report:** https://mpuert.github.io/statsbomb-scouting-report/ (Manchester United, Premier League 2015/16)

A Python pipeline that turns one team-season of [StatsBomb open event data](https://github.com/statsbomb/open-data) into a single-file interactive HTML scouting report for a coaching staff preparing to face that team. One command per team.

## Problem
Opposition scouting usually means stitching together results, lineups, and video notes by hand. I wanted one report, built the same way for any team in the open data, that covers the questions a staff asks before a match: how they line up, how they build, where they press, where they're dangerous, and how they take set pieces. Every section explains in plain language what the numbers mean on the pitch.

## Data
StatsBomb open data: match, lineup, and event files for every match the team played in the chosen competition-season. The data is not included in this repo; clone [statsbomb/open-data](https://github.com/statsbomb/open-data) into `open-data/`.

## Method
- `build/build_report.py` reads every match, extracts the report data (all spatial values converted from StatsBomb's 120x80 grid to meters), and writes one JSON object that follows the data contract in `report_spec.md`.
- That JSON is inserted into a fixed template (`template/template.html`). The template never changes between teams; only the data does.
- Sections: record and match timelines, squad by position, team stats, in/out-of-possession shape, style of play, possession, build-up zones, pressure points, attacking threats, area overloads, corners, free kicks.

```
git clone https://github.com/statsbomb/open-data
python build/build_report.py --team "Manchester United" --competition 2 --season 27
```
Python 3 standard library only.

**Checks:** the United record (19-9-10, 66 pts, 49-35) matches the real 2015/16 table. The same pipeline reproduces Bayer Leverkusen 2023/24 (28-6-0, 90 pts, 89-24).

## A finding from checking my own metric: PPDA mostly tracks possession
The first version labeled United's PPDA of 9.3 as an "intense high press." To check that, I ran PPDA for all 20 Premier League teams in 2015/16. United ranked 2nd-lowest (Liverpool 9.0), which looked like confirmation, but the top six teams in possession were also the top six in PPDA, while United were only 13th in pressures per game. PPDA counts opponent passes per defensive action, so a team that keeps the ball faces fewer opponent passes and gets a low PPDA without pressing hard. This is a known property of the metric; the point here was catching it in my own output. The report now describes PPDA without a pressing label and flags the possession effect.

## Known issues
- PPDA needs context: next step is adding league rank and pressures per minute of opponent possession.
- Leverkusen 2023/24 gets a high PPDA (14.6) despite 34% of their pressures coming in the attacking third (United 21%). Open data has only Leverkusen's own matches for that season, so there's no league benchmark.
- The "Pressure points" section reports the share of pressures in the middle and attacking thirds. Every team I checked lands between 59% and 70%, so the number doesn't separate high-pressing teams from deeper ones. Next version: attacking-third share only (Leverkusen 34% vs United 21%) plus each team's league rank.
- Out-of-possession positions come from on-ball defensive actions, not off-ball positioning (event data has no tracking).
- "Saved Off Target" shots are counted as on target.
- Pass accuracy includes throw-ins and goal kicks (open-play accuracy is 82.7% vs 80.5% shown).

## Author
Marcelo Puertas, MS Data Science, Vanderbilt University (2027). Former men's soccer player at Viterbo University.

![StatsBomb](statsbomb-logo.png)

Data: StatsBomb open data.
