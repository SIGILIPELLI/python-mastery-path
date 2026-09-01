"""
Animated stick-figure scenes for video beats.

Each figure is its own inline <svg> drawn around a local origin, so CSS
transform-origin values for the joints stay simple (no nested-translate
math). Limbs are <g> wrappers rotated by CSS keyframes, which keeps the
whole thing pure CSS -- no JS timing to stay in sync with, and it renders
identically frame-to-frame under Playwright's recorder.

Design goals (set 2026-08-29 per user request "more motions... most
engaging"):
  * Every figure is ALWAYS moving -- a constant breathing/sway idle under
    whatever the scene-specific limb animation is doing. Nothing freezes:
    scene animations loop (`infinite alternate`) rather than playing once
    with `forwards`.
  * The scene catalog covers conceptual / product / leadership topics
    (present, discuss, pushback, balance, prioritize, roadmap, checklist,
    search, write, measure, climb, idea, handshake) as well as the original
    code-oriented concurrency scenes (sequential, parallel, blocked, gil,
    handoff). The writer agents pick the scene that literally matches what
    the narration is saying on that beat.
"""

# Joint coordinates, shared by the SVG markup and the CSS transform-origins.
SHOULDER_Y = -24
HIP_Y = 12

FIGURE_SVG = """
<svg class="fig {extra_class}" viewBox="-42 -78 84 128" style="{style}">
  <ellipse class="shadow" cx="0" cy="42" rx="20" ry="4"/>
  <g class="body">
    <circle class="head" cx="0" cy="-42" r="11"/>
    <line class="spine" x1="0" y1="-31" x2="0" y2="12"/>
    <g class="arm arm-l"><line x1="0" y1="-24" x2="-20" y2="-4"/></g>
    <g class="arm arm-r"><line x1="0" y1="-24" x2="20" y2="-4"/></g>
    <g class="leg leg-l"><line x1="0" y1="12" x2="-14" y2="40"/></g>
    <g class="leg leg-r"><line x1="0" y1="12" x2="14" y2="40"/></g>
    {props}
  </g>
</svg>
"""

