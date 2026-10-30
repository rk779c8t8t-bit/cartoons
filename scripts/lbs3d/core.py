"""Core helpers: scene reset, materials, primitive objects, easing/keyframe math."""
import math
import random

import bmesh
import bpy
from mathutils import Vector, Euler

# --------------------------------------------------------------------------- scene

_MESH_CACHE = {}
USE_SSS = False  # subsurface costs ~30% render time on CPU for little visual gain here


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _MESH_CACHE.clear()


def link(obj):
    bpy.context.scene.collection.objects.link(obj)
    return obj


# --------------------------------------------------------------------------- materials

def _principled(m):
    return m.node_tree.nodes.get("Principled BSDF")


def new_mat(name, color, rough=0.5, metal=0.0, sheen=0.0, sheen_tint=(1, 1, 1),
            coat=0.0, sss=0.0, emit=None, emit_str=0.0, transm=0.0, ior=1.45,
            spec=0.5):
    m = bpy.data.materials.new(name)
    p = _principled(m)
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    p.inputs["IOR"].default_value = ior
    p.inputs["Specular IOR Level"].default_value = spec
    if sheen:
        p.inputs["Sheen Weight"].default_value = sheen
        p.inputs["Sheen Tint"].default_value = (*sheen_tint, 1)
        p.inputs["Sheen Roughness"].default_value = 0.35
    if coat:
        p.inputs["Coat Weight"].default_value = coat
        p.inputs["Coat Roughness"].default_value = 0.08
    if sss and USE_SSS:
        p.inputs["Subsurface Weight"].default_value = sss
        p.inputs["Subsurface Radius"].default_value = (1.0, 0.5, 0.25)
        p.inputs["Subsurface Scale"].default_value = 0.02
    if transm:
        p.inputs["Transmission Weight"].default_value = transm
    if emit is not None:
        p.inputs["Emission Color"].default_value = (*emit, 1)
        p.inputs["Emission Strength"].default_value = emit_str
    m.diffuse_color = (*color, 1)
    return m


def fur_mat(name, base, stripe, stripe_scale=3.2, flour_white=(0.97, 0.96, 0.93)):
    """Stylized fur: tabby wave stripes + fine fur bump + sheen. Has a 'Flour' value
    node (0..1) that mixes the coat to flour-white for the flour gag."""
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    p = _principled(m)
    tc = N.new("ShaderNodeTexCoord")
    wave = N.new("ShaderNodeTexWave")
    wave.inputs["Scale"].default_value = stripe_scale
    wave.bands_direction = "Z"
    wave.inputs["Distortion"].default_value = 2.5
    wave.inputs["Detail"].default_value = 2.0
    wave.wave_profile = "SIN"
    L.new(tc.outputs["Object"], wave.inputs["Vector"])
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.62
    ramp.color_ramp.elements[0].color = (*base, 1)
    ramp.color_ramp.elements[1].position = 0.8
    ramp.color_ramp.elements[1].color = (*stripe, 1)
    L.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    flour = N.new("ShaderNodeValue")
    flour.name = "Flour"
    flour.outputs[0].default_value = 0.0
    mix = N.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    L.new(flour.outputs[0], mix.inputs["Factor"])
    L.new(ramp.outputs["Color"], mix.inputs[6])
    mix.inputs[7].default_value = (*flour_white, 1)
    L.new(mix.outputs[2], p.inputs["Base Color"])
    noise = N.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 260.0
    noise.inputs["Detail"].default_value = 1.0
    L.new(tc.outputs["Object"], noise.inputs["Vector"])
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.35
    bump.inputs["Distance"].default_value = 0.002
    L.new(noise.outputs["Fac"], bump.inputs["Height"])
    L.new(bump.outputs["Normal"], p.inputs["Normal"])
    p.inputs["Roughness"].default_value = 0.7
    p.inputs["Sheen Weight"].default_value = 0.35
    p.inputs["Sheen Roughness"].default_value = 0.3
    p.inputs["Sheen Tint"].default_value = (1.0, 0.85, 0.6, 1)
    p.inputs["Subsurface Weight"].default_value = 0.08 if USE_SSS else 0.0
    p.inputs["Subsurface Radius"].default_value = (1.0, 0.4, 0.2)
    p.inputs["Subsurface Scale"].default_value = 0.01
    m.diffuse_color = (*base, 1)
    return m


def flourable(name, color, rough=0.6, sheen=0.3):
    """Plain cloth/cream material that can also be dusted with flour."""
    m = new_mat(name, color, rough=rough, sheen=sheen)
    nt = m.node_tree
    p = _principled(m)
    flour = nt.nodes.new("ShaderNodeValue")
    flour.name = "Flour"
    flour.outputs[0].default_value = 0.0
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    nt.links.new(flour.outputs[0], mix.inputs["Factor"])
    mix.inputs[6].default_value = (*color, 1)
    mix.inputs[7].default_value = (0.97, 0.96, 0.93, 1)
    nt.links.new(mix.outputs[2], p.inputs["Base Color"])
    return m


