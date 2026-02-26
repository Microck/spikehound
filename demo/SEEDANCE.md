# Seedance Montage Pack: Spikehound (30s master)

## Repo-Derived Notes

- **Product:** Spikehound — multi-agent incident workflow for Azure cost anomalies. Ingests an alert, fans out to 3 specialized investigator agents in parallel, synthesizes a diagnosis with confidence scoring, proposes remediation, and gates execution behind human approval via Slack/Discord buttons.
- **Audience:** Microsoft AI Dev Days Hackathon judges evaluating across 3 prize categories (Agentic DevOps $20k, Best Multi-Agent System $10k, Best Azure Integration $10k). Secondary: DevOps/SRE/FinOps engineers who manage cloud spend.
- **Key features/screens to show:**
  1. Architecture diagram (6-agent parallel fan-out flow, portrait orientation, pastel palette)
  2. Terminal: `func start` server logs showing parallel agent execution
  3. Terminal: `curl` webhook trigger firing the investigation
  4. Slack message with rich investigation summary + Approve/Reject/Investigate buttons
  5. Slack follow-up showing remediation outcome (green checkmark, $450/day savings)
  6. Discord message with embeds + interactive buttons (parity channel)
  7. Azure Portal VM page showing status transition (Running -> Stopped)
- **Brand/style cues detected:**
  - Logo mark: stylized hound/tracker glyph in `#f66930` (burnt orange) + `#221a6f` (deep indigo)
  - Architecture diagram: light theme, pale yellow containers, lavender nodes, green outcome accents
  - Overall feel: professional, clean, enterprise-grade but approachable
  - No neon/cyberpunk — lean into confident deep-blue + warm-orange accent palette

---

## Asset Plan (Upload Order)

> You need to capture/prepare these before generating. Paths marked with `[CAPTURE]` require a screenshot you take during a live demo run.

```
@Image1: Spikehound logo (horizontal, light bg)
         Source: docs/brand/logo-horizontal.svg (export as PNG 1280x216)
         Use: Title cards, watermarks, intro/outro

@Image2: Architecture diagram (full)
         Source: docs/architecture.png (784x1367, portrait)
         Use: Segments 2 and 3 — the "reveal" and "agent fan-out" beats

@Image3: [CAPTURE] Terminal split — server logs showing agent fan-out
         Content: Terminal 1 with func start output showing:
           webhook_received → coordinator_fanout → cost_analyst_completed →
           resource_agent_completed → history_agent_completed →
           diagnosis_completed → remediation_completed → slack_webhook_sent
         Tips: Large font (18pt+), dark terminal, green/white text
         Use: Segment 3 — parallel investigation beat

@Image4: [CAPTURE] Terminal — curl webhook trigger command
         Content: The curl -X POST command visible in a clean terminal
         Use: Segment 3 — "fire the alert" moment

@Image5: [CAPTURE] Slack investigation message (full)
         Content: The rich Slack message showing:
           - Alert ID, top cost driver ($450/day)
           - 85% confidence, root cause
           - Approve / Reject / Investigate buttons visible
         Tips: Crop tight to the message, ensure buttons are large and readable
         Use: Segment 4 — human-in-the-loop reveal

@Image6: [CAPTURE] Slack follow-up message (remediation outcome)
         Content: Green checkmark message showing:
           - Action: stop_vm, Target: spikehound-gpu-vm
           - Outcome: SUCCESS, Savings: $450/day
         Use: Segment 5 — proof/resolution beat

@Image7: [CAPTURE] Discord investigation message with buttons
         Content: Rich embed with same investigation data + interactive buttons
         Tips: Show Discord's dark theme for visual contrast with Slack
         Use: Segment 4 alternate — multi-channel proof

@Image8: Spikehound logo (square mark, dark bg)
         Source: docs/brand/logo-dark.svg (export as PNG 512x512)
         Use: Outro title card, thumbnail

@Image9: [CAPTURE] Azure Portal — VM page showing "Stopped (deallocated)" status
         Content: Azure Portal VM overview with status badge
         Use: Segment 5 — real Azure proof
```

