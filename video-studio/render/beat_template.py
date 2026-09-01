"""
Builds a single self-contained HTML page for one video "beat" (title card,
editor typing animation, terminal typing + output, or a plain text card).
Playwright loads this via page.set_content() and records the animation as
video for exactly `duration_ms` milliseconds.
"""
import json

from render.stick_figures import build_scene, stick_css

# Generic, language-agnostic token colorer -- good enough visual highlighting
# across all 12 languages without needing a real grammar per language.
_HIGHLIGHT_JS = r"""
function highlight(code) {
  const keywords = new Set(("if else elif for while def function class return import from as let const var "
    + "public private protected static void int long float double bool boolean string String true false "
    + "null None nil undefined print println echo fn impl match case switch try except catch finally throw "
    + "async await select insert update delete into values where join struct enum interface new this self "
    + "package namespace use mod pub fn end do begin then module require include typedef sizeof").split(" "));
  let out = "";
  let i = 0;
  const n = code.length;
  while (i < n) {
    const c = code[i];
    // line comments: # // --
    if (c === "#" || (c === "/" && code[i+1] === "/") || (c === "-" && code[i+1] === "-")) {
      let j = code.indexOf("\n", i);
      if (j === -1) j = n;
      out += `<span class="cm">${escapeHtml(code.slice(i, j))}</span>`;
      i = j;
      continue;
    }
    // strings
    if (c === '"' || c === "'" || c === "`") {
      let j = i + 1;
      while (j < n && code[j] !== c) {
        if (code[j] === "\\") j++;
        j++;
      }
      j = Math.min(j + 1, n);
      out += `<span class="st">${escapeHtml(code.slice(i, j))}</span>`;
      i = j;
      continue;
    }
    // numbers
    if (/[0-9]/.test(c) && !/[A-Za-z_]/.test(code[i-1] || "")) {
      let j = i;
      while (j < n && /[0-9._]/.test(code[j])) j++;
      out += `<span class="nu">${escapeHtml(code.slice(i, j))}</span>`;
      i = j;
      continue;
    }
    // identifiers / keywords
    if (/[A-Za-z_]/.test(c)) {
      let j = i;
      while (j < n && /[A-Za-z0-9_]/.test(code[j])) j++;
      const word = code.slice(i, j);
      if (keywords.has(word)) {
        out += `<span class="kw">${escapeHtml(word)}</span>`;
      } else {
        out += escapeHtml(word);
      }
      i = j;
      continue;
    }
    out += escapeHtml(c);
    i++;
  }
  return out;
}
function escapeHtml(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
"""

_BASE_CSS = """
:root { color-scheme: dark; }
* { box-sizing: border-box; }
html, body {
  margin: 0; padding: 0; width: 100%; height: 100%;
  background: radial-gradient(circle at 30% 20%, #1b2130 0%, #0d0f14 65%);
  font-family: ui-monospace, "SF Mono", Menlo, Monaco, Consolas, monospace;
  overflow: hidden;
}
.stage {
  width: 100%; height: 100%;
  display: flex; align-items: center; justify-content: center;
  padding: var(--pad);
}
.brand {
  position: absolute; top: 28px; left: 50%; transform: translateX(-50%);
  color: #6b7a99; letter-spacing: 0.12em; font-size: var(--brand-size);
  text-transform: uppercase; opacity: 0.85;
}
.card {
  width: 100%;
  background: #12151c;
  border: 1px solid #262c3a;
  border-radius: 18px;
  box-shadow: 0 30px 80px rgba(0,0,0,0.55);
  overflow: hidden;
}
.titlebar {
  display: flex; align-items: center; gap: 8px;
  padding: 16px 20px; background: #171b24; border-bottom: 1px solid #262c3a;
}
.dot { width: 13px; height: 13px; border-radius: 50%; }
.dot.r { background: #ff5f57; } .dot.y { background: #febc2e; } .dot.g { background: #28c840; }
.filename { margin-left: 14px; color: #7d8aa3; font-size: var(--ui-size); }
.body { padding: var(--body-pad); }
pre.code {
  margin: 0; white-space: pre-wrap; word-break: break-word;
  font-size: var(--code-size); line-height: 1.55; color: #d6deee;
}
.kw { color: #c586c0; } .st { color: #ce9178; } .nu { color: #b5cea8; } .cm { color: #6a9955; font-style: italic; }
.cursor {
  display: inline-block; width: 0.55ch; height: 1.05em; background: #7ee787;
  vertical-align: text-bottom; animation: blink 0.9s steps(1) infinite;
}
@keyframes blink { 50% { opacity: 0; } }
.term { border-top: 1px solid #262c3a; padding: var(--body-pad); background: #0c0e13; }
.term .prompt { color: #7ee787; }
.term pre.output {
  margin: 10px 0 0; color: #9fb3d1; white-space: pre-wrap; font-size: var(--code-size); line-height: 1.5;
}
.textcard { text-align: center; color: #e7ecf7; }
.textcard h1 { font-size: var(--h1-size); margin: 0 0 18px; letter-spacing: -0.01em; }
.textcard h2 { font-size: var(--h2-size); margin: 0; color: #8fa2c7; font-weight: 500; }
.fade-in { animation: fadein 0.5s ease-out both; }
@keyframes fadein { from { opacity: 0; transform: translateY(10px);} to { opacity: 1; transform: translateY(0);} }
.caption {
  position: absolute; left: 50%; transform: translateX(-50%);
  bottom: var(--caption-bottom); width: var(--caption-width);
  text-align: center; color: #f3f6fc; font-weight: 600;
  font-size: var(--caption-size); line-height: 1.4;
  text-shadow: 0 2px 10px rgba(0,0,0,0.65), 0 0 2px rgba(0,0,0,0.8);
}
.caption span.chunk { display: inline-block; transition: opacity 0.15s; }
""" + stick_css()


