from __future__ import annotations

from pathlib import Path


def resolve_raster_path(prediction_id: str, *, base_dir: str | Path | None = None) -> Path:
    """Resolve a raster path while forbidding traversal outside the allowed output directory."""

    if prediction_id in {"", ".", ".."}:
        raise ValueError("Invalid prediction ID")

    root = Path(base_dir) if base_dir is not None else Path(__file__).resolve().parents[3] / "ai" / "outputs"
    candidate = (root / prediction_id).resolve()
    root_resolved = root.resolve()

    if root_resolved not in candidate.parents and candidate != root_resolved:
        raise ValueError("Invalid raster path")

    if not candidate.exists():
        raise FileNotFoundError(f"Raster for prediction '{prediction_id}' does not exist.")
    return candidate