**Skipped (not enough slots):** Discord follow-up message, terminal test output (23/23 pass), Azure cost chart. If you have extra generation credits, add Discord follow-up as @Image9 and bump Azure Portal to a live-recording-only shot.

**Audio guidance:**
- `@Audio1` (optional): Clean ambient tech track, 100-110 BPM, no lyrics, builds energy. Recommend: royalty-free "corporate tech" or "innovation" track from Artlist/Epidemic Sound.
- You will likely add a voiceover track in post — Seedance generations are silent visual-only clips.

---

## 30s Script

| Seg | Time | Beat | VO (what you say in the real demo overlay) | Visual Intent |
|-----|------|------|---------------------------------------------|---------------|
| 1 | 0-6s | Hook / Problem | "A GPU VM is burning $450 a day. Nobody knows." | Dark, tense. Cost number appears large. Terminal blinks. Urgency. |
| 2 | 6-12s | Product Reveal | "Spikehound. Six AI agents investigate in parallel — automatically." | Logo reveals. Architecture diagram animates top-down. Clean, confident. |
| 3 | 12-18s | Feature: Multi-Agent Investigation | "Cost Analyst. Resource Agent. History Agent. All running simultaneously." | Terminal logs scroll. Agent names appear. Parallel motion. Energy builds. |
| 4 | 18-24s | Feature: Human-in-the-Loop | "One Slack message. Three buttons. Human stays in control." | Slack message appears. Buttons pulse. Cursor clicks Approve. |
| 5 | 24-30s | Proof + CTA | "VM stopped. $13,500 saved per month. From alert to fix — one click." | Green checkmark. Savings number grows. Logo lockup. Hackathon badge. |

---

## Real Recording Integration Plan

The final 2-minute submission video will combine Seedance-generated motion graphics with real screen recordings. Here is the integration map:

### What Seedance handles (the "sizzle reel" / intro hook):
- **Opening 30s** of the video: the Seedance montage plays as a polished cold open
- Sets the tone, communicates the product story visually before the live demo begins
- Think of it as the "trailer before the documentary"

### What you record live (the "proof" / main demo):
- **Remaining ~90s**: real screen recording following `demo/script.md`
- Architecture walkthrough (real diagram on screen)
- Real `curl` trigger → real server logs → real Slack message → real button click → real follow-up
- Optional: Azure Portal showing VM stopped

### Stitch plan:
```
[0:00 - 0:30]  Seedance montage (generated, edited from 5x15s clips)
[0:30 - 0:32]  Crossfade transition to live recording
[0:32 - 2:00]  Live demo recording (per demo/script.md, starting from Architecture Overview)
```

### Why this works:
- Judges see a polished, high-energy intro that communicates the value proposition in 30s
- Then they see real proof that it actually works
- The Seedance clips don't need to be pixel-perfect UI — they're mood/energy/story
- The live recording provides the authentic credibility

### Screenshots to capture (for both Seedance @Images AND live recording):
Run the full demo flow once with screen recording ON. During that run, also take these screenshots:
1. Server logs after full investigation (@Image3)
2. Curl command in terminal (@Image4)
3. Slack investigation message (@Image5)
4. Slack follow-up message (@Image6)
5. Discord message with buttons (@Image7)
6. Azure Portal VM stopped (@Image9)

This single run gives you everything for both the Seedance prompts AND the real demo footage.

---

## Segment Prompts (15s mini montages)

> **How to use these prompts:**
> 1. Upload your @Image assets to Seedance in the order listed above
> 2. Copy-paste one prompt at a time
> 3. Generate at 15s duration
> 4. The "keeper" action is in the first 6-8 seconds — that is your final edit segment
> 5. Seconds 8-15 are coverage/variations for backup
>
> **Credit-saving mode:** If credits are tight, generate at 10s instead of 15s. The keeper window shrinks to 0-6s but still works. Generate all 5 recommended prompts first. Only do alternates for segments that underperformed.