_EXT_MAP = {
    "python": "py", "javascript": "js", "typescript": "ts", "java": "java",
    "c": "c", "cpp": "cpp", "go": "go", "rust": "rs", "ruby": "rb",
    "php": "php", "sql": "sql", "shell": "sh", "bash": "sh", "text": "txt",
}


def render_beat_html(beat: dict, duration_ms: int, vertical: bool) -> str:
    display = beat.get("display", {})
    kind = display.get("kind", "text")
    narration = beat.get("narration", "").strip()

    if vertical:
        vars_css = ("--pad:64px 48px; --brand-size:15px; --ui-size:16px; --body-pad:40px 34px; "
                     "--code-size:26px; --h1-size:52px; --h2-size:26px; "
                     "--caption-bottom:180px; --caption-width:86%; --caption-size:30px; "
                     "--fig-size:300px; --fig-gap:34px; --stick-gap:56px; --label-size:20px; "
                     "--stick-h-size:50px; --stick-sub-size:28px;")
    else:
        vars_css = ("--pad:70px 90px; --brand-size:16px; --ui-size:15px; --body-pad:34px 42px; "
                     "--code-size:24px; --h1-size:50px; --h2-size:24px; "
                     "--caption-bottom:60px; --caption-width:74%; --caption-size:26px; "
                     "--fig-size:340px; --fig-gap:64px; --stick-gap:44px; --label-size:20px; "
                     "--stick-h-size:48px; --stick-sub-size:26px;")

    lang = display.get("lang", "text")
    code = display.get("code", "")
    output = display.get("output", "")
    heading = display.get("heading", "")
    subheading = display.get("subheading", "")

    show_caption = kind in ("editor", "terminal", "stick") and bool(narration)

    if kind == "stick":
        body = build_scene(
            display.get("scene", "idle"),
            _escape(heading),
            _escape(subheading),
            display.get("figures"),
        )
    elif kind in ("editor", "terminal"):
        body = f"""
        <div class="card fade-in">
          <div class="titlebar">
            <div class="dot r"></div><div class="dot y"></div><div class="dot g"></div>
            <div class="filename">main.{_EXT_MAP.get(lang, lang)}</div>
          </div>
          <div class="body"><pre class="code" id="code"></pre></div>
          {'<div class="term"><span class="prompt">$</span> <span id="runline"></span><pre class="output" id="output" style="opacity:0"></pre></div>' if kind == "terminal" else ''}
        </div>
        """
    else:
        body = f"""
        <div class="textcard fade-in">
          <h1>{_escape(heading)}</h1>
          <h2>{_escape(subheading)}</h2>
        </div>
        """

    caption_div = '<div class="caption" id="caption"><span class="chunk" id="captionText"></span></div>' if show_caption else ""

    payload = json.dumps({
        "kind": kind,
        "code": code,
        "output": output,
        "durationMs": duration_ms,
        "narration": narration,
    })

    return f"""<!doctype html>
<html><head><meta charset="utf-8"><style>{_BASE_CSS} :root {{ {vars_css} }}</style></head>
<body>
  <div class="brand">Mastery Path</div>
  <div class="stage">{body}</div>
  {caption_div}
  <script>{_HIGHLIGHT_JS}</script>
  <script>
    const DATA = {payload};
    window.__done = false;
    function typeInto(el, text, totalMs, cb) {{
      if (!text) {{ cb && cb(); return; }}
      let i = 0;
      const stepMs = Math.max(6, totalMs / text.length);
      const cursor = document.createElement('span');
      cursor.className = 'cursor';
      function tick() {{
        i++;
        el.innerHTML = highlight(text.slice(0, i)) ;
        el.appendChild(cursor);
        if (i < text.length) {{
          setTimeout(tick, stepMs);
        }} else {{
          cursor.remove();
          cb && cb();
        }}
      }}
      tick();
    }}
    (function run() {{
      if (DATA.kind === 'editor') {{
        const el = document.getElementById('code');
        typeInto(el, DATA.code, DATA.durationMs * 0.68);
      }} else if (DATA.kind === 'terminal') {{
        const el = document.getElementById('code');
        const runline = document.getElementById('runline');
        typeInto(el, DATA.code, DATA.durationMs * 0.45, function() {{
          setTimeout(function() {{
            runline.textContent = 'run';
            const out = document.getElementById('output');
            out.textContent = DATA.output;
            out.style.transition = 'opacity 0.4s';
            out.style.opacity = '1';
          }}, 250);
        }});
      }}
      const captionEl = document.getElementById('captionText');
      if (captionEl && DATA.narration) {{
        const words = DATA.narration.split(/\s+/).filter(Boolean);
        const chunkSize = 6;
        const chunks = [];
        for (let i = 0; i < words.length; i += chunkSize) {{
          chunks.push(words.slice(i, i + chunkSize).join(' '));
        }}
        const interval = Math.max(400, DATA.durationMs / chunks.length);
        let ci = 0;
        function showChunk() {{
          captionEl.style.opacity = '0';
          setTimeout(function() {{
            captionEl.textContent = chunks[ci];
            captionEl.style.opacity = '1';
          }}, 90);
          ci++;
          if (ci < chunks.length) setTimeout(showChunk, interval);
        }}
        showChunk();
      }}
    }})();
  </script>
</body></html>"""


def _escape(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
