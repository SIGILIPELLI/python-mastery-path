"""
Builds one self-contained HTML page per scene: forest background, Kiko +
Bibbo positioned/posed per render/scene_poses.py, any props, and a caption
track timed to that scene's per-line audio durations. Playwright records
this page for the scene's total duration (render/record.py, reused as-is
from the coding-tutorial pipeline).
"""
from render.characters import kiko_svg, bibbo_svg, berry_svg, nut_pile_svg, mushroom_svg, sparkle_svg

VERTICAL_SIZE = {"width": 1080, "height": 1920}
HORIZONTAL_SIZE = {"width": 1920, "height": 1080}

BG_SKY = {
    "morning": ("#BEE7F5", "#FFF4D6"),
    "golden": ("#FFD9A0", "#FFB199"),
}

PROP_BUILDERS = {
    "berry": berry_svg,
    "nuts": nut_pile_svg,
    "mushroom": mushroom_svg,
}

FONT_STACK = {
    "en": "'Baloo 2','Arial Rounded MT Bold','Helvetica Neue',Arial,sans-serif",
    "te": "'Kohinoor Telugu','Noto Sans Telugu','Telugu Sangam MN',sans-serif",
}

CAP_COLORS = {
    "kiko": "#F0B27A",
    "bibbo": "#AEE1F0",
    "narrator": "#E7DFF5",
}


def _background_svg(w: int, h: int, bg: str) -> str:
    top, bottom = BG_SKY.get(bg, BG_SKY["morning"])
    ground_top = h * 0.72
    return f"""
    <svg class="bg-layer" viewBox="0 0 {w} {h}" width="{w}" height="{h}" preserveAspectRatio="none">
      <defs>
        <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="{top}"/>
          <stop offset="100%" stop-color="{bottom}"/>
        </linearGradient>
        <linearGradient id="ground" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#8FCB6B"/>
          <stop offset="100%" stop-color="#6FAE4E"/>
        </linearGradient>
      </defs>
      <rect x="0" y="0" width="{w}" height="{h}" fill="url(#sky)"/>
      <circle cx="{w*0.86}" cy="{h*0.16}" r="{h*0.07}" fill="#FFF3B0" opacity="0.9"/>
      <g opacity="0.85" fill="#ffffff">
        <ellipse cx="{w*0.18}" cy="{h*0.14}" rx="70" ry="26"/>
        <ellipse cx="{w*0.25}" cy="{h*0.10}" rx="55" ry="22"/>
        <ellipse cx="{w*0.55}" cy="{h*0.22}" rx="60" ry="20"/>
      </g>
      <rect x="0" y="{ground_top}" width="{w}" height="{h-ground_top}" fill="url(#ground)"/>
      <ellipse cx="{w*0.08}" cy="{ground_top+10}" rx="90" ry="26" fill="#7fbf5b"/>
      <ellipse cx="{w*0.95}" cy="{ground_top+18}" rx="110" ry="30" fill="#7fbf5b"/>
      <g transform="translate({w*0.90},{h*0.30})">
        <rect x="-14" y="120" width="28" height="150" rx="10" fill="#8a5a34"/>
        <circle cx="0" cy="60" r="95" fill="#4f9a52"/>
        <circle cx="-70" cy="110" r="70" fill="#57a656"/>
        <circle cx="70" cy="110" r="70" fill="#57a656"/>
      </g>
      <g transform="translate({w*0.06},{h*0.40})" opacity="0.9">
        <circle cx="0" cy="90" r="60" fill="#5cab5b"/>
        <circle cx="40" cy="110" r="46" fill="#63b361"/>
      </g>
    </svg>
    """


