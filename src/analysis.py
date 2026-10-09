"""Summary statistics and groupings shown on the Overview page."""

import math

import pandas as pd

# The Tropic of Capricorn (about 23.44 degrees south) is used as a simple,
# purely geographic way to split the continent into a northern and a southern zone.
TROPIC_OF_CAPRICORN = -23.44

SYNONYM_BINS = [
    ("0", 0, 0),
    ("1", 1, 1),
    ("2-4", 2, 4),
    ("5-9", 5, 9),
    ("10+", 10, math.inf),
]


def summary_stats(df):
    """Headline numbers for the dataset."""
    total = len(df)
    if total == 0:
        return {"total": 0, "with_location": 0, "pct_location": 0.0,
                "with_synonyms": 0, "mean_synonyms": 0.0, "max_synonyms": 0}
    with_location = int(df["has_location"].sum())
    return {
        "total": total,
        "with_location": with_location,
        "pct_location": round(100 * with_location / total, 1),
        "with_synonyms": int((df["synonym_count"] > 0).sum()),
        "mean_synonyms": round(float(df["synonym_count"].mean()), 2),
        "max_synonyms": int(df["synonym_count"].max()),
    }


def counts_by_state(df):
    """Number of records per state/territory, largest first."""
    counts = df["state"].value_counts().rename_axis("state").reset_index(name="count")
    counts["percent"] = (100 * counts["count"] / len(df)).round(1) if len(df) else 0.0
    return counts


def zone_of(lat):
    """'North' if the point is north of the Tropic of Capricorn, else 'South'."""
    if pd.isna(lat):
        return "No location"
    return "North of Tropic" if lat > TROPIC_OF_CAPRICORN else "South of Tropic"


def zone_counts(df):
    """Records per zone, in a fixed order."""
    zones = df["lat"].apply(zone_of)
    order = ["North of Tropic", "South of Tropic", "No location"]
    counts = zones.value_counts().reindex(order, fill_value=0)
    return counts.rename_axis("zone").reset_index(name="count")


def synonym_distribution(df):
    """How many languages have 0, 1, 2-4, 5-9 or 10+ alternative names."""
    rows = []
    for label, low, high in SYNONYM_BINS:
        mask = (df["synonym_count"] >= low) & (df["synonym_count"] <= high)
        rows.append({"alternative_names": label, "languages": int(mask.sum())})
    return pd.DataFrame(rows)


def grid_cell(lat, lon, cell_deg):
    """Return the (south, west) corner of the grid cell containing the point.

    math.floor means a point exactly on a cell edge belongs to the cell to its
    north/east, so every point falls in exactly one cell.
    """
    return (math.floor(lat / cell_deg) * cell_deg,
            math.floor(lon / cell_deg) * cell_deg)


def grid_density(df, cell_deg=2.0, top=10):
    """Split the map into square cells and rank cells by number of language points."""
    if cell_deg <= 0:
        raise ValueError("Cell size must be greater than 0.")
    counts = {}
    for row in df.itertuples(index=False):
        if not row.has_location:
            continue
        cell = grid_cell(row.lat, row.lon, cell_deg)
        counts[cell] = counts.get(cell, 0) + 1

    rows = []
    for (south, west), count in counts.items():
        rows.append({
            "centre_lat": round(south + cell_deg / 2, 2),
            "centre_lon": round(west + cell_deg / 2, 2),
            "languages": count,
        })
    result = pd.DataFrame(rows, columns=["centre_lat", "centre_lon", "languages"])
    result = result.sort_values(["languages", "centre_lat"], ascending=[False, True])
    return result.head(top).reset_index(drop=True)
