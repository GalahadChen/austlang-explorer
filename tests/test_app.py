"""Automated tests for AUSTLANG Explorer.

All tests use tests/fixtures/sample.csv, a small file of made-up placeholder
records ("Test Alpha", "Test Bravo", ...). It deliberately contains bad rows
(duplicate code, missing code, missing name, missing and impossible coordinates)
so the cleaning and edge-case handling can be checked without real data.

Run with:  pytest -v
"""

from pathlib import Path

import pandas as pd
import pytest

from src.analysis import (grid_cell, grid_density, summary_stats,
                          synonym_distribution, zone_counts)
from src.data_loader import (check_minimum_records, clean, load_dataset,
                             load_raw, split_synonyms)
from src.geo import (count_within_radius, haversine_km, nearest_languages,
                     validate_coordinates)
from src.search import fuzzy_search, levenshtein, normalise, similarity

FIXTURE = Path(__file__).parent / "fixtures" / "sample.csv"
PERTH = (-31.95, 115.86)
SYDNEY = (-33.87, 151.21)


@pytest.fixture
def df():
    return clean(load_raw(FIXTURE))


# ---------------------------------------------------------------- data cleaning

def test_clean_removes_missing_code_name_and_duplicates(df):
    # 10 raw rows -> 7 usable: duplicate T001, missing code and missing name removed.
    assert len(df) == 7
    assert df["code"].is_unique
    assert "Duplicate Alpha" not in df["name"].values  # first T001 kept


def test_invalid_and_missing_coordinates_are_flagged(df):
    by_code = df.set_index("code")
    assert not by_code.loc["T004", "has_location"]   # blank coordinates
    assert not by_code.loc["T005", "has_location"]   # latitude -50 is outside Australia
    assert pd.isna(by_code.loc["T005", "lat"])
    assert int(df["has_location"].sum()) == 5


def test_split_synonyms_handles_pipes_commas_and_blanks():
    assert split_synonyms("Alfa|Test Alfa") == ["Alfa", "Test Alfa"]
    assert split_synonyms(" Fox , Foxy ") == ["Fox", "Foxy"]
    assert split_synonyms("A|A|B") == ["A", "B"]
    assert split_synonyms("") == []
    assert split_synonyms(None) == []


def test_missing_file_and_too_few_records_raise_errors(df, tmp_path):
    with pytest.raises(FileNotFoundError):
        load_raw(tmp_path / "does_not_exist.csv")
    with pytest.raises(ValueError):
        check_minimum_records(df)            # 7 records < 200
    with pytest.raises(ValueError):
        load_dataset(FIXTURE)                # full pipeline enforces the minimum


def test_missing_required_column_raises():
    with pytest.raises(ValueError):
        clean(pd.DataFrame({"language_name": ["Only a name"]}))


# ---------------------------------------------------------------- distance algorithm

def test_haversine_known_distances():
    assert haversine_km(*PERTH, *PERTH) == 0
    # One degree of latitude is about 111.19 km on a sphere of radius 6371 km.
    assert haversine_km(-30, 120, -31, 120) == pytest.approx(111.19, abs=0.01)
    # Perth to Sydney is about 3,290 km.
    assert 3250 < haversine_km(*PERTH, *SYDNEY) < 3320
    # Distance is the same in both directions.
    assert haversine_km(*PERTH, *SYDNEY) == pytest.approx(haversine_km(*SYDNEY, *PERTH))


def test_nearest_languages_sorted_and_skip_unlocated(df):
    results = nearest_languages(df, *PERTH, k=3)
    codes = [r["code"] for r in results]
    assert codes[0] == "T001"                # same point as Perth
    assert codes[1] == "T002"                # about 7 km away
    distances = [r["distance_km"] for r in results]
    assert distances == sorted(distances)
    assert "T004" not in codes and "T005" not in codes


def test_nearest_languages_boundaries(df):
    # Asking for more results than exist returns every located record.
    assert len(nearest_languages(df, *PERTH, k=100)) == 5
    # A small radius limits the results.
    assert [r["code"] for r in nearest_languages(df, *PERTH, k=10, max_km=50)] == ["T001", "T002"]
    assert count_within_radius(df, *PERTH, 50) == 2


def test_invalid_location_input_raises(df):
    with pytest.raises(ValueError):
        validate_coordinates("abc", 115)
    with pytest.raises(ValueError):
        validate_coordinates(51.5, -0.1)     # London is outside Australia
    with pytest.raises(ValueError):
        nearest_languages(df, *PERTH, k=0)
    with pytest.raises(ValueError):
        nearest_languages(df, *PERTH, k=5, max_km=-1)


# ---------------------------------------------------------------- fuzzy search algorithm

def test_levenshtein_known_values():
    assert levenshtein("kitten", "sitting") == 3
    assert levenshtein("", "abc") == 3
    assert levenshtein("same", "same") == 0
    assert levenshtein("abc", "acb") == 2


def test_normalise_and_similarity():
    assert normalise("  Té-st   ALPHA! ") == "te st alpha"
    assert similarity("test alpha", "Test Alpha") == 1.0
    assert similarity("test al", "Test Alpha") == 0.9   # prefix
    assert similarity("alpha", "Test Alpha") == 0.8     # substring


def test_fuzzy_search_finds_misspellings_and_synonyms(df):
    # A one-letter typo still finds the right language.
    assert fuzzy_search(df, "Test Bravp")[0]["code"] == "T002"
    # Searching an alternative name finds the language and reports the match.
    top = fuzzy_search(df, "Foxy")[0]
    assert top["code"] == "T007" and top["matched_on"] == "Foxy"
    # Nothing similar returns an empty list rather than crashing.
    assert fuzzy_search(df, "zzzzzzzz", threshold=0.9) == []


def test_fuzzy_search_rejects_invalid_queries(df):
    for bad in ["", "   ", "!!!", "x" * 51]:
        with pytest.raises(ValueError):
            fuzzy_search(df, bad)
    with pytest.raises(ValueError):
        fuzzy_search(df, "alpha", threshold=1.5)


# ---------------------------------------------------------------- analysis

def test_summary_stats_and_zones(df):
    stats = summary_stats(df)
    assert stats["total"] == 7
    assert stats["with_location"] == 5
    assert stats["pct_location"] == pytest.approx(71.4)
    assert stats["with_synonyms"] == 3
    zones = dict(zip(zone_counts(df)["zone"], zone_counts(df)["count"]))
    assert zones == {"North of Tropic": 1, "South of Tropic": 4, "No location": 2}
    assert summary_stats(df.iloc[0:0])["total"] == 0   # empty data does not crash


def test_synonym_distribution_counts_every_language(df):
    dist = synonym_distribution(df)
    assert dist["languages"].sum() == len(df)
    assert dict(zip(dist["alternative_names"], dist["languages"]))["2-4"] == 2


def test_grid_cells_edges_and_density(df):
    # A point exactly on a cell edge belongs to exactly one cell.
    assert grid_cell(-24.0, 134.0, 2.0) == (-24.0, 134.0)
    assert grid_cell(-24.01, 134.0, 2.0) == (-26.0, 134.0)
    density = grid_density(df, cell_deg=2.0)
    assert density["languages"].sum() == 5
    assert density.iloc[0]["languages"] == 2      # Perth cell holds T001 and T002
    with pytest.raises(ValueError):
        grid_density(df, cell_deg=0)