def _char_wrap(kind: str, pose: dict, base_width: int) -> str:
    svg = kiko_svg(pose) if kind == "kiko" else bibbo_svg(pose)
    anim = pose.get("anim", "idle")
    scale = pose.get("scale", 1.0)
    x, y = pose["x"], pose["y"]
    delay = "0.15s" if kind == "bibbo" else "0s"
    holds = ""
    if kind == "bibbo" and pose.get("holds_berry"):
        holds = f'<div class="held-berry"><svg viewBox="0 0 40 40" width="42" height="42">{berry_svg()}</svg></div>'
    return f"""
    <div class="char-wrap" style="left:{x}%; top:{y}%; width:{base_width*scale}px;">
      <div class="char-bounce" style="animation-delay:{delay}">
        <div class="char-anim-{anim}">
          <svg viewBox="0 0 220 260" width="100%">{svg}</svg>
          {holds}
        </div>
      </div>
    </div>
    """


def _prop_html(prop: dict) -> str:
    builder = PROP_BUILDERS.get(prop["kind"])
    if not builder:
        return ""
    size = 90 * prop.get("scale", 1)
    return f"""
    <div class="prop" style="left:{prop['x']}%; top:{prop['y']}%; width:{size}px;">
      <svg viewBox="0 0 80 80" width="100%">{builder()}</svg>
    </div>
    """


def _sparkles(props: list) -> str:
    out = []
    for i, prop in enumerate(p for p in props if p["kind"] == "sparkle"):
        size = 26 * prop.get("scale", 1)
        delay = 0.25 * i
        out.append(f"""
        <div class="sparkle" style="left:{prop['x']}%; top:{prop['y']}%; width:{size}px; animation-delay:{delay}s;">
          <svg viewBox="0 0 22 22" width="100%">{sparkle_svg()}</svg>
        </div>
        """)
    return "".join(out)


def _captions_html(lines: list, lang: str) -> str:
    """lines: list of dicts {speaker, text, start_ms, dur_ms}"""
    out = []
    for ln in lines:
        color = CAP_COLORS.get(ln["speaker"], "#EFEFEF")
        out.append(f"""
        <div class="cap-line" style="background:{color};
          animation-duration:{ln['dur_ms']}ms; animation-delay:{ln['start_ms']}ms;">
          {ln['text']}
        </div>
        """)
    return f'<div class="caption-track lang-{lang}">{"".join(out)}</div>'


def _moral_html(text: str, lang: str) -> str:
    return f'<div class="moral-card lang-{lang}"><div class="moral-text">{text}</div></div>'


