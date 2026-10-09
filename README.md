# AUSTLANG Explorer

A Streamlit web app for exploring Aboriginal and Torres Strait Islander language varieties recorded in the AUSTLANG dataset published by AIATSIS. Built for the CITS1501 project under the **Language and Country Explorer** brief.

**Who it is for:** students, teachers and visitors who want to find out which languages are recorded near a place, look up a language even when they are unsure of the spelling, and see an overview of how the records are distributed.

**Live app:** _add your Streamlit Community Cloud link here_
**Author:** Zhiwen Chen

## Features

| View | What the user can do |
|---|---|
| Overview | Headline figures, a map of all recorded points, north/south split at the Tropic of Capricorn, distribution of alternative names, records by state/territory, densest map areas |
| Search languages | Search names and alternative spellings with typo-tolerant fuzzy matching; adjustable strictness |
| Languages near a place | Pick a town or enter coordinates; see the nearest language points, their distances and a map |
| About the data | Source, licence, how the data is used, respectful-use and privacy notes |

## Data

- **Source:** AUSTLANG dataset, Australian Institute of Aboriginal and Torres Strait Islander Studies (AIATSIS), published on data.gov.au: https://data.gov.au/data/dataset/austlang-dataset-001
- **Licence:** Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Fields used:** language code, language name, alternative names, approximate latitude/longitude, record URI, and state/territory where present.
- **Cleaning** (`src/data_loader.py`): strip whitespace and the UTF-8 byte-order mark; drop records with no code or name; drop duplicate codes; convert coordinates to numbers and set aside any outside Australia; split alternative names into lists.
- The app checks that at least 200 records remain after cleaning.

No language, cultural or historical content in the app is AI-generated; everything shown comes from the dataset.

## Install and run

Requires Python 3.10+.

```bash
git clone <your-repo-url>
cd austlang-explorer
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python scripts/fetch_data.py     # downloads data/austlang.csv and reports record counts
streamlit run app.py
```

The app opens at http://localhost:8501.

## Run the tests

```bash
pytest -v
```

Manual user-workflow tests are listed in `docs/TESTING.md`.

16 automated tests in `tests/test_app.py` cover data cleaning, the distance algorithm, the fuzzy search algorithm, the analysis functions, invalid input and boundary cases. They use a small file of placeholder records (`tests/fixtures/sample.csv`) that deliberately includes bad rows.

## Project structure

```
app.py                  Streamlit interface: navigation and the four views
src/data_loader.py      Load, clean and validate the CSV
src/geo.py              Haversine distance and nearest-languages algorithm
src/search.py           Levenshtein distance and fuzzy name search
src/analysis.py         Summary statistics, zones, grid density
scripts/fetch_data.py   Download the dataset from AIATSIS
tests/                  Automated tests and fixture data
docs/ARCHITECTURE.md    Architecture and data-flow diagram
AI-LOG.md               Record of AI tool use
```

## Deployment

Deployed on Streamlit Community Cloud from the GitHub repository's `main` branch, with `app.py` as the entry point. `data/austlang.csv` is committed so the deployed app has its data without calling an external API.

## Security and privacy

The app has no accounts, collects no personal information, stores nothing the user types and uses no API keys or passwords. All user input (search text, coordinates, numbers) is validated before use, and errors are shown as messages rather than crashes.

## Attribution

Data: AUSTLANG dataset, AIATSIS, via data.gov.au, CC BY 4.0. Language locations are approximate reference points, not boundaries. For authoritative information, consult the AUSTLANG record for each language or the relevant language centre.
