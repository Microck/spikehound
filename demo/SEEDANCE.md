# Seedance Clips for Spikehound Demo

## What you need

You're generating 2-3 short video clips in Seedance to use as B-roll over your screen recording. These overlay on top of sections where the screen recording alone would be boring (intro, architecture explanation, closing).

You do NOT need to upload 9 images. You do NOT need to do 5+ generations. Just run these prompts.

## Assets to upload (optional, improves output)

If Seedance lets you attach reference images, use these. If not, the prompts work standalone.

- **Architecture diagram**: `docs/architecture-light.svg` (screenshot/export as PNG)
- **Logo**: the Spikehound logo from the README header

---

## Prompt 1 — Intro + Architecture Reveal (use as B-roll for 0:00-0:35)

Generate at **10-15 seconds**, 16:9 landscape.

```
A sleek dark control room environment. A large floating holographic dashboard shows a cost graph spiking sharply upward, with the number "$450/day" pulsing in warning red. The atmosphere is tense and urgent.

After a beat, the scene transitions smoothly: the dark dashboard dissolves into a clean light-background system architecture diagram. The diagram shows a top-down flow: a single alert node at the top fans out into three parallel investigation branches (labeled "Cost", "Resource", "History"), which converge back into a "Diagnosis" node, then flow down to "Remediation" and finally "Notification" at the bottom. Data flows animate along the connections as each node illuminates in sequence.

Camera: Slow dramatic push-in on the cost spike, then smooth pull-back as the architecture reveals. Steady, confident motion throughout. No sudden cuts.

Style: Cinematic tech aesthetic. First half uses dark indigo shadows with hot orange warning accents. Second half transitions to a clean, professional light background with lavender nodes and orange highlights on active connections. No people, no faces. Sharp, enterprise-grade.

Duration: 15 seconds.
```

## Prompt 2 — Approval + Resolution (use as B-roll for 1:15-1:50)

Generate at **10-15 seconds**, 16:9 landscape.

```
A clean messaging notification card slides into frame against a subtle dark gradient background. The card displays an investigation summary with data fields: an alert identifier, a cost figure "$450/day", a confidence badge showing "85%", and a root cause description. Below the card, three action buttons are visible: a green "Approve" button, a red "Reject" button, and a gray "Investigate More" button.

A soft cursor glow approaches the green Approve button and clicks it. The button pulses with a satisfying green light. The scene transitions: a large green checkmark draws itself into frame. Below it, the text "$13,500/month saved" scales up prominently. The scene resolves into a clean title card: a stylized hound logo mark in burnt orange on a deep indigo background, with the text "Spikehound" beneath it.

Camera: Notification slides in and holds. Slow push toward buttons for the click. Pull back to reveal checkmark and savings number. Final hold on title card. Smooth throughout.

Style: Clean UI aesthetic transitioning to celebration. White card on dark gradient. Green approval pulse. Orange and indigo brand colors on the title card. Minimal, confident, professional. No people.

Duration: 15 seconds.
```

## Prompt 3 (optional) — Parallel Agents Visual (use as B-roll for 0:35-0:55)

Only generate this if you want extra visual flair over the "agents running" section. Otherwise your screen recording of the terminal logs is enough.

```
Three transparent floating data panels arranged side by side, each representing an AI agent analyzing different aspects of a cloud cost anomaly. The left panel shows cost charts and dollar figures, the center panel shows server infrastructure details and status indicators, the right panel shows timeline history entries. All three panels are actively processing simultaneously — data scrolling, values highlighting, progress indicators advancing in sync.

The three panels pulse and their findings stream downward into a single convergence point below, which glows brightly as it synthesizes the results into a unified diagnosis.

Camera: Wide establishing shot of all three panels processing in parallel. Gentle drift that connects them visually. Energy builds as findings converge. Smooth, no sudden motion.

Style: Futuristic but restrained. Dark background with glass-like transparent panels. Color coding: orange for cost data, indigo for infrastructure, teal for history. Subtle holographic feel. Clean and professional. No people, no faces.

Duration: 10 seconds.
```

---

## How to use the clips

In your video editor (CapCut, DaVinci, Premiere, whatever):

1. Your **main track** is the screen recording of the full demo
2. Your **audio track** is the ElevenLabs voiceover from `demo/voiceover.md`
3. Drop the Seedance clips on a **track above** the screen recording as B-roll overlays:
   - Prompt 1 clip → overlay during 0:00-0:15 (intro hook) and/or 0:15-0:35 (architecture)
   - Prompt 3 clip (if generated) → overlay during 0:35-0:55 (agents running)
   - Prompt 2 clip → overlay during 1:40-2:00 (closing/title card)
4. Use **crossfade transitions** (0.5s) between B-roll and screen recording
5. The screen recording is visible during the "live proof" sections (trigger, Slack/Discord messages, approval click, VM deallocate)

The B-roll makes the intro and closing look polished. The middle is all real footage — that's your credibility.
