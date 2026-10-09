# Testing

## Automated tests

Run `pytest -v`. The 16 tests in `tests/test_app.py` cover data cleaning, the haversine and nearest-languages algorithm, Levenshtein and fuzzy search, the analysis functions, invalid input and boundary cases.

## Manual user-workflow tests

Run these against the deployed app with the real data and fill in the result column. Record any problem found and how it was fixed.

| # | Workflow | Steps | Expected result | Result / fix |
|---|---|---|---|---|
| 1 | Open the app | Visit the deployed URL | Overview loads with figures, map and charts | |
| 2 | Navigate | Click each item in the sidebar | Each of the four views opens | |
| 3 | Search exact name | Search a name copied from the map | That language is the top result, score 1.0 | |
| 4 | Search misspelling | Change one letter of that name | Same language still appears near the top | |
| 5 | Search alternative name | Search one of its alternative names | Language appears; "matched_on" shows the alternative name | |
| 6 | Search nothing found | Search "zzzzzz" with strictness 0.9 | Yellow "No matches" message, no crash | |
| 7 | Invalid search | Search "!!!" | Red error message, no crash | |
| 8 | Near a preset town | Choose Perth, WA | Nearest languages listed with distances, map centred on Perth | |
| 9 | Small radius | Set radius to 50 km in a remote area | Fewer or no results, warning if none | |
| 10 | Invalid coordinates | Custom coordinates, latitude 10 | Red "outside Australia" error, no crash | |
| 11 | Change grid size | Overview, change grid cell size | Density table updates | |
| 12 | Record link | Click "Open" in a results table | AUSTLANG record opens in a new tab | |
