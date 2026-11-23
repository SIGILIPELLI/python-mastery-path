import unittest, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import count_content as cc

def course(**lv): return cc.classify({int(k[1:]): v for k, v in lv.items()})
STD = lambda n=9: [f"{i:02d}-lesson-{i}" for i in range(1, n + 1)]

class Classifier(unittest.TestCase):
    def test_standard_course(self):
        r = course(L1=STD()+["10-project-a"], L2=STD()+["10-project-b"], L3=STD()+["10-project-c"], L4=STD()+["10-capstone"])
        self.assertEqual((r["lessons"], r["projects"], r["capstones"]), (36, 4, 1))
        self.assertEqual(cc.deviations(r), [])

    def test_lesson_named_project_is_still_a_lesson(self):
        # regression: 'project' inside a lesson slug must not make it a project
        pages = ["01-intro", "02-project-setup", "03-cli-project-structure"] + STD(6)[3:] + ["10-project-x"]
        r = course(L1=pages)
        self.assertEqual(r["projects"], 1)
        self.assertIn("level-1/02-project-setup", r["lesson_ids"])

    def test_capstone_counted_once_and_not_a_lesson(self):
        r = course(L1=STD()+["10-project-a"], L4=STD()+["10-capstone-x"])
        self.assertEqual((r["projects"], r["capstones"]), (2, 1))
        self.assertNotIn("level-4/10-capstone-x", r["lesson_ids"])

    def test_missing_project_flagged(self):
        r = course(L1=STD()+["10-more-lessons"])
        self.assertTrue(any("not a project" in i for i in r["issues"]))

    def test_ten_lesson_level_flagged(self):
        r = course(L1=STD(10)+["11-project-a"], L2=STD()+["10-project-b"], L3=STD()+["10-project-c"], L4=STD()+["10-capstone"])
        self.assertEqual(r["lessons"], 37)
        self.assertTrue(any("level-1 has 10" in d for d in cc.deviations(r)))

class RepoCourses(unittest.TestCase):
    root = Path(__file__).resolve().parents[1]
    def test_mcp_and_vector_are_36_plus_4(self):
        for d in ("mcp-mastery-path", "vector-databases-mastery-path"):
            r = cc.from_local(self.root / d / "docs")
            self.assertEqual((r["lessons"], r["projects"]), (36, 4), d)
    def test_python_is_36_plus_4(self):
        r = cc.from_local(self.root / "docs")
        self.assertEqual((r["lessons"], r["projects"]), (36, 4))
        idx = (self.root / "docs/index.md").read_text()
        self.assertIn("36 hands-on lessons", idx)
        self.assertNotIn("40 hands-on lessons", idx)

if __name__ == "__main__":
    unittest.main()
