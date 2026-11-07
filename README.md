# The Man on Somerton Beach — a code-drawn documentary

A 15½-minute cinematic investigative documentary about Australia's most famous unidentified-man
case — the Somerton Man (Tamám Shud) — produced **entirely in code**: every frame is drawn by a
deterministic SVG/halftone page rendered headless frame-by-frame, the score and foley are
synthesized in numpy, and the narration is offline TTS verified by speech-to-text.
No video generation, no stock footage, no archival photographs — every "photograph" is a labelled
in-frame reconstruction.

**▶ Watch:** download `somerton-man.mp4` from the [Releases](../../releases) page.

| Deliverable | File |
|---|---|
| The film (1080p, 24 fps, ~15:30) | `somerton-man.mp4` (Release asset) |
| Subtitles | `film/somerton-man.srt` |
| YouTube thumbnail (1280×720) | `film/somerton-man-thumb.jpg` |
| YouTube title / description / chapters | `film/YOUTUBE.md` |
| Verified fact sheet (every claim sourced) | `film/FACTS.md` |
| Source list | `film/SOURCES.md` |
| Third-party assets & licences | `film/CREDITS` |
| Directing treatment | `film/TREATMENT.md` |
| Narration script (1,967 words) | `film/lines.json` |
| Locked timeline & caption cues | `film/timeline.json`, `film/cues.json` |

## Structure (chapter markers are in the YouTube description)

1. Cold Open — the discovery at dawn (0:00)
2. Exhibit 01 — The Man Without an Identity (1:02)
3. Exhibit 02 — Tamám Shud (3:31)
4. Exhibit 03 — The Book and the Cipher (5:13)
5. Exhibit 04 — The Suitcase (7:38)
6. Exhibit 05 — The Theories (9:36) — every theory stamped SPECULATION
7. Exhibit 06 — The DNA Investigation (11:21) — the 2022 Carl Webb claim, with its caveats
8. Exhibit 07 — What the Evidence Actually Proves (14:04)
9. Close (14:56)

## Editorial rules

- Evidence vs speculation is enforced visually: red SPECULATION stamps, an evidence ledger,
  and a "NOT VERIFIED" caveat beside the 2022 identification.
- No fabricated evidence, quotes, photographs or forensic conclusions. Quotes appear only where
  documented (Dwyer, Leane, the 1949 editorial, the grave marker).
- The film ends honestly: the strongest evidence, the contradictions, the open questions.

## Build

Requires Node 20+, ffmpeg, Python 3.11+ (or uv). The film lives inside the
[lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar) library clone (style: Halftone Dossier):

```sh
git clone https://github.com/lemomo-ai/lemo-opuscar.git
cp -r film lemo-opuscar/films/somerton-man
cd lemo-opuscar
sh plugin/skills/lemo-opuscar/scripts/setup.sh deps voice
./films/somerton-man/build.sh     # render → mix → mux → subtitles
```

`build.sh` renders the 24 fps timeline in segments (the render tool joins them losslessly),
synthesizes score + foley + voice into one mix, and masters to −14 LUFS.

## Pipeline

```
timeline.json (single source of truth)
   ├─ picture:  index.html  (render(t) — deterministic, 24 fps)  ─ headless Chrome ─ segments ─ concat
   ├─ voice:    Kokoro bm_george @0.92 ─ faster-whisper check (0 mismatches) ─ word timings
   ├─ music:    numpy score (drone / heartbeat / marimba motif / music-box / pizz) + foley from EV
   └─ subtitles: caption bars burned in + somerton-man.srt
mix: ducking + silence windows ─ two-pass loudnorm −14 LUFS ─ somerton-man.mp4
```

---

## Project status

**Completed project** — verified in the portfolio audit of **7 November 2026** (README, codebase and project state reviewed).

_Last verified: 7 November 2026_