---

### Segment 1 Prompt — Hook / Problem (recommended)

```
@Image3 @Image1

A dark, moody technology control room. A large floating holographic display shows a cost dashboard with a number climbing rapidly: "$450/day" pulses in warning red against a deep navy background. The Spikehound logo mark glows subtly in the corner.

Camera: Slow dramatic push-in toward the display. The red cost number dominates the frame. Terminal text scrolls faintly in the background, reflecting off a dark glass surface. Atmosphere is tense — something is wrong and no one has noticed yet.

Style: Cinematic tech thriller. Dark tones with deep indigo (#221a6f) shadows and hot orange (#f66930) warning accents. Shallow depth of field. Clean, no clutter. Stable camera, smooth motion. No people.

Duration: 15 seconds. The key moment (big red cost number, tense atmosphere) should land in the first 5 seconds.
```

### Segment 1 Prompt — Hook / Problem (alternate)

```
@Image4

A minimalist dark terminal screen fills the frame. A blinking cursor sits idle. Then a command appears character by character — a webhook alert firing. The terminal background is pure black with crisp monospace text in green and white. A subtle red glow creeps in from the edges of the frame as the alert payload reveals cost anomaly data.

Camera: Static medium shot of the terminal, then slow creep-in as the alert text appears. No lateral motion. Text should be large and suggestive (not pixel-readable — just the feel of urgent technical output).

Style: Minimal hacker aesthetic. Black, green terminal glow, red warning accents. Clean and restrained. No people, no faces. Stable layout throughout.

Duration: 15 seconds.
```

---

### Segment 2 Prompt — Product Reveal (recommended)

```
@Image1 @Image2

The Spikehound logo emerges from darkness — the burnt-orange hound mark resolves first, then the deep indigo wordmark slides in beside it. The logo holds for a beat, then dissolves into an architectural blueprint: a top-down system diagram with connected nodes and flowing data paths. The diagram animates to life — arrows light up sequentially showing data flowing from a single alert at the top, fanning out to three parallel investigation nodes, then converging back into a diagnosis.

Camera: Starts tight on the logo, then pulls back smoothly to reveal the full architecture. Gentle top-down drift as the diagram activates. No sudden cuts.

Style: Clean professional motion graphics. Deep indigo background transitioning to a light blueprint aesthetic. Pastel lavender nodes with orange accent highlights on active connections. Geometric, precise, confident. No organic textures. No people.

Duration: 15 seconds. Logo reveal completes by second 3. Full architecture visible and animating by second 6.
```

### Segment 2 Prompt — Product Reveal (alternate)

```
@Image2

A detailed system architecture diagram on a light background. The diagram is viewed from a slight three-quarter angle, giving it depth. One by one, each component box illuminates with a soft glow — starting from "Azure Monitor Cost Alert" at the top, flowing through "Coordinator," then three parallel branches light up simultaneously (Cost Analyst, Resource Agent, History Agent), converging into "Unified Findings" and continuing down through Diagnosis and Remediation.

Camera: Gentle orbital drift around the diagram, almost like examining a blueprint on a table. Slow, stable, confident motion. The parallel branch activation is the hero moment.

Style: Technical documentation come to life. Light cream background, lavender component boxes, orange accent on active paths. Clean sans-serif labels (suggestive, not pixel-perfect). No people.

Duration: 15 seconds.
```

---

### Segment 3 Prompt — Multi-Agent Investigation (recommended)

