#!/usr/bin/env python3
"""Deterministically shuffles each question's options in questions.json.

Authored questions tend to put the correct answer first, which lets a learner
game the quiz by always picking option A. This redistributes answer positions
using a per-question seed derived from the question text, so the shuffle is
stable across runs (re-running never churns the file) but unpredictable to a
user.

    python3 mobile-app/tool/shuffle_answers.py
"""
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

QUESTIONS_FILE = Path(__file__).resolve().parent / "questions.json"


def shuffle_question(q: dict) -> dict:
    correct = q["options"][q["answerIndex"]]
    seed = int(hashlib.sha256(q["question"].encode()).hexdigest()[:8], 16)
    # Sort first so the shuffle input is independent of the current order --
    # otherwise re-running would reshuffle an already-shuffled list and churn
    # the file on every invocation.
    options = sorted(q["options"])
    random.Random(seed).shuffle(options)
    return {**q, "options": options, "answerIndex": options.index(correct)}


def main():
    data = json.loads(QUESTIONS_FILE.read_text())
    before = Counter(q["answerIndex"] for qs in data.values() for q in qs)

    shuffled = {vid: [shuffle_question(q) for q in qs] for vid, qs in data.items()}

    after = Counter(q["answerIndex"] for qs in shuffled.values() for q in qs)
    QUESTIONS_FILE.write_text(json.dumps(shuffled, indent=2))
    print(f"answerIndex before: {dict(sorted(before.items()))}")
    print(f"answerIndex after:  {dict(sorted(after.items()))}")


if __name__ == "__main__":
    main()