_CSS = """
.stage-stick {
  width: 100%; height: 100%;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  gap: var(--stick-gap);
}
.fig-row {
  display: flex; align-items: flex-end; justify-content: center;
  gap: var(--fig-gap);
  animation: row-sway 4.2s ease-in-out infinite;
}
.fig-row.pair  { gap: calc(var(--fig-gap) * 0.5); }
.fig-row.pair  .fig { width: calc(var(--fig-size) * 0.74); }
.fig-row.crowd { gap: calc(var(--fig-gap) * 0.7); flex-wrap: nowrap; }
.fig-row.crowd .fig { width: calc(var(--fig-size) * 0.42); }
.fig-slot { display: flex; flex-direction: column; align-items: center; gap: 14px; }
.fig-label {
  color: #8fa2c7; font-size: var(--label-size); letter-spacing: 0.04em;
  font-family: ui-monospace, "SF Mono", Menlo, monospace; text-align: center;
}
.fig-label.done { color: #7ee787; }
.fig-label.wait { color: #febc2e; }

.fig { width: var(--fig-size); height: auto; overflow: visible; }
.fig line, .fig circle, .fig path, .fig rect, .fig polyline, .fig ellipse {
  stroke: #e7ecf7; stroke-width: 4.2; stroke-linecap: round;
  stroke-linejoin: round; fill: none;
  vector-effect: non-scaling-stroke;
}
.fig .head { stroke-width: 4.2; }
.fig .shadow { stroke: none; fill: rgba(0,0,0,0.32);
               animation: shadow-pulse 2.6s ease-in-out infinite; }
.fig.accent line, .fig.accent circle, .fig.accent path, .fig.accent polyline { stroke: #7ee787; }
.fig.warn   line, .fig.warn   circle, .fig.warn   path, .fig.warn   polyline { stroke: #febc2e; }
.fig.danger line, .fig.danger circle, .fig.danger path, .fig.danger polyline { stroke: #ff6b6b; }

.fig g { transform-box: view-box; }
/* the whole standing body gets a constant, subtle life-signs motion */
.fig .body { animation: breathe 2.6s ease-in-out infinite; transform-origin: 0px 40px; }
.arm { transform-origin: 0px -24px; }   /* shoulder */
.leg { transform-origin: 0px 12px; }    /* hip */
.head { transform-origin: 0px -42px; }

/* prop panels that sit beside a figure in the row */
.panel { width: calc(var(--fig-size) * 1.15); height: auto; overflow: visible; }
.panel line, .panel rect, .panel path, .panel polyline, .panel circle, .panel text {
  vector-effect: non-scaling-stroke;
}
.panel .axis  { stroke: #46506a; stroke-width: 3; fill: none; }
.panel .barA  { fill: #7ee787; }
.panel .barB  { fill: #5b8bd0; }
.panel .barC  { fill: #febc2e; }
.panel .lbl   { fill: #8fa2c7; font: 700 13px ui-monospace, Menlo, monospace; text-anchor: middle; }
.panel .lbl.hot { fill: #7ee787; }
.panel .tick  { stroke: #7ee787; stroke-width: 4; stroke-linecap: round; fill: none; }
.panel .rowbox { stroke: #46506a; stroke-width: 3; fill: none; }

.stick-head {
  color: #e7ecf7; font-size: var(--stick-h-size); font-weight: 600;
  text-align: center; letter-spacing: -0.01em;
}
.stick-sub {
  color: #8fa2c7; font-size: var(--stick-sub-size); font-weight: 500;
  text-align: center; max-width: 82%; line-height: 1.4;
}

/* ---- always-on idle motion ---- */
@keyframes breathe    { 0%,100% { transform: translateY(0) scaleY(1);} 50% { transform: translateY(-2px) scaleY(1.025);} }
@keyframes row-sway   { 0%,100% { transform: translateX(-6px) rotate(-0.6deg);} 50% { transform: translateX(6px) rotate(0.6deg);} }
@keyframes shadow-pulse { 0%,100% { transform: scaleX(1); opacity:.5;} 50% { transform: scaleX(.82); opacity:.32;} }

/* ---- limb / body animations (all loop, nothing freezes) ----
   Rotation notes: arm-r rest vector points down-right, arm-l down-left.
   Negative rotate() raises arm-r toward "up"; positive raises arm-l. */
@keyframes wave-arm   { 0% { transform: rotate(-82deg);} 50% { transform: rotate(-112deg);} 100% { transform: rotate(-82deg);} }
@keyframes bob        { 0%,100% { transform: translateY(0);} 50% { transform: translateY(-7px);} }
@keyframes bob-fast   { 0%,100% { transform: translateY(0);} 50% { transform: translateY(-5px);} }
@keyframes think-tap  { 0%,100% { transform: rotate(-92deg);} 50% { transform: rotate(-112deg);} }
@keyframes head-tilt  { 0%,100% { transform: rotate(-7deg);} 50% { transform: rotate(6deg);} }
@keyframes head-shake { 0%,100% { transform: rotate(-9deg);} 50% { transform: rotate(9deg);} }
@keyframes head-nod   { 0%,100% { transform: rotate(0deg);} 50% { transform: rotate(11deg);} }
@keyframes jab        { 0%,100% { transform: rotate(-6deg);} 35% { transform: rotate(-52deg);} 70% { transform: rotate(-40deg);} }
@keyframes cheer-l    { 0%,100% { transform: rotate(70deg);} 50% { transform: rotate(98deg);} }
@keyframes cheer-r    { 0%,100% { transform: rotate(-70deg);} 50% { transform: rotate(-98deg);} }
@keyframes hop        { 0%,100% { transform: translateY(0);} 45% { transform: translateY(-30px);} 55% { transform: translateY(-30px);} }
@keyframes shrug-l    { 0%,100% { transform: rotate(30deg);} 50% { transform: rotate(64deg);} }
@keyframes shrug-r    { 0%,100% { transform: rotate(-30deg);} 50% { transform: rotate(-64deg);} }
@keyframes work-l     { 0%,100% { transform: rotate(30deg);} 50% { transform: rotate(62deg);} }
@keyframes work-r     { 0%,100% { transform: rotate(-30deg);} 50% { transform: rotate(-62deg);} }
@keyframes step-f     { 0%,100% { transform: rotate(24deg);} 50% { transform: rotate(-24deg);} }
@keyframes step-b     { 0%,100% { transform: rotate(-24deg);} 50% { transform: rotate(24deg);} }
@keyframes gesture-l  { 0%,100% { transform: rotate(22deg);} 50% { transform: rotate(-26deg);} }
@keyframes gesture-r  { 0%,100% { transform: rotate(-22deg);} 50% { transform: rotate(26deg);} }
@keyframes sweep-arm  { 0% { transform: rotate(-14deg);} 50% { transform: rotate(-44deg);} 100% { transform: rotate(-14deg);} }
@keyframes lean-back  { 0%,100% { transform: rotate(0deg);} 50% { transform: rotate(-9deg);} }
@keyframes push-arm   { 0%,100% { transform: rotate(-34deg);} 50% { transform: rotate(-56deg);} }
@keyframes reach-in   { 0%,100% { transform: rotate(-28deg);} 50% { transform: rotate(-42deg);} }
@keyframes raise-hold { 0%,100% { transform: rotate(-72deg);} 50% { transform: rotate(-86deg);} }
@keyframes climb-l    { 0%,100% { transform: rotate(-8deg);} 50% { transform: rotate(-44deg);} }
@keyframes climb-r    { 0%,100% { transform: rotate(-44deg);} 50% { transform: rotate(-8deg);} }
@keyframes climb-legf { 0%,100% { transform: rotate(28deg);} 50% { transform: rotate(-6deg);} }
@keyframes climb-legb { 0%,100% { transform: rotate(-6deg);} 50% { transform: rotate(28deg);} }
@keyframes climb-body { 0%,100% { transform: translateY(3px);} 50% { transform: translateY(-9px);} }

/* ---- prop animations ---- */
@keyframes float-y    { 0%,100% { transform: translateY(0);} 50% { transform: translateY(-7px);} }
@keyframes pulse      { 0%,100% { opacity:.4;} 50% { opacity:1;} }
@keyframes pop-in     { 0% { opacity:0; transform: scale(.4);} 60% { opacity:1; transform: scale(1.12);} 100% { transform: scale(1);} }
@keyframes spin       { to { transform: rotate(360deg);} }
@keyframes fadeUp     { from { opacity:0; transform: translateY(12px);} to { opacity:1; transform: translateY(0);} }
@keyframes fade-cycle { 0%,40% { opacity:0;} 50%,90% { opacity:1;} 100% { opacity:0;} }
@keyframes bar-grow   { 0% { transform: scaleY(.15);} 70% { transform: scaleY(1);} 100% { transform: scaleY(1);} }
@keyframes seesaw     { 0%,100% { transform: rotate(-9deg);} 50% { transform: rotate(9deg);} }
@keyframes tick-in    { 0%,55% { stroke-dashoffset: 26;} 75%,100% { stroke-dashoffset: 0;} }
@keyframes glow       { 0%,100% { opacity:.5;} 50% { opacity:1;} }
@keyframes marker-hop { 0%,100% { transform: translateY(0);} 40% { transform: translateY(-9px);} }
@keyframes magnify    { 0%,100% { transform: rotate(-40deg) translateX(-3px);} 50% { transform: rotate(-14deg) translateX(3px);} }
@keyframes pen-write  { 0%,100% { transform: rotate(6deg);} 25% { transform: rotate(16deg);} 75% { transform: rotate(-2deg);} }

.anim-idle .arm-l { transform: rotate(14deg); }
.anim-idle .arm-r { transform: rotate(-14deg); }

.anim-wave .arm-r  { animation: wave-arm .8s ease-in-out infinite; }
.anim-wave .head   { animation: head-tilt 1.6s ease-in-out infinite; }
.anim-wave         { animation: bob 1.5s ease-in-out infinite; }

.anim-think .arm-r { animation: think-tap 1.3s ease-in-out infinite; }
.anim-think .arm-l { transform: rotate(24deg); }
.anim-think .head  { animation: head-tilt 2.4s ease-in-out infinite; }

.anim-point .arm-r { animation: jab 1.05s cubic-bezier(.3,1.4,.5,1) infinite; }
.anim-point .arm-l { transform: rotate(16deg); }
.anim-point .head  { animation: head-nod 1.05s ease-in-out infinite; }

.anim-cheer .arm-l { animation: cheer-l .5s ease-in-out infinite; }
.anim-cheer .arm-r { animation: cheer-r .5s ease-in-out infinite; }
.anim-cheer        { animation: hop .8s ease-in-out infinite; }

.anim-shrug .arm-l { animation: shrug-l 1.5s ease-in-out infinite; }
.anim-shrug .arm-r { animation: shrug-r 1.5s ease-in-out infinite; }
.anim-shrug .head  { animation: head-shake 3s ease-in-out infinite; }

.anim-work .arm-l  { animation: work-l .4s ease-in-out infinite; }
.anim-work .arm-r  { animation: work-r .4s ease-in-out infinite; }
.anim-work         { animation: bob-fast .8s ease-in-out infinite; }

.anim-walk .leg-l  { animation: step-f .58s ease-in-out infinite; }
.anim-walk .leg-r  { animation: step-b .58s ease-in-out infinite; }
.anim-walk .arm-l  { animation: step-b .58s ease-in-out infinite; }
.anim-walk .arm-r  { animation: step-f .58s ease-in-out infinite; }

.anim-talk .arm-l  { animation: gesture-l 1.15s ease-in-out infinite; }
.anim-talk .arm-r  { animation: gesture-r 1.35s ease-in-out infinite; }
.anim-talk .head   { animation: head-nod 1.15s ease-in-out infinite; }

.anim-present .arm-r { animation: sweep-arm 2.1s ease-in-out infinite; }
.anim-present .arm-l { transform: rotate(20deg); }
.anim-present .head  { animation: head-tilt 3s ease-in-out infinite; }

.anim-push .arm-r  { animation: push-arm .7s ease-in-out infinite; }
.anim-push .arm-l  { transform: rotate(26deg); }
.anim-push         { animation: bob-fast 1.4s ease-in-out infinite; }

.anim-recoil       { animation: lean-back 1.4s ease-in-out infinite; }
.anim-recoil .arm-l{ transform: rotate(40deg); }
.anim-recoil .arm-r{ transform: rotate(-40deg); }
.anim-recoil .head { animation: head-shake 1.4s ease-in-out infinite; }

.anim-shake .arm-r { animation: reach-in .9s ease-in-out infinite; }
.anim-shake .arm-l { transform: rotate(18deg); }
.anim-shake .head  { animation: head-nod 1.8s ease-in-out infinite; }
.anim-shake        { animation: bob-fast 1.8s ease-in-out infinite; }

.anim-idea .arm-r  { animation: raise-hold 1.6s ease-in-out infinite; }
.anim-idea .arm-l  { transform: rotate(22deg); }
.anim-idea .head   { animation: head-tilt 2.2s ease-in-out infinite; }

.anim-hold .arm-l  { transform: rotate(64deg); }
.anim-hold .arm-r  { transform: rotate(-64deg); }
.anim-hold .head   { animation: head-tilt 2.6s ease-in-out infinite; }

.anim-climb .arm-l { animation: climb-l .66s ease-in-out infinite; }
.anim-climb .arm-r { animation: climb-r .66s ease-in-out infinite; }
.anim-climb .leg-l { animation: climb-legf .66s ease-in-out infinite; }
.anim-climb .leg-r { animation: climb-legb .66s ease-in-out infinite; }
.anim-climb        { animation: climb-body .66s ease-in-out infinite; }

.anim-search .arm-r { animation: magnify 1.9s ease-in-out infinite; }
.anim-search .arm-l { transform: rotate(20deg); }
.anim-search .head  { animation: head-tilt 1.9s ease-in-out infinite; }

.anim-write .arm-r { animation: pen-write 1.1s ease-in-out infinite; }
.anim-write .arm-l { transform: rotate(28deg); }
.anim-write .head  { animation: head-nod 2.2s ease-in-out infinite; }

/* props attached inside a figure svg */
.bubble { fill: rgba(18,21,28,0.9); stroke: #6b7a99; stroke-width: 3;
          animation: float-y 2.2s ease-in-out infinite; }
.bubble-txt { fill: #e7ecf7; stroke: none; font-size: 26px; font-weight: 700;
              font-family: ui-monospace, Menlo, monospace; text-anchor: middle;
              animation: float-y 2.2s ease-in-out infinite; }
.bubble-alt { animation-delay: 1.1s; }
.zzz { fill: #febc2e; stroke: none; font-size: 20px; font-weight: 700;
       font-family: ui-monospace, Menlo, monospace; text-anchor: middle;
       animation: pulse 1.4s ease-in-out infinite; }
.spinner { stroke: #febc2e; stroke-width: 4; stroke-dasharray: 14 10;
           transform-origin: 0px -78px; animation: spin 1.1s linear infinite; }
.box { stroke: #7ee787; stroke-width: 4; fill: none; animation: float-y 2s ease-in-out infinite; }
.bulb { stroke: #febc2e; stroke-width: 4; fill: rgba(254,188,46,0.16);
        transform-origin: 24px -66px; animation: pop-in .7s ease-out both, glow 1.3s ease-in-out .7s infinite; }
.bulb-ray { stroke: #febc2e; stroke-width: 3; animation: glow 1.3s ease-in-out infinite; }
.mag { stroke: #8fa2c7; stroke-width: 4; fill: rgba(143,162,199,0.12); }
.gil-bar {
  color: #ff6b6b; font-size: var(--label-size); letter-spacing:.08em;
  font-family: ui-monospace, Menlo, monospace;
  border: 2px dashed #ff6b6b; border-radius: 10px;
  padding: 8px 18px; opacity: .9;
}
.fade-up { animation: fadeUp .5s ease-out both; }
/* wrapper flip so a second figure can face the first (interaction scenes) */
.fig-mirror { display: flex; transform: scaleX(-1); }
"""