```
@Image3 @Image2

A split composition: on the left, a dark terminal window with scrolling log output — agent names appearing in sequence (Cost Analyst, Resource Agent, History Agent) with completion timestamps. On the right, an abstract visualization of three parallel data streams flowing simultaneously — represented as luminous threads of data moving in parallel tracks, each a different color (orange, indigo, teal), converging into a single bright point.

Camera: Starts with a medium shot of both panels, then slowly pushes into the convergence point on the right as all three streams merge. Energy builds as the parallel streams synchronize.

Style: Technical + abstract. Left side is grounded reality (terminal logs, monospace text). Right side is conceptual (data flow visualization). Colors: deep indigo base, orange/teal/lavender for the three agent streams. Clean, professional, energetic but controlled. No people.

Duration: 15 seconds. All three streams should be visibly running in parallel by second 3. Convergence happens at second 6.
```

### Segment 3 Prompt — Multi-Agent Investigation (alternate)

```
@Image3

Three transparent floating panels arranged in a triangular formation, each representing an AI agent at work. The left panel shows cost data and charts (Cost Analyst), the center panel shows infrastructure configuration details (Resource Agent), the right panel shows historical incident records (History Agent). All three panels are actively processing simultaneously — data scrolling, charts updating, findings highlighting.

Camera: Wide establishing shot of all three panels, then a slow orbit that connects them visually. The panels pulse in sync as they complete their analysis. A subtle connecting thread links all three to a central synthesis point below them.

Style: Futuristic but restrained. Dark background, glass-like transparent panels with soft inner glow. Color coding: orange for cost, indigo for resources, teal for history. Holographic feel without being gaudy. No people, no faces.

Duration: 15 seconds.
```

---

### Segment 4 Prompt — Human-in-the-Loop (recommended)

```
@Image5 @Image7

A messaging interface appears — a rich notification card with a clean investigation summary. The card shows key data points: an alert identifier, a cost figure, a confidence percentage, and a root cause description. Below the card, three action buttons are clearly visible — a green primary button, a red danger button, and a neutral button. The composition emphasizes that a human must make the decision.

Camera: The notification slides in from below and settles in the center of frame. Hold on the full message for a beat, then slowly push in toward the buttons. A cursor indicator (soft glow, not a literal mouse arrow) hovers toward the green Approve button and clicks it. The button depresses with a satisfying pulse of green light.

Style: Clean messaging UI aesthetic. White/light card on a subtle gradient background (indigo to dark). Button colors: green for approve, red for reject, gray for investigate. The approval click is the hero moment — make it feel decisive and satisfying. Warm orange glow radiates outward from the click. No people, no faces.

Duration: 15 seconds. Notification fully visible by second 2. Button click lands at second 5-6.
```

### Segment 4 Prompt — Human-in-the-Loop (alternate)

```
@Image5 @Image1

A dark workspace with two glowing screens side by side — one showing a Slack-style messaging interface with an investigation report, the other showing a Discord-style interface with the same report in a different visual format. Both screens show identical investigation data and interactive buttons, demonstrating multi-channel capability. The Spikehound logo watermark sits subtly between the two screens.

Camera: Wide shot establishing both screens, then slow push toward the Slack screen as a cursor approaches the Approve button. Both screens show the same alert being handled, proving cross-platform parity.

Style: Dual-screen composition. Left screen: white/light Slack aesthetic. Right screen: dark Discord aesthetic. The contrast between the two messaging platforms is visually interesting. Deep indigo ambient lighting ties them together. Clean, professional. No people.

Duration: 15 seconds.
```

---

### Segment 5 Prompt — Proof + CTA (recommended)

```
@Image6 @Image1 @Image8

A green checkmark animates into frame — large, confident, satisfying. Below it, a success message card appears showing remediation completed. The key number "$13,500/month saved" scales up prominently. The scene transitions to a clean title card: the Spikehound logo (horizontal) centered on a deep indigo background, with the tagline "From alert to fix. One click." beneath it. A subtle "Microsoft AI Dev Days Hackathon 2026" badge appears in the lower third.

Camera: Starts tight on the green checkmark as it draws itself (stroke animation feel). Pulls back to reveal the savings number. Then a smooth dissolve/transition to the logo lockup title card. Final seconds hold on the title card — stable, confident.

Style: Celebration into confidence. Green success tones transitioning to the brand's deep indigo + burnt orange palette. The savings number should feel impactful — large, bold, clean typography (suggestive, not pixel-perfect). The title card is minimal and prestigious. No people, no faces.

Duration: 15 seconds. Checkmark + savings visible by second 3. Title card transition at second 6. Hold on title card through second 15.
```

