import argparse

import requests

from ingest.fetch_matches import fetch_season
from ingest.load_matches import get_connection, load_season


def main():
    parser = argparse.ArgumentParser(description="Fetch and load a range of seasons")
    parser.add_argument("--from-season", type=int, required=True, help="e.g. 2023")
    parser.add_argument("--to-season", type=int, required=True, help="e.g. 2025")
    args = parser.parse_args()
    if args.from_season > args.to_season:
        parser.error("--from-season must be less than or equal to --to-season")

    conn = get_connection()
    try:
        for season in range(args.from_season, args.to_season + 1):
            print(f"--- Season {season} ---")
            try:
                fetch_season(season)
            except requests.HTTPError as error:
                print(f"Skipping {season}: {error}")
                continue
            load_season(conn, season)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
