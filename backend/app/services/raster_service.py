from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image

# Simple green -> yellow -> red risk gradient, keyed by risk value 0..1.
_GRADIENT_STOPS: tuple[tuple[float, tuple[int, int, int]], ...] = (
    (0.0, (34, 139, 34)),
    (0.5, (240, 200, 20)),
    (1.0, (200, 30, 30)),
)

# Upscale factor so a small feature grid (e.g. 19x17) is still visible as a map overlay.
_PREVIEW_UPSCALE = 16


def resolve_raster_path(prediction_id: str, *, base_dir: str | Path | None = None) -> Path:
    """Resolve a raster path while forbidding traversal outside the allowed output directory."""

    if prediction_id in {"", ".", ".."}:
        raise ValueError("Invalid prediction ID")

    root = Path(base_dir) if base_dir is not None else Path(__file__).resolve().parents[3] / "ai" / "outputs"
    candidate = (root / prediction_id / "risk_raster.tif").resolve()
    root_resolved = root.resolve()

    if root_resolved not in candidate.parents:
        raise ValueError("Invalid raster path")

    if not candidate.exists():
        raise FileNotFoundError(f"Raster for prediction '{prediction_id}' does not exist.")
    return candidate


def _colorize(risk: np.ndarray) -> np.ndarray:
    """Map a 0..1 risk array to RGBA using the gradient, with alpha scaled by risk magnitude."""
    clipped = np.clip(risk, 0.0, 1.0)
    rgb = np.zeros((*clipped.shape, 3), dtype=np.float32)

    for (start_v, start_c), (end_v, end_c) in zip(_GRADIENT_STOPS[:-1], _GRADIENT_STOPS[1:]):
        band = (clipped >= start_v) & (clipped <= end_v)
        span = end_v - start_v or 1.0
        t = np.where(span > 0, (clipped - start_v) / span, 0.0)
        for channel in range(3):
            rgb[..., channel] = np.where(
                band,
                start_c[channel] + t * (end_c[channel] - start_c[channel]),
                rgb[..., channel],
            )

    alpha = (40 + clipped * 180).astype(np.uint8)
    rgba = np.dstack([rgb.astype(np.uint8), alpha])
    return rgba


def read_risk_grid(prediction_id: str, *, base_dir: str | Path | None = None) -> dict:
    """Return each grid cell's real center coordinate and risk value.

    Used to render discrete color-coded markers (rather than a translucent image overlay), which
    reads more clearly as "this specific spot is high/medium/low risk" at a glance.
    """
    raster_path = resolve_raster_path(prediction_id, base_dir=base_dir)

    with rasterio.open(raster_path) as src:
        risk = src.read(1)
        rows, cols = risk.shape
        cells = []
        for row in range(rows):
            for col in range(cols):
                lon, lat = src.xy(row, col)
                cells.append({"lat": lat, "lon": lon, "value": float(risk[row, col])})

    return {"rows": rows, "cols": cols, "cells": cells}


def render_risk_preview_png(prediction_id: str, *, base_dir: str | Path | None = None) -> bytes:
    """Render the risk raster as an upsampled, color-mapped RGBA PNG for a Leaflet ImageOverlay."""
    raster_path = resolve_raster_path(prediction_id, base_dir=base_dir)

    with rasterio.open(raster_path) as src:
        risk = src.read(1)

    rgba = _colorize(risk)
    image = Image.fromarray(rgba, mode="RGBA")
    upscaled = image.resize(
        (image.width * _PREVIEW_UPSCALE, image.height * _PREVIEW_UPSCALE),
        resample=Image.NEAREST,
    )

    buffer = io.BytesIO()
    upscaled.save(buffer, format="PNG")
    return buffer.getvalue()
