# Kinect Scan 2 (mesh cleanup)

This folder contains Kinect/FlexScan3D scan exports (mostly `.ply`) plus two small Python scripts to **merge**, **clean**, **fill holes**, **smooth**, and **repair** the mesh for export (including **STL** for 3D printing).

## What it does

Given a scan folder containing many `.ply` meshes (multiple viewpoints/frames):

1. `merge_and_fill.py` produces `merged_filled.ply`
   - merges all `.ply` files in the folder (excluding ones named like `merged*`, `repaired*`, `*filled*`)
   - removes noisy/outlier vertices (KNN distance threshold)
   - welds duplicate vertices, removes degenerate faces
   - fills holes
   - Taubin smooths to reduce Kinect noise
2. `repair_mesh.py` produces `repaired.ply` and `repaired.stl`
   - runs additional cleanup + MeshFix repair to make the mesh more watertight/manifold

## Requirements

- Python 3
- Packages:
  - `trimesh`, `numpy`, `scipy` (for `merge_and_fill.py`)
  - `pymeshfix` (for `repair_mesh.py`)

## How to run

Pick a scan folder that contains the `.ply` files and the scripts (for example `Kinect Scan/` or `Kinect Scan 2/Banu/`), then run:

```bash
python3 -m pip install numpy scipy trimesh
python3 merge_and_fill.py

python3 -m pip install pymeshfix
python3 repair_mesh.py
```

## Outputs

- `merged_filled.ply` (merged + cleaned + hole-filled + smoothed)
- `repaired.ply` (repaired mesh)
- `repaired.stl` (STL export)

