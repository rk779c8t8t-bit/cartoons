"""Geometry helpers for the procedural Blender scenes (runs inside Blender's Python)."""
import math
import bmesh
import bpy
from mathutils import Vector, Matrix


def link(obj, coll=None):
    (coll or bpy.context.scene.collection).objects.link(obj)
    return obj


def empty(name, loc=(0, 0, 0), parent=None, rot=(0, 0, 0), size=0.1):
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = size
    e.location = loc
    e.rotation_euler = rot
    link(e)
    if parent is not None:
        e.parent = parent
    return e


def _mesh_obj(name, bm, mat=None, parent=None, smooth=True):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    link(ob)
    if mat is not None:
        if isinstance(mat, (list, tuple)):
            for m in mat:
                me.materials.append(m)
        else:
            me.materials.append(mat)
    if parent is not None:
        ob.parent = parent
    return ob


def sphere(name, loc=(0, 0, 0), scale=(1, 1, 1), mat=None, parent=None, seg=32, rings=16, rot=(0, 0, 0), subsurf=0):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=1.0)
    ob = _mesh_obj(name, bm, mat, parent)
    ob.location = loc
    ob.scale = scale
    ob.rotation_euler = rot
    if subsurf:
        m = ob.modifiers.new("sub", "SUBSURF")
        m.levels = 0
        m.render_levels = subsurf
    return ob


def box(name, loc=(0, 0, 0), size=(1, 1, 1), mat=None, parent=None, rot=(0, 0, 0), bevel=0.0, bevel_seg=2, smooth=False):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    ob = _mesh_obj(name, bm, mat, parent, smooth=smooth)
    ob.location = loc
    ob.rotation_euler = rot
    if bevel > 0:
        m = ob.modifiers.new("bev", "BEVEL")
        m.width = bevel
        m.segments = bevel_seg
        m.limit_method = "NONE"
        if smooth:
            ob.data.use_auto_smooth = True if hasattr(ob.data, "use_auto_smooth") else None
    return ob


def cylinder(name, loc=(0, 0, 0), radius=1.0, depth=1.0, mat=None, parent=None, rot=(0, 0, 0), seg=24, radius2=None, smooth=True, cap=True):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=cap, cap_tris=False, segments=seg,
                          radius1=radius, radius2=radius if radius2 is None else radius2, depth=depth)
    ob = _mesh_obj(name, bm, mat, parent, smooth=smooth)
    ob.location = loc
    ob.rotation_euler = rot
    return ob


def catmull(points, samples_per_seg=6):
    """Catmull-Rom spline through points -> dense list."""
    pts = [Vector(p) for p in points]
    if len(pts) < 2:
        return pts
    ext = [pts[0] + (pts[0] - pts[1])] + pts + [pts[-1] + (pts[-1] - pts[-2])]
    out = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for s in range(samples_per_seg):
            t = s / samples_per_seg
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(pts[-1])
    return out


def _frames(path):
    """Rotation-minimising frames along a polyline."""
    n = len(path)
    tans = []
    for i in range(n):
        a = path[max(i - 1, 0)]
        b = path[min(i + 1, n - 1)]
        t = (b - a)
        tans.append(t.normalized() if t.length > 1e-9 else Vector((0, 0, 1)))
    ref = Vector((0, 0, 1)) if abs(tans[0].z) < 0.9 else Vector((1, 0, 0))
    nrm = tans[0].cross(ref).normalized()
    frames = []
    for i in range(n):
        if i > 0:
            # project previous normal
            nrm = (nrm - tans[i] * nrm.dot(tans[i]))
            if nrm.length < 1e-9:
                nrm = tans[i].orthogonal()
            nrm.normalize()
        bin_ = tans[i].cross(nrm).normalized()
        frames.append((tans[i], nrm, bin_))
    return frames