# props: extra SVG appended inside a figure's <g class="body">
_PROPS = {
    "question": '<g><ellipse class="bubble" cx="30" cy="-64" rx="19" ry="15"/>'
                '<text class="bubble-txt" x="30" y="-56">?</text></g>',
    "bang": '<g><ellipse class="bubble" cx="30" cy="-64" rx="19" ry="15"/>'
            '<text class="bubble-txt" x="30" y="-56">!</text></g>',
    "zzz": '<text class="zzz" x="28" y="-62">z z z</text>',
    "spinner": '<path class="spinner" d="M -13 -78 A 13 13 0 1 1 13 -78 A 13 13 0 1 1 -13 -78"/>',
    "box": '<rect class="box" x="18" y="-14" width="26" height="22" rx="4"/>',
    "bulb": ('<g><path class="bulb" d="M 24 -78 a 13 13 0 0 1 0 24 l 0 4 -0 0 l 0 -4 a 13 13 0 0 1 0 -24 z"/>'
             '<line class="bulb-ray" x1="24" y1="-88" x2="24" y2="-94"/>'
             '<line class="bulb-ray" x1="10" y1="-80" x2="5" y2="-84"/>'
             '<line class="bulb-ray" x1="38" y1="-80" x2="43" y2="-84"/></g>'),
    "mag": '<g><circle class="mag" cx="30" cy="-6" r="11"/><line class="mag" x1="38" y1="2" x2="48" y2="12"/></g>',
    "doc": ('<g><rect class="box" x="16" y="-18" width="26" height="30" rx="3"/>'
            '<line x1="21" y1="-10" x2="37" y2="-10"/><line x1="21" y1="-2" x2="37" y2="-2"/>'
            '<line x1="21" y1="6" x2="31" y2="6"/></g>'),
}