### Segment 5 Prompt — Proof + CTA (alternate)

```
@Image9 @Image6 @Image1

An Azure cloud portal interface showing a virtual machine status page. The status badge transitions from "Running" (with a spinning activity indicator) to "Stopped (deallocated)" (with a gray/green confirmed badge). The frame pulls back to reveal a cost savings counter incrementing: $450... $900... $1,350... representing daily savings accumulating. The scene ends with the Spikehound logo resolving over the Azure interface, positioned as the system that made this happen.

Camera: Starts on the VM status badge, holds during the transition, then pulls back to include the savings counter. Final pull-back to the logo over the full scene. Smooth, deliberate motion throughout.

Style: Azure Portal aesthetic (light, clean, Microsoft blue accents) combined with Spikehound branding (indigo + orange). Professional, enterprise-grade. The status transition should feel real and grounded. No people.

Duration: 15 seconds.
```

---

## Assembly Notes (how to cut back to 30s)

### Generation Plan (batch order)

**Phase 1 — Recommended prompts only (5 generations, ~5 credits):**
1. Generate Segment 1 recommended (Hook)
2. Generate Segment 2 recommended (Reveal)
3. Generate Segment 3 recommended (Investigation)
4. Generate Segment 4 recommended (Approval)
5. Generate Segment 5 recommended (Proof + CTA)

**Phase 2 — Fix underperformers (1-3 generations):**
- Review all 5 clips. For any segment where the first 6s are unusable (artifacts, layout drift, incoherent motion), generate that segment's alternate prompt.
- Typical: 1-2 segments need a redo. Budget 2 extra generations.

**Phase 3 — Optional polish (1-2 generations):**
- If Segment 4 (approval click) doesn't feel satisfying, try the dual-screen alternate.
- If Segment 5 title card isn't clean, try the Azure Portal alternate.

**Total budget: 5-8 generations (recommended: 7)**

### Selection Rubric

**Keep:**
- Stable camera motion with no sudden jumps
- Legible UI layouts (cards, buttons, terminal text recognizable even if not pixel-readable)
- Coherent color palette matching brand (indigo + orange + white)
- Clean transitions between visual elements within the clip
- The "hero moment" happening in the first 6 seconds

**Reject:**
- Melting/dithering text or UI elements
- Layout drift (elements sliding or morphing unexpectedly)
- Sudden object swaps (one UI becoming a completely different UI)
- Heavy color banding or compression artifacts
- Camera motion that fights the content (shaking, snapping)
- Any faces or human figures appearing (even if not requested)

### Editing Plan

**Timeline structure (30s master):**
```
[0:00-0:06]  Seg 1 keeper (seconds 0-6 of best Seg 1 generation)
[0:06-0:12]  Seg 2 keeper (seconds 0-6 of best Seg 2 generation)
[0:12-0:18]  Seg 3 keeper (seconds 0-6 of best Seg 3 generation)
[0:18-0:24]  Seg 4 keeper (seconds 0-6 of best Seg 4 generation)
[0:24-0:30]  Seg 5 keeper (seconds 0-6 of best Seg 5 generation)
```

**Transitions between segments:**
- Use 6-12 frame (0.2-0.5s) crossfades between segments
- Trim from the tail of each keeper to maintain 6s per segment with transition overlap
- Alternative: hard cuts work if the visual flow is strong enough

