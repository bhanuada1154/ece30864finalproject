# Low Cost 3D Scanning and Reconstruction

A two-stage Python pipeline for turning raw multi-view Xbox 360 Kinect scans (captured with KScan3D) into a clean, watertight 3D mesh.

## Overview

KScan3D exports each freeze-frame scan as a separate `.ply` file. This pipeline merges them, removes noise, fills holes, and repairs the result into a manifold mesh suitable for 3D printing.

`*.ply (raw scans)` → `merge_and_fill.py` → `merged_filled.ply` → `repair_mesh.py` → `repaired.ply` / `repaired.stl`

## Requirements

- Python 3.8+
- Dependencies: `pip install trimesh scipy numpy pymeshfix`

## Usage

Place all your raw `.ply` scans (e.g. `12.ply`, `13.ply`, ...) in the same directory as the scripts, then run:

    python merge_and_fill.py
    python repair_mesh.py

### `merge_and_fill.py`

Loads all `.ply` files in the script directory, concatenates them, and runs:

1. **Statistical outlier removal** — KDTree-based, drops vertices whose mean distance to their `OUTLIER_K` nearest neighbors exceeds the global mean by `OUTLIER_STD` standard deviations.
2. **Vertex welding** — collapses near-duplicate vertices at frame seams.
3. **Hole filling** — `trimesh.repair.fill_holes`.
4. **Taubin smoothing** — `SMOOTH_ITERATIONS` passes (volume-preserving, unlike Laplacian).

Outputs `merged_filled.ply`.

### `repair_mesh.py`

Loads `merged_filled.ply` and runs:

1. Trimesh pre-cleanup (`fix_normals`, `fix_winding`, `fill_holes`).
2. **MeshFix** repair — removes self-intersections, fills remaining holes, joins components, drops smallest stray components.
3. Post-cleanup (`merge_vertices`, `fix_normals`).

Outputs `repaired.ply` and `repaired.stl`.

## Tuning

In `merge_and_fill.py`:

- `OUTLIER_K` (default 20) — Higher = stricter outlier detection.
- `OUTLIER_STD` (default 2.0) — Lower = more aggressive vertex removal.
- `SMOOTH_ITERATIONS` (default 10) — Higher = smoother surface, less fine detail.

Files matching the `EXCLUDE_NAMES` / `EXCLUDE_WORDS` lists are skipped — useful for ignoring leftover scans or already-processed outputs.

## Notes

- All coordinates are in millimeters (Kinect default).
- Vertex colors are preserved through outlier removal.
- Subject movement during capture is the dominant source of error — keep still.