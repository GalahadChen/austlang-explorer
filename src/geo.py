"""Distance calculations and the nearest-languages algorithm.

AUSTLANG gives an approximate point for each language variety. Given any place
in Australia, this module finds the language points closest to it.
"""

import heapq
import math

from src.data_loader import is_valid_coordinate

EARTH_RADIUS_KM = 6371.0


def validate_coordinates(lat, lon):
    """Check user-supplied coordinates. Raises ValueError if they are unusable."""
    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError):
        raise ValueError("Latitude and longitude must be numbers.")
    if math.isnan(lat) or math.isnan(lon):
        raise ValueError("Latitude and longitude must be numbers.")
    if not is_valid_coordinate(lat, lon):
        raise ValueError(
            "That point is outside Australia. Latitude must be between -45 and -9 "
            "and longitude between 112 and 155."
        )
    return lat, lon


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in kilometres between two points on Earth.

    The haversine formula treats the Earth as a sphere. That is accurate to
    within about 0.5%, which is more than enough for approximate points.
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (math.sin(d_phi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2)
    # min() guards against tiny floating-point errors pushing a above 1.
    c = 2 * math.asin(min(1.0, math.sqrt(a)))
    return EARTH_RADIUS_KM * c


def nearest_languages(df, lat, lon, k=10, max_km=None):
    """Return the k language records closest to (lat, lon).

    Steps:
      1. Validate the query point and k.
      2. Skip records without a location.
      3. Compute the haversine distance to every remaining record.
      4. Optionally drop records further than max_km.
      5. Use a heap to keep the k smallest distances (O(n log k)).

    Returns a list of dicts sorted from nearest to furthest.
    """
    lat, lon = validate_coordinates(lat, lon)
    if not isinstance(k, int) or k < 1:
        raise ValueError("k must be a whole number of at least 1.")
    if max_km is not None and max_km <= 0:
        raise ValueError("max_km must be greater than 0.")

    candidates = []
    for row in df.itertuples(index=False):
        if not row.has_location:
            continue
        distance = haversine_km(lat, lon, row.lat, row.lon)
        if max_km is not None and distance > max_km:
            continue
        # The code is a tie-breaker so equal distances sort predictably.
        candidates.append((distance, row.code, row))

    closest = heapq.nsmallest(k, candidates, key=lambda item: (item[0], item[1]))

    results = []
    for distance, _code, row in closest:
        results.append({
            "code": row.code,
            "name": row.name,
            "distance_km": round(distance, 1),
            "lat": row.lat,
            "lon": row.lon,
            "uri": row.uri,
        })
    return results


def count_within_radius(df, lat, lon, radius_km):
    """How many language points lie within radius_km of the given point."""
    lat, lon = validate_coordinates(lat, lon)
    if radius_km <= 0:
        raise ValueError("Radius must be greater than 0.")
    count = 0
    for row in df.itertuples(index=False):
        if row.has_location and haversine_km(lat, lon, row.lat, row.lon) <= radius_km:
            count += 1
    return count