def _figure(anim: str, prop: str = "", extra_class: str = "", style: str = "",
            mirror: bool = False) -> str:
    cls = f"anim-{anim} {extra_class}".strip()
    svg = FIGURE_SVG.format(
        extra_class=cls,
        props=_PROPS.get(prop, ""),
        style=style,
    )
    return f'<div class="fig-mirror">{svg}</div>' if mirror else svg


def _slot(anim: str, label: str = "", prop: str = "", extra_class: str = "",
          label_class: str = "", delay_ms: int = 0, mirror: bool = False) -> str:
    style = f"animation-delay:{delay_ms}ms" if delay_ms else ""
    lbl = f'<div class="fig-label {label_class}">{label}</div>' if label else ""
    return f'<div class="fig-slot">{_figure(anim, prop, extra_class, style, mirror)}{lbl}</div>'


# ---- prop panels: standalone inline-SVGs that sit next to a figure ----

def _panel_bars():
    bars = ""
    heights = [34, 58, 46, 72]
    for i, h in enumerate(heights):
        x = 14 + i * 26
        bars += (f'<rect class="barA" x="{x}" y="{96 - h}" width="16" height="{h}" '
                 f'style="transform-origin:{x}px 96px; animation: bar-grow 2.4s ease-out {i*0.18:.2f}s infinite alternate;"/>')
    return (f'<svg class="panel" viewBox="0 0 130 110">'
            f'<polyline class="axis" points="8,8 8,96 124,96"/>{bars}</svg>')


