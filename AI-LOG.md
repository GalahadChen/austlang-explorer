# AI-LOG

This log records significant use of AI tools in the project, as required by section 12 of the brief.

**Tool used:** Claude (Anthropic), via claude.ai.

| Stage | What the AI did | What I did |
|---|---|---|
| Planning | Reviewed the brief, suggested several briefs and datasets, and drafted a work schedule | I chose the Language and Country Explorer brief and the AUSTLANG dataset from its suggestions |
| Building | Generated the `src/` modules, `app.py`, `scripts/fetch_data.py`, 16 tests, README, architecture diagram and testing notes | I ran and tested the generated code (see Verification below) |
| Data | Changed the download script after the automatic download failed on my Mac, and loaded the file into the project | I found the dataset page on data.gov.au, downloaded the CSV in my browser and supplied it |
| Running and testing | Explained how to run the app and the tests from the terminal | I ran the app locally with the real data, checked all four views and ran the 16 tests with `pytest -v` |
| Version control | Explained the Git commands, including how to fix the commit author | I created the GitHub repository, committed the work in five stages, fixed the commit author identity and pushed the code |
| Deploying | Explained the Streamlit Community Cloud steps | I deployed the app and checked all four views on the live site |
| Report writing | Drafted the technical report from the code and the real data, and wrote the contribution statement from my answers to its questions | I answered questions about my own work, edited the report and checked that it is accurate |

## Verification of AI output

- I ran the app locally with the real AUSTLANG data (1,204 records) and opened all four views.
- I opened all four views on the deployed app at https://austlang-explorer.streamlit.app/.
- I ran the 16 automated tests with `pytest -v` on my own computer.
- Before I used it, the AI also ran the tests and tested the app with the real data. This testing found that 369 records use (0, 0) as a placeholder location, which the code excludes from the map.

## Cultural content

AI was **not** used to generate any language, cultural or historical content. All language names, alternative names and locations shown in the app come from the AUSTLANG dataset. The test fixture uses obviously fake placeholder names ("Test Alpha", "Test Bravo") so that no real language data is invented.