def set_flour(materials, amount):
    for m in materials:
        n = m.node_tree.nodes.get("Flour")
        if n:
            n.outputs[0].default_value = amount


def textured_mat(name, kind, c1, c2, scale=8.0, rough=0.5, coat=0.0, c3=None):
    """Procedural surfaces: checker floor, brick tiles, wood."""
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    p = _principled(m)
    tc = N.new("ShaderNodeTexCoord")
    p.inputs["Roughness"].default_value = rough
    if coat:
        p.inputs["Coat Weight"].default_value = coat
    if kind == "checker":
        t = N.new("ShaderNodeTexChecker")
        t.inputs["Scale"].default_value = scale
        t.inputs["Color1"].default_value = (*c1, 1)
        t.inputs["Color2"].default_value = (*c2, 1)
        L.new(tc.outputs["Object"], t.inputs["Vector"])
        L.new(t.outputs["Color"], p.inputs["Base Color"])
    elif kind == "tiles":
        t = N.new("ShaderNodeTexBrick")
        t.inputs["Scale"].default_value = scale
        t.inputs["Color1"].default_value = (*c1, 1)
        t.inputs["Color2"].default_value = (*c2, 1)
        t.inputs["Mortar"].default_value = (*(c3 or (0.95, 0.95, 0.92)), 1)
        t.inputs["Mortar Size"].default_value = 0.025
        t.inputs["Brick Width"].default_value = 0.5
        t.inputs["Row Height"].default_value = 0.5
        t.offset = 0.0
        L.new(tc.outputs["Object"], t.inputs["Vector"])
        L.new(t.outputs["Color"], p.inputs["Base Color"])
        bump = N.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.3
        L.new(t.outputs["Fac"], bump.inputs["Height"])
        L.new(bump.outputs["Normal"], p.inputs["Normal"])
    elif kind == "wood":
        t = N.new("ShaderNodeTexWave")
        t.inputs["Scale"].default_value = scale
        t.inputs["Distortion"].default_value = 4.0
        t.inputs["Detail"].default_value = 3.0
        t.bands_direction = "X"
        L.new(tc.outputs["Object"], t.inputs["Vector"])
        ramp = N.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].color = (*c1, 1)
        ramp.color_ramp.elements[1].color = (*c2, 1)
        L.new(t.outputs["Fac"], ramp.inputs["Fac"])
        L.new(ramp.outputs["Color"], p.inputs["Base Color"])
    m.diffuse_color = (*c1, 1)
    return m


# --------------------------------------------------------------------------- meshes

def _base_mesh(kind, **kw):
    key = (kind, tuple(sorted(kw.items())))
    if key in _MESH_CACHE:
        return _MESH_CACHE[key]
    me = bpy.data.meshes.new(f"{kind}")
    bm = bmesh.new()
    if kind == "sphere":
        bmesh.ops.create_uvsphere(bm, u_segments=kw.get("u", 40), v_segments=kw.get("v", 24), radius=1.0)
    elif kind == "cylinder":
        bmesh.ops.create_cone(bm, cap_ends=True, segments=kw.get("seg", 48), radius1=1.0, radius2=1.0, depth=1.0)
    elif kind == "cone":
        bmesh.ops.create_cone(bm, cap_ends=True, segments=kw.get("seg", 32), radius1=1.0,
                              radius2=kw.get("r2", 0.0), depth=1.0)
    elif kind == "cube":
        bmesh.ops.create_cube(bm, size=1.0)
    elif kind == "rcube":  # rounded box via bevel
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.bevel(bm, geom=list(bm.edges) + list(bm.verts), offset=kw.get("b", 0.08),
                        segments=3, affect="EDGES", profile=0.5)
    elif kind == "torus":
        R, r = 1.0, kw.get("r", 0.25)
        n1, n2 = 48, 16
        verts = []
        for i in range(n1):
            a = 2 * math.pi * i / n1
            for j in range(n2):
                b = 2 * math.pi * j / n2
                verts.append(bm.verts.new(((R + r * math.cos(b)) * math.cos(a),
                                           (R + r * math.cos(b)) * math.sin(a), r * math.sin(b))))
        for i in range(n1):
            for j in range(n2):
                a = verts[i * n2 + j]
                b = verts[((i + 1) % n1) * n2 + j]
                c = verts[((i + 1) % n1) * n2 + (j + 1) % n2]
                d = verts[i * n2 + (j + 1) % n2]
                bm.faces.new((a, b, c, d))
    elif kind == "bowl":  # open hemisphere shell (lathe)
        prof = kw.get("prof")
        n = 48
        rings = []
        for (r, z) in prof:
            ring = [bm.verts.new((r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n), z)) for i in range(n)]
            rings.append(ring)
        for k in range(len(rings) - 1):
            for i in range(n):
                bm.faces.new((rings[k][i], rings[k][(i + 1) % n], rings[k + 1][(i + 1) % n], rings[k + 1][i]))
        # close the bottom with a cap
        bm.faces.new(list(reversed(rings[0])))
    bm.to_mesh(me)
    bm.free()
    for poly in me.polygons:
        poly.use_smooth = kind not in ("cube",)
    _MESH_CACHE[key] = me
    return me