def _panel_seesaw():
    return ('<svg class="panel" viewBox="0 0 140 110">'
            '<line class="axis" x1="70" y1="60" x2="70" y2="96"/>'
            '<g style="transform-origin:70px 60px; animation: seesaw 2.6s ease-in-out infinite;">'
            '<line class="axis" x1="18" y1="60" x2="122" y2="60"/>'
            '<rect class="barB" x="22" y="40" width="26" height="20" rx="3"/>'
            '<rect class="barC" x="92" y="40" width="26" height="20" rx="3"/>'
            '<text class="lbl" x="35" y="34">A</text><text class="lbl" x="105" y="34">B</text>'
            '</g></svg>')


def _panel_stack():
    rows = ""
    for i in range(3):
        y = 20 + i * 26
        hot = " hot" if i == 0 else ""
        glow = ' style="animation: glow 1.4s ease-in-out infinite;"' if i == 0 else ""
        rows += (f'<rect class="rowbox" x="16" y="{y}" width="86" height="20" rx="3"{glow}/>'
                 f'<text class="lbl{hot}" x="59" y="{y + 14}">{i + 1}</text>')
    return f'<svg class="panel" viewBox="0 0 118 110">{rows}</svg>'


def _panel_roadmap():
    posts = ""
    for i, name in enumerate(("NOW", "NEXT", "LATER")):
        x = 18 + i * 40
        hop = ' style="animation: marker-hop 1.3s ease-in-out infinite;"' if i == 0 else ""
        col = "#7ee787" if i == 0 else "#46506a"
        posts += (f'<line x1="{x}" y1="40" x2="{x}" y2="88" style="stroke:{col};"/>'
                  f'<circle cx="{x}" cy="36" r="5" style="stroke:{col}; fill:{col};"{hop}/>'
                  f'<text class="lbl" x="{x}" y="102" style="font-size:11px;">{name}</text>')
    return (f'<svg class="panel" viewBox="0 0 118 110">'
            f'<line class="axis" x1="8" y1="88" x2="112" y2="88"/>{posts}</svg>')


