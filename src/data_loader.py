"""Load and clean the AUSTLANG dataset.

The raw CSV is published by AIATSIS on data.gov.au. This module turns it into a
tidy pandas DataFrame with short column names, valid coordinates and a list of
alternative names (synonyms) for each language.
"""

from pathlib import Path

import pandas as pd

# Minimum number of records required by the CITS1501 brief.
MIN_RECORDS = 200

# Rough bounding box around Australia, including the Torres Strait.
# Coordinates outside this box are treated as data errors.
AUS_LAT_RANGE = (-45.0, -9.0)
AUS_LON_RANGE = (112.0, 155.0)

# Raw column name -> short name used in the rest of the app.
COLUMN_MAP = {
    "language_code": "code",
    "language_name": "name",
    "language_synonym": "synonyms_raw",
    "approximate_latitude_of_language_variety": "lat",
    "approximate_longitude_of_language_variety": "lon",
    "uri": "uri",
    "state_territory": "state",
}

REQUIRED_COLUMNS = ["language_code", "language_name"]


def load_raw(path):
    """Read the raw CSV file. Raises FileNotFoundError with a helpful message."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Data file not found: {path}. Run 'python scripts/fetch_data.py' first."
        )
    # utf-8-sig removes the byte-order mark (BOM) at the start of the file.
    return pd.read_csv(path, encoding="utf-8-sig", dtype=str)


def standard_column_name(column):
    """Map a raw column header to the name used in COLUMN_MAP.

    Headers are lower-cased and spaces become underscores, so "Language Code"
    and "language_code" are treated the same. Headers that mention latitude,
    longitude or synonym are matched even if their exact wording differs.
    """
    name = str(column).strip().lstrip("﻿").lower().replace(" ", "_")
    if name in COLUMN_MAP:
        return name
    if "latitude" in name:
        return "approximate_latitude_of_language_variety"
    if "longitude" in name:
        return "approximate_longitude_of_language_variety"
    if "synonym" in name:
        return "language_synonym"
    return name


def split_synonyms(value):
    """Turn the raw synonym text into a clean list of names.

    The data dictionary describes the field as pipe-delimited, but another part
    of the metadata says comma-delimited, so both separators are handled.
    """
    if not isinstance(value, str) or not value.strip():
        return []
    separator = "|" if "|" in value else ","
    parts = [part.strip() for part in value.split(separator)]
    # Keep order but drop blanks and duplicates.
    seen = []
    for part in parts:
        if part and part not in seen:
            seen.append(part)
    return seen


def is_valid_coordinate(lat, lon):
    """Return True if lat/lon are real numbers inside the Australian box."""
    if pd.isna(lat) or pd.isna(lon):
        return False
    return (AUS_LAT_RANGE[0] <= lat <= AUS_LAT_RANGE[1]
            and AUS_LON_RANGE[0] <= lon <= AUS_LON_RANGE[1])


def clean(raw):
    """Clean the raw DataFrame and return a new, tidy DataFrame."""
    df = raw.copy()
    df.columns = [standard_column_name(col) for col in df.columns]

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")

    # Keep only the columns we know about, then rename them.
    known = [col for col in COLUMN_MAP if col in df.columns]
    df = df[known].rename(columns=COLUMN_MAP)
    for optional in ["synonyms_raw", "lat", "lon", "uri", "state"]:
        if optional not in df.columns:
            df[optional] = None

    # Trim whitespace in text columns.
    for col in ["code", "name", "synonyms_raw", "uri", "state"]:
        df[col] = df[col].where(df[col].isna(), df[col].astype(str).str.strip())

    # A record without a code or a name cannot be used.
    df = df[df["code"].notna() & (df["code"] != "")]
    df = df[df["name"].notna() & (df["name"] != "")]

    # Each language code should appear once; keep the first occurrence.
    df = df.drop_duplicates(subset="code", keep="first")

    # Coordinates: convert to numbers, blank out anything invalid.
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    valid = [is_valid_coordinate(lat, lon) for lat, lon in zip(df["lat"], df["lon"])]
    df["has_location"] = valid
    df.loc[~df["has_location"], ["lat", "lon"]] = float("nan")

    df["synonyms"] = df["synonyms_raw"].apply(split_synonyms)
    df["synonym_count"] = df["synonyms"].apply(len)
    df["state"] = df["state"].fillna("Not recorded").replace("", "Not recorded")

    return df.drop(columns=["synonyms_raw"]).reset_index(drop=True)


def check_minimum_records(df, minimum=MIN_RECORDS):
    """Raise ValueError if the cleaned dataset is smaller than required."""
    if len(df) < minimum:
        raise ValueError(f"Dataset has {len(df)} records; at least {minimum} are required.")
    return len(df)


def load_dataset(path):
    """Load, clean and check the dataset in one step (used by the app)."""
    df = clean(load_raw(path))
    check_minimum_records(df)
    return df
