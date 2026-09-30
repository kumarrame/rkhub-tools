"""Regenerate the RKHUB logo raster tiers.

Run from the project root:  python tools/build_logo.py

The artwork is drawn with PIL primitives at 4x and downsampled, which gives
clean antialiased edges without needing a native Cairo/rlPyCairo library. The
vector file static/images/rkhub-logo.svg is the design source of truth and
mirrors this composition exactly.

Palette is intentionally blue (iOS system blue) rather than saffron/white/
green, and contains no emblem, crest or chakra, so the mark cannot be mistaken
for a national or government symbol.
"""
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "static", "images")

SIZES = [64, 84, 128, 168, 180, 256, 512]
SS = 4  # supersample factor

TOP = (90, 200, 250)      # #5AC8FA
MID = (10, 132, 255)      # #0A84FF
BOT = (10, 63, 207)       # #0A3FCF

# Glyph outlines scaled to a 128x128 design grid (same coordinates as the SVG).
RK_R = (
    "M38 40h16.2c8.1 0 13.1 4.1 13.1 10.7 0 4.6-2.5 7.9-6.6 9.4L69.2 80H58.9"
    "l-7.2-18.1h-3.6V80H38V40Zm10.1 8.6v6.2h5.3c2.6 0 4.1-1.2 4.1-3.1s-1.5-3.1-4.1-3.1h-5.3Z"
)
RK_K = (
    "M72 40h10.1v16.6L93.4 40H104L90.2 58.3 105 80H94.1L85.6 64.1l-3.5 3.7V80H72V40Z"
)

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\segoeuib.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\calibrib.ttf",
]


def _font(size):
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _rounded_gradient(size):
    """Vertical iOS-blue gradient clipped to a continuous-corner square."""
    grad = Image.new("RGB", (1, size))
    px = grad.load()
    for y in range(size):
        t = y / float(max(1, size - 1))
        if t < 0.48:
            k = t / 0.48
            c = tuple(int(TOP[i] + (MID[i] - TOP[i]) * k) for i in range(3))
        else:
            k = (t - 0.48) / 0.52
            c = tuple(int(MID[i] + (BOT[i] - MID[i]) * k) for i in range(3))
        px[0, y] = c
    grad = grad.resize((size, size))

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, size - 1, size - 1], radius=int(size * 29 / 128.0), fill=255
    )
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(grad, (0, 0), mask)
    return out


def _draw_glyphs(size):
    """RK monogram, drawn as filled paths.

    PIL cannot stroke arbitrary SVG path data, so the two glyphs are drawn with
    rectangles/polygons that follow the same silhouettes as the SVG.
    """
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    s = size / 128.0
    white = (255, 255, 255, 255)

    def R(x, y, w, h, radius=0):
        box = [x * s, y * s, (x + w) * s, (y + h) * s]
        if radius:
            d.rounded_rectangle(box, radius=radius * s, fill=white)
        else:
            d.rectangle(box, fill=white)

    # --- R (stem + bowl + leg)
    R(38, 40, 10.1, 40)                     # stem
    R(48.1, 40, 6.1, 8.6)                    # bowl top
    R(48.1, 48.6, 6.1, 6.2)                  # bowl mid
    R(44, 55, 10.2, 8.6, radius=1.5)         # bowl inner fill
    R(58.9, 61.9, 5.6, 18.1)                 # leg
    # bowl counter (punch out)
    d.rectangle([48.1 * s, 48.6 * s, 54.2 * s, 54.8 * s], fill=(0, 0, 0, 0))

    # --- K
    R(72, 40, 10.1, 40)                     # stem
    d.polygon(
        [(82.1 * s, 56.6 * s), (93.4 * s, 40 * s), (104 * s, 40 * s),
         (90.2 * s, 58.3 * s)],
        fill=white,
    )
    d.polygon(
        [(90.2 * s, 58.3 * s), (105 * s, 80 * s), (94.1 * s, 80 * s),
         (82.1 * s, 63.4 * s)],
        fill=white,
    )

    return layer


def build(size):
    big = size * SS
    img = _rounded_gradient(big)

    # Sheen highlight across the top 60%.
    sheen = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sheen)
    for y in range(int(big * 0.6)):
        a = int(56 * (1 - y / float(big * 0.6)))
        sd.line([(0, y), (big, y)], fill=(255, 255, 255, a))
    img.alpha_composite(sheen)

    glyphs = _draw_glyphs(big)
    img.alpha_composite(glyphs)

    # 1.5px inner hairline border (scaled).
    # Drawn on its own layer and alpha-composited: ImageDraw writes pixel values
    # directly, so stroking on the base image would replace the opaque alpha
    # with the stroke's 56/255 and punch a translucent hole through the mark.
    stroke = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stroke)
    inset = big * 2.75 / 128.0
    sd.rounded_rectangle(
        [inset, inset, big - 1 - inset, big - 1 - inset],
        radius=int(big * 28.5 / 128.0),
        outline=(255, 255, 255, 56),
        width=max(1, int(1.5 * big / 128.0)),
    )
    img.alpha_composite(stroke)

    return img.resize((size, size), Image.LANCZOS)


def main():
    os.makedirs(OUT, exist_ok=True)
    for size in SIZES:
        img = build(size)
        png = os.path.join(OUT, "rkhub-logo-%d.png" % size)
        webp = os.path.join(OUT, "rkhub-logo-%d.webp" % size)
        img.save(png, "PNG", optimize=True)
        img.save(webp, "WEBP", quality=88, method=6)
        print("%3dpx  png %6.1f KB   webp %6.1f KB"
              % (size, os.path.getsize(png) / 1024.0, os.path.getsize(webp) / 1024.0))

    # Legacy unsuffixed names kept for older cached templates.
    legacy = build(512)
    legacy.save(os.path.join(OUT, "rkhub-logo.png"), "PNG", optimize=True)
    legacy.save(os.path.join(OUT, "rkhub-logo.webp"), "WEBP", quality=88, method=6)
    print("done")


if __name__ == "__main__":
    main()
