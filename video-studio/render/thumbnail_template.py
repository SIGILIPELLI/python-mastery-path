"""
Builds a static 1280x720 YouTube thumbnail HTML page, styled to match the
video beats (same dark gradient, card look, Mastery Path brand) rendered
by beat_template.py. Playwright screenshots this -- no animation, one frame.
"""

_LANG_COLORS = {
    "python": ("#3776AB", "#ffffff", "PYTHON"),
    "java": ("#E76F00", "#ffffff", "JAVA"),
    "javascript": ("#F7DF1E", "#12151c", "JAVASCRIPT"),
    "c": ("#5C6BC0", "#ffffff", "C"),
    "bash": ("#4EAA25", "#ffffff", "BASH"),
    "go": ("#00ADD8", "#12151c", "GO"),
    "sql": ("#F29111", "#12151c", "SQL"),
}

_CSS = """
:root { color-scheme: dark; }
* { box-sizing: border-box; }
html, body {
  margin: 0; padding: 0; width: 1280px; height: 720px;
  background: radial-gradient(circle at 28% 22%, #1b2130 0%, #0d0f14 68%);
  font-family: -apple-system, "SF Pro Display", "Segoe UI", Helvetica, Arial, sans-serif;
  overflow: hidden;
}
.brand {
  position: absolute; top: 40px; left: 56px;
  color: #7d8aa3; letter-spacing: 0.14em; font-size: 22px;
  text-transform: uppercase; font-weight: 600;
}
.badge {
  position: absolute; top: 36px; right: 56px;
  padding: 12px 26px; border-radius: 999px;
  font-size: 24px; font-weight: 800; letter-spacing: 0.04em;
  background: BADGE_BG; color: BADGE_FG;
  box-shadow: 0 10px 30px rgba(0,0,0,0.35);
}
.stage {
  position: absolute; left: 0; right: 0; top: 0; bottom: 0;
  display: flex; align-items: center; justify-content: center;
  padding: 170px 90px 120px;
}
.glow {
  position: absolute; width: 620px; height: 620px; border-radius: 50%;
  background: GLOW_COLOR; opacity: 0.16; filter: blur(90px);
  right: -120px; bottom: -160px;
}
h1 {
  margin: 0; color: #f3f6fc; font-size: TITLE_SIZE; font-weight: 800;
  line-height: 1.14; letter-spacing: -0.01em; text-align: center;
  text-shadow: 0 4px 24px rgba(0,0,0,0.55);
  max-width: 1060px;
}
.accent {
  position: absolute; left: 0; bottom: 0; width: 100%; height: 10px;
  background: BADGE_BG;
}
"""


def render_thumbnail_html(title: str, language: str) -> str:
    bg, fg, label = _LANG_COLORS.get(language, ("#6b7a99", "#ffffff", language.upper()))
    # bigger font for short titles, smaller for long ones so 3 lines still fits
    if len(title) <= 40:
        size = "84px"
    elif len(title) <= 60:
        size = "68px"
    else:
        size = "56px"

    css = (
        _CSS.replace("BADGE_BG", bg)
        .replace("BADGE_FG", fg)
        .replace("GLOW_COLOR", bg)
        .replace("TITLE_SIZE", size)
    )

    return f"""<!doctype html>
<html><head><meta charset="utf-8"><style>{css}</style></head>
<body>
  <div class="glow"></div>
  <div class="brand">Mastery Path</div>
  <div class="badge">{label}</div>
  <div class="stage"><h1>{_escape(title)}</h1></div>
  <div class="accent"></div>
</body></html>"""


def _escape(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
