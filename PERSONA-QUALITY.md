# Sente Browser page: fixed seven-axis acceptance rubric

## Personas and realistic jobs

1. First-time Mac user: decide if this is useful, identify prerequisites, install,
   and hand a concrete first task to an AI client without terminal guesswork.
2. Developer: understand the trust boundary and native host, inspect the source,
   copy exact paths/commands, and verify a repeatable first operation.
3. Mobile visitor: understand the product and retain the setup URL for a Mac,
   rather than download an unusable package on a phone.

This is an expert simulation of these perspectives, not research with actual users.
Each axis has five fixed checks worth 20 points. Automated acceptance is not a
human preference, usability, or visual-quality score. Unmeasured criteria remain
unverified, never rounded up to 100. Criteria must not be relaxed to improve scores.

| Axis | Five criteria |
|---|---|
| Value | Concrete browser benefit; three realistic requests; extension versus AI client distinction; Mac prerequisites before setup; useful mobile path |
| Visual hierarchy | One h1; clear section headings; no horizontal overflow at 320/390/768/1440; primary action before long content; human review of visual balance |
| Onboarding | Python download link; exact folder-navigation instructions; copyable install command/path; copyable AI handoff; local practice and success state |
| Interaction | Copy succeeds; copy-denied fallback; practice empty-input error; practice reset; keyboard-operable navigation/forms |
| Trust | Named publisher/contact; privacy with cloud-client boundary; truthful store status; release/source/support links; local practice makes no network submissions |
| Language & accessibility | ja/en parity; localized accessible labels; WCAG AA automated checks without serious/critical findings; visible keyboard focus/skip link; manual screen-reader review |
| Performance | No third-party runtime resources; no autoplay/video download before play; core HTML/CSS/JS under 100KB; CLS <=0.1; reproducible mobile Lighthouse performance >=90 |

Run `python3 tools/verify_personas.py` for browser acceptance and
`python3 tools/verify_site.py` for video/legacy checks. Lighthouse and manual checks
are recorded separately with their environment, not inferred from source size.
