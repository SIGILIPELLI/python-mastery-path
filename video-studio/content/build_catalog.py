#!/usr/bin/env python3
"""
Scans every local Mastery Path repo's docs/*.md, and builds a single JSON
catalog mapping each lesson to its live URL and structured content
(sections, prose, code blocks). This catalog is the only thing the
yt-shorts-writer / yt-longform-producer subagents read to pick topics and
cite source links -- keeps them from having to re-walk the filesystem.

Usage:
    .venv/bin/python content/build_catalog.py
Writes:
    content/catalog.json
"""
import json
import re
from pathlib import Path

DESKTOP = Path.home() / "Desktop"
REPO_GLOB = "*-mastery-path"
THIS_REPO = Path(__file__).resolve().parents[2]  # vremployee == python-mastery-path

H1_RE = re.compile(r"^#\s+(.*)$", re.MULTILINE)
H2_RE = re.compile(r"^##\s+(.*)$")
CODE_FENCE_RE = re.compile(r"^```(\w*)\s*$")


def find_repos():
    repos = {THIS_REPO}
    if DESKTOP.is_dir():
        repos.update(p for p in DESKTOP.glob(REPO_GLOB) if p.is_dir())
    return sorted(repos)


def mkdocs_field(repo: Path, key: str) -> str | None:
    mkdocs_yml = repo / "mkdocs.yml"
    if not mkdocs_yml.is_file():
        return None
    for line in mkdocs_yml.read_text().splitlines():
        if line.strip().startswith(f"{key}:"):
            return line.split(":", 1)[1].strip().rstrip("/")
    return None


def site_url_for(repo: Path) -> str | None:
    return mkdocs_field(repo, "site_url")


def url_for(site_url: str, rel_path: Path) -> str:
    parts = list(rel_path.with_suffix("").parts)
    if parts[-1] == "index":
        parts = parts[:-1]
    tail = "/".join(parts)
    return f"{site_url}/{tail}/" if tail else f"{site_url}/"


def parse_lesson(text: str):
    lines = text.splitlines()
    title_match = H1_RE.search(text)
    title = title_match.group(1).strip() if title_match else None

    sections = []
    current = None
    in_code = False
    code_lang = ""
    code_lines: list[str] = []

    for line in lines:
        fence = CODE_FENCE_RE.match(line)
        if fence and not in_code:
            in_code = True
            code_lang = fence.group(1) or "text"
            code_lines = []
            continue
        if fence and in_code:
            in_code = False
            if current is not None:
                current["code_blocks"].append(
                    {"lang": code_lang, "code": "\n".join(code_lines)}
                )
            continue
        if in_code:
            code_lines.append(line)
            continue

        h2 = H2_RE.match(line)
        if h2:
            current = {"heading": h2.group(1).strip(), "prose": [], "code_blocks": []}
            sections.append(current)
            continue

        if current is not None and line.strip() and not line.startswith("#"):
            current["prose"].append(line.strip())

    for s in sections:
        s["prose"] = " ".join(s["prose"]).strip()

    return title, sections


def main():
    catalog = []
    for repo in find_repos():
        docs = repo / "docs"
        if not docs.is_dir():
            continue
        site_url = site_url_for(repo)
        if not site_url:
            continue
        repo_name = mkdocs_field(repo, "repo_name") or repo.name
        language = repo_name.replace("-mastery-path", "")

        for md_path in sorted(docs.rglob("*.md")):
            rel = md_path.relative_to(docs)
            if "overrides" in rel.parts:
                continue
            if rel.name == "privacy.md":
                continue
            text = md_path.read_text(encoding="utf-8")
            title, sections = parse_lesson(text)
            if not title:
                continue
            is_index = rel.name == "index.md"
            level = rel.parts[0] if len(rel.parts) > 1 else None
            has_code = any(s["code_blocks"] for s in sections)

            catalog.append({
                "language": language,
                "repo": repo_name,
                "level": level,
                "slug": str(rel.with_suffix("")),
                "title": title,
                "url": url_for(site_url, rel),
                "is_overview": is_index,
                "has_code": has_code,
                "sections": sections,
            })

    out_path = Path(__file__).parent / "catalog.json"
    out_path.write_text(json.dumps(catalog, indent=2))
    langs = sorted({e["language"] for e in catalog})
    print(f"Wrote {len(catalog)} lessons across {len(langs)} languages -> {out_path}")
    print("Languages:", ", ".join(langs))


if __name__ == "__main__":
    main()
