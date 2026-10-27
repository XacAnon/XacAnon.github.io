"""Site images built from the profile photo.

  icons()       favicons, iPhone home-screen icon and app icons (run once; static)
  share_card()  1200x630 link-preview image with the latest release, rebuilt by
                update_site_data.py whenever the latest release changes

Needs Pillow. Font: Syne (SIL Open Font License, see fonts/OFL.txt).
"""
import io
import os
import urllib.request

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FONT = os.path.join(os.path.dirname(__file__), "fonts", "Syne.ttf")
AVATAR = os.path.join(ROOT, "assets", "img", "xac-anon.jpg")
OUT = os.path.join(ROOT, "assets", "img")

BG = (9, 8, 13)
PINK = (255, 79, 129)
VIOLET = (125, 91, 255)
TEXT = (243, 241, 246)
MUTED = (165, 159, 176)


def font(size, weight=800):
    f = ImageFont.truetype(FONT, size)
    f.set_variation_by_axes([weight])
    return f


def circle(img, size):
    img = img.resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size * 4, size * 4), fill=255)
    out = Image.new("RGBA", (size, size))
    out.paste(img, (0, 0), mask.resize((size, size), Image.LANCZOS))
    return out


def rounded(img, size, radius):
    img = img.convert("RGB").resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size * 4, size * 4), radius * 4, fill=255)
    out = Image.new("RGBA", (size, size))
    out.paste(img, (0, 0), mask.resize((size, size), Image.LANCZOS))
    return out


def glow(size, center, radius, color, alpha):
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    x, y = center
    ImageDraw.Draw(layer).ellipse((x - radius, y - radius, x + radius, y + radius), fill=color + (alpha,))
    return layer.filter(ImageFilter.GaussianBlur(radius // 2))


def icons():
    src = Image.open(AVATAR).convert("RGB")
    for size, name in [(32, "favicon-32.png"), (180, "apple-touch-icon.png"), (192, "icon-192.png"), (512, "icon-512.png")]:
        src.resize((size, size), Image.LANCZOS).save(os.path.join(OUT, name), optimize=True)
    print("icons written")


def share_card(latest=None):
    """latest: {'title': ..., 'artwork': url} or None."""
    W, H = 1200, 630
    card = Image.new("RGBA", (W, H), BG + (255,))
    card.alpha_composite(glow((W, H), (230, 300), 330, PINK, 70))
    card.alpha_composite(glow((W, H), (1080, 120), 300, VIOLET, 60))

    # Profile photo with a soft ring
    av = circle(Image.open(AVATAR).convert("RGB"), 300)
    ring = Image.new("RGBA", (340, 340), (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse((0, 0, 339, 339), fill=PINK + (60,))
    card.alpha_composite(ring, (60, 145))
    card.alpha_composite(av, (80, 165))

    d = ImageDraw.Draw(card)
    x = 450
    d.text((x, 150), "LO-FI  ·  EMO RAP  ·  NEWCASTLE, NSW", font=font(24, 700), fill=PINK)
    name_size = 118
    while font(name_size).getlength("XAC ANON") > W - x - 60:
        name_size -= 2
    d.text((x, 185), "XAC ANON", font=font(name_size, 800), fill=TEXT)

    if latest and latest.get("artwork"):
        try:
            art = Image.open(io.BytesIO(urllib.request.urlopen(latest["artwork"], timeout=30).read()))
            panel_y = 345
            # Draw the translucent panel on its own layer so it blends with the background
            panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(panel).rounded_rectangle((x, panel_y, 1130, panel_y + 130), 22,
                                                    fill=(255, 255, 255, 16), outline=(255, 255, 255, 46), width=2)
            card.alpha_composite(panel)
            card.alpha_composite(rounded(art, 100, 14), (x + 15, panel_y + 15))
            d.text((x + 140, panel_y + 27), "LATEST RELEASE", font=font(20, 700), fill=MUTED)
            title = latest["title"]
            size = 48
            while font(size).getlength(title) > 520 and size > 28:
                size -= 2
            d.text((x + 140, panel_y + 55), title, font=font(size, 800), fill=TEXT)
        except Exception as err:  # artwork unreachable: card still works without it
            print("Share card: no artwork,", err)

    d.text((x, 520), "xacanonmusic.com", font=font(30, 700), fill=TEXT)
    card.convert("RGB").save(os.path.join(OUT, "share.jpg"), quality=88, optimize=True, progressive=True)
    print("share card written")


if __name__ == "__main__":
    import json
    icons()
    try:
        latest = json.load(open(os.path.join(ROOT, "data", "latest-release.json"), encoding="utf-8")).get("latest")
    except FileNotFoundError:
        latest = None
    share_card(latest)
