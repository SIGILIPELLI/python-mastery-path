"""
Per-scene staging for kiko-tries-new-foods: where each character stands,
what expression/pose they hold, which props are on screen, and which CSS
animation class drives the scene's motion. Keyed by scene_number from the
script JSON. Purely a layout table -- the actual SVG/CSS lives in
characters.py and scene_template.py.

x/y are percent-of-stage anchors for the character's feet (bottom-center).
"""

GROUND_Y = 80

SCENES = {
    1: {
        "bg": "morning",
        "kiko": {"x": 50, "y": GROUND_Y, "scale": 1.15, "tail": "back", "eyes": "normal", "mouth": "open", "anim": "munch"},
        "bibbo": None,
        "props": [{"kind": "nuts", "x": 68, "y": GROUND_Y + 4, "scale": 1.1}],
    },
    2: {
        "bg": "morning",
        "kiko": {"x": 68, "y": GROUND_Y, "scale": 1.05, "tail": "poof", "eyes": "wide", "mouth": "neutral", "anim": "idle"},
        "bibbo": {"x": 26, "y": GROUND_Y, "scale": 1.0, "eyes": "normal", "mouth": "smile", "ear": "wiggle", "anim": "hop-in", "holds_berry": True},
        "props": [],
    },
    3: {
        "bg": "morning",
        "kiko": {"x": 70, "y": GROUND_Y, "scale": 1.0, "tail": "wrap", "eyes": "worried", "mouth": "neutral", "anim": "idle"},
        "bibbo": {"x": 32, "y": GROUND_Y, "scale": 1.0, "eyes": "normal", "mouth": "smile", "ear": "perk", "anim": "idle", "holds_berry": True},
        "props": [],
    },
    4: {
        "bg": "morning",
        "kiko": {"x": 82, "y": GROUND_Y + 2, "scale": 0.85, "tail": "wrap", "eyes": "wide", "mouth": "neutral", "anim": "idle"},
        "bibbo": {"x": 38, "y": GROUND_Y, "scale": 1.1, "eyes": "wide", "mouth": "open", "ear": "wiggle", "anim": "twirl", "holds_berry": False},
        "props": [{"kind": "sparkle", "x": 30, "y": 45, "scale": 1}, {"kind": "sparkle", "x": 55, "y": 38, "scale": 0.7}],
    },
    5: {
        "bg": "morning",
        "kiko": {"x": 58, "y": GROUND_Y, "scale": 1.0, "tail": "peek", "eyes": "normal", "mouth": "neutral", "anim": "peek"},
        "bibbo": {"x": 30, "y": GROUND_Y, "scale": 1.0, "eyes": "normal", "mouth": "smile", "ear": "perk", "anim": "idle", "holds_berry": True},
        "props": [],
    },
    6: {
        "bg": "morning",
        "kiko": {"x": 55, "y": GROUND_Y, "scale": 1.15, "tail": "back", "eyes": "wide", "mouth": "open", "anim": "idle"},
        "bibbo": {"x": 30, "y": GROUND_Y, "scale": 0.95, "eyes": "normal", "mouth": "smile", "ear": "perk", "anim": "idle", "holds_berry": False},
        "props": [{"kind": "sparkle", "x": 66, "y": 48, "scale": 0.8}],
    },
    7: {
        "bg": "morning",
        "kiko": {"x": 42, "y": GROUND_Y, "scale": 1.05, "tail": "back", "eyes": "normal", "mouth": "smile", "anim": "twirl"},
        "bibbo": {"x": 66, "y": GROUND_Y, "scale": 1.05, "eyes": "normal", "mouth": "smile", "ear": "wiggle", "anim": "twirl", "holds_berry": False},
        "props": [
            {"kind": "sparkle", "x": 30, "y": 45, "scale": 1},
            {"kind": "sparkle", "x": 55, "y": 35, "scale": 0.6},
            {"kind": "sparkle", "x": 75, "y": 48, "scale": 0.9},
        ],
    },
    8: {
        "bg": "morning",
        "kiko": {"x": 38, "y": GROUND_Y, "scale": 1.0, "tail": "back", "eyes": "normal", "mouth": "smile", "anim": "walk"},
        "bibbo": {"x": 66, "y": GROUND_Y, "scale": 1.0, "eyes": "normal", "mouth": "smile", "ear": "wiggle", "anim": "cheer", "holds_berry": False},
        "props": [{"kind": "mushroom", "x": 82, "y": GROUND_Y + 2, "scale": 1.0}],
    },
    9: {
        "bg": "golden",
        "kiko": {"x": 40, "y": GROUND_Y, "scale": 1.0, "tail": "back", "eyes": "normal", "mouth": "smile", "anim": "idle"},
        "bibbo": {"x": 62, "y": GROUND_Y, "scale": 1.0, "eyes": "normal", "mouth": "smile", "ear": "perk", "anim": "idle", "holds_berry": False},
        "props": [
            {"kind": "nuts", "x": 48, "y": GROUND_Y + 6, "scale": 0.9},
            {"kind": "mushroom", "x": 58, "y": GROUND_Y + 7, "scale": 0.7},
        ],
    },
}
