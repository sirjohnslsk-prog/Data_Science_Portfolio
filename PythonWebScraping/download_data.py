"""Download the official UCI Online Retail II dataset.

Source: https://archive.ics.uci.edu/dataset/502/online+retail+ii
License: CC BY 4.0
"""
from pathlib import Path
from urllib.request import urlretrieve
import zipfile

URL = "https://archive.ics.uci.edu/static/public/502/online%2Bretail%2Bii.zip"
HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
ZIP_PATH = RAW / "online_retail_ii.zip"
XLSX_PATH = RAW / "online_retail_II.xlsx"


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    if XLSX_PATH.exists():
        print(f"Dataset already present: {XLSX_PATH}")
        return
    print("Downloading UCI Online Retail II...")
    urlretrieve(URL, ZIP_PATH)
    with zipfile.ZipFile(ZIP_PATH) as zf:
        zf.extractall(RAW)
    ZIP_PATH.unlink(missing_ok=True)
    if not XLSX_PATH.exists():
        candidates = list(RAW.glob("*.xlsx"))
        if len(candidates) == 1:
            candidates[0].rename(XLSX_PATH)
    print(f"Saved: {XLSX_PATH}")


if __name__ == "__main__":
    main()
