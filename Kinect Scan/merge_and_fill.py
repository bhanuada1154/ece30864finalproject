"""
Merge multiple Kinect .ply scans, remove outliers, fill holes, and smooth.
Coordinates are in millimetres (Kinect default).
Requires: pip install trimesh scipy numpy
"""

import glob
import os
import numpy as np
import importlib
import trimesh
import trimesh.repair
from scipy.spatial import KDTree

_smoothing = importlib.import_module("trimesh.smoothing")

SCAN_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PLY = os.path.join(SCAN_DIR, "merged_filled.ply")

# --- Tuning knobs ---
# Neighbours used for outlier detection. Higher = stricter.
OUTLIER_K         = 20
# Vertices whose mean-neighbour-distance exceeds (global_mean + N*std) are removed.
OUTLIER_STD       = 2.0
# Taubin smoothing passes — more = smoother but less detail.
SMOOTH_ITERATIONS = 10

# --- 1. Load and merge all .ply files ---
ply_files = sorted(glob.glob(os.path.join(SCAN_DIR, "*.ply")))
EXCLUDE_NAMES = {"84.ply"}          # leftover from previous scan session
EXCLUDE_WORDS = {"merged", "repaired", "filled"}
ply_files = [
    f for f in ply_files
    if os.path.basename(f) not in EXCLUDE_NAMES
    and not any(e in os.path.basename(f) for e in EXCLUDE_WORDS)
]
print(f"Found {len(ply_files)} .ply files")

meshes = []
for path in ply_files:
    m = trimesh.load(path, process=False, force="mesh")
    if isinstance(m, trimesh.Scene):
        m = trimesh.util.concatenate(list(m.geometry.values()))
    print(f"  {os.path.basename(path):12s}  {len(m.vertices):>7,} verts  {len(m.faces):>7,} faces")
    meshes.append(m)

combined = trimesh.util.concatenate(meshes)
print(f"\nCombined: {len(combined.vertices):,} verts, {len(combined.faces):,} faces")

# --- 2. Statistical outlier removal ---
# For each vertex find its K nearest neighbours and compute mean distance.
# Vertices that are far from their neighbours are scan noise / misaligned frames.
print(f"\nOutlier removal (k={OUTLIER_K}, threshold={OUTLIER_STD} sigma) ...")
verts = np.asarray(combined.vertices)
tree  = KDTree(verts)
dists, _ = tree.query(verts, k=OUTLIER_K + 1)   # +1 because index 0 is self
mean_dists = dists[:, 1:].mean(axis=1)           # drop self-distance

threshold = mean_dists.mean() + OUTLIER_STD * mean_dists.std()
keep_verts = mean_dists < threshold
print(f"  Removing {(~keep_verts).sum():,} outlier vertices "
      f"({(~keep_verts).mean()*100:.1f}%)")

# Remap vertex indices and drop any face that references a removed vertex
old_to_new = np.full(len(verts), -1, dtype=np.int64)
old_to_new[keep_verts] = np.arange(keep_verts.sum())

faces = np.asarray(combined.faces)
face_mask = keep_verts[faces].all(axis=1)
new_faces = old_to_new[faces[face_mask]]
new_verts = verts[keep_verts]

# Preserve vertex colours if present
new_colors = None
if combined.visual is not None and hasattr(combined.visual, "vertex_colors"):
    vc = np.asarray(combined.visual.vertex_colors)
    if len(vc) == len(verts):
        new_colors = vc[keep_verts]

combined = trimesh.Trimesh(vertices=new_verts, faces=new_faces, process=False)
if new_colors is not None:
    combined.visual.vertex_colors = new_colors

print(f"  After removal: {len(combined.vertices):,} verts, {len(combined.faces):,} faces")

# --- 3. Weld near-duplicate vertices (seams between frames) ---
combined.merge_vertices(merge_tex=False, merge_norm=False)
mask = combined.nondegenerate_faces()
combined.update_faces(mask)
combined.remove_unreferenced_vertices()
print(f"After weld/cleanup: {len(combined.vertices):,} verts, {len(combined.faces):,} faces")

# --- 4. Fill holes ---
# fill_holes triangulates open boundary loops (gaps between scan frames).
trimesh.repair.fill_holes(combined)
print(f"After fill_holes — watertight: {combined.is_watertight}")

# --- 5. Taubin smoothing ---
# Removes Kinect sensor noise while preserving volume (unlike plain Laplacian).
print(f"\nSmoothing ({SMOOTH_ITERATIONS} Taubin iterations) ...")
_smoothing.filter_taubin(combined, iterations=SMOOTH_ITERATIONS)

# --- 6. Save ---
combined.export(OUTPUT_PLY)
print(f"\nSaved: {OUTPUT_PLY}")
print(f"Final: {len(combined.vertices):,} verts, {len(combined.faces):,} faces")
print(f"Watertight: {combined.is_watertight}")