def obj(name, kind, loc=(0, 0, 0), scale=(1, 1, 1), material=None, parent=None, rot=(0, 0, 0), **kw):
    me = _base_mesh(kind, **kw)
    o = bpy.data.objects.new(name, me)
    link(o)
    if parent is not None:
        o.parent = parent
    o.location = loc
    o.scale = scale if hasattr(scale, "__len__") else (scale, scale, scale)
    o.rotation_euler = rot
    if material is not None:
        if len(me.materials) == 0:
            me.materials.append(None)
        o.material_slots[0].link = "OBJECT"
        o.material_slots[0].material = material
    return o


def empty(name, loc=(0, 0, 0), parent=None, rot=(0, 0, 0)):
    o = bpy.data.objects.new(name, None)
    link(o)
    if parent is not None:
        o.parent = parent
    o.location = loc
    o.rotation_euler = rot
    return o


def curve_obj(name, npts=32, bevel=0.01, material=None, parent=None, closed=False, res=2):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = bevel
    cu.bevel_resolution = res
    cu.use_fill_caps = True
    cu.resolution_u = 6
    sp = cu.splines.new("NURBS")
    sp.points.add(npts - 1)
    sp.order_u = 4
    sp.use_endpoint_u = not closed
    sp.use_cyclic_u = closed
    o = bpy.data.objects.new(name, cu)
    link(o)
    if parent is not None:
        o.parent = parent
    if material is not None:
        cu.materials.append(material)
    return o


def set_curve_points(o, pts, radii=None):
    sp = o.data.splines[0]
    n = len(sp.points)
    if len(pts) != n:
        pts = resample(pts, n)
    for i, p in enumerate(pts):
        sp.points[i].co = (p[0], p[1], p[2], 1.0)
        if radii is not None:
            sp.points[i].radius = radii[i] if hasattr(radii, "__len__") else radii


def resample(pts, n):
    """Catmull-Rom resample of a polyline to n points."""
    P = [Vector(p) for p in pts]
    if len(P) == 1:
        return [P[0].copy() for _ in range(n)]
    out = []
    m = len(P) - 1
    for i in range(n):
        u = i / (n - 1) * m
        k = min(int(u), m - 1)
        f = u - k
        p0 = P[max(k - 1, 0)]
        p1 = P[k]
        p2 = P[k + 1]
        p3 = P[min(k + 2, m)]
        f2, f3 = f * f, f * f * f
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f2 + (-p0 + 3 * p1 - 3 * p2 + p3) * f3))
    return out


# --------------------------------------------------------------------------- math / easing

def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in(x):
    x = clamp(x)
    return x ** 3


def back_out(x, s=1.7):
    x = clamp(x) - 1
    return x * x * ((s + 1) * x + s) + 1


def elastic_out(x):
    x = clamp(x)
    if x in (0, 1):
        return x
    return 2 ** (-10 * x) * math.sin((x * 10 - 0.75) * (2 * math.pi) / 3) + 1


def seg(t, a, b):
    """normalized progress of t inside [a,b]"""
    if b == a:
        return 1.0 if t >= b else 0.0
    return clamp((t - a) / (b - a))


def lerp(a, b, f):
    if hasattr(a, "__len__"):
        return tuple(x + (y - x) * f for x, y in zip(a, b))
    return a + (b - a) * f


def kf(t, keys, ease=smooth):
    """keys: [(time, value), ...] piecewise interpolation with easing per segment.
    A key may be (time, value, easefn) to override the easing of the segment ending there."""
    if t <= keys[0][0]:
        return keys[0][1]
    for i in range(1, len(keys)):
        if t <= keys[i][0]:
            t0, v0 = keys[i - 1][0], keys[i - 1][1]
            t1, v1 = keys[i][0], keys[i][1]
            e = keys[i][2] if len(keys[i]) > 2 else ease
            return lerp(v0, v1, e((t - t0) / (t1 - t0)) if t1 > t0 else 1.0)
    return keys[-1][1]


def bounce_arc(t, t0, t1, p0, p1, h):
    """parabolic hop from p0 to p1 between t0..t1 with apex height h."""
    f = seg(t, t0, t1)
    p = lerp(p0, p1, f)
    return (p[0], p[1], p[2] + 4 * h * f * (1 - f))


def rng(seed):
    return random.Random(seed)


V = Vector
E = Euler
