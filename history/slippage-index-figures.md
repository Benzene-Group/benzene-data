# Grid Date Slippage Index, November 2026: figures and sources (DRAFT)

Page: /home/claude/benzene-data-repo/site/slippage-index.html (not committed, not published; robots set to noindex, nofollow while a draft).
Generator: /home/claude/scripts/slippage_page.py (run: `python3 -I scripts/slippage_page.py /home/claude/benzene-data-repo x`). Every figure below is computed by that script from the files named; nothing is typed in by hand.
Repo: Benzene-Group/benzene-data at f2b81c0 (matches origin; read only).

## Definition
A "move" = a row in history/events.csv with kind == date and |months| >= 1.0 (months = days / 30.44, rounded to 0.1, between consecutive weekly copies, matched on Project Number). Thresholds of 0.9, 0.95 and 1.0 all give 287, so there is no boundary sensitivity.

## Six-month figures (Reported: weekly copies 19 May to 17 Nov 2026)
| Figure | Value | Source and method |
|---|---|---|
| All date changes, any size | 353 | events.csv, kind == date |
| Moves of a month or more | 287 | as defined above |
| Projects with such a move | 235 | unique pid among the 287 |
| Later / earlier | 210 / 77 | sign of months |
| Smaller changes left out | 66 | 353 minus 287 |
| Projects moving more than once | 45 | pid count > 1 |
| Median later move | 19.15 months (shown "19") | median of months > 0 |
| Median earlier move | 24.0 months | median of abs(months) < 0 |
| Moves in copies of 13 and 20 Oct | 144 (86 later, 58 earlier); 50% of 287; 58 of 77 earlier moves | week in (2026-10-13, 2026-10-20) |
| Gate 2 moves | 79 later, 9 earlier (88 moves) | gate column == 2. NOTE: history.py takes gate from the NEWER copy of each pair, so this is "Gate 2 in the copy where the move appeared", not "now". On the 19 Nov register's Gate field the count is 97 later, 13 earlier (110 moves). Page uses the accurate wording. |
| Storage only | 125 of 287 (44%) | Plant Type exactly "Energy Storage System" |
| Storage only on the register | 732 of 2,188 (33%) | archive/tec-weekly/tec-register-2026-11-17.csv, Plant Type exactly ESS |
| Net over window, a month or more | 158 later, 35 earlier (193 projects) | net_date_changes.csv (first vs last copy), abs(months) >= 1 |
| Sites with any move | 203 | unique site among the 287 |
| Weekly chart series | 25 copy intervals; sums 210 / 77 (asserted) | weekly.csv for the interval list; counts from events.csv. First bar is 19 May to 2 Jun (no 26 May copy); 14 Jul and 15 Sep have zero |

Weekly (later, earlier): 2 Jun 1,1; 9 Jun 5,0; 16 Jun 2,0; 23 Jun 7,0; 30 Jun 4,2; 7 Jul 12,0; 14 Jul 0,0; 21 Jul 9,0; 28 Jul 9,1; 4 Aug 4,0; 11 Aug 9,1; 18 Aug 7,1; 25 Aug 3,0; 1 Sep 4,0; 8 Sep 5,0; 15 Sep 0,0; 22 Sep 4,1; 29 Sep 1,2; 6 Oct 7,0; 13 Oct 60,40; 20 Oct 26,18; 27 Oct 6,4; 3 Nov 15,4; 10 Nov 8,1; 17 Nov 2,1.

Note: weekly.csv's own later/earlier columns count ALL date changes (215 later, 138 counting 0.0 as earlier), so they are not used for the chart. history/substations.csv also counts all 353 changes (Alverdiscott 8 there vs 7 at a month or more); the page recomputes from events.csv at a month or more.

### Substations (moves at the site in the newer copy)
Top ten places, 15 substations (9 tie on 3): Alverdiscott 7 (5 later, 2 earlier, 4 projects); Grimsby West 5 (3/2, 2); High Marnham 5 (3/2, 4); Cilfynydd 4 (3/1, 3); Enderby 4 (3/1, 2); Leeds North Connection Node C 4 (3/1, 2); then on 3: Berryburn 275/33kV GSP (SHET), Cellarhead, Fiddlers Ferry, Kincardine North (SPT), Kingsnorth, North Anglia Connection Node A, North Anglia Connection Node E, Warley, Wymondley. Sort: moves, then later, then name.
Caveat: North Anglia Node A and Node E each show 1 project with 3 moves; may be one project whose site name changed. Worth a look before publishing.

### Technology (precedence: offshore wind, onshore wind, storage only, storage + solar, solar only, else)
Storage only 125 (89/36, median later 16.6); storage with solar 66 (41/25, 21.5); onshore wind incl. hybrids 58 (47/11, 17.0); everything else 19 (19/0, 24.0); offshore wind 12 (8/4, 35.95); solar only 7 (6/1, 32.85). Totals 287.

### Transmission owner (HOST TO), with projects on the 17 Nov copy
NGET 155 (107/48, median later 23.9; 1,278 projects; 12 per 100); SHET 67 (48/19, 16.5; 439; 15 per 100); SPT 65 (55/10, 12.0; 456; 14 per 100). OFTO (15 projects) had no moves. Medians shown to whole months with Python round-half-even (16.5 shows as 16).

## This month (Confirmed: our NESO downloads of 16 and 19 Nov)
Source: data/changes/tec-register-19-november-2026.json, months recomputed from its was/date fields; independently re-diffed inputs/tec-register-19-november-2026.csv against archive/tec/tec-register-16-november-2026.csv (same 5 date moves).
- 5 date moves, all later: Norwich Yare +16.2 (18 Dec 2025 to 24 Apr 2027); Sellindge Grid Stability Services +14.6 (11 Aug 2026 to 30 Oct 2027); Achany Extension Wind Farm +11.9 (30 Mar 2028 to 26 Mar 2029); Spennymoor Greener Grid Park, reactive row, +11.1 (29 Oct 2027 to 1 Oct 2028); Melksham (Tertiary) +6.2 (26 Jun 2026 to 31 Dec 2026). Four hold Gate 2, one Gate 1.
- 3 of 5 old dates were already past on 19 Nov (Norwich Yare, Sellindge, Melksham).
- 8 "other" entries with a blank Gate field filled in (of 12 other changes).
- Templeton BESS: two rows at Lyndhurst 132/33kV (30 MW, 19.9 MW) left, one 49.9 MW row at Lyndhurst GSP with Gate 2 joined.
- Patford Bridge Farm (200 MW, Gate 1) left.
- 19 Nov register rows: 2,186 (16 Nov: 2,188).

## 17 Nov copy vs our NESO download
archive/tec-weekly/tec-register-2026-11-17.csv vs archive/tec/tec-register-16-november-2026.csv: 2,188 rows each; identical after normalising date and number formats on Project Number, date, MW, Gate, site and customer (re-checked 21 Nov). A raw string compare differs only on formatting. Also stated in archive/tec-weekly/README.md.

## Not checked
ops/register-history.md in the Claude Project could not be read from this session (no Projects tool), so the page wording was written from the brief, not that doc. Compare before publishing.
