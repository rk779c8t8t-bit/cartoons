"""Single source of truth for the film timeline (no bpy import: shared with audio)."""
FPS = 30
SCENE_LEN = 4.0
N_SCENES = 9
DURATION = SCENE_LEN * N_SCENES

SCENES = [
    (1, "Little chef"), (2, "Flour cloud"), (3, "Giant spaghetti"), (4, "Kitchen catastrophe"),
    (5, "The chase"), (6, "Unexpected discovery"), (7, "Birth of a masterpiece"),
    (8, "Mom comes home"), (9, "The smallest chef"),
]

# (global_time_seconds, cue_name, gain) -- every cue matches an on-screen action
SFX_CUES = [
    (0.00, "whoosh_up", 0.7), (0.05, "tomato_toss", 0.6), (1.90, "catch_pop", 0.8), (2.45, "wink_ting", 0.6),
    (3.25, "tiny_steps", 0.4),
    (4.15, "stir", 0.5), (4.65, "stir", 0.5), (5.15, "stir", 0.5), (5.55, "bag_rustle", 0.8),
    (6.05, "bag_slip", 0.6), (6.35, "flour_poof", 0.8), (7.10, "blink", 0.6), (7.45, "shake", 0.8),
    (8.25, "lid_open", 0.8), (8.85, "noodle_rise", 0.9), (9.05, "gasp_boing", 0.6), (10.30, "noodle_squish", 0.7),
    (11.00, "zoom_hit", 0.8),
    (12.10, "noodle_slither", 0.7), (12.45, "tomato_fall", 0.7), (12.65, "tomato_fall", 0.6), (12.85, "spoon_clatter", 0.6),
    (13.20, "running_steps", 0.6), (14.00, "slip_squeak", 0.9), (14.70, "pot_bong", 0.55), (15.10, "peek_pop", 0.5),
    (16.00, "running_steps", 0.7), (16.80, "noodle_boing", 0.6), (17.20, "noodle_boing", 0.6), (17.70, "slide_hide", 0.6),
    (18.70, "peek_pop", 0.6), (18.80, "peek_pop", 0.6), (19.20, "double_take", 0.7),
    (20.30, "plate_ting", 0.5), (21.20, "idea_ding", 0.8), (21.80, "fork_pick", 0.6), (22.60, "twirl", 0.8),
    (24.00, "twirl", 0.8), (25.60, "sauce_plop", 0.9), (26.30, "basil_flutter", 0.5), (26.80, "cheese_sprinkle", 0.5),
    (27.40, "sparkle", 0.6),
    (28.05, "door_open", 0.8), (28.40, "mom_steps", 0.6), (29.50, "surprise_sting", 0.8), (30.60, "fork_plate", 0.6),
    (31.00, "chew", 0.6), (31.55, "delight_boing", 0.9),
    (32.10, "more_taps", 0.7), (33.40, "hat_adjust", 0.5), (34.80, "bow_ta_da", 0.9),
]
