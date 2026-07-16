# Vibe Coding Is Dead — YouTube Video Design

Date: 2026-07-16
Status: approved for autonomous production

## Objective

Create a 3–5 minute, 16:9 YouTube learning video titled **“Vibe Coding Is Dead. Here’s What Replaced It.”** The video should reach the editorial quality of the supplied Coding Sloth reference while remaining recognizably BiosRios: Ohad’s existing illustrated character is the host, and the narration uses the existing approved voice clone.

The result must feel like an entertaining YouTube essay, not a product launch video. It should teach one durable idea, earn its jokes from the subject, use real evidence on screen, and avoid a mid-video product pitch.

## Authoritative Inputs

- Style and pacing reference: `C:/Users/ohad1/OneDrive/שולחן העבודה/Everything You Need To Know About AI Agents - The Coding Sloth (1080p, h264).mp4`
- BiosRios visual and voice reference: `videos/long-claude-code/renders/BiosRios - Everything You Need To Know About Claude Code (1080p).mp4`
- Approved voice prompt: `videos/long-claude-code/assets/vref/clean_calm.wav`
- Existing host poses: `videos/long-claude-code/assets/cast/*.png`
- Existing voice-generation baseline: `videos/long-claude-code/tools/gen_vo_long.py`

The Coding Sloth reference supplies editorial principles only: mixed-media pacing, comedic interruption, rough diagrams, source evidence, and contrast between dense and quiet moments. The production must not reproduce its script, branding, exact layouts, or proprietary assets.

## Editorial Thesis

Vibe coding is useful for getting a first version quickly, but it breaks when a project needs continuity, controlled changes, or proof. The replacement is not “stop using AI.” It is **agentic engineering**: define the outcome, constrain the work, preserve the project’s context, and verify the result.

The viewer should leave with one practical loop:

1. Define the result.
2. Bound the task.
3. Give the agent the right context.
4. Demand evidence before accepting the work.

## Audience and Tone

The primary viewer uses ChatGPT, Claude, Codex, Cursor, or another AI coding tool and can build small projects, but does not need formal software-engineering experience.

The voice is direct, self-aware, slightly chaotic, and useful. Jokes should sound like observations a real user would make after an agent breaks a project. Avoid corporate language, benchmark worship, fearbait, and claims that coding or developers are obsolete.

## Story and Runtime

Target runtime: **4:00–4:30**. Acceptable final range: **3:30–5:00**.

### 0:00–0:20 — Cold open: the celebration and collapse

The BiosRios character asks an agent for an app. A rapid success montage ends in celebration. One tiny follow-up request causes a cascade of rewrites, broken tests, and an absurd error wall.

Hook line direction: “Vibe coding is amazing. Right up until your app becomes old enough to remember yesterday.”

### 0:20–0:55 — What vibe coding actually is

Explain the original idea fairly: describe what you want, accept generated code, and judge mostly by whether the result appears to work. Show the appeal before showing the limit.

### 0:55–1:45 — Why it breaks

Use three escalating failures:

- the agent loses project intent between sessions;
- a local fix silently damages another surface;
- visual success hides security, data, or test failures.

Each failure gets a concrete screen example, one short visual joke, and one plain-language consequence.

### 1:45–2:50 — What replaced it

Introduce agentic engineering as a workflow rather than a new product. The host gives the agent a small spec, a bounded task, durable context, and a verification requirement. A rough hand-drawn system diagram replaces the improvised prompt cloud.

### 2:50–3:35 — Before and after

Run the same small app-change scenario in two modes:

- **Vibes:** one broad request, no constraints, acceptance based on appearance.
- **System:** explicit outcome, named files or surfaces, acceptance checks, and an evidence report.

The demonstration must use real captured outputs. It may be compact, but it cannot imply a result that was not observed.

### 3:35–4:15 — The four-rule takeaway

Recap: define, bound, preserve context, verify. Close on the character discovering that the “boring” checklist is what lets the fast AI stay fast.

No product pitch is included. A brief subscribe prompt is allowed only after the teaching payoff and must fit the character’s voice.

## Visual Language

The episode alternates among six visual modes:

1. BiosRios character performance and reaction poses.
2. Real tool or browser captures.
3. Rough marker-style diagrams.
4. Kinetic text for short punch lines only.
5. Brief, transformed meme or reaction cutaways.
6. News, research, or documentation evidence with the relevant sentence visibly highlighted.

The host appears throughout the narrative but does not remain permanently parked in a corner. Character appearances should cover roughly 35–50% of the timeline, concentrated in the hook, transitions, jokes, and close.

Default visual-change cadence is 2–6 seconds. Intentional explanatory holds may run up to 9 seconds when internal motion or narration continues. Fast sequences should be followed by quiet frames so the video does not become exhausting.

The production keeps the existing black/charcoal BiosRios base but loosens the current uniform motion-graphics system. Screenshots may retain their native colors. Diagrams use off-white marker lines. Accent colors are reserved for meaning, not decoration.

## Internet Media and Evidence

Current claims must be supported by first-party documentation, published research, or clearly labeled community examples. Every downloaded image, article capture, meme, and clip receives a source URL and purpose in `assets/sources.jsonl`.

Internet media is used briefly and transformatively for commentary or explanation. Prefer first-party press assets, public-domain material, permissively licensed images, and original recreations. Do not download long source videos when a short cited still or browser capture is enough.

## Voice and Audio

Narration uses the existing `clean_calm.wav` reference and the approved Chatterbox baseline. The script is generated line by line so failed pronunciation can be replaced without regenerating the entire track.

- Conversational lines use the existing calm/mid settings.
- Hooks, punch lines, and reveals may use slightly higher exaggeration.
- Every kept line must pass Whisper transcription clarity of at least 0.90 or receive manual review.
- Pauses and emphasis are authored in the script; the final read should not sound like an advertisement.
- Final mix target: approximately -14 LUFS integrated, with true peak no higher than -1 dBTP.

Music is a low-volume bed with a few deliberate dropouts. Sound effects support edits and jokes but do not fire on every transition.

## Technical Output

- Container: MP4
- Video: H.264, 1920×1080, 60 fps
- Audio: AAC stereo, 48 kHz
- Captions: embedded readability pass plus separate `.srt`
- Final duration: 3:30–5:00
- Upload master target: no more than 500 MB unless a higher bitrate is visibly necessary

## Storage Contract

Create the episode under `videos/vibe-coding-dead/`. Keep reusable character and voice references in their existing shared locations; do not duplicate them into the episode.

- Keep browser captures and downloaded media at the smallest resolution that survives a 1080p crop.
- Read the two reference videos in place. Do not copy them.
- Put all render scratch files under `videos/vibe-coding-dead/.scratch/`, not the system temp directory.
- Delete `.scratch/`, extracted frames, failed voice takes, duplicate renders, and browser caches after final verification.
- Retain only source files, selected voice lines, selected media, the final master, captions, transcript, source manifest, and QA contact sheet.
- Working episode directory soft cap: 1.5 GB.
- Retained episode directory target after cleanup: 750 MB or less.

A cleanup command must list the exact files it will remove before deletion and must never touch shared character or voice-reference assets.

## Verification

Completion requires all of the following evidence:

- Script is 3–5 minutes when read by the selected voice takes.
- Every factual claim has a source or is clearly framed as opinion.
- The before/after demonstration uses captured real results.
- Voice-line clarity passes the threshold or is manually approved.
- Source manifest covers every external visual.
- HyperFrames lint and project checks pass.
- A full-timeline contact sheet shows no blank frames, accidental overlaps, unreadable evidence, or repetitive template cadence.
- The final MP4 passes FFprobe checks for codec, size, frame rate, audio, and duration.
- The final mix passes loudness and clipping checks.
- Captions match the final narration.
- Storage cleanup leaves the retained episode within the target or documents the specific reason it exceeds it.
- A final side-by-side editorial review against the Coding Sloth reference confirms mixed-media variety, comedic interruption, explanatory clarity, and rhythm without copying its visual identity.

## Deliverables

- `renders/vibe-coding-is-dead-1080p60.mp4`
- `renders/vibe-coding-is-dead.srt`
- `script.md`
- `transcript.txt`
- `assets/sources.jsonl`
- `renders/qa-contact-sheet.jpg`
- reusable build, render, verify, and cleanup commands documented in the episode README
