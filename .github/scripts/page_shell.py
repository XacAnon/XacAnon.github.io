"""Shared page frame (head, menu, footer) for pages built by scripts.

Used by build_pages.py for the release pages; the Shows, Videos and Links
pages were made from it too. Paths are absolute so pages work in any folder.
"""
from html import escape

SITE = "https://www.xacanonmusic.com"
DEFAULT_IMAGE = SITE + "/assets/img/share.jpg"

SOCIALS = [
    ("Instagram", "https://instagram.com/xacanon/", "fab fa-instagram"),
    ("Spotify", "https://open.spotify.com/artist/2u0UlmbzNuKCBNfueWuqsx", "fab fa-spotify"),
    ("Apple Music", "https://music.apple.com/au/artist/xac-anon/1668739775", "fab fa-apple"),
    ("YouTube", "https://youtube.com/@XacAnonRS", "fab fa-youtube"),
    ("SoundCloud", "https://soundcloud.com/xac-anon", "fab fa-soundcloud"),
    ("TikTok", "https://www.tiktok.com/@xacanon", "fab fa-tiktok"),
    ("X", "https://x.com/xacanonau", "fab fa-x-twitter"),
    ("Discord", "https://discord.gg/u6ARJDzu5X", "fab fa-discord"),
]

MENU = [("Music", "/music"), ("Videos", "/videos"), ("Shows", "/shows"), ("Lyrics", "/lyrics"),
        ("Blog", "/blog"), ("Contact", "/contact"), ("About", "/about")]


def page(*, title, path, description, body, theme_version, image=DEFAULT_IMAGE,
         scripts="", head_extra="", og_type="website", nav=True, footer=True):
    t, d = escape(title), escape(description)
    menu = "\n".join(f'        <li><a href="{href}">{name}</a></li>' for name, href in MENU)
    navbar = f"""<nav class="navbar">
  <div class="navbar-container">
    <a href="/" class="nav-logo"><img src="/assets/img/xac-anon.jpg" alt="Xac Anon Logo"></a>
    <div class="nav-right">
      <a href="/" class="home-button">Home</a>
      <div class="hamburger"><i class="fas fa-bars"></i></div>
      <ul class="nav-links">
{menu}
        <li><a href="https://shop.xacanonmusic.com">Shop</a></li>
      </ul>
    </div>
  </div>
</nav>
""" if nav else ""
    icons = "\n".join(
        f'    <a href="{u}" target="_blank" rel="noopener" aria-label="{n}"><i class="{i}"></i></a>' for n, u, i in SOCIALS)
    foot = f"""<footer class="site-footer">
  <div class="socials">
{icons}
  </div>
  <p class="footer-copy">&copy; 2026 Xac Anon &middot; Newcastle, NSW &middot; <a href="mailto:business@xacanonmusic.com">business@xacanonmusic.com</a></p>
  <p class="footer-credit">Website by Xachariah Anonymous</p>
</footer>
""" if footer else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{t}</title>
<meta name="description" content="{d}" />
<link rel="canonical" href="{SITE}{path}" />
<meta property="og:type" content="{og_type}" />
<meta property="og:site_name" content="Xac Anon" />
<meta property="og:title" content="{t}" />
<meta property="og:description" content="{d}" />
<meta property="og:url" content="{SITE}{path}" />
<meta property="og:image" content="{escape(image)}" />
<meta name="twitter:card" content="{"summary_large_image" if image == DEFAULT_IMAGE else "summary"}" />
<meta name="twitter:title" content="{t}" />
<meta name="twitter:description" content="{d}" />
<meta name="twitter:image" content="{escape(image)}" />
<link rel="icon" type="image/png" sizes="32x32" href="/assets/img/favicon-32.png" />
<link rel="apple-touch-icon" href="/assets/img/apple-touch-icon.png" />
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#09080d">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Syne:wght@700;800&display=swap" rel="stylesheet" />
<link rel="stylesheet" href="/assets/theme.css?v={theme_version}" />
{head_extra}</head>
<body>

{navbar}
{body}

{foot}
<script type="module" src="/assets/site.js"></script>
{scripts}
</body>
</html>
"""
