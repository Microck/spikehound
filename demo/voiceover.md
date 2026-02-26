# Spikehound Demo Voiceover (ElevenLabs TTS)

## Settings

- **Voice:** Pick a calm, confident male or female voice (e.g. "Adam", "Rachel", or "Antoni")
- **Stability:** 0.50
- **Clarity + Similarity Enhancement:** 0.75
- **Style:** 0 (neutral — no dramatic flair)
- **Speed:** Slightly slow (the video is 2 minutes, you want breathing room)

## How to use

Generate each section as a **separate audio clip** in ElevenLabs. This lets you align each clip to the matching section of your screen recording in your video editor (CapCut, DaVinci, etc).

If you want to do it in one shot, paste the full script (Section 1-6 combined) and generate once. Just add a 2-second pause between sections by inserting a blank line.

---

## Section 1 — Intro + Hook (0:00 - 0:15)

```
Spikehound. A multi-agent system that automatically investigates Azure cost anomalies.

Right now, a GPU VM is burning four hundred and fifty dollars a day. Nobody noticed for three days. That's thirteen thousand dollars wasted. Spikehound catches this in under a second.
```

## Section 2 — Architecture (0:15 - 0:35)

```
Here's how it works.

An Azure Monitor alert hits our webhook. The Coordinator fans out to three specialized agents in parallel: a Cost Analyst, a Resource Agent, and a History Agent. They investigate simultaneously.

Their findings converge into a Diagnosis Agent, which synthesizes a root cause with eighty-five percent confidence. Then a Remediation Agent proposes fix actions. All of this happens automatically, before a human touches anything.
```

## Section 3 — Live Trigger (0:35 - 0:55)

```
Let me show you. I'm sending the alert now.

You can see the server logs streaming in real time. All five agents ran in parallel and completed in under one second. The investigation results are already posted to both Slack and Discord.
```

## Section 4 — Slack + Discord Messages (0:55 - 1:15)

```
Here's the Slack notification. It shows the top cost driver: the GPU VM at four fifty a day. Eighty-five percent confidence that the root cause is the VM left running after a training job completed seventy-two hours ago.

The system recommends stopping the VM. And here's the same investigation in Discord, with interactive buttons on both channels.

No action executes without human approval. That's the safety guarantee.
```

## Section 5 — Approve + Remediation (1:15 - 1:40)

```
I'm clicking Approve now.

Watch the server logs. The approval is received, the remediation orchestrator kicks in, and the system sends a real deallocate command to Azure. The VM is shutting down right now.

The follow-up message confirms it: VM stopped and deallocated. Four hundred and fifty dollars a day saved, starting immediately.
```

## Section 6 — Closing (1:40 - 2:00)

```
From alert to fix. Five AI agents. Two notification channels. One human click.

Spikehound turns a three-day-old cost anomaly into a sixty-second resolution. Thirteen thousand five hundred dollars saved per month, for just this one VM.

Built for the Microsoft AI Dev Days Hackathon twenty twenty-six. Thank you for watching.
```

---

## Full Script (single paste for one-shot generation)

Copy everything below the line for a single ElevenLabs generation. The blank lines create natural pauses.

---

Spikehound. A multi-agent system that automatically investigates Azure cost anomalies.

Right now, a GPU VM is burning four hundred and fifty dollars a day. Nobody noticed for three days. That's thirteen thousand dollars wasted. Spikehound catches this in under a second.

Here's how it works.

An Azure Monitor alert hits our webhook. The Coordinator fans out to three specialized agents in parallel: a Cost Analyst, a Resource Agent, and a History Agent. They investigate simultaneously.

Their findings converge into a Diagnosis Agent, which synthesizes a root cause with eighty-five percent confidence. Then a Remediation Agent proposes fix actions. All of this happens automatically, before a human touches anything.

Let me show you. I'm sending the alert now.

You can see the server logs streaming in real time. All five agents ran in parallel and completed in under one second. The investigation results are already posted to both Slack and Discord.

Here's the Slack notification. It shows the top cost driver: the GPU VM at four fifty a day. Eighty-five percent confidence that the root cause is the VM left running after a training job completed seventy-two hours ago.

The system recommends stopping the VM. And here's the same investigation in Discord, with interactive buttons on both channels.

No action executes without human approval. That's the safety guarantee.

I'm clicking Approve now.

Watch the server logs. The approval is received, the remediation orchestrator kicks in, and the system sends a real deallocate command to Azure. The VM is shutting down right now.

The follow-up message confirms it: VM stopped and deallocated. Four hundred and fifty dollars a day saved, starting immediately.

From alert to fix. Five AI agents. Two notification channels. One human click.

Spikehound turns a three-day-old cost anomaly into a sixty-second resolution. Thirteen thousand five hundred dollars saved per month, for just this one VM.

Built for the Microsoft AI Dev Days Hackathon twenty twenty-six. Thank you for watching.
