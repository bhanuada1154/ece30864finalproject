"""
Repair a mesh using pymeshfix (MeshFix) + trimesh cleanup.
Produces a watertight, manifold mesh ready for 3D printing or further use.
Requires: pip install pymeshfix trimesh numpy
"""

import os
import numpy as np
import trimesh
import trimesh.repair
import pymeshfix

SCAN_DIR  = os.path.dirname(os.path.abspath(__file__))
INPUT_PLY = os.path.join(SCAN_DIR, "merged_filled.ply")
OUTPUT_PLY = os.path.join(SCAN_DIR, "repaired.ply")
OUTPUT_STL = os.path.join(SCAN_DIR, "repaired.stl")

# --- 1. Load ---
print(f"Loading {os.path.basename(INPUT_PLY)} ...")
mesh = trimesh.load(INPUT_PLY, process=False, force="mesh")
if isinstance(mesh, trimesh.Scene):
    mesh = trimesh.util.concatenate(list(mesh.geometry.values()))
print(f"  {len(mesh.vertices):,} verts, {len(mesh.faces):,} faces")
print(f"  Watertight before repair: {mesh.is_watertight}")

# --- 2. Trimesh pre-cleanup ---
# Fix face winding consistency and fill small holes before handing to MeshFix.
trimesh.repair.fix_normals(mesh)
trimesh.repair.fix_winding(mesh)
trimesh.repair.fill_holes(mesh)
mesh.merge_vertices()
mask = mesh.nondegenerate_faces()
mesh.update_faces(mask)
mesh.remove_unreferenced_vertices()
print(f"After trimesh pre-cleanup: {len(mesh.vertices):,} verts, {len(mesh.faces):,} faces")

# --- 3. MeshFix repair ---
# This is the heavy lifter: removes self-intersections, fills all remaining
# holes, and produces a manifold (non-self-intersecting, watertight) mesh.
print("\nRunning MeshFix repair ...")
verts = np.asarray(mesh.vertices, dtype=np.float64)
faces = np.asarray(mesh.faces,    dtype=np.int32)

mf = pymeshfix.MeshFix(verts, faces)
mf.repair(joincomp=True, remove_smallest_components=True)

repaired = trimesh.Trimesh(
    vertices=np.array(mf.points),
    faces=np.array(mf.faces).reshape(-1, 3),
    process=False,
)

# --- 4. Trimesh post-cleanup ---
repaired.merge_vertices()
trimesh.repair.fix_normals(repaired)
mask = repaired.nondegenerate_faces()
repaired.update_faces(mask)
repaired.remove_unreferenced_vertices()

print(f"\nAfter repair: {len(repaired.vertices):,} verts, {len(repaired.faces):,} faces")
print(f"Watertight:   {repaired.is_watertight}")
print(f"Volume:       {repaired.volume:.1f} mm^3")

# --- 5. Save ---
repaired.export(OUTPUT_PLY)
repaired.export(OUTPUT_STL)
print(f"\nSaved: {OUTPUT_PLY}")
print(f"Saved: {OUTPUT_STL}")
