# AI-LOG

This log records significant use of AI tools in the project, as required by section 12 of the brief.

**Tool used:** Claude (Anthropic), via claude.ai.

| Date | What I asked for | What the AI produced | What I checked or changed |
|---|---|---|---|
| 2026-09 (Week 9) | Help choosing a brief and a suitable dataset | Suggested the Language and Country Explorer brief using AUSTLANG; checked the data.gov.au listing and fields | Confirmed the dataset page and the CC BY 4.0 licence myself |
| 2026-10-08 | Generate the application code, tests and documentation | `src/` modules, `app.py`, `scripts/fetch_data.py`, 16 tests, README, architecture diagram | _Fill in: e.g. read every file, ran `pytest`, ran the app with the real data, fixed X_ |
| _date_ | _next significant use_ | | |

## Verification of AI output

_Fill in honestly before submitting. Examples of what to record:_

- Ran `python scripts/fetch_data.py` and checked the record count and columns against the data.gov.au data dictionary.
- Ran `pytest -v`: all tests passed.
- Checked the haversine result for Perth to Sydney against an online distance calculator.
- Tried misspelled searches and invalid coordinates in the running app.
- Anything you changed, rejected or rewrote, and why.

## Cultural content

AI was **not** used to generate any language, cultural or historical content. All language names, alternative names and locations shown in the app come from the AUSTLANG dataset. The test fixture uses obviously fake placeholder names ("Test Alpha", "Test Bravo") so that no real language data is invented.
