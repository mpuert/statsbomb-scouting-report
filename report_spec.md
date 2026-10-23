## Overview
Create a scouting report about the opposing team for a soccer team. The report shall have the opponent's record, previous results, key players separated by position, statistics, formation (broken down by phase of play), and tactical information such as: style of play, possession, build-up zones, pressure points, attacking threats, area overloads, and corner and free kick tactics.

The report is a dashboard for the coaching staff to review and gain insight from.

## Goal
The goal is to provide a complete scouting report about a soccer team's opponent. This report should serve as a tool for the coaching staff to analyze and prepare adequately for their match.

## Inputs/Outputs
The inputs are players' and team's statistics from each game, in .json format (StatsBomb open-data: match, lineup, and event files for every game the opponent played).

The output is a complete interactive scouting report dashboard in .html format.

### Units
All measurements in the dashboard are reported in **SI units (meters)**, not the source data's native yard-based coordinate grid.

- The source event data locates every action on a 120 × 80 coordinate grid (StatsBomb's normalized pitch). This is treated as 120 × 80 yards and converted to meters using 1 unit = 1 yard = 0.9144 m, giving a working pitch of **109.7 m × 73.2 m**.
- Any distance derived from that grid — average pass length, shot distance from goal, zone/grid cell dimensions, average player position — must be converted to meters before it is shown or labeled in the dashboard. Raw yard/grid values are never displayed to the coaching staff.
- Percentages (possession, pass accuracy, shot accuracy) and counts (goals, cards, shots) are unitless and unaffected by this conversion.
- Timestamps are shown as match-clock minutes:seconds (`MM:SS`), taken directly from each event's own recorded time so they stay accurate to the video/broadcast clock; they are not converted or re-derived.

## Architecture
- Read the data (matches, lineups, events for every game the opponent played)
- Find key topics about the opposing team
- Extract information to present in dashboard, converting all spatial values to SI units (meters) at extraction time, and write it as one JSON object that follows the **Data Contract** (see Dashboard Template)
- Create the Dashboard by inserting that JSON into the fixed template (`template/template.html`). The template's layout, styling and code are never regenerated or modified per build; only its data changes

## Constraint
- The report shall always be limited to one opposing team only

## Dashboard Sections
Each section below must be clearly labeled in the dashboard and must explain, in plain language next to the visualization, what the underlying numbers represent on the pitch — not just show a chart or grid of counts.

### Record & Previous Results
Season record (played/won/drawn/lost, points, goals for/against, clean sheets) and a chronological list of previous results (date, venue, opponent, score, competition stage). Each result expands into a match timeline of goals, cards, and substitutions with their exact match-clock timestamps. The timeline includes events for **both** teams, shown in three columns: the scouted team's events on the left, the match clock in the center, and the opponent's events on the right.

### Squad by Position
Every player who appeared, grouped into Goalkeepers / Defenders / Midfielders / Forwards, with season totals: appearances, starts, minutes played, goals, assists, shots, xG, passing (attempted/completed/accuracy), defensive actions (tackles, interceptions), dribbles, fouls, and cards.

### Team Statistics
Season-aggregate totals: goals for/against, shots, xG for/against, average pass accuracy, average possession, discipline (fouls, cards), clean sheets.

### Formation — In Possession vs. Out of Possession
A team's shape is rarely identical with and without the ball, so the formation view must show **two separate average-position diagrams built from the same primary formation's matches**:
- **In possession:** each starting player's average location across only the events that occurred while their own team held the ball (`possession_team` = the opponent team).
- **Out of possession:** each starting player's average location across only the events that occurred while the other team held the ball.

Each starter's events count toward their starting position only until they are substituted off or move to a different position (the end of their first position entry in the lineup file). Tactical shifts and substitutes therefore do not distort the primary shape. Each slot is labeled with the player who started there most often.

Showing both side by side reveals shape distortion — e.g., wing-backs who push high and wide in possession but tuck in to form a back five out of possession. Both diagrams use the same primary-formation label and the same meter-scaled pitch.

## Tactical Analysis
Every metric here must ship with a short, concrete explanation of what it means on the field, not just a number or a heatmap. Minimum required explanations:

### Style of Play
Descriptive season-wide indicators:
- **Average possession** — % of ball-in-play time the team controlled, averaged across matches.
- **Average pass length (meters)** — how directly the team plays; short average length suggests a possession-based build-up, long average length suggests a more direct style.
- **Forward pass share** — % of passes played toward the opponent's goal, indicating how proactively the team looks to progress the ball versus keep it side-to-side/backward.
- **Average pass accuracy** — % of attempted passes completed.
- **PPDA (Passes allowed Per Defensive Action)** — the number of passes the opponent **attempts** in the team's attacking two-thirds of the pitch for every defensive action the team makes in that same area. Defensive actions are tackles (Duel events of type Tackle), interceptions, fouls committed, and challenges (Dribbled Past events, where the team challenged the ball carrier but was beaten). A **low** PPDA means the team presses intensely and disrupts the opponent quickly high up the pitch; a **high** PPDA means the team sits off and allows the opponent to build freely until they get closer to their own goal.

### Possession
Per-match possession % (time-based, computed from the duration of each possession phase) plotted match by match, plus the season average. Shows whether possession share is consistent or swings with the opponent faced. Each plotted point is interactive: hovering over it with a mouse, or tapping/clicking it on a touch device, must reveal which opponent, date, venue, and score that point belongs to, so a value on the chart can always be traced back to a specific match without leaving the chart.

### Build-Up Zones
The pitch is divided into a labeled grid of zones (~18.3 m × 18.3 m each, in the SI-converted pitch). Each zone's count is the number of passes and carries the team made, **starting in that zone**, during build-up phases specifically — i.e., possessions that began from Regular Play, a Goal Kick, a Keeper restart, or a Kick Off (not from a corner, free kick, or throw-in). In plain terms: a dark zone shows an area of the pitch the team habitually uses to move the ball out from the back and start attacks. A concentration in the defensive-third half-spaces means they build through their center-backs and holding midfielders rather than going long; a concentration down one flank only means their build-up is lopsided toward that side, which a defending team can prepare to press.

### Pressure Points
Same grid, but each zone's count is the number of Pressure events (moments the team closed down the ball carrier) recorded starting in that zone. In plain terms: dark zones in the attacking or middle third mean the team presses aggressively and tries to win the ball back high up the pitch (a high press); dark zones concentrated in their own defensive third mean the team presses passively and waits in a mid/low block until the opponent is already close to goal.

### Attacking Threats
Every shot the team took, plotted at the exact spot (in meters from the byline/touchline) it was struck from, sized by its expected-goals (xG) value and colored by outcome (goal / on target / off target). Saved shots (including "Saved to Post") count as **On Target**; blocked, wayward, post and off-target shots count as **Off Target**. In plain terms: a cluster of large dots in one area shows where the team most reliably generates high-quality chances — the zone(s) an opposing defense needs to prioritize closing down. The accompanying top-shooters list shows which individual players take on the most shot responsibility.

### Area Overloads
Same grid as build-up/pressure, but counting **every** touch (pass, carry, receipt, dribble, shot) regardless of phase of play. In plain terms: this shows where on the pitch the team spends the most time on the ball across a whole match, i.e., which zones and channels they look to outnumber the opponent in — useful for identifying which areas an opponent should commit extra numbers to.

### Corners & Free Kicks
This section appears as its own top-level tab in the dashboard (it has too much content to sit inside the Tactical Analysis tab), but it is still part of the tactical analysis and follows the same explanation rules.

Both are broken down by **delivery outcome zone** (Near Post / Central / Far Post / Short, based on where the delivery ends relative to the corner-taker's side of goal; attacking-third free kicks also have a fifth zone, **Direct Shot**, for free kicks struck straight at goal) and by **technique** (inswinging/outswinging/straight), with totals for deliveries taken, shots generated, and goals scored from that possession phase (including second balls and rebounds, not only the first contact).

Delivery zones are assigned from where the delivery ends (StatsBomb yard grid, converted to meters for display):
- **Short**: the delivery ends outside the penalty box.
- Otherwise, measure the end point's distance from the taker's touchline, i.e. the touchline on the side of the pitch where the set piece was taken:
  - **Near Post**: less than 37 yd (33.8 m).
  - **Central**: 37–43 yd (33.8–39.3 m).
  - **Far Post**: more than 43 yd (39.3 m).

  The goal posts are at 36 yd and 44 yd from each touchline.

Free kicks are additionally split into **three groups by the third of the pitch the free kick was taken from**, because a free kick's tactical purpose changes with field position:
- **Defensive third** — primarily about safely clearing danger and restarting possession; expect mostly short/backward distribution rather than direct box deliveries.
- **Middle third** — about progressing or switching the point of attack; a mix of short combination play and longer probing balls forward.
- **Attacking third** — functionally a set-piece delivery into the box, and is the group the Near/Central/Far-Post/Short and technique breakdown above is most meaningful for, since these are the free kicks that most resemble corners in intent.

A free-kick pass is **completed** when it reaches a teammate. A direct free-kick shot counts as completed when it is on target (a goal or a save).

Each of the three groups gets its own count of free kicks taken, completion rate, and (for the attacking third only) the same zone/technique/goal breakdown used for corners.

## Dashboard Template
The dashboard's look and structure are fixed by an approved template, so every build produces the same report. The reference implementation is `template/template.html`, previewed with placeholder data from `template/mock_data.js`.

### Build mechanism
- The template contains a single placeholder: `<script id="report-data" type="application/json">__REPORT_DATA__</script>`.
- The build step replaces `__REPORT_DATA__` with the JSON described in the **Data Contract** below (escaping any `</` as `<\/`), removes the `<script src="mock_data.js">` line, and saves the result as a single self-contained `.html` file named `<Team_Name>_Scouting_Report.html`.
- The build step must not edit the template's HTML, CSS or JavaScript. If the dashboard needs to change, the template is changed and re-approved, not the build output.
- The template does its own light formatting and aggregation (per-match averages, per-90 values, pass %, zone shares, set-piece tables, auto-written readings). The extractor supplies the raw values in the contract; it does not pre-format numbers as strings.

### Navigation and layout
- **Header:** team name + "Scouting Report", competition, season, number of matches analysed, generation date, a theme toggle, and summary chips: record (W-D-L), points, goals for–against, clean sheets, average possession, primary formation.
- **Tabs** (sticky while scrolling), in this order. Each tab and sub-tab has its own URL hash (e.g. `#tactics/buildup`) so a view can be linked to directly:
  1. **Overview**: one-paragraph season summary; recent form (last 10 results as W/D/L badges); key numbers per match (goals for/against, xG for/against, shots, PPDA); a small in-possession formation diagram; key players (top scorer, top assister, highest xG, most minutes); and 4 scouting takeaways, each linking to the tab it comes from.
  2. **Record & Results**: record tiles; results table (date, stage, home/away, opponent, venue, score, result, possession, xG for–against, formation) with sortable columns, W/D/L and Home/Away filters, and a click-to-expand match timeline.
  3. **Squad by Position**: one table grouped Goalkeepers / Defenders / Midfielders / Forwards, sortable within each group, with a group filter and a **Season totals / Per 90** toggle.
  4. **Team Statistics**: one tile per season total, each with its per-match average (xG tiles also show goals minus xG).
  5. **Formation**: the in-possession and out-of-possession diagrams side by side, an optional overlay that draws each player's shift from the other phase, a table of each slot's two average positions ranked by shift distance, and a bar chart of formations used.
  6. **Tactical Analysis**, with sub-tabs: Style of Play, Possession, Build-Up Zones, Pressure Points, Attacking Threats, Area Overloads.
  7. **Corners & Free Kicks**, with sub-tabs: Corners, Free Kicks.
- **Explanations:** every section has a short intro under its heading. Every tactical and set-piece view has two boxes next to the visualization: **How to read this** (fixed plain-language text taken from this spec) and **What it says** (sentences written by the template from the data, e.g. "Build-up is tilted toward the left flank (31% vs 22%)").
- **Zone grid:** 6 columns × 4 rows over the 109.7 m × 73.2 m pitch (each cell 18.28 m × 18.3 m). Columns are labeled **A–F** from the team's own goal forward (A–B defensive third, C–D middle third, E–F attacking third); rows **1–4** run from the team's left touchline to its right. Each cell shows its label, count and share of the total. Each zone map has a companion bar chart of the share by third and by channel (left = row 1, center = rows 2–3, right = row 4).
- **Style of Play gauges:** each indicator has a banded gauge using these rough reference ranges, which are labeled in the dashboard as rough guides, not league benchmarks:
  - Possession: below 45% cedes the ball, 45–55% shared, above 55% dominates.
  - Average pass length: below 16 m short, 16–22 m mixed, above 22 m direct.
  - Forward pass share: below 30% patient, 30–40% balanced, above 40% vertical.
  - Pass accuracy: below 78% low, 78–85% average, above 85% high.
  - PPDA: below 10 high press, 10–13 mid, above 13 sits off.
- **Set-piece views:** delivery diagrams draw a line from where each delivery started to where it ended. Corners use a zoomed view of the attacking end and can be filtered by zone and technique. Free kicks use the full pitch; clicking a third's summary card shows that third. Corners and attacking-third free kicks each have a zone × technique table with totals, shots, goals and shot %.

### Visual rules
- **Theme:** light by default; follows the device's dark mode, with a manual toggle (System / Light / Dark). All colors are defined once as CSS variables with light and dark values.
- **Pitch:** every pitch drawing uses a viewBox in meters (109.7 × 73.2) with standard markings (16.5 m penalty box, 5.5 m goal area, 9.15 m circle and arcs, 11 m penalty spot). The team always attacks left → right, and each diagram states the direction.
- **Fixed color meanings:**
  - Blue = in possession / the scouted team's main data color.
  - Orange = out of possession.
  - Shots: goal = orange, on target = blue, off target = gray.
  - Set-piece deliveries: led to a goal = orange, led to a shot = blue, no shot = gray.
  - Zone maps: one blue ramp, where darker means more.
  - Results: W = green, D = gray, L = red, always shown with the letter.
- **Interaction:** every plotted mark (zone, shot, player dot, possession point, delivery) shows its details on hover, on click/tap, or on keyboard focus. Clicking a player in the top-shooters table shows only that player's shots.
- **Responsive:** the layout works on phone-width screens with no sideways page scrolling; wide tables scroll inside their own container.
- **Print:** printing shows every tab and sub-tab in sequence, without navigation controls.

### Data Contract
The build writes exactly one JSON object with these fields. All spatial values are already in **meters**:
- `x` = distance from the team's **own** goal line, with the team always attacking toward x = 109.7.
- `y` = distance from the team's **left** touchline (the top edge of every diagram).

Clock strings are `"MM:SS"` copied from each event's own `minute`/`second`.

| Field | Shape |
|---|---|
| `meta` | `{ team, competition, season, generated, pitch: { length_m: 109.7, width_m: 73.2 } }` |
| `record` | `{ played, won, drawn, lost, points, goals_for, goals_against, clean_sheets }` |
| `matches[]` | `{ id, date "YYYY-MM-DD", stage, stadium, home_away "H"/"A", opponent, team_score, opp_score, result "W"/"D"/"L", possession_pct, xg_for, xg_against, formation, timeline[] }` in date order |
| `matches[].timeline[]` | `{ clock "MM:SS", period, side "team"/"opp", type "goal"/"own_goal"/"yellow"/"second_yellow"/"red"/"sub", player, detail }` in match-clock order |
| `squad[]` | `{ name, jersey, group "GK"/"DEF"/"MID"/"FWD", position, apps, starts, minutes, goals, assists, shots, xg, passes_att, passes_cmp, tackles, interceptions, dribbles_att, dribbles_cmp, fouls, yellow, red }` |
| `team_stats` | `{ goals_for, goals_against, shots, shots_on_target, xg_for, xg_against, pass_accuracy_pct, possession_pct, fouls, yellow, red, clean_sheets }` |
| `formation` | `{ primary, matches_used, matches_total, usage[] { formation, matches }, in_possession[], out_of_possession[] }`, with each position as `{ slot, abbr, player, x_m, y_m }`. `abbr` is the short position code (e.g. RWB) and matches between the two phases |
| `style` | `{ possession_pct, avg_pass_length_m, forward_pass_share_pct, pass_accuracy_pct, ppda }` |
| `zones` | `{ cols: 6, rows: 4, cell_length_m, cell_width_m, buildup[4][6], pressure[4][6], overloads[4][6] }`: season counts, indexed `[row][col]` |
| `shots[]` | `{ match_id, clock, player, x_m, y_m, xg, outcome "Goal"/"On Target"/"Off Target" }` |
| `corners[]` | `{ match_id, clock, side "left"/"right", technique, zone, start_x_m, start_y_m, end_x_m, end_y_m, shot, goal }` |
| `free_kicks[]` | `{ match_id, clock, third "Defensive"/"Middle"/"Attacking", completed, technique, zone, start_x_m, start_y_m, end_x_m, end_y_m, shot, goal }` |

Value rules:
- `technique` is one of `"Inswinging"`, `"Outswinging"`, `"Straight"`, `"Not recorded"`. It is never guessed when the source data has no value.
- `zone` is one of `"Near Post"`, `"Central"`, `"Far Post"`, `"Short"`, `"Direct Shot"`. `"Direct Shot"` is used only for free kicks.
- `shot` / `goal` are true if the possession the set piece started produced a shot or goal, including second balls and rebounds.
- Defensive- and middle-third free kicks still carry a `zone` and `technique` value (normally `"Short"` / `"Not recorded"`), but these are not broken down in the dashboard.
- Players are grouped by the position they played most minutes in.

## Acceptance Criteria
- Output is an interactive dashboard
- Dashboard is labeled for each section
- Timestamps are accurate to the video
- All spatial measurements (distances, pitch positions, zone sizes) are displayed in SI units (meters), not the source data's yard-based grid
- Formation is shown separately for in-possession and out-of-possession phases
- Free kicks are broken down by defensive/middle/attacking third, with the near/central/far-post/short delivery breakdown applied to attacking-third free kicks and corners
- Every tactical visualization (build-up zones, pressure points, attacking threats, area overloads, possession, style of play) is accompanied by a plain-language explanation of what the numbers mean on the field
- Every point on the per-match possession chart identifies its opponent, date, venue, and score on hover or on click/tap
- The output is produced from the approved template (`template/template.html`) by inserting data only; its tabs, layout, colors and explanation text match the Dashboard Template section
- The embedded data follows the Data Contract exactly (field names, units, allowed values)
- The dashboard works in light and dark mode and at phone width with no sideways page scrolling
