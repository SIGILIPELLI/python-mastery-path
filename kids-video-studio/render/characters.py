"""
Hand-built flat-vector SVG characters for the Kids Video Studio -- Kiko the
squirrel and Bibbo the bunny -- plus a few small props. Everything is drawn
with basic shapes (ellipse/circle/path) so it can be generated purely from
Python with no external art assets, keeping the whole pipeline free/offline.

Each function returns an SVG fragment (a <g>...</g>) meant to be dropped
inside a per-character wrapper <svg viewBox="0 0 220 260">. Pose is a plain
dict so render/scene_poses.py can describe each scene's expressions without
touching this file.
"""

KIKO_BODY = "#C97B4A"
KIKO_BODY_DARK = "#A85F35"
KIKO_BELLY = "#F3E0C6"
KIKO_SCARF = "#4C9A5B"

BIBBO_BODY = "#FBF7EF"
BIBBO_SHADE = "#E9E1D2"
BIBBO_EAR_PINK = "#F6A6C1"
BIBBO_BOW = "#6FB7E0"


def _eyes(cx1, cx2, cy, state):
    """state: normal | wide | closed | worried"""
    if state == "closed":
        return f"""
        <path d="M {cx1-9} {cy} Q {cx1} {cy-8} {cx1+9} {cy}" stroke="#3a2a1a" stroke-width="3" fill="none" stroke-linecap="round"/>
        <path d="M {cx2-9} {cy} Q {cx2} {cy-8} {cx2+9} {cy}" stroke="#3a2a1a" stroke-width="3" fill="none" stroke-linecap="round"/>
        """
    r = 11 if state == "wide" else 9
    pr = 5.5 if state == "wide" else 4.5
    extra = ""
    if state == "worried":
        r, pr = 10, 4
        extra = f"""
        <path d="M {cx1-10} {cy-14} L {cx1+2} {cy-10}" stroke="#3a2a1a" stroke-width="2.5" stroke-linecap="round"/>
        <path d="M {cx2+10} {cy-14} L {cx2-2} {cy-10}" stroke="#3a2a1a" stroke-width="2.5" stroke-linecap="round"/>
        """
    return f"""
    <circle cx="{cx1}" cy="{cy}" r="{r}" fill="white"/>
    <circle cx="{cx2}" cy="{cy}" r="{r}" fill="white"/>
    <circle cx="{cx1+1.5}" cy="{cy+1}" r="{pr}" fill="#2b1c10"/>
    <circle cx="{cx2+1.5}" cy="{cy+1}" r="{pr}" fill="#2b1c10"/>
    <circle cx="{cx1-2}" cy="{cy-2}" r="1.6" fill="white"/>
    <circle cx="{cx2-2}" cy="{cy-2}" r="1.6" fill="white"/>
    {extra}
    """


def _mouth(cx, cy, state, color="#3a2a1a"):
    """state: neutral | open | smile"""
    if state == "open":
        return f'<ellipse cx="{cx}" cy="{cy}" rx="7" ry="9" fill="#7a3b2e"/>'
    if state == "smile":
        return f'<path d="M {cx-10} {cy-2} Q {cx} {cy+9} {cx+10} {cy-2}" stroke="{color}" stroke-width="2.5" fill="none" stroke-linecap="round"/>'
    return f'<path d="M {cx-5} {cy} Q {cx} {cy+3} {cx+5} {cy}" stroke="{color}" stroke-width="2" fill="none" stroke-linecap="round"/>'


def kiko_svg(pose: dict) -> str:
    tail = pose.get("tail", "back")
    eyes = pose.get("eyes", "normal")
    mouth = pose.get("mouth", "neutral")
    tail_angle = {"back": 28, "wrap": -150, "peek": -115, "poof": 55}.get(tail, 28)

    return f"""
    <g class="kiko-rig">
      <g class="kiko-tail" style="transform-origin: 148px 178px; transform: rotate({tail_angle}deg);">
        <ellipse cx="148" cy="98" rx="30" ry="74" fill="{KIKO_BODY_DARK}"/>
        <ellipse cx="148" cy="94" rx="16" ry="60" fill="{KIKO_BELLY}"/>
      </g>
      <ellipse cx="110" cy="182" rx="46" ry="54" fill="{KIKO_BODY}"/>
      <ellipse cx="110" cy="196" rx="25" ry="36" fill="{KIKO_BELLY}"/>
      <path d="M 84 148 Q 110 138 136 148 L 132 166 Q 110 158 88 166 Z" fill="{KIKO_SCARF}"/>
      <circle cx="86" cy="76" r="15" fill="{KIKO_BODY_DARK}"/>
      <circle cx="134" cy="76" r="15" fill="{KIKO_BODY_DARK}"/>
      <circle cx="86" cy="76" r="8" fill="{KIKO_BELLY}"/>
      <circle cx="134" cy="76" r="8" fill="{KIKO_BELLY}"/>
      <circle cx="110" cy="108" r="40" fill="{KIKO_BODY}"/>
      <ellipse cx="110" cy="122" rx="19" ry="13" fill="{KIKO_BELLY}"/>
      {_eyes(97, 123, 98, eyes)}
      <ellipse cx="110" cy="110" rx="4" ry="3" fill="#3a2a1a"/>
      {_mouth(110, 130, mouth)}
      <ellipse cx="84" cy="214" rx="12" ry="9" fill="{KIKO_BODY}"/>
      <ellipse cx="136" cy="214" rx="12" ry="9" fill="{KIKO_BODY}"/>
    </g>
    """


