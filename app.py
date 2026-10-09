"""AUSTLANG Explorer - Streamlit user interface.

Run with:  streamlit run app.py
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.analysis import (counts_by_state, grid_density, summary_stats,
                          synonym_distribution, zone_counts)
from src.data_loader import load_dataset
from src.geo import count_within_radius, nearest_languages
from src.search import fuzzy_search

DATA_PATH = Path(__file__).parent / "data" / "austlang.csv"

# General town coordinates used as quick starting points for the "near" view.
PRESET_PLACES = {
    "Perth, WA": (-31.95, 115.86),
    "Albany, WA": (-35.02, 117.88),
    "Geraldton, WA": (-28.78, 114.61),
    "Kalgoorlie, WA": (-30.75, 121.47),
    "Broome, WA": (-17.96, 122.24),
    "Darwin, NT": (-12.46, 130.84),
    "Alice Springs, NT": (-23.70, 133.88),
    "Cairns, QLD": (-16.92, 145.77),
    "Brisbane, QLD": (-27.47, 153.03),
    "Sydney, NSW": (-33.87, 151.21),
    "Melbourne, VIC": (-37.81, 144.96),
    "Adelaide, SA": (-34.93, 138.60),
    "Hobart, TAS": (-42.88, 147.33),
    "Custom coordinates": None,
}

ATTRIBUTION = (
    "Data: AUSTLANG dataset, Australian Institute of Aboriginal and Torres Strait "
    "Islander Studies (AIATSIS), via data.gov.au, licensed under CC BY 4.0."
)

st.set_page_config(page_title="AUSTLANG Explorer", page_icon="🗺️", layout="wide")


@st.cache_data
def get_data():
    """Load the dataset once and reuse it across reruns."""
    return load_dataset(DATA_PATH)


def link_table(rows, columns):
    """Show a list of result dicts as a table with clickable AUSTLANG links."""
    table = pd.DataFrame(rows)[columns]
    st.dataframe(
        table,
        hide_index=True,
        width="stretch",
        column_config={"uri": st.column_config.LinkColumn("AUSTLANG record",
                                                          display_text="Open")},
    )


def show_map(points, centre=None, zoom=3, size_col=None):
    """Plot language points (and an optional query point) on a map."""
    fig = px.scatter_map(
        points, lat="lat", lon="lon", hover_name="name",
        hover_data={"code": True, "lat": ":.2f", "lon": ":.2f"},
        zoom=zoom, height=480, size=size_col,
    )
    fig.update_traces(marker={"color": "#b5532c"})
    if centre is not None:
        fig.add_scattermap(lat=[centre[0]], lon=[centre[1]], name="Your point",
                           marker={"size": 16, "color": "#1d4e89"}, hovertext=["Your point"])
        fig.update_layout(map_center={"lat": centre[0], "lon": centre[1]})
    else:
        fig.update_layout(map_center={"lat": -26.0, "lon": 134.0})
    fig.update_layout(map_style="open-street-map", margin={"l": 0, "r": 0, "t": 0, "b": 0},
                      showlegend=False)
    st.plotly_chart(fig, width="stretch")


# ---------------------------------------------------------------- pages

def page_overview(df):
    st.title("AUSTLANG Explorer")
    st.write(
        "Explore Aboriginal and Torres Strait Islander language varieties recorded in "
        "AIATSIS's AUSTLANG dataset: where they are recorded, how many alternative "
        "names they have, and which languages are recorded near a place you choose."
    )
    stats = summary_stats(df)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Language records", stats["total"])
    c2.metric("With an approximate location", f"{stats['pct_location']}%")
    c3.metric("With alternative names", stats["with_synonyms"])
    c4.metric("Average alternative names", stats["mean_synonyms"])

    st.subheader("Where the records are")
    located = df[df["has_location"]]
    if located.empty:
        st.info("No records have a usable location.")
    else:
        show_map(located)
        st.caption("Each dot is an approximate point for a language variety, "
                   "not a boundary.")

    left, right = st.columns(2)
    with left:
        st.subheader("North vs south of the Tropic of Capricorn")
        zones = zone_counts(df)
        st.plotly_chart(px.bar(zones, x="zone", y="count", text="count",
                               color_discrete_sequence=["#b5532c"]),
                        width="stretch")
    with right:
        st.subheader("How many alternative names per language")
        dist = synonym_distribution(df)
        st.plotly_chart(px.bar(dist, x="alternative_names", y="languages", text="languages",
                               color_discrete_sequence=["#1d4e89"]),
                        width="stretch")
        st.caption("Many languages were written down by different recorders using "
                   "different spellings, which is why search must allow for variation.")

    states = counts_by_state(df)
    if not (len(states) == 1 and states["state"].iloc[0] == "Not recorded"):
        st.subheader("Records by state or territory")
        st.plotly_chart(px.bar(states, x="state", y="count", text="count",
                               color_discrete_sequence=["#5b7f3a"]),
                        width="stretch")

    st.subheader("Areas with the most recorded language points")
    cell = st.select_slider("Grid cell size (degrees)", options=[1.0, 2.0, 3.0, 5.0], value=2.0)
    st.dataframe(grid_density(df, cell_deg=cell, top=10), hide_index=True,
                 width="stretch")


def page_search(df):
    st.title("Search languages")
    st.write("Search by name or by any recorded alternative spelling. Small spelling "
             "differences are allowed.")
    query = st.text_input("Language name", max_chars=50, placeholder="Type a name")
    strictness = st.slider("Match strictness", 0.4, 1.0, 0.6, 0.05,
                           help="Higher values only show closer matches.")
    if not query:
        st.info("Enter a name to start searching.")
        return
    try:
        results = fuzzy_search(df, query, threshold=strictness)
    except ValueError as error:
        st.error(str(error))
        return
    if not results:
        st.warning(f"No matches for '{query}'. Try lowering the strictness or a "
                   "different spelling.")
        return
    st.success(f"{len(results)} match(es) found.")
    link_table(results, ["name", "code", "matched_on", "score", "uri"])


def page_near(df):
    st.title("Languages near a place")
    st.write("Choose a place to list the language varieties whose approximate points "
             "are closest to it.")
    place = st.selectbox("Place", list(PRESET_PLACES))
    if PRESET_PLACES[place] is None:
        c1, c2 = st.columns(2)
        lat = c1.number_input("Latitude", value=-31.95, format="%.4f")
        lon = c2.number_input("Longitude", value=115.86, format="%.4f")
    else:
        lat, lon = PRESET_PLACES[place]

    c1, c2 = st.columns(2)
    k = c1.slider("Number of languages", 1, 30, 10)
    radius = c2.slider("Only within (km)", 50, 2000, 500, 50)

    try:
        results = nearest_languages(df, lat, lon, k=k, max_km=radius)
        total_in_radius = count_within_radius(df, lat, lon, radius)
    except ValueError as error:
        st.error(str(error))
        return

    st.metric(f"Language points within {radius} km", total_in_radius)
    if not results:
        st.warning("No language points in that radius. Try a larger distance.")
        return
    nearest = results[0]
    st.success(f"Nearest: {nearest['name']} ({nearest['code']}), "
               f"about {nearest['distance_km']} km away.")
    show_map(pd.DataFrame(results), centre=(lat, lon), zoom=5)
    link_table(results, ["name", "code", "distance_km", "uri"])


def page_about():
    st.title("About the data")
    st.markdown(
        f"""
