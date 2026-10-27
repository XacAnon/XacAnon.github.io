"""Refresh the site's generated data and pages.

Run by .github/workflows/latest-release.yml (every 6 hours, or by hand).
Uses only public endpoints, no API keys:
  - Apple's iTunes lookup API: releases, dates, artwork, tracklists
  - YouTube's channel RSS feed: newest videos (keeps the old list if it's down)

Writes:
  data/latest-release.json  home countdown, music page button, links page
  data/releases.json        every release (used by the music page and release pages)
  data/videos.json          videos page
  releases/<slug>.html      one page per release, plus releases/index.html
  sitemap.xml

Hand-edited extras per release (Spotify album, YouTube video, story) live in
data/releases-extra.json, keyed by slug.
"""
import hashlib
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from html import escape

sys.path.insert(0, os.path.dirname(__file__))
from page_shell import SITE, page  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ARTIST_ID = "1668739775"  # Xac Anon on Apple Music
YT_CHANNEL = "UCfK0GN9-1RZHko0p6HP0L8Q"  # @XacAnonRS
UA = {"User-Agent": "xacanonmusic.com site updater"}
SPOTIFY_ARTIST = "https://open.spotify.com/artist/2u0UlmbzNuKCBNfueWuqsx"


def path(*p):
    return os.path.join(ROOT, *p)


def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return r.read()