STYLE = """
* { margin:0; padding:0; box-sizing:border-box; }
html,body { width:100%; height:100%; overflow:hidden; background:#000; }
.stage { position:relative; width:100%; height:100%; overflow:hidden; }
.bg-layer { position:absolute; inset:0; width:100%; height:100%; display:block; }
.char-wrap { position:absolute; transform:translate(-50%,-100%); z-index:5; }
.char-bounce { animation:idleBounce 2.2s ease-in-out infinite; }
.prop { position:absolute; transform:translate(-50%,-100%); z-index:4; filter:drop-shadow(0 6px 4px rgba(0,0,0,0.15)); }
.sparkle { position:absolute; transform:translate(-50%,-50%); z-index:6; animation:floatSparkle 1.6s ease-in-out infinite; opacity:0; }
.held-berry { position:absolute; left:14px; top:196px; transform:rotate(-8deg); }

@keyframes idleBounce { 0%,100%{ transform:translateY(0);} 50%{ transform:translateY(-1.4%);} }
@keyframes munchPulse { 0%,100%{ transform:scaleY(1);} 50%{ transform:scaleY(0.95);} }
@keyframes hopIn {
  0% { transform:translateX(-38vw) translateY(0); opacity:0; }
  55% { opacity:1; }
  70% { transform:translateX(3%) translateY(-4%); }
  85% { transform:translateX(-1%) translateY(0); }
  100% { transform:translateX(0) translateY(0); opacity:1; }
}
@keyframes twirl { 0%{ transform:rotate(0deg) translateY(0);} 50%{ transform:rotate(180deg) translateY(-3%);} 100%{ transform:rotate(360deg) translateY(0);} }
@keyframes walkAcross { 0%{ transform:translateX(-10%);} 100%{ transform:translateX(10%);} }
@keyframes cheerBounce { 0%,100%{ transform:translateY(0) rotate(0deg);} 50%{ transform:translateY(-6%) rotate(-4deg);} }
@keyframes peekLean { 0%{ transform:translateX(0);} 100%{ transform:translateX(1.2%);} }
@keyframes earWiggle { 0%,100%{ transform:rotate(-8deg);} 50%{ transform:rotate(10deg);} }
@keyframes floatSparkle { 0%{ opacity:0; transform:translateY(0) scale(0.6);} 40%{ opacity:1;} 100%{ opacity:0; transform:translateY(-40px) scale(1.1);} }
@keyframes capShow { 0%{ opacity:0; transform:translateY(14px);} 14%{ opacity:1; transform:translateY(0);} 86%{ opacity:1;} 100%{ opacity:0;} }
@keyframes moralIn { 0%{ opacity:0; transform:scale(0.9);} 20%{ opacity:1; transform:scale(1);} 88%{ opacity:1;} 100%{ opacity:0;} }

.char-anim-idle {}
.char-anim-munch { animation:munchPulse 0.55s ease-in-out infinite; transform-origin:bottom center; }
.char-anim-hop-in { animation:hopIn 1s ease-out both; }
.char-anim-twirl { animation:twirl 1.5s linear infinite; }
.char-anim-walk { animation:walkAcross 6s ease-in-out both; }
.char-anim-cheer { animation:cheerBounce 0.7s ease-in-out infinite; }
.char-anim-peek { animation:peekLean 1.3s ease-in-out infinite alternate; }
.bibbo-ear-wiggle-anim { animation:earWiggle 0.9s ease-in-out infinite; }

.caption-track { position:absolute; left:6%; right:6%; bottom:5%; z-index:10; }
.cap-line {
  position:absolute; left:0; right:0; bottom:0;
  padding:1.6% 3%; border-radius:22px;
  font-size: 2.6vw; line-height:1.35; text-align:center; color:#2b2118;
  box-shadow:0 8px 18px rgba(0,0,0,0.18);
  opacity:0; animation-name:capShow; animation-timing-function:ease-out; animation-fill-mode:both;
}
.lang-te .cap-line { font-size:2.5vw; }

.moral-card { position:absolute; inset:0; display:flex; align-items:center; justify-content:center; z-index:10; }
.moral-text {
  background:rgba(255,255,255,0.92); border-radius:32px; padding:3% 5%;
  font-size:3.4vw; font-weight:700; text-align:center; color:#3a2a1a; max-width:80%;
  box-shadow:0 10px 30px rgba(0,0,0,0.2);
  opacity:0; animation:moralIn 6s ease-out both;
}
"""


def render_scene_html(scene_pose: dict, caption_lines: list, moral_text: str | None,
                       lang: str, vertical: bool, base_char_width: int = 280) -> str:
    size = VERTICAL_SIZE if vertical else HORIZONTAL_SIZE
    w, h = size["width"], size["height"]
    bg = scene_pose.get("bg", "morning")

    layers = [_background_svg(w, h, bg)]
    for prop in scene_pose.get("props", []):
        if prop["kind"] == "sparkle":
            continue
        layers.append(_prop_html(prop))
    if scene_pose.get("bibbo"):
        layers.append(_char_wrap("bibbo", scene_pose["bibbo"], base_char_width))
    if scene_pose.get("kiko"):
        layers.append(_char_wrap("kiko", scene_pose["kiko"], base_char_width))
    layers.append(_sparkles(scene_pose.get("props", [])))

    if moral_text is not None:
        layers.append(_moral_html(moral_text, lang))
    else:
        layers.append(_captions_html(caption_lines, lang))

    font = FONT_STACK.get(lang, FONT_STACK["en"])
    body = "".join(layers)
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
    body {{ font-family: {font}; }}
    {STYLE}
    </style></head><body><div class="stage">{body}</div></body></html>"""