**Source.** {ATTRIBUTION}

**What the data contains.** For each language variety: a stable AUSTLANG code, a
name, alternative names and spellings, an approximate latitude and longitude, and a
link to the full AUSTLANG record.

**How this app uses it.** The data is loaded from a local CSV file, cleaned
(blank and duplicate records removed, invalid coordinates set aside), then searched,
measured and counted. All language information shown comes directly from the
dataset; none of it is generated.

**Using it respectfully.** Locations are approximate points supplied for
reference, not language boundaries. For authoritative information, and for
community-endorsed spellings, follow the link to each AUSTLANG record or contact
the relevant language centre. The app shows no images, recordings or names of
people, and uses only publicly released, unrestricted data.

**Privacy.** The app has no accounts, stores nothing you type, and uses no API keys.
        """
    )
    st.link_button("Open AUSTLANG at AIATSIS", "https://aiatsis.gov.au/austlang")


# ---------------------------------------------------------------- main

PAGES = {
    "Overview": page_overview,
    "Search languages": page_search,
    "Languages near a place": page_near,
    "About the data": None,
}


def main():
    st.sidebar.title("AUSTLANG Explorer")
    choice = st.sidebar.radio("Go to", list(PAGES))
    st.sidebar.caption(ATTRIBUTION)

    if choice == "About the data":
        page_about()
        return
    try:
        df = get_data()
    except (FileNotFoundError, ValueError) as error:
        st.error(f"The dataset could not be loaded: {error}")
        return
    PAGES[choice](df)


main()
