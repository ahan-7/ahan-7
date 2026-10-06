"""
Prepare the portrait photo/avatar for clean ASCII conversion:
  1. Remove background so the subject is cleanly isolated.
     - For solid/neutral backgrounds (like illustrations/pixel art): instant high-precision color distance.
     - For complex real-world photos: rembg (when USE_REMBG=1 or when automatic solid background check fails).
  2. Smooth flat skin tones while keeping drawn outline edges sharp.
  3. Stretch tones so skin lands bright (sparser characters) and hair/shirt stay dark.
  4. Darken the line work (difference-of-gaussians ridges) so eyes, mouth, and contours pop.
  5. Composite onto pure white (feathered) and crop square around the subject.

Output: source-prepped.png (grayscale), consumed by make_ascii_svg.py.

Usage:
    python scripts/prep_photo.py [input.png] [output.png]
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_INP = os.path.join(HERE, "..", "avatar.png")
DEFAULT_OUT = os.path.join(HERE, "..", "source-prepped.png")

INP = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_INP
OUT = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT

LINE_WEIGHT = 0.6  # how hard outline lines are pushed toward black


def extract_subject(img_path):
    img = Image.open(img_path).convert("RGBA")
    rgb = np.array(img.convert("RGB"))
    h, w = rgb.shape[:2]

    # Sample corners to test if background is uniform
    corners = np.array([
        rgb[0, 0], rgb[0, w - 1],
        rgb[0, w // 2], rgb[min(5, h - 1), 0],
        rgb[min(5, h - 1), w - 1]
    ], dtype=np.float32)
    bg_std = np.std(corners, axis=0)

    # If background corners are very similar or USE_REMBG is not forced:
    if os.environ.get("USE_REMBG") != "1" and np.all(bg_std < 15.0):
        bg_color = np.median(corners, axis=0)
        # Euclidean distance in RGB color space
        dist = np.linalg.norm(rgb.astype(np.float32) - bg_color, axis=-1)
        # Threshold: background pixels have very small dist
        alpha = np.clip((dist - 14.0) / 10.0, 0.0, 1.0) * 255.0
        alpha = alpha.astype(np.uint8)
        # Morphological close to clean any tiny interior noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        alpha = cv2.morphologyDefault = cv2.morphologyEx(alpha, cv2.MORPH_CLOSE, kernel)
        print("Using fast, lossless background segmentation from background color:", [int(c) for c in bg_color])
        return rgb, alpha

    # Otherwise try rembg for complex photographic backgrounds
    try:
        from rembg import remove, new_session
        print("Using rembg for neural background removal...")
        session = new_session("u2netp")  # lightweight fast model
        cut = remove(img, session=session)
        alpha = np.array(cut.split()[-1])
        return np.array(cut.convert("RGB")), alpha
    except Exception as e:
        print(f"rembg unavailable or skipped ({e}); using chroma fallback.")
        bg_color = np.median(corners, axis=0)
        dist = np.linalg.norm(rgb.astype(np.float32) - bg_color, axis=-1)
        alpha = np.clip((dist - 14.0) / 10.0, 0.0, 1.0) * 255.0
        return rgb, alpha.astype(np.uint8)


def prep_photo():
    if not os.path.exists(INP):
        print(f"Error: {INP} not found", file=sys.stderr)
        sys.exit(1)

    rgb, alpha = extract_subject(INP)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

    # Smooth texture while preserving edges
    smooth = gray.copy()
    for _ in range(2):
        smooth = cv2.bilateralFilter(smooth, 7, 30, 7)

    # Tone stretch over subject area only
    subj_mask = alpha > 100
    if np.any(subj_mask):
        lo, hi = np.percentile(smooth[subj_mask], [3, 93])
        if hi <= lo:
            hi = lo + 1.0
        tone = np.clip((smooth.astype(np.float32) - lo) / (hi - lo), 0.0, 1.0)
    else:
        tone = smooth.astype(np.float32) / 255.0

    # Difference of Gaussians (DoG) to darken fine line work
    fine = cv2.GaussianBlur(smooth, (0, 0), 1.2).astype(np.float32)
    coarse = cv2.GaussianBlur(smooth, (0, 0), 5.0).astype(np.float32)
    lines = np.clip((coarse - fine) / 35.0, 0.0, 1.0)
    out = np.clip(tone - LINE_WEIGHT * lines, 0.0, 1.0) * 255.0

    # Composite onto pure white background so whitespace maps to space glyph
    mask = cv2.GaussianBlur(alpha.astype(np.float32) / 255.0, (0, 0), 0.8)
    out = out * mask + 255.0 * (1.0 - mask)

    # Square crop around subject with clean margins
    ys, xs = np.where(alpha > 30)
    if len(xs) > 0 and len(ys) > 0:
        side = max(xs.max() - xs.min(), ys.max() - ys.min()) + 40
        cx, cy = int((xs.min() + xs.max()) // 2), int((ys.min() + ys.max()) // 2)
        canvas = np.full((side, side), 255, dtype=np.uint8)
        x0, y0 = cx - side // 2, cy - side // 2
        sx0, sy0 = max(x0, 0), max(y0, 0)
        sx1, sy1 = min(x0 + side, out.shape[1]), min(y0 + side, out.shape[0])
        canvas[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = out[sy0:sy1, sx0:sx1].astype(np.uint8)
    else:
        canvas = out.astype(np.uint8)

    Image.fromarray(canvas, mode="L").save(OUT)
    print(f"Wrote prepped image: {OUT} ({canvas.shape[1]}x{canvas.shape[0]})")


if __name__ == "__main__":
    prep_photo()