**Audio layers:**
1. **Music bed:** Ambient tech track (start quiet, build energy through Seg 3, sustain through Seg 4, resolve in Seg 5). Fade in at 0:00, full volume by 0:06, fade out at 0:28.
2. **VO track (optional for montage):** If adding voiceover to the Seedance portion, record the VO lines from the script table above and layer over the visuals. Keep VO minimal — let the visuals carry.
3. **SFX (optional):** Subtle UI sounds — soft "pop" for button appearance, gentle "whoosh" for data flow, satisfying "click" for approval button. Don't overdo it.

**Export settings for the 30s montage clip:**
- Resolution: 1920x1080 (16:9) or 1080x1920 (9:16)
- Codec: H.264, high profile
- Frame rate: 30fps (matching Seedance output)
- Bitrate: 10-15 Mbps for quality

**Integration into 2-minute submission video:**
```
[0:00 - 0:30]  Seedance 30s montage (this pack)
[0:30 - 0:32]  2-second crossfade transition to live recording
[0:32 - 2:00]  Live demo recording (follow demo/script.md starting from "Architecture Overview")
```

The crossfade at 0:30 should transition from the Seedance title card (Segment 5 end) into the live recording of the architecture diagram. This creates a seamless handoff from "sizzle" to "substance."

---

## Variants

### 9:16 (vertical / phone-safe)

**Framing adjustments for all prompts:**
- Replace "wide shot" and "wide establishing" with "tall vertical composition"
- Replace lateral camera pans with vertical tilts (top-to-bottom)
- Architecture diagram (@Image2) works great in 9:16 since it is already portrait (784x1367)
- Slack/Discord messages: crop tighter, show one message card filling the vertical frame
- Logo reveals: use the square mark (@Image8) instead of horizontal lockup (@Image1)
- Terminal screenshots: crop to show fewer but larger lines of text
- Title card (Seg 5): stack logo above tagline vertically instead of horizontal layout

**Prompt modifications for 9:16:**
Add this line to the end of each prompt:
```
Aspect ratio: 9:16 vertical. Frame all elements in a tall portrait composition. Prefer vertical camera tilts over horizontal pans. Keep key elements centered in the vertical middle third.
```

**When to use 9:16:**
- Social media clips (Instagram Reels, TikTok, YouTube Shorts)
- Mobile-first presentation contexts
- Quick teaser clips to share on social alongside the hackathon submission

### 16:9 (landscape / presentation)

**Framing adjustments for all prompts:**
- This is the default assumed by the prompts above — no modifications needed
- Architecture diagram (@Image2) will need to be displayed centered with indigo side bars or at reduced scale since the source is portrait
- Dual-screen compositions (Seg 4 alternate) work best in 16:9
- Wide establishing shots and lateral camera motion are available and encouraged
- Terminal content can show more horizontal context (wider command lines)

**When to use 16:9:**
- Primary hackathon submission video (required format for YouTube/Vimeo)
- Presentation slides with embedded video
- Demo during live judging sessions

**Recommendation:** Generate 16:9 first (it is the submission format). Generate 9:16 only if you want social media clips — share the same keeper selections, just re-crop or re-generate with the 9:16 suffix line.

---

## Quick-Start Checklist

1. [ ] Run the full demo flow once with screen recording to capture @Image3-7 and @Image9
2. [ ] Export @Image1 and @Image8 from the SVG brand files
3. [ ] Upload all 9 images to Seedance in order (@Image1 first, @Image9 last)
4. [ ] Generate Segment 1-5 recommended prompts (5 runs)
5. [ ] Review: mark each as KEEP or REDO
6. [ ] Re-generate any REDO segments using alternate prompts
7. [ ] Import all keeper clips into video editor (DaVinci Resolve, Premiere, CapCut)
8. [ ] Trim each to best 6s, arrange in sequence, add crossfades
9. [ ] Add music bed and optional VO
10. [ ] Export 30s montage as separate clip
11. [ ] Prepend montage to live demo recording
12. [ ] Export final 2-minute submission video
13. [ ] Upload to YouTube/Vimeo, get public link
