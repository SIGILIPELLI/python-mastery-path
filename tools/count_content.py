#!/usr/bin/env python3
"""Canonical lesson/project counter for Mastery Path courses (methodology 1.1).

Structural rule (never a substring match on "project"):
  * a course has levels  level-N/  with numbered pages  NN-slug
  * the LAST numbered page of each level is that level's project;
    in level 4 it is the capstone (a project subtype, counted once as a project)
  * every other numbered page is a lesson
  * level index pages, quiz, cheat-sheet, interview pages are none of the above

Usage:
  count_content.py local <docs_dir> [<docs_dir> ...]
  count_content.py live  <slug> [<slug> ...]          # reads the published sitemap
  count_content.py live-all [--out counts]            # every course in the live catalogue
"""
import csv, json, re, sys, urllib.request, concurrent.futures as cf
from pathlib import Path

METHODOLOGY = "1.1"
EXPECTED = {"levels": 4, "lessons": 36, "projects": 4, "capstones": 1}
NUM = re.compile(r"^(\d+)-(.+)$")
PROJ = re.compile(r"^(project|capstone)")


def classify(level_pages):
    """level_pages: {level:int -> [page slug like '10-project-x', ...]} -> course record."""
    lessons, projects, capstones, issues, per = [], [], [], [], {}
    for lv in sorted(level_pages):
        pages = sorted(p for p in level_pages[lv] if NUM.match(p))
        if not pages:
            issues.append(f"level-{lv}: no numbered pages")
            continue
        *ls, last = pages
        name = NUM.match(last).group(2)
        if not PROJ.match(name):
            issues.append(f"level-{lv}: last page '{last}' is not a project/capstone")
        projects.append(f"level-{lv}/{last}")
        if lv == max(level_pages):
            capstones.append(f"level-{lv}/{last}")
        lessons += [f"level-{lv}/{p}" for p in ls]
        per[lv] = len(ls)
    return {
        "levels": len(level_pages), "lessons": len(lessons), "projects": len(projects),
        "capstones": len(capstones), "lessons_per_level": per,
        "lesson_ids": lessons, "project_ids": projects, "capstone_ids": capstones,
        "issues": issues,
    }


def deviations(rec):
    out = list(rec["issues"])
    for k, want in EXPECTED.items():
        if rec[k] != want:
            out.append(f"{k}={rec[k]} (expected {want})")
    for lv, n in rec["lessons_per_level"].items():
        if n != 9:
            out.append(f"level-{lv} has {n} lessons (expected 9)")
    return out


def from_local(docs: Path):
    lv = {}
    for d in docs.glob("level-*"):
        if d.is_dir():
            lv[int(d.name.split("-")[1])] = [p.stem for p in d.glob("*.md") if p.stem != "index"]
    return classify(lv)


def from_urls(urls):
    lv = {}
    for l, rest in re.findall(r"/level-(\d)/([^/]+)/?$", "\n".join(urls), flags=re.M):
        lv.setdefault(int(l), []).append(rest)
    return classify(lv)


def live(slug, base="https://learnmasterypath.com"):
    x = urllib.request.urlopen(f"{base}/{slug}/sitemap.xml", timeout=30).read().decode()
    return from_urls(re.findall(r"<loc>([^<]*)</loc>", x))


def live_catalogue(base="https://learnmasterypath.com"):
    h = urllib.request.urlopen(f"{base}/course-catalogue/", timeout=30).read().decode()
    slugs = re.findall(r'<h2><a href="https://learnmasterypath\.com/([^"/]+)/">', h)
    slugs += re.findall(r'<h2><a href="https://learnmasterypath\.com/([^"]+/[^"/]+)/">', h)  # nested courses
    return sorted(set(slugs))


def main(argv):
    mode = argv[1] if len(argv) > 1 else ""
    recs = {}
    if mode == "local":
        for d in argv[2:]:
            recs[d] = from_local(Path(d))
    elif mode == "live":
        for s in argv[2:]:
            recs[s] = live(s)
    elif mode == "live-all":
        out = Path(argv[argv.index("--out") + 1]) if "--out" in argv else Path("counts")
        slugs = live_catalogue()
        with cf.ThreadPoolExecutor(12) as ex:
            recs = dict(zip(slugs, ex.map(live, slugs)))
        out.mkdir(exist_ok=True)
        (out / "course-counts.json").write_text(json.dumps(
            {"methodology": METHODOLOGY, "courses": recs}, indent=1))
        with open(out / "course-counts.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["course", "levels", "lessons", "projects", "capstones", "deviations"])
            for s, r in recs.items():
                w.writerow([s, r["levels"], r["lessons"], r["projects"], r["capstones"], "; ".join(deviations(r))])
    else:
        print(__doc__); return 2
    bad = 0
    for s, r in recs.items():
        d = deviations(r)
        bad += bool(d)
        print(f"{s}: {r['lessons']} lessons + {r['projects']} projects (capstone {r['capstones']})"
              + (f"  DEVIATES: {'; '.join(d)}" if d else ""))
    print(f"{len(recs)} courses, {bad} deviate")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
