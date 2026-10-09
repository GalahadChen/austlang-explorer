"""Fuzzy search over language names and their alternative spellings.

Many languages in AUSTLANG are recorded under several spellings, so an exact
search often misses. This module scores every name and synonym against the
user's query using edit distance (Levenshtein distance), written from scratch.
"""

import re
import unicodedata

MAX_QUERY_LENGTH = 50


def normalise(text):
    """Lower-case, remove accents and punctuation, and collapse spaces."""
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9 ]", " ", text.lower())
    return " ".join(text.split())


def levenshtein(a, b):
    """Minimum number of single-character edits (insert, delete, substitute)
    needed to turn string a into string b.

    Dynamic programming, keeping only two rows of the table, so memory is
    O(len(b)) and time is O(len(a) * len(b)).
    """
    if a == b:
        return 0
    if len(a) == 0:
        return len(b)
    if len(b) == 0:
        return len(a)

    previous = list(range(len(b) + 1))
    for i, char_a in enumerate(a, start=1):
        current = [i]
        for j, char_b in enumerate(b, start=1):
            cost = 0 if char_a == char_b else 1
            current.append(min(
                previous[j] + 1,         # delete a character from a
                current[j - 1] + 1,      # insert a character into a
                previous[j - 1] + cost,  # substitute (or match)
            ))
        previous = current
    return previous[-1]


def similarity(query, candidate):
    """Score between 0 and 1 for how well candidate matches query.

    1.0  exact match after normalising
    0.9  candidate starts with the query (e.g. typing the first few letters)
    0.8  query appears inside the candidate
    else 1 - edit_distance / length of the longer string
    """
    q = normalise(query)
    c = normalise(candidate)
    if not q or not c:
        return 0.0
    if q == c:
        return 1.0
    if c.startswith(q):
        return 0.9
    if q in c:
        return 0.8
    return 1 - levenshtein(q, c) / max(len(q), len(c))


def validate_query(query):
    """Raise ValueError for empty or overly long queries; return the trimmed query."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Please enter a language name to search for.")
    query = query.strip()
    if len(query) > MAX_QUERY_LENGTH:
        raise ValueError(f"Search text must be {MAX_QUERY_LENGTH} characters or fewer.")
    if not normalise(query):
        raise ValueError("Search text must contain at least one letter or number.")
    return query


def fuzzy_search(df, query, threshold=0.6, limit=20):
    """Search names and synonyms; return the best matches as a list of dicts.

    Each language is scored by its best-matching name or synonym, and that
    matching text is reported so users can see why a result appeared.
    """
    query = validate_query(query)
    if not 0 <= threshold <= 1:
        raise ValueError("Threshold must be between 0 and 1.")

    results = []
    for row in df.itertuples(index=False):
        best_score = similarity(query, row.name)
        best_match = row.name
        for synonym in row.synonyms:
            score = similarity(query, synonym)
            if score > best_score:
                best_score, best_match = score, synonym
        if best_score >= threshold:
            results.append({
                "code": row.code,
                "name": row.name,
                "matched_on": best_match,
                "score": round(best_score, 2),
                "uri": row.uri,
            })

    # Highest score first; ties broken alphabetically by name.
    results.sort(key=lambda item: (-item["score"], item["name"]))
    return results[:limit]