def bibbo_svg(pose: dict) -> str:
    eyes = pose.get("eyes", "normal")
    mouth = pose.get("mouth", "smile")
    ear = pose.get("ear", "perk")
    ear_angle = -18 if ear == "wiggle" else 0

    return f"""
    <g class="bibbo-rig">
      <ellipse cx="70" cy="52" rx="15" ry="46" fill="{BIBBO_BODY}" stroke="{BIBBO_SHADE}" stroke-width="2"
        style="transform-origin: 70px 96px; transform: rotate(-14deg);"/>
      <ellipse cx="66" cy="70" rx="7" ry="26" fill="{BIBBO_EAR_PINK}"
        style="transform-origin: 70px 96px; transform: rotate(-14deg);"/>
      <g class="bibbo-ear-wiggle" style="transform-origin: 150px 96px; transform: rotate({ear_angle}deg);">
        <ellipse cx="150" cy="50" rx="15" ry="48" fill="{BIBBO_BODY}" stroke="{BIBBO_SHADE}" stroke-width="2"/>
        <ellipse cx="150" cy="30" rx="8" ry="8" fill="{BIBBO_BOW}"/>
      </g>
      <ellipse cx="110" cy="184" rx="48" ry="52" fill="{BIBBO_BODY}" stroke="{BIBBO_SHADE}" stroke-width="2"/>
      <ellipse cx="110" cy="198" rx="26" ry="34" fill="#ffffff"/>
      <circle cx="110" cy="108" r="42" fill="{BIBBO_BODY}" stroke="{BIBBO_SHADE}" stroke-width="2"/>
      {_eyes(96, 124, 100, eyes)}
      <ellipse cx="110" cy="118" rx="4.5" ry="3.5" fill="#e88ba0"/>
      {_mouth(110, 128, mouth, color="#b5675a")}
      <ellipse cx="82" cy="220" rx="13" ry="10" fill="{BIBBO_BODY}"/>
      <ellipse cx="138" cy="220" rx="13" ry="10" fill="{BIBBO_BODY}"/>
      <circle cx="110" cy="234" r="14" fill="#ffffff" stroke="{BIBBO_SHADE}" stroke-width="2"/>
    </g>
    """


def berry_svg() -> str:
    return """
    <g>
      <path d="M 20 6 Q 26 0 30 6" stroke="#4C9A5B" stroke-width="3" fill="none" stroke-linecap="round"/>
      <circle cx="20" cy="24" r="18" fill="#D8433D"/>
      <circle cx="14" cy="18" r="4" fill="#F08A85" opacity="0.8"/>
    </g>
    """


def nut_pile_svg() -> str:
    return """
    <g>
      <ellipse cx="40" cy="52" rx="42" ry="10" fill="#00000018"/>
      <ellipse cx="18" cy="42" rx="14" ry="11" fill="#B9773E"/>
      <ellipse cx="42" cy="36" rx="16" ry="13" fill="#C98A4C"/>
      <ellipse cx="66" cy="44" rx="13" ry="10" fill="#B9773E"/>
      <path d="M 42 23 Q 46 16 52 22" stroke="#7a5228" stroke-width="3" fill="none" stroke-linecap="round"/>
    </g>
    """


def mushroom_svg() -> str:
    return """
    <g>
      <rect x="26" y="34" width="12" height="22" rx="5" fill="#F3E7D3"/>
      <path d="M 6 34 Q 32 -6 58 34 Z" fill="#E08A3C"/>
      <circle cx="20" cy="24" r="3" fill="#F6D9B6"/>
      <circle cx="42" cy="20" r="3.5" fill="#F6D9B6"/>
      <circle cx="32" cy="30" r="2.5" fill="#F6D9B6"/>
    </g>
    """


def sparkle_svg(size=22, color="#FFD166") -> str:
    s = size
    return f"""
    <path d="M {s/2} 0 L {s*0.62} {s*0.38} L {s} {s/2} L {s*0.62} {s*0.62} L {s/2} {s} L {s*0.38} {s*0.62} L 0 {s/2} L {s*0.38} {s*0.38} Z" fill="{color}"/>
    """