def _panel_checklist():
    rows = ""
    for i in range(3):
        y = 18 + i * 28
        rows += (f'<rect class="rowbox" x="30" y="{y}" width="12" height="12" rx="2"/>'
                 f'<path class="tick" d="M 31 {y + 6} l 4 5 l 8 -11" stroke-dasharray="26" '
                 f'style="animation: tick-in 3s ease-in-out {i*0.5:.1f}s infinite;"/>'
                 f'<line x1="50" y1="{y + 6}" x2="104" y2="{y + 6}" style="stroke:#46506a;"/>')
    return f'<svg class="panel" viewBox="0 0 118 104">{rows}</svg>'


def _panel_stairs():
    steps = ""
    for i in range(4):
        x = 8 + i * 26
        y = 92 - i * 20
        steps += f'<rect class="rowbox" x="{x}" y="{y}" width="26" height="{92 - y}" style="stroke:#46506a;"/>'
    return (f'<svg class="panel" viewBox="0 0 120 104">{steps}'
            f'<path class="tick" d="M 96 26 l 10 -10 l 10 10 M 106 16 l 0 26"/></svg>')


_PANELS = {
    "bars": _panel_bars,
    "seesaw": _panel_seesaw,
    "stack": _panel_stack,
    "roadmap": _panel_roadmap,
    "checklist": _panel_checklist,
    "stairs": _panel_stairs,
}


