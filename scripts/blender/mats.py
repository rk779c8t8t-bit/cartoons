"""Procedural materials (EEVEE friendly)."""
import bpy

_cache = {}


def _rgba(c):
    return (c[0], c[1], c[2], 1.0) if len(c) == 3 else tuple(c)


def hexc(h):
    h = h.lstrip("#")
    srgb = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    lin = [(c / 12.92) if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
    return (lin[0], lin[1], lin[2], 1.0)


def _new(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    return m, nt, bsdf


def basic(name, color, rough=0.5, metal=0.0, sheen=0.0, spec=0.5, emission=None, emit_strength=0.0, coat=0.0, alpha=1.0):
    key = ("basic", name)
    if key in _cache:
        return _cache[key]
    m, nt, b = _new(name)
    b.inputs["Base Color"].default_value = _rgba(color)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Sheen Weight"].default_value = sheen
    b.inputs["Specular IOR Level"].default_value = spec
    b.inputs["Coat Weight"].default_value = coat
    if emission is not None:
        b.inputs["Emission Color"].default_value = _rgba(emission)
        b.inputs["Emission Strength"].default_value = emit_strength
    if alpha < 1.0:
        b.inputs["Alpha"].default_value = alpha
        m.blend_method = "BLEND"
        m.shadow_method = "HASHED"
    _cache[key] = m
    return m


def _noise_bump(nt, b, scale=60.0, strength=0.25, dist=0.01, detail=6.0, coord="Object"):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = detail
    nt.links.new(tc.outputs[coord], nz.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = strength
    bump.inputs["Distance"].default_value = dist
    nt.links.new(nz.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return tc, nz, bump


def fur(name, color, tip=None, var=0.12, rough=0.8, stripes=None, stripe_scale=6.0, fuzz=0.35):
    """Soft fur look: fine anisotropic-ish noise bump, sheen, lighter 'fuzz' rim, colour variation.
    stripes: optional darker colour drawn as soft tabby bands (object space)."""
    key = ("fur", name)
    if key in _cache:
        return _cache[key]
    m, nt, b = _new(name)
    base = _rgba(color)
    tipc = _rgba(tip) if tip else tuple(min(1.0, c * 1.35 + 0.05) for c in base[:3]) + (1.0,)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    # strand-like stretched noise for bump
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (90.0, 90.0, 22.0)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 1.0
    nz.inputs["Detail"].default_value = 8.0
    nz.inputs["Roughness"].default_value = 0.65
    nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.32
    bump.inputs["Distance"].default_value = 0.006
    nt.links.new(nz.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    # colour variation (low frequency)
    nz2 = nt.nodes.new("ShaderNodeTexNoise")
    nz2.inputs["Scale"].default_value = 7.0
    nz2.inputs["Detail"].default_value = 3.0
    nt.links.new(tc.outputs["Object"], nz2.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = tuple(c * (1 - var) for c in base[:3]) + (1.0,)
    ramp.color_ramp.elements[1].color = tuple(min(1.0, c * (1 + var)) for c in base[:3]) + (1.0,)
    nt.links.new(nz2.outputs["Fac"], ramp.inputs["Fac"])
    col_out = ramp.outputs["Color"]
    if stripes is not None:
        wave = nt.nodes.new("ShaderNodeTexWave")
        wave.wave_type = "BANDS"
        wave.bands_direction = "Z"
        wave.inputs["Scale"].default_value = stripe_scale
        wave.inputs["Distortion"].default_value = 4.0
        wave.inputs["Detail"].default_value = 2.0
        nt.links.new(tc.outputs["Object"], wave.inputs["Vector"])
        sr = nt.nodes.new("ShaderNodeValToRGB")
        sr.color_ramp.elements[0].position = 0.6
        sr.color_ramp.elements[1].position = 0.85
        sr.color_ramp.elements[0].color = (0, 0, 0, 1)
        sr.color_ramp.elements[1].color = (0.55, 0.55, 0.55, 1)
        nt.links.new(wave.outputs["Fac"], sr.inputs["Fac"])
        mixs = nt.nodes.new("ShaderNodeMix")
        mixs.data_type = "RGBA"
        nt.links.new(sr.outputs["Color"], mixs.inputs["Factor"])
        nt.links.new(col_out, mixs.inputs[6])
        mixs.inputs[7].default_value = _rgba(stripes)
        col_out = mixs.outputs[2]
    # fuzz rim: lighter towards grazing angles
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.45
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = fuzz * 2.0
    nt.links.new(lw.outputs["Facing"], mul.inputs[0])
    nt.links.new(mul.outputs[0], mix.inputs["Factor"])
    nt.links.new(col_out, mix.inputs[6])
    mix.inputs[7].default_value = tipc
    nt.links.new(mix.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    b.inputs["Sheen Weight"].default_value = 0.9
    b.inputs["Sheen Roughness"].default_value = 0.35
    b.inputs["Specular IOR Level"].default_value = 0.25
    b.inputs["Subsurface Weight"].default_value = 0.0
    _cache[key] = m
    return m


def fabric(name, color, rough=0.9, weave=140.0, worn=0.0, worn_color=None):
    """Cloth with fine weave bump; worn>0 adds faded patches."""
    key = ("fabric", name)
    if key in _cache:
        return _cache[key]
    m, nt, b = _new(name)
    base = _rgba(color)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.inputs["Scale"].default_value = weave
    bump_strength = 0.06
    wave.inputs["Distortion"].default_value = 0.6
    nt.links.new(tc.outputs["Object"], wave.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = bump_strength
    bump.inputs["Distance"].default_value = 0.002
    nt.links.new(wave.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    if worn > 0:
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 9.0
        nz.inputs["Detail"].default_value = 5.0
        nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.55 - worn * 0.1
        ramp.color_ramp.elements[1].position = 0.85
        wc = _rgba(worn_color) if worn_color else tuple(min(1, c * 1.5 + 0.08) for c in base[:3]) + (1,)
        ramp.color_ramp.elements[0].color = base
        ramp.color_ramp.elements[1].color = wc
        nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    else:
        b.inputs["Base Color"].default_value = base
    b.inputs["Roughness"].default_value = rough
    b.inputs["Sheen Weight"].default_value = 0.6
    b.inputs["Specular IOR Level"].default_value = 0.3
    _cache[key] = m
    return m


def leather_worn(name, color, scuff_color):
    """Old brown boots: scuffs and creases."""
    key = ("leather", name)
    if key in _cache:
        return _cache[key]
    m, nt, b = _new(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 14.0
    nz.inputs["Detail"].default_value = 8.0
    nz.inputs["Roughness"].default_value = 0.7
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.42
    ramp.color_ramp.elements[1].position = 0.62
    ramp.color_ramp.elements[0].color = _rgba(color)
    ramp.color_ramp.elements[1].color = _rgba(scuff_color)
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    rr = nt.nodes.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value = 0.35
    rr.inputs["To Max"].default_value = 0.85
    nt.links.new(nz.outputs["Fac"], rr.inputs["Value"])
    nt.links.new(rr.outputs["Result"], b.inputs["Roughness"])
    v = nt.nodes.new("ShaderNodeTexVoronoi")
    v.inputs["Scale"].default_value = 40.0
    nt.links.new(tc.outputs["Object"], v.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.3
    bump.inputs["Distance"].default_value = 0.004
    nt.links.new(v.outputs["Distance"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    _cache[key] = m
    return m


def eye_iris(name, color, dark):
    key = ("iris", name)
    if key in _cache:
        return _cache[key]
    m, nt, b = _new(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    grad = nt.nodes.new("ShaderNodeTexGradient")
    grad.gradient_type = "SPHERICAL"
    nt.links.new(tc.outputs["Object"], grad.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = _rgba(dark)
    ramp.color_ramp.elements[1].position = 0.55
    ramp.color_ramp.elements[1].color = _rgba(color)
    e = ramp.color_ramp.elements.new(0.9)
    e.color = tuple(min(1, c * 1.6) for c in _rgba(color)[:3]) + (1,)
    nt.links.new(grad.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.05
    b.inputs["Coat Weight"].default_value = 1.0
    b.inputs["Coat Roughness"].default_value = 0.02
    b.inputs["Emission Color"].default_value = _rgba(color)
    b.inputs["Emission Strength"].default_value = 0.08
    _cache[key] = m
    return m


def wood(name, c1, c2, scale=3.0, rough=0.7, dry=False):
    key = ("wood", name)
    if key in _cache:
        return _cache[key]
    m, nt, b = _new(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0, 12.0, 12.0) if not dry else (1.0, 1.0, 6.0)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.inputs["Scale"].default_value = scale
    wave.inputs["Distortion"].default_value = 6.0
    wave.inputs["Detail"].default_value = 4.0
    nt.links.new(mp.outputs["Vector"], wave.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = _rgba(c1)
    ramp.color_ramp.elements[1].color = _rgba(c2)
    nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.35
    bump.inputs["Distance"].default_value = 0.01
    nt.links.new(wave.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = rough
    _cache[key] = m
    return m


def noisy(name, c1, c2, scale=5.0, rough=0.8, bump=0.3, detail=6.0, rough2=None, pos=(0.35, 0.7)):
    """Generic two-colour noise material (ground, stone, foliage)."""
    key = ("noisy", name)
    if key in _cache:
        return _cache[key]
    m, nt, b = _new(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = detail
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = pos[0]
    ramp.color_ramp.elements[1].position = pos[1]
    ramp.color_ramp.elements[0].color = _rgba(c1)
    ramp.color_ramp.elements[1].color = _rgba(c2)
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    if bump > 0:
        bp = nt.nodes.new("ShaderNodeBump")
        bp.inputs["Strength"].default_value = bump
        bp.inputs["Distance"].default_value = 0.02
        nz2 = nt.nodes.new("ShaderNodeTexNoise")
        nz2.inputs["Scale"].default_value = scale * 6
        nz2.inputs["Detail"].default_value = 4
        nt.links.new(tc.outputs["Object"], nz2.inputs["Vector"])
        nt.links.new(nz2.outputs["Fac"], bp.inputs["Height"])
        nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    if rough2 is not None:
        rr = nt.nodes.new("ShaderNodeMapRange")
        rr.inputs["To Min"].default_value = rough
        rr.inputs["To Max"].default_value = rough2
        nt.links.new(nz.outputs["Fac"], rr.inputs["Value"])
        nt.links.new(rr.outputs["Result"], b.inputs["Roughness"])
    else:
        b.inputs["Roughness"].default_value = rough
    _cache[key] = m
    return m


def set_wetness(value, frame=None):
    """Global wetness driver stored on a world custom prop; materials that support it read roughness via a value node."""
    pass
