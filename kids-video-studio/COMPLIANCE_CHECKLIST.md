# YouTube Kids-Content Compliance Checklist

Every script `kids-animation-writer` produces must be run through this list
before it's marked `ready`. This is content-level compliance the agent can
actually control through writing choices. It is **not** a substitute for the
account-level steps a human has to do in YouTube Studio (see "Not the
agent's to set" at the bottom).

## 1. Subject matter & tone

- [ ] Story is clearly aimed at young children (target age stated in the
      script, e.g. 3-7) — no themes, jokes, or references only an adult
      would get.
- [ ] No violence beyond mild, cartoonish, consequence-free slapstick. No
      weapons depicted realistically. No graphic peril.
- [ ] No content that could scare or disturb a young child (no horror
      imagery, no realistic threat to a character's safety played for
      tension).
- [ ] No sexual content, no romance beyond simple friendship/family
      affection.
- [ ] No depiction of alcohol, drugs, smoking, gambling, or dangerous
      "challenge"-style behavior a child could imitate.
- [ ] No hate speech, bullying played as funny/acceptable, or stereotypes —
      including in the Telugu track (check culturally, not just literally).
- [ ] Story has a clear, positive takeaway (kindness, honesty, sharing,
      safety, curiosity, etc.) stated explicitly in the script's
      `moral_or_theme` field.

## 2. No off-platform pulls, no data collection

- [ ] No verbal or on-screen call-to-action urging the child to leave
      YouTube (no "go to our website," no app download prompts, no QR
      codes, no phone numbers or addresses).
- [ ] No prompts asking a child to comment, share personal info, enter a
      giveaway, or interact with a form/quiz that collects data. (Comments
      are disabled on Made-for-Kids videos by YouTube automatically, but the
      script must not write dialogue that assumes commenting is possible.)
- [ ] No third-party brand mentions, product placement, or "unboxing"-style
      segments. If a prop resembles a real toy/product, it must be generic
      enough not to read as an ad.
- [ ] Standard subscribe/like/bell language is avoided or kept minimal and
      non-manipulative — no "smash that button," no urgency/pressure
      language directed at a child viewer.

## 3. Originality & rights

- [ ] All characters, character names, and visual designs are original —
      not existing copyrighted/trademarked characters (no reskinned Disney,
      Peppa Pig, etc., even as "inspired by").
- [ ] Any music/sound cues specified are either original, royalty-free, or
      explicitly flagged in the script as "needs a licensed track" — never
      assumed to be free to use.
- [ ] On-screen text/logos don't reproduce a real brand's trademark.

## 4. Bilingual accuracy & accessibility

- [ ] Telugu dialogue is a natural, age-appropriate translation (not a
      literal/machine-style translation) — reviewed for tone, not just
      vocabulary.
- [ ] Both language tracks tell the exact same story and land the exact
      same moral — no content added/dropped between EN and TE versions.
- [ ] Vocabulary in both languages fits the stated target age band (short
      sentences, no complex/abstract words without explanation).
- [ ] Every spoken line has a corresponding caption-ready text field in the
      script (captions must be added at render time in both languages).

## 5. Metadata

- [ ] Title and description (both languages) accurately describe the video
      — no clickbait, no misleading thumbnail concept.
- [ ] Description contains no external links, no email, no calls to action
      off-platform.
- [ ] `made_for_kids: true` is set in the script's metadata block.
- [ ] Tags are genre/topic-accurate, no unrelated trending terms stuffed in
      to game search.

## Not the agent's to set (human/account-level — needs explicit go-ahead)

These happen in YouTube Studio or via the upload API's `selfDeclaredMadeForKids`
flag at publish time, not in the script file, and per CLAUDE.md section 3
they're an externally-visible action that needs your explicit confirmation
before anything gets uploaded or made public:

- Setting the channel or per-video "Made for Kids" designation.
- Confirming ads are contextual-only (not personalized) for the video.
- Verifying comments/live chat/notifications are off for the upload.
- Any channel-level privacy policy / data-collection disclosure.
