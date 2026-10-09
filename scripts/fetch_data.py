"""Get the AUSTLANG dataset into data/austlang.csv and check it.

Option 1 - download automatically:
    python scripts/fetch_data.py

Option 2 - if the download fails, download the CSV in your web browser, then:
    python scripts/fetch_data.py ~/Downloads/<the-file-you-downloaded>.csv

Either way the script prints the record count and columns, so you can check
the data before running the app.
"""

import shutil
import ssl
import sys
import urllib.request
from pathlib import Path

# Allow "from src..." imports when run as a script.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data_loader import check_minimum_records, clean, load_raw  # noqa: E402

SOURCE_URLS = [
    "https://api.aiatsis.gov.au/files/public/austlang/austlang_dataset.csv",
    "https://data.gov.au/data/dataset/70132e6f-259c-4e0f-9f95-4aed1101c053/resource/"
    "e9a9ea06-d821-4b53-a05f-877409a1a19c/download/aiatsis_austlang_endpoint_001.csv",
]
OUTPUT = PROJECT_ROOT / "data" / "austlang.csv"


def ssl_context():
    """Use certifi's certificates when available.

    Python installed from python.org on macOS often has no certificates set up,
    which causes CERTIFICATE_VERIFY_FAILED. certifi fixes this safely.
    """
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def download(url):
    """Download url and return the bytes. Raises an exception on failure."""
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (CITS1501 project)"})
    with urllib.request.urlopen(request, timeout=180, context=ssl_context()) as response:
        return response.read()


def fetch():
    """Try each source URL in turn and save the first one that works."""
    for url in SOURCE_URLS:
        print(f"Trying {url}")
        try:
            content = download(url)
        except Exception as error:  # report and try the next source
            print(f"  failed: {type(error).__name__}: {error}")
            continue
        if not content.strip() or content.lstrip()[:1] == b"<":
            print("  failed: the server returned a web page, not a CSV file")
            continue
        OUTPUT.write_bytes(content)
        print(f"  saved {len(content):,} bytes to {OUTPUT}")
        return True
    return False


def report():
    """Print what the data looks like after loading and cleaning."""
    raw = load_raw(OUTPUT)
    print(f"\nRaw records: {len(raw)}")
    print(f"Columns: {list(raw.columns)}")
    cleaned = clean(raw)
    print(f"Records after cleaning: {check_minimum_records(cleaned)}")
    print(f"Records with a usable location: {int(cleaned['has_location'].sum())}")
    print("\nData is ready. Next: streamlit run app.py")


def main():
    OUTPUT.parent.mkdir(exist_ok=True)

    if len(sys.argv) > 1:
        source = Path(sys.argv[1]).expanduser()
        if not source.exists():
            sys.exit(f"File not found: {source}")
        if source.resolve() != OUTPUT.resolve():
            shutil.copyfile(source, OUTPUT)
            print(f"Copied {source} to {OUTPUT}")
    elif not fetch():
        sys.exit(
            "\nAutomatic download failed. Download the CSV in your browser instead:\n"
            f"  {SOURCE_URLS[0]}\n"
            "then run:\n"
            "  python scripts/fetch_data.py ~/Downloads/<downloaded-file>.csv"
        )
    report()


if __name__ == "__main__":
    main()
