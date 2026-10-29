"""Scene-wide setup: render settings, colour management, world, lights."""
import math
import bpy
from mathutils import Vector

import mats
from mats import hexc


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats._cache.clear()


def render_settings(res=(1080, 1920), pct=100, samples=32, fps=30, motion_blur=True, volumetrics=False, ssr=False):
    s = bpy.context.scene
    s.render.engine = "BLENDER_EEVEE"
    s.render.resolution_x, s.render.resolution_y = res
    s.render.resolution_percentage = pct
    s.render.fps = fps
    s.render.film_transparent = False
    e = s.eevee
    e.taa_render_samples = samples
    e.use_gtao = True
    e.gtao_distance = 0.6
    e.gtao_factor = 1.0
    e.use_soft_shadows = True
    e.shadow_cube_size = "1024"
    e.shadow_cascade_size = "4096"
    e.use_shadow_high_bitdepth = True
    e.use_bloom = True
    e.bloom_threshold = 1.2
    e.bloom_intensity = 0.03
    e.use_ssr = ssr
    e.use_ssr_refraction = False
    e.use_volumetric_lights = volumetrics
    e.use_volumetric_shadows = volumetrics
    e.volumetric_tile_size = "8"
    e.volumetric_samples = 32
    e.use_motion_blur = motion_blur
    e.motion_blur_shutter = 0.5
    e.motion_blur_steps = 1
    s.view_settings.view_transform = "AgX"
    try:
        s.view_settings.look = "AgX - Medium High Contrast"
    except TypeError:
        pass
    s.view_settings.exposure = 0.0
    s.render.image_settings.file_format = "PNG"
    s.render.image_settings.color_mode = "RGB"
    s.render.image_settings.compression = 30


def world_sky(top="#8fc2ef", horizon="#f6e7cf", strength=1.0, ground="#7a8f5a", clouds=0.5, cloud_color="#ffffff"):
    w = bpy.data.worlds.new("World") if not bpy.data.worlds else bpy.data.worlds[0]
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.elements[0].position = 0.0
    cr.elements[0].color = hexc(horizon)
    cr.elements[1].position = 0.45
    cr.elements[1].color = hexc(top)
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    # soft clouds: noise on the view direction, stretched horizontally
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.2, 1.2, 3.5)
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 2.2
    nz.inputs["Detail"].default_value = 6.0
    nz.inputs["Roughness"].default_value = 0.55
    nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
    cramp = nt.nodes.new("ShaderNodeValToRGB")
    cramp.color_ramp.elements[0].position = 0.62 - clouds * 0.2
    cramp.color_ramp.elements[1].position = 0.78 - clouds * 0.15
    cramp.color_ramp.elements[0].color = (0, 0, 0, 1)
    cramp.color_ramp.elements[1].color = (1, 1, 1, 1)
    nt.links.new(nz.outputs["Fac"], cramp.inputs["Fac"])
    # fade clouds near the zenith a bit and below horizon
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    nt.links.new(cramp.outputs["Color"], mix.inputs["Factor"])
    nt.links.new(ramp.outputs["Color"], mix.inputs[6])
    mix.inputs[7].default_value = hexc(cloud_color)
    nt.links.new(mix.outputs[2], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength
    nt.links.new(bg.outputs[0], out.inputs[0])
    return w, bg, ramp


def sun(name="Sun", rot=(50, 0, 30), energy=3.0, color="#fff1d6", angle=3.0):
    d = bpy.data.lights.new(name, "SUN")
    d.energy = energy
    d.color = hexc(color)[:3]
    d.angle = math.radians(angle)
    d.shadow_cascade_max_distance = 40
    d.shadow_cascade_count = 4
    d.shadow_cascade_fade = 0.1
    ob = bpy.data.objects.new(name, d)
    bpy.context.scene.collection.objects.link(ob)
    ob.rotation_euler = tuple(math.radians(a) for a in rot)
    return ob


def area(name, loc, target, energy=200, size=3.0, color="#ffffff", shadow=True):
    d = bpy.data.lights.new(name, "AREA")
    d.energy = energy
    d.size = size
    d.color = hexc(color)[:3]
    d.use_shadow = shadow
    ob = bpy.data.objects.new(name, d)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    direction = Vector(target) - Vector(loc)
    ob.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    return ob


def point(name, loc, energy=50, radius=0.3, color="#ffffff", shadow=True):
    d = bpy.data.lights.new(name, "POINT")
    d.energy = energy
    d.shadow_soft_size = radius
    d.color = hexc(color)[:3]
    d.use_shadow = shadow
    ob = bpy.data.objects.new(name, d)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    return ob


def camera(name="Cam", lens=40, fstop=4.0, dof=True):
    c = bpy.data.cameras.new(name)
    c.lens = lens
    c.sensor_fit = "VERTICAL"
    c.sensor_height = 24 * 16 / 9 / 1.0
    c.sensor_width = 24
    c.clip_start = 0.05
    c.clip_end = 400
    ob = bpy.data.objects.new(name, c)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.scene.camera = ob
    tgt = bpy.data.objects.new(name + "_target", None)
    bpy.context.scene.collection.objects.link(tgt)
    con = ob.constraints.new("TRACK_TO")
    con.target = tgt
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"
    c.dof.use_dof = dof
    c.dof.focus_object = tgt
    c.dof.aperture_fstop = fstop
    return ob, tgt


def cam_key(cam, tgt, frame, loc, look, lens=None, roll=None):
    cam.location = loc
    cam.keyframe_insert("location", frame=frame)
    tgt.location = look
    tgt.keyframe_insert("location", frame=frame)
    if lens is not None:
        cam.data.lens = lens
        cam.data.keyframe_insert("lens", frame=frame)
    if roll is not None:
        con = cam.constraints[0]
        cam.rotation_euler = (0, 0, 0)


def ease_all(kind="BEZIER"):
    for a in bpy.data.actions:
        for fc in a.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = kind


def join_static(exclude_prefixes=()):
    """Merge every static, unparented mesh (modifiers applied) into one object to cut draw calls."""
    cands = []
    for ob in bpy.context.scene.objects:
        if ob.type != "MESH" or ob.parent is not None or ob.animation_data is not None:
            continue
        if ob.data.shape_keys is not None or ob.particle_systems:
            continue
        if any(ob.name.startswith(p) for p in exclude_prefixes):
            continue
        if ob.location.z < -40:  # prototypes
            continue
        cands.append(ob)
    if len(cands) < 2:
        return None
    bpy.ops.object.select_all(action="DESELECT")
    for ob in cands:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = cands[0]
    bpy.ops.object.make_single_user(object=True, obdata=True)
    bpy.ops.object.convert(target="MESH")
    bpy.ops.object.join()
    j = bpy.context.view_layer.objects.active
    j.name = "static_env"
    return j
