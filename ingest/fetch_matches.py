import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()  # reads the .env file

API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")
BASE_URL = "https://api.football-data.org/v4"
RAW_DIR = Path("data/raw")


def fetch(endpoint, params=None, retries=3):
    """Call the API. Retry on rate limits and server errors."""
    headers = {"X-Auth-Token": API_KEY}
    for attempt in range(1, retries + 1):
        response = requests.get(
            f"{BASE_URL}/{endpoint}", headers=headers, params=params, timeout=30
        )
        if response.status_code == 200:
            return response.json()
        if response.status_code == 429 or response.status_code >= 500:
            print(f"Got {response.status_code}, waiting 60s (attempt {attempt}/{retries})")
            time.sleep(60)
            continue
        response.raise_for_status()  # other errors: stop and show the problem
    raise RuntimeError(f"Failed after {retries} attempts: {endpoint}")


def save_raw(data, name, season):
    """Save the response untouched, in a new timestamped file every time."""
    now = datetime.now()
    folder = RAW_DIR / name / f"season={season}" / f"fetched_date={now:%Y-%m-%d}"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{name}_{now:%Y%m%dT%H%M%S}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, required=True, help="Start year, e.g. 2025")
    args = parser.parse_args()

    if not API_KEY:
        raise SystemExit("FOOTBALL_DATA_API_KEY is missing. Check your .env file.")

    for name in ["matches", "teams"]:
        data = fetch(f"competitions/PL/{name}", params={"season": args.season})
        path = save_raw(data, name, args.season)
        print(f"Saved {name} to {path}")
        time.sleep(7)  # stay under the free tier rate limit


if __name__ == "__main__":
    main()
