# T2S Manual Testing Protocol

This is a checklist for human-executed verification. Automated test runners
cannot execute these tests because they require human judgment about video correctness,
Arabic fluency, and accessibility quality.

## Schedule

Run this protocol:
- Before any milestone demo
- After any major model retraining
- Quarterly during regular operation
- Before final milestone delivery

## Section A — Visual verification (30 minutes)

For each test, observe the video that plays and check:
- Does the video actually load (no broken player icon)?
- Does the sign in the video match the Arabic word?
- Is the video quality acceptable (not pixelated, frame rate smooth)?
- Does the video have audio? (It should NOT — these are visual signs.)

Test inputs:

| Input | Expected sign | Pass? | Notes |
|-------|---------------|-------|-------|
| كرة السلة | Basketball sign (two-handed bouncing motion) | ☐ | |
| البحر الميت | Dead Sea sign (compound: sea + dead) | ☐ | |
| يتعلم | Learn sign (hand to forehead) | ☐ | |
| طبيب أسنان | Dentist sign (tooth + doctor) | ☐ | |
| أنا | First-person pronoun (index finger to chest) | ☐ | |
| يقرأ | Read sign (book + eyes) | ☐ | |
| مدرسة | School sign | ☐ | |
| قط | Cat sign (whiskers gesture) | ☐ | |
| أحمر | Red sign | ☐ | |
| واحد | Number one | ☐ | |

If any sign looks wrong: note the Arabic word, the matched_lemma in the
response, and the video URL. Send to P1 for verification.

## Section B — Arabic fluency review (1 hour)

Recruit a native Arabic speaker (ideally a deaf community member or a sign
language interpreter). Have them try 20 highlighted Arabic words from real
web content (news article, blog, Wikipedia).

For each word, ask:
1. Did the system find the word?
2. Was the matched sign appropriate for the meaning?
3. Did the playback feel smooth?
4. Would they use this system again?

Document responses in `tests/manual/fluency_review_<date>.md`.

## Section C — Accessibility check (45 minutes)

This is a partial accessibility audit. A full WCAG audit requires
specialized tooling and is out of scope for this milestone.

Test these scenarios:

1. **Keyboard-only operation**: Can a user navigate the React app using only
   Tab, Enter, and Arrow keys? No mouse allowed.

2. **Screen reader compatibility**: Open the React app with a screen reader
   (NVDA on Windows, VoiceOver on Mac). Are the input field, button, and
   video player announced correctly?

3. **High contrast mode**: Enable Windows high contrast mode. Is the React
   app still readable?

4. **Reduced motion**: Enable Windows "Reduce motion" setting. Do the
   video transitions respect this preference?

For each, note: pass / fail / partial / not tested.

## Section D — Deaf community feedback session

This is the most important section. Schedule a 30-minute call with at least
one member of the Jordanian deaf community. Walk them through the system
live. Ask:

1. What words do you wish the system knew that it doesn't?
2. What signs in the videos look wrong or unnatural?
3. Is the playback speed comfortable?
4. Would you use this in your daily life? Why or why not?
5. What would make you more likely to use it?

Document all feedback verbatim in `tests/manual/community_feedback_<date>.md`.
This document is archived for QA review.

## Section E — Demo run-through

Before the major milestone demo, run a full dress rehearsal:

1. Start Django server. Wait for "All inference models warmed and ready."
2. Open the React app in Chrome.
3. Walk through every sentence in `data/demo_sentences.json`.
4. Time the latency on each one (use Chrome DevTools Network tab).
5. Note any sentence where:
   - Latency exceeds 3 seconds
   - The wrong sign appears
   - The video fails to load
   - The system returns an unexpected match_type

If any issue surfaces, fix before the live demo. Re-run the full dress
rehearsal after any fix.

## Recording results

After running each section, fill in `tests/manual/results_<date>.md`:

```markdown
# T2S Manual Test Results

Date: YYYY-MM-DD
Tester: <name>
System version: <git commit hash>

## Section A — Visual verification
Passed: X/10
Failed: Y/10
Notes: ...

## Section B — Arabic fluency review
[paste review notes]

## Section C — Accessibility
Keyboard: pass/fail
Screen reader: pass/fail
High contrast: pass/fail
Reduced motion: pass/fail

## Section D — Community feedback
[paste verbatim feedback]

## Section E — Demo dress rehearsal
All sentences passed: yes/no
Issues found: [list]
```