def tube_coords(points, radii, ring=12, samples=6, cap=True):
    path = catmull(points, samples)
    # radius interpolation along dense path
    m = len(points)
    rs = []
    for i in range(len(path)):
        f = i / max(len(path) - 1, 1) * (m - 1)
        j = min(int(f), m - 2)
        t = f - j
        rs.append(radii[j] * (1 - t) + radii[j + 1] * t)
    fr = _frames(path)
    coords = []
    for p, r, (t, n, b) in zip(path, rs, fr):
        for k in range(ring):
            a = 2 * math.pi * k / ring
            coords.append(p + (n * math.cos(a) + b * math.sin(a)) * r)
    if cap:
        coords.append(path[0] - fr[0][0] * rs[0] * 0.5)
        coords.append(path[-1] + fr[-1][0] * rs[-1] * 0.5)
    return coords, len(path)


def tube(name, points, radii, mat=None, parent=None, ring=12, samples=6, cap=True, shape_keys=None):
    """Smooth swept tube. shape_keys: dict name -> list of points (same count as points)."""
    coords, n = tube_coords(points, radii, ring, samples, cap)
    bm = bmesh.new()
    vs = [bm.verts.new(c) for c in coords]
    for i in range(n - 1):
        for k in range(ring):
            a = vs[i * ring + k]
            b = vs[i * ring + (k + 1) % ring]
            c = vs[(i + 1) * ring + (k + 1) % ring]
            d = vs[(i + 1) * ring + k]
            bm.faces.new((a, b, c, d))
    if cap:
        c0, c1 = vs[-2], vs[-1]
        for k in range(ring):
            bm.faces.new((vs[(k + 1) % ring], vs[k], c0))
            bm.faces.new((vs[(n - 1) * ring + k], vs[(n - 1) * ring + (k + 1) % ring], c1))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = _mesh_obj(name, bm, mat, parent)
    if shape_keys:
        ob.shape_key_add(name="Basis")
        for kname, pts in shape_keys.items():
            sk = ob.shape_key_add(name=kname)
            cs, _ = tube_coords(pts, radii, ring, samples, cap)
            for i, c in enumerate(cs):
                sk.data[i].co = c
    return ob


def cone(name, loc=(0, 0, 0), r1=1.0, r2=0.0, depth=1.0, mat=None, parent=None, rot=(0, 0, 0), seg=24, scale=(1, 1, 1)):
    ob = cylinder(name, loc, r1, depth, mat, parent, rot, seg, radius2=r2)
    ob.scale = scale
    return ob


def torus(name, loc=(0, 0, 0), major=1.0, minor=0.1, mat=None, parent=None, rot=(0, 0, 0), seg=32, mseg=12, scale=(1, 1, 1)):
    bm = bmesh.new()
    verts = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        ring = []
        for j in range(mseg):
            b = 2 * math.pi * j / mseg
            r = major + minor * math.cos(b)
            ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), minor * math.sin(b))))
        verts.append(ring)
    for i in range(seg):
        for j in range(mseg):
            bm.faces.new((verts[i][j], verts[(i + 1) % seg][j], verts[(i + 1) % seg][(j + 1) % mseg], verts[i][(j + 1) % mseg]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = _mesh_obj(name, bm, mat, parent)
    ob.location = loc
    ob.rotation_euler = rot
    ob.scale = scale
    return ob


def displace(ob, strength=0.2, scale=1.0, seed=0, subdiv=0):
    if subdiv:
        s = ob.modifiers.new("sub", "SUBSURF")
        s.levels = subdiv
        s.render_levels = subdiv
    tex = bpy.data.textures.new(ob.name + "_disp", "CLOUDS")
    tex.noise_scale = scale
    tex.noise_depth = 2
    d = ob.modifiers.new("disp", "DISPLACE")
    d.texture = tex
    d.strength = strength
    d.texture_coords = "GLOBAL" if seed == 0 else "OBJECT"
    return ob


def apply_modifiers(ob):
    bpy.context.view_layer.objects.active = ob
    for m in list(ob.modifiers):
        try:
            bpy.ops.object.modifier_apply(modifier=m.name)
        except Exception:
            pass