def read_json(rel, default):
    try:
        with open(path(rel), encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def write_if_changed(rel, text):
    full = path(rel)
    old = open(full, encoding="utf-8").read() if os.path.exists(full) else None
    if old == text:
        return False
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("updated", rel)
    return True


def write_json(rel, data):
    return write_if_changed(rel, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def slugify(text):
    text = text.lower().replace("&", "and").replace("'", "").replace("’", "")
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


FEAT = re.compile(r"\s*[\(\[]feat\.?\s*([^\)\]]+)[\)\]]", re.I)


# ---------------------------------------------------------------- releases
def load_releases():
    data = json.loads(fetch(
        f"https://itunes.apple.com/lookup?id={ARTIST_ID}&entity=album&sort=recent&limit=200&country=au"))
    albums = [r for r in data.get("results", []) if r.get("wrapperType") == "collection"]
    extra = read_json("data/releases-extra.json", {})
    releases = []
    for a in albums:
        full = re.sub(r"\s+-\s+(Single|EP)$", "", a["collectionName"]).strip()
        feat = FEAT.search(full)
        title = FEAT.sub("", full).strip()
        slug = slugify(title)
        kind = "Single" if a["collectionName"].endswith(" - Single") else ("EP" if a["collectionName"].endswith(" - EP") else "Album")
        r = {
            "slug": slug,
            "title": title,
            "featuring": feat.group(1).strip() if feat else "",
            "type": kind,
            "trackCount": a.get("trackCount", 1),
            "releaseDate": a["releaseDate"],
            "artwork": a.get("artworkUrl100", "").replace("100x100bb", "600x600bb"),
            "appleMusic": a.get("collectionViewUrl", "").split("?")[0],
            "appleId": a["collectionId"],
            "tracks": [],
        }
        r.update({k: v for k, v in extra.get(slug, {}).items() if v})
        releases.append(r)
    for r in releases:
        if r["trackCount"] > 1:
            songs = json.loads(fetch(f"https://itunes.apple.com/lookup?id={r['appleId']}&entity=song&country=au"))
            r["tracks"] = [s["trackName"] for s in sorted(
                (s for s in songs["results"] if s.get("wrapperType") == "track"), key=lambda s: s.get("trackNumber", 0))]
    releases.sort(key=lambda r: r["releaseDate"], reverse=True)
    return releases


def latest_release_data(releases):
    now = datetime.now(timezone.utc)
    when = lambda r: datetime.fromisoformat(r["releaseDate"].replace("Z", "+00:00"))
    upcoming = sorted((r for r in releases if when(r) > now), key=when)
    released = [r for r in releases if when(r) <= now]

    def short(r):
        return {"title": r["title"], "slug": r["slug"], "releaseDate": r["releaseDate"], "artwork": r["artwork"],
                "appleMusic": r["appleMusic"], "link": r["appleMusic"]}
    return {"upcoming": short(upcoming[0]) if upcoming else None, "latest": short(released[0]) if released else None}


# ---------------------------------------------------------------- videos
def update_videos():
    old = read_json("data/videos.json", [])
    try:
        root = ET.fromstring(fetch(f"https://www.youtube.com/feeds/videos.xml?channel_id={YT_CHANNEL}"))
    except Exception as err:  # the feed has outages; keep what we have
        print("YouTube feed unavailable, keeping existing videos:", err)
        return old
    ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
    fresh = [{"id": e.find("yt:videoId", ns).text, "title": e.find("a:title", ns).text,
              "published": e.find("a:published", ns).text} for e in root.findall("a:entry", ns)]
    hidden = set(read_json("data/videos-hidden.json", []))
    known = {v["id"] for v in fresh}
    merged = [v for v in fresh if v["id"] not in hidden] + [v for v in old if v["id"] not in known and v["id"] not in hidden]
    return merged


# ---------------------------------------------------------------- pages
def release_page(r, prev_r, next_r, theme_v):
    d = datetime.fromisoformat(r["releaseDate"].replace("Z", "+00:00"))
    when = d.strftime("%-d %B %Y") if os.name != "nt" else d.strftime("%#d %B %Y")
    kind = r["type"] if r["type"] != "Album" else f"Album &middot; {r['trackCount']} tracks"
    feat = f'<p class="release-feat">feat. {escape(r["featuring"])}</p>' if r["featuring"] else ""
    spotify = r.get("spotify")
    buttons = [
        f'<a class="btn" href="{escape(spotify or SPOTIFY_ARTIST)}" target="_blank" rel="noopener"><i class="fab fa-spotify"></i> Spotify</a>',
        f'<a class="btn btn-ghost" href="{escape(r["appleMusic"])}" target="_blank" rel="noopener"><i class="fab fa-apple"></i> Apple Music</a>',
    ]
    if r.get("youtube"):
        buttons.append(f'<a class="btn btn-ghost" href="https://www.youtube.com/watch?v={escape(r["youtube"])}" target="_blank" rel="noopener"><i class="fab fa-youtube"></i> YouTube</a>')
    embed = ""
    if spotify and "/album/" in spotify:
        sid = spotify.rstrip("/").split("/")[-1].split("?")[0]
        height = 352 if r["trackCount"] > 1 else 152
        embed = f'<iframe class="release-embed" src="https://open.spotify.com/embed/album/{sid}?utm_source=generator&theme=0" height="{height}" loading="lazy" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" title="Listen to {escape(r["title"])} on Spotify"></iframe>'
    tracks = ""
    if r["tracks"]:
        items = "\n".join(f"      <li>{escape(t)}</li>" for t in r["tracks"])
        tracks = f'<section class="release-section"><h2>Tracklist</h2>\n    <ol class="tracklist">\n{items}\n    </ol></section>'
    story = ""
    if r.get("story"):
        paras = "".join(f"<p>{escape(p.strip())}</p>" for p in r["story"].split("\n\n") if p.strip())
        story = f'<section class="release-section"><h2>The story</h2>{paras}</section>'
    video = ""
    if r.get("youtube"):
        video = f'<section class="release-section"><h2>Watch</h2><div class="yt-frame"><iframe src="https://www.youtube-nocookie.com/embed/{escape(r["youtube"])}?rel=0" title="{escape(r["title"])} on YouTube" loading="lazy" allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe></div></section>'
    nav_links = []
    if next_r:
        nav_links.append(f'<a href="/releases/{next_r["slug"]}" class="release-nav-link"><span>Newer</span>{escape(next_r["title"])}</a>')
    if prev_r:
        nav_links.append(f'<a href="/releases/{prev_r["slug"]}" class="release-nav-link release-nav-link--older"><span>Older</span>{escape(prev_r["title"])}</a>')
    schema = {
        "@context": "https://schema.org",
        "@type": "MusicAlbum" if r["type"] == "Album" else "MusicRecording",
        "name": r["title"], "byArtist": {"@type": "MusicGroup", "name": "Xac Anon", "url": SITE},
        "datePublished": r["releaseDate"][:10], "image": r["artwork"], "url": f"{SITE}/releases/{r['slug']}",
        "sameAs": [u for u in (spotify, r["appleMusic"]) if u],
    }
    body = f"""<main class="release-page">
  <section class="release-hero">
    <img class="release-cover" src="{escape(r['artwork'])}" alt="{escape(r['title'])} cover art" />
    <div class="release-meta">
      <p class="eyebrow">{kind} &middot; {d.year}</p>
      <h1>{escape(r['title'])}</h1>
      {feat}
      <p class="release-date">Released {when}</p>
      <div class="release-buttons">
        {"".join(buttons)}
      </div>
    </div>
  </section>
  {embed}
  {tracks}
  {story}
  <section class="release-section" id="release-lyrics" hidden><h2>Lyrics</h2><div class="lyric-body" id="release-lyrics-body"></div></section>
  {video}
  <nav class="release-nav">{"".join(nav_links)}</nav>
  <p class="release-back"><a href="/music"><i class="fas fa-arrow-left"></i> All music</a></p>
</main>"""
    scripts = f"""<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
<script type="module">
// Show lyrics if they've been added in the admin panel under the same title
import {{ db }} from "/assets/site.js";
import {{ collection, getDocs }} from "https://www.gstatic.com/firebasejs/10.4.0/firebase-firestore.js";
const norm = s => String(s || "").toLowerCase().replace(/[^a-z0-9]+/g, "");
try {{
  const snap = await getDocs(collection(db, "lyrics"));
  const match = snap.docs.find(d => norm(d.data().title) === norm({json.dumps(r['title'])}));
  if (match) {{
    document.getElementById("release-lyrics-body").innerHTML = match.data().content || "";
    document.getElementById("release-lyrics").hidden = false;
  }}
}} catch (err) {{ console.warn("Lyrics:", err); }}
</script>"""
    title = f"{r['title']} | Xac Anon"
    desc = f"{r['title']} by Xac Anon{(' feat. ' + r['featuring']) if r['featuring'] else ''}, released {when}. Listen on Spotify and Apple Music."
    return page(title=title, path=f"/releases/{r['slug']}", description=desc, body=body,
                scripts=scripts, theme_version=theme_v, image=r["artwork"], og_type="music.song")


def index_page(releases, theme_v):
    cards = "\n".join(f"""    <a class="music-card release-card" href="/releases/{r['slug']}">
      <img src="{escape(r['artwork'])}" alt="" loading="lazy">
      <h3>{escape(r['title'])}</h3>
      <span class="video-date">{r['type']} &middot; {r['releaseDate'][:4]}</span>
    </a>""" for r in releases)
    body = f"""<header class="page-hero">
  <p class="eyebrow">Discography</p>
  <h1>Releases</h1>
  <p>Every Xac Anon release, with streaming links, lyrics and the story behind the songs.</p>
</header>
<main class="page-main page-main--wide">
  <div class="music-grid">
{cards}
  </div>
</main>"""
    return page(title="Releases | Xac Anon", path="/releases/", body=body, theme_version=theme_v,
                description="Every Xac Anon release, with streaming links, lyrics and the story behind the songs.")


def sitemap(releases):
    today = date.today().isoformat()
    pages = [("/", "1.0", "weekly"), ("/music", "0.9", "weekly"), ("/releases/", "0.8", "weekly"),
             ("/videos", "0.8", "weekly"), ("/epk", "0.8", "monthly"), ("/shows", "0.7", "monthly"),
             ("/about", "0.7", "monthly"), ("/links", "0.6", "monthly"), ("/lyrics", "0.6", "weekly"),
             ("/blog", "0.6", "weekly"), ("/contact", "0.5", "yearly")]
    pages += [(f"/releases/{r['slug']}", "0.7", "monthly") for r in releases]
    rows = "\n".join(f"""  <url>
    <loc>{SITE}{p}</loc>
    <changefreq>{c}</changefreq>
    <priority>{pr}</priority>
  </url>""" for p, pr, c in pages)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{rows}\n</urlset>\n'


def main():
    releases = load_releases()
    if not releases:
        sys.exit("No releases returned from Apple; leaving everything alone.")
    theme_v = hashlib.md5(open(path("assets", "theme.css"), "rb").read()).hexdigest()[:8]

    write_json("data/latest-release.json", latest_release_data(releases))
    public = [{k: v for k, v in r.items() if k != "appleId"} for r in releases]
    write_json("data/releases.json", public)
    write_json("data/videos.json", update_videos())

    for i, r in enumerate(releases):
        newer = releases[i - 1] if i > 0 else None
        older = releases[i + 1] if i + 1 < len(releases) else None
        write_if_changed(f"releases/{r['slug']}.html", release_page(r, older, newer, theme_v))
    write_if_changed("releases/index.html", index_page(releases, theme_v))
    write_if_changed("sitemap.xml", sitemap(releases))


if __name__ == "__main__":
    main()
