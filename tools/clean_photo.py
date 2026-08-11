#!/usr/bin/env python3
"""Clean a source photo for ASCII-portrait conversion.

Usage:
    python tools/clean_photo.py my-photo.jpg
"""
import io
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove


def clean_photo(src_path, out_path="assets/photo-ready.png"):
    src = Path(src_path)
    if not src.exists():
        raise FileNotFoundError(f"No such file: {src}")

    # 1. Cut the background so only the subject remains.
    cutout_bytes = remove(src.read_bytes())
    rgba = Image.open(io.BytesIO(cutout_bytes)).convert("RGBA")

    # 2. Even out lighting with CLAHE so a flat-lit face doesn't
    #    collapse into mid-gray mush once it's downscaled to ASCII.
    rgb = np.array(rgba.convert("RGB"))
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    l_eq = clahe.apply(l)
    rgb_eq = cv2.cvtColor(cv2.merge((l_eq, a, b)), cv2.COLOR_LAB2RGB)

    equalized = Image.fromarray(rgb_eq).convert("RGBA")
    equalized.putalpha(rgba.getchannel("A"))

    # 3. Drop onto white so the background reads as empty glyphs,
    #    not dark ones.
    canvas = Image.new("RGBA", equalized.size, (255, 255, 255, 255))
    canvas.alpha_composite(equalized)

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out)
    print(f"wrote {out}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python tools/clean_photo.py path/to/photo.jpg")
    clean_photo(sys.argv[1])
