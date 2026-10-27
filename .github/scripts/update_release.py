"""Write data/latest-release.json from Xac Anon's Apple Music catalogue.

Run daily by .github/workflows/latest-release.yml. Uses only public endpoints
(no API keys): the iTunes lookup API for releases, dates, artwork and links.
A presave link for an upcoming release can be set in the admin Countdown tab.
"""
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone

ARTIST_ID = "1668739775"  # Xac Anon on Apple Music
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "data", "latest-release.json")
UA = {"User-Agent": "xacanonmusic.com release updater"}


def fetch_json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return json.load(r)


def clean_title(name):
    return re.sub(r"\s+-\s+(Single|EP)$", "", name).strip()


def to_release(item):
    title = clean_title(item["collectionName"])
    art = item.get("artworkUrl100", "").replace("100x100bb", "600x600bb")
    apple = item.get("collectionViewUrl", "").split("?")[0]
    return {
        "title": title,
        "releaseDate": item["releaseDate"],
        "artwork": art,
        "appleMusic": apple,
        "link": apple,
    }


def main():
    data = fetch_json(
        f"https://itunes.apple.com/lookup?id={ARTIST_ID}&entity=album&sort=recent&limit=50&country=au"
    )
    albums = [r for r in data.get("results", []) if r.get("wrapperType") == "collection"]
    if not albums:
        sys.exit("No releases returned from Apple; leaving the existing file alone.")

    now = datetime.now(timezone.utc)
    when = lambda r: datetime.fromisoformat(r["releaseDate"].replace("Z", "+00:00"))
    albums.sort(key=when)
    upcoming = [r for r in albums if when(r) > now]
    released = [r for r in albums if when(r) <= now]

    old = None
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            old = json.load(f)

    result = {
        "upcoming": to_release(upcoming[0]) if upcoming else None,
        "latest": to_release(released[-1]) if released else None,
    }
    if old == result:
        print("No change.")
        return
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("Updated:", json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