def _panel(name: str) -> str:
    fn = _PANELS.get(name)
    return f'<div class="fig-slot">{fn()}</div>' if fn else ""


# ---- scene catalog ----

def build_scene(scene: str, heading: str, subheading: str, figures: list | None = None) -> str:
    """Returns the inner HTML for a stick-figure beat."""
    head_html = f'<div class="stick-head fade-up">{heading}</div>' if heading else ""
    sub_html = f'<div class="stick-sub fade-up">{subheading}</div>' if subheading else ""

    if scene == "custom" and figures:
        slots = "".join(
            _slot(f.get("anim", "idle"), f.get("label", ""), f.get("prop", ""),
                  f.get("extra_class", ""), f.get("label_class", ""), i * 120)
            for i, f in enumerate(figures)
        )
        row = f'<div class="fig-row">{slots}</div>'

    # ---- single expressive figure ----
    elif scene == "wave":
        row = f'<div class="fig-row">{_slot("wave")}</div>'
    elif scene == "think":
        row = f'<div class="fig-row">{_slot("think", prop="question")}</div>'
    elif scene == "point":
        row = f'<div class="fig-row">{_slot("point", prop="bang", extra_class="accent")}</div>'
    elif scene == "celebrate":
        row = f'<div class="fig-row">{_slot("cheer", extra_class="accent")}</div>'
    elif scene == "confused":
        row = f'<div class="fig-row">{_slot("shrug", prop="question", extra_class="warn")}</div>'
    elif scene == "idea":
        row = f'<div class="fig-row">{_slot("idea", prop="bulb", extra_class="accent")}</div>'
    elif scene == "search":
        row = f'<div class="fig-row">{_slot("search", prop="mag")}</div>'
    elif scene == "write":
        row = f'<div class="fig-row">{_slot("write", prop="doc")}</div>'

    # ---- figure + prop panel ----
    elif scene == "present":
        row = f'<div class="fig-row">{_slot("present")}{_panel("bars")}</div>'
    elif scene == "measure":
        row = f'<div class="fig-row">{_slot("present", extra_class="accent")}{_panel("bars")}</div>'
    elif scene == "balance":
        row = f'<div class="fig-row">{_slot("hold")}{_panel("seesaw")}</div>'
    elif scene == "prioritize":
        row = f'<div class="fig-row">{_slot("point", extra_class="accent")}{_panel("stack")}</div>'
    elif scene == "roadmap":
        row = f'<div class="fig-row">{_slot("walk")}{_panel("roadmap")}</div>'
    elif scene == "checklist":
        row = f'<div class="fig-row">{_slot("write", extra_class="accent")}{_panel("checklist")}</div>'
    elif scene == "climb":
        row = f'<div class="fig-row">{_slot("climb", extra_class="accent")}{_panel("stairs")}</div>'

    # ---- two-figure interaction (2nd figure mirrored so they face each other) ----
    elif scene == "discuss":
        row = ('<div class="fig-row pair">'
               + _slot("talk", prop="question")
               + _slot("talk", prop="bang", delay_ms=140, mirror=True)
               + '</div>')
    elif scene == "pushback":
        row = ('<div class="fig-row pair">'
               + _slot("push", extra_class="warn")
               + _slot("recoil", prop="bang", delay_ms=90, mirror=True)
               + '</div>')
    elif scene == "handshake":
        row = ('<div class="fig-row pair">'
               + _slot("shake", extra_class="accent")
               + _slot("shake", extra_class="accent", delay_ms=120, mirror=True)
               + '</div>')
    elif scene == "handoff":
        row = ('<div class="fig-row pair">'
               + _slot("point", "returns", extra_class="accent", label_class="done")
               + _slot("idle", "receives", prop="box", delay_ms=200, mirror=True)
               + '</div>')

    # ---- multi-figure concurrency (code topics) ----
    elif scene == "sequential":
        row = ('<div class="fig-row crowd">'
               + _slot("work", "running", extra_class="accent", label_class="done")
               + _slot("idle", "waiting", prop="zzz", extra_class="warn", label_class="wait", delay_ms=120)
               + _slot("idle", "waiting", prop="zzz", extra_class="warn", label_class="wait", delay_ms=240)
               + _slot("idle", "waiting", prop="zzz", extra_class="warn", label_class="wait", delay_ms=360)
               + '</div>')
    elif scene == "parallel":
        row = ('<div class="fig-row crowd">'
               + "".join(
                   _slot("work", f"core {i+1}", extra_class="accent", label_class="done", delay_ms=i * 110)
                   for i in range(4))
               + '</div>')
    elif scene == "blocked":
        row = ('<div class="fig-row crowd">'
               + "".join(
                   _slot("idle", "waiting on I/O", prop="spinner", extra_class="warn",
                         label_class="wait", delay_ms=i * 130)
                   for i in range(3))
               + '</div>')
    elif scene == "gil":
        row = ('<div class="fig-row crowd">'
               + _slot("work", "holds the GIL", extra_class="accent", label_class="done")
               + _slot("idle", "blocked", prop="zzz", extra_class="warn", label_class="wait", delay_ms=120)
               + _slot("idle", "blocked", prop="zzz", extra_class="warn", label_class="wait", delay_ms=240)
               + '</div>'
               + '<div class="gil-bar fade-up">ONE LOCK &mdash; ONE RUNNER AT A TIME</div>')

    else:  # "idle" fallback
        row = f'<div class="fig-row">{_slot("idle")}</div>'

    return f'<div class="stage-stick">{head_html}{row}{sub_html}</div>'


def stick_css() -> str:
    return _CSS


# Scene catalog exported for the writer agents / schema doc to reference.
SCENES = [
    "wave", "think", "point", "celebrate", "confused", "idea", "search", "write",
    "present", "measure", "balance", "prioritize", "roadmap", "checklist", "climb",
    "discuss", "pushback", "handshake", "handoff",
    "sequential", "parallel", "blocked", "gil",
    "custom", "idle",
]
