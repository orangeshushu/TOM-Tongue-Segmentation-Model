"""Generate app icons from resources/icon_source.png.

Large icon frames keep the full TOM artwork. Small frames use a tighter crop
around the tongue and scanner brackets so the mark stays recognizable in the
Windows title bar and taskbar.
"""
from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "resources")
SOURCE = os.path.join(OUT_DIR, "icon_source.png")

FULL_SIZES = [256, 128, 64]
MARK_SIZES = [48, 32, 24, 16]


def remove_black_corners(img: Image.Image) -> Image.Image:
    """Turn the black rounded-rectangle background into transparency."""
    img = img.convert("RGBA")
    px = img.load()
    w, h = img.size

    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            maxc = max(r, g, b)
            minc = min(r, g, b)
            if maxc <= 6:
                px[x, y] = (255, 255, 255, 0)
            elif maxc < 210 and maxc - minc <= 10:
                # Antialiased app-tile edge composited over black.
                edge_alpha = max(0, min(255, int(maxc * 1.25)))
                px[x, y] = (255, 255, 255, min(a, edge_alpha))
    return img


def crop_to_content(img: Image.Image, threshold: int = 4) -> Image.Image:
    alpha = img.getchannel("A")
    mask = alpha.point(lambda p: 255 if p > threshold else 0)
    bbox = mask.getbbox()
    if not bbox:
        return img
    return img.crop(bbox)


def extract_mark(img: Image.Image) -> Image.Image:
    """Crop out the TOM text and keep the scanner + tongue mark."""
    w, h = img.size
    # Coordinates are proportional to the provided square artwork.
    box = (
        int(w * 0.12),
        int(h * 0.10),
        int(w * 0.88),
        int(h * 0.78),
    )
    return img.crop(box)


def fit_square(img: Image.Image, size: int, scale: float) -> Image.Image:
    img = crop_to_content(img)
    canvas = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    max_side = max(1, int(size * scale))
    fitted = ImageOps.contain(img, (max_side, max_side), Image.Resampling.LANCZOS)
    x = (size - fitted.width) // 2
    y = (size - fitted.height) // 2
    canvas.alpha_composite(fitted, (x, y))
    return canvas


def polish(img: Image.Image, size: int) -> Image.Image:
    """Add a little crispness after downscaling, especially for small frames."""
    if size <= 48:
        img = ImageEnhance.Contrast(img).enhance(1.06)
        img = ImageEnhance.Sharpness(img).enhance(1.35)
    return img


def render_frame(source: Image.Image, size: int, use_mark: bool) -> Image.Image:
    art = extract_mark(source) if use_mark else source
    scale = 0.94 if use_mark else 0.98
    frame = fit_square(art, size, scale)
    return polish(frame, size)


def save_preview_strip(source: Image.Image) -> None:
    sizes = FULL_SIZES + MARK_SIZES
    cell = 84
    strip = Image.new("RGBA", (cell * len(sizes), 112), (255, 252, 247, 255))
    d = ImageDraw.Draw(strip)
    for i, size in enumerate(sizes):
        frame = render_frame(source, min(size, 64), use_mark=size in MARK_SIZES)
        x = i * cell + (cell - frame.width) // 2
        y = 14 + (64 - frame.height) // 2
        strip.alpha_composite(frame, (x, y))
        label = f"{size}px"
        d.text((i * cell + 24, 86), label, fill=(45, 39, 46, 255))
    strip.save(os.path.join(OUT_DIR, "icon_sizes_preview.png"), format="PNG")


def main() -> None:
    if not os.path.exists(SOURCE):
        raise SystemExit(f"Missing source image: {SOURCE}")

    source = remove_black_corners(Image.open(SOURCE))
    source = crop_to_content(source)

    icon_png = render_frame(source, 1024, use_mark=False)
    icon_png.save(os.path.join(OUT_DIR, "icon.png"), format="PNG")
    icon_png.save(os.path.join(OUT_DIR, "icon_preview.png"), format="PNG")

    ico_frames = []
    for size in FULL_SIZES + MARK_SIZES:
        ico_frames.append(render_frame(source, size, use_mark=size in MARK_SIZES))

    ico = os.path.join(OUT_DIR, "icon.ico")
    ico_frames[0].save(
        ico,
        format="ICO",
        sizes=[(s, s) for s in FULL_SIZES + MARK_SIZES],
        append_images=ico_frames[1:],
    )

    save_preview_strip(source)
    print(f"icon written: {ico} ({os.path.getsize(ico)} bytes)")
    print(f"png written: {os.path.join(OUT_DIR, 'icon.png')}")
    print(f"preview strip: {os.path.join(OUT_DIR, 'icon_sizes_preview.png')}")


if __name__ == "__main__":
    main()
