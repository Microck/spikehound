# Demo Recording Checklist

Use this checklist to produce a consistent, high-quality 2-minute demo video for hackathon submission.

---

## Pre-Flight Checklist (Before Recording)

### Environment Setup

- [ ] **Azure CLI authenticated**
  - Verify: `az account show` shows correct subscription
  - Optional: `az account show --query '{user:user.name, subscription:id}' -o json`

- [ ] **Spikehound server is running**
  - Verify: `curl http://localhost:7071/api/health` returns `{"ok":true}`
  - Terminal 1 shows Functions host startup logs

- [ ] **Slack app configured**
  - Verify: `.env` has `SLACK_WEBHOOK_URL` and `SLACK_SIGNING_SECRET`
  - Test: Slack test message sent (optional, but good for verification)

- [ ] **Webhook mode set for synchronous demo**
  - Verify: `INCIDENT_WR_USE_DURABLE=false` in `.env`
  - Note: `true` schedules Durable orchestration and returns async `202`

- [ ] **Demo VM is staged**
  - Verify: VM is running and tagged with `demo=true`
  - Run: `bash demo/stage_anomaly.sh --vm-name gpu-training-vm --resource-group ai-dev-days-hackathon-eu`
  - Check: `demo=true` tag visible in Azure Portal

### Recording Preparation

- [ ] **Screen recording software ready**
  - Options: OBS, QuickTime, Loom, or built-in macOS screen recorder
  - Settings: 1080p or higher, MP4 format, 60fps or higher
  - Audio: System audio or external mic (test levels before recording)

- [ ] **Windows/Terminals prepared**
  - Layout: Split screen or arrange side-by-side
  - Terminal 1 (Server logs): Large font, visible on screen, scroll to show recent logs
  - Terminal 2 (Webhook trigger): Separate window for `curl` command
  - Slack: Open in browser, #alerts or demo channel visible

- [ ] **Browser windows ready**
  - Tab 1: README.md (or architecture.png) for intro
  - Tab 2: Azure Portal → GPU VM details (optional)
  - Tab 3: Slack channel for showing notifications

- [ ] **Demo payload file prepared**
  - File: `demo-alert-payload.json` saved and ready to copy-paste
  - Verify: Alert ID matches staged VM resource ID

---

## Recording Script (Execute in Order)

### Segment 0:00 - 0:10 | Introduction (10 seconds)

**What to show:**
- README.md opened, highlight project name
- Say: "Today I'll demonstrate Spikehound..." intro speech

**Checklist:**
- [ ] Project name is clearly stated
- [ ] Three prize categories mentioned (Agentic DevOps, Multi-Agent, Azure Integration)
- [ ] Recording software is capturing (check preview window)
- [ ] Audio is clear (test: "Today I'll demonstrate..." is audible)

**Expected one-liners:**
- "Spikehound — Multi-Agent Azure Cost Anomaly War Room"
- "Targets: Agentic DevOps, Multi-Agent, Azure Integration"

---

### Segment 0:10 - 0:30 | Architecture Overview (20 seconds)

**What to show:**
- docs/architecture.png in viewer or editor
- Say: "Let me show you the architecture..." explanation speech

**Checklist:**
- [ ] Diagram is visible and centered
- [ ] Each section is called out (Coordinator, 6 agents, Slack)
- [ ] Recording captures full diagram
- [ ] Arrows and labels are readable

**Expected one-liners:**
- "Architecture: Alert → Coordinator → 6 Parallel Agents"
- "Agents: Cost Analyst, Resource Agent, History Agent"
- "Output: Root cause 85% confidence → Remediation → Slack buttons"

---

### Segment 0:30 - 0:45 | Staged Anomaly (15 seconds)

**What to show:**
- Azure Portal VM page (or `az vm show` output)
- Say: "For this demo, I've staged..." anomaly explanation

**Checklist:**
- [ ] VM name (gpu-training-vm) is visible
- [ ] Status shows "Running" (or "VM running")
- [ ] Cost spike numbers are visible ($12 vs $450, 36x factor)
- [ ] Recording shows VM details panel

**Expected one-liners:**
- "Staged Anomaly: GPU VM running 72 hours"
- "Baseline: $12/day → Actual: $450/day (36x spike)"
- "Root Cause: Training job finished, no auto-shutdown"

---

### Segment 0:45 - 1:00 | Trigger Investigation (15 seconds)

**What to show:**
- Terminal 2 window, paste/type `curl` command
- Terminal 1 shows server logs updating in real-time
- Say: "Now I'm triggering..." setup speech

**Checklist:**
- [ ] `curl` command is visible (type or paste from file)
- [ ] Terminal 1 shows logs: `webhook_received`, `coordinator_fanout`, agent completions
- [ ] Recording captures both terminals side-by-side
- [ ] Timestamp segment is clear (0:45 mark in server logs)

**Expected one-liners:**
- "Trigger: POST /api/webhooks/alert"
- "Logs: 6 agents running in parallel"
- "Investigation completed in 15 seconds"

---

### Segment 1:00 - 1:20 | Multi-Agent Outputs (20 seconds)

**What to show:**
- Slack channel (refresh if needed)
- Say: "The investigation completed automatically..." read Slack message

**Checklist:**
- [ ] Slack message is fully visible
- [ ] All fields are readable: Alert ID, cost driver, confidence, root cause, action
- [ ] Three buttons are visible: Approve (primary), Reject (danger), Investigate (default)
- [ ] Recording captures Slack message clearly

**Expected one-liners:**
- "Slack: Cost driver $450/day, Confidence 85%"
- "Root cause: VM left running 72 hours ago"
- "Remediation: stop_vm action, requires approval"

---

### Segment 1:20 - 1:40 | Human Approval (20 seconds)

**What to show:**
- Click "Approve" button in Slack
- Terminal 1 shows approval callback logs
- Say: "To execute... I'm clicking Approve" click speech

**Checklist:**
- [ ] Mouse cursor is visible when clicking
- [ ] Button click is captured on screen
- [ ] Terminal 1 shows: `slack_approval_received`, `slack_approval_recorded`, `remediation_execution_queued`
- [ ] Recording captures the moment of click

**Expected one-liners:**
- "Clicking Approve button in Slack"
- "Logs: Approval recorded, execution queued"
- "Safety: Human approval required"

---

### Segment 1:40 - 2:00 | Remediation Execution (20 seconds)

**What to show:**
- Refresh Slack channel for follow-up message
- Azure Portal VM status (optional, shows "Stopped")
- Say: "The remediation executed successfully..." conclusion speech

**Checklist:**
- [ ] Follow-up Slack message is visible with green checkmark
- [ ] All outcome fields are clear: action, target, result, savings
- [ ] Azure Portal shows VM "Stopped" or "VM deallocated"
- [ ] Recording shows the resolution and impact

**Expected one-liners:**
- "Follow-up: Remediation completed"
- "Outcome: VM stopped and deallocated, SUCCESS"
- "Savings: $450/day = $13,500/month"

---

## Post-Flight Checklist (After Recording)

### Video Export

- [ ] **Export in correct format**
  - File: `demo/video.mp4`
  - Codec: H.264 or H.265
  - Duration: Between 1:45 and 2:15 (target 2:00)
  - Resolution: 1080p or higher
  - File size: Under 100 MB (for easy sharing)

- [ ] **Quality check**
  - Audio is clear throughout
  - Text in terminals is readable (large font, contrast)
  - Diagram is sharp and labels are legible
  - No flickering or stuttering

- [ ] **Content verification**
  - All 6 segments are included
  - Timecodes roughly match script (don't need to be exact)
  - Slack messages are fully visible
  - Server logs are captured showing agent flow
  - Human approval click is captured

### File Placement

- [ ] **Save to correct location**
  - Path: `demo/video.mp4`
  - Verify: File exists in project directory

### Final Verification

- [ ] **Watch the exported video once**
  - Confirm: Audio is in sync with video
  - Confirm: No glitches or gaps
  - Confirm: Story flows logically from intro to conclusion
  - Confirm: Total time is ~2:00 minutes

---

## Troubleshooting

### Common Issues

**Issue:** Server logs not visible on screen
- **Fix:** Increase terminal font size before recording
- **Command:** Terminal → Preferences → Text → Larger

**Issue:** Slack buttons not clickable during recording
- **Fix:** Make sure Slack tab is active before clicking
- **Fix:** Record at 30fps or higher for smoother interaction capture

**Issue:** VM status doesn't update in Azure Portal
- **Fix:** Refresh the VM page (F5 or refresh button)
- **Fix:** Wait 10-15 seconds for Azure to propagate status changes

**Issue:** Video file too large
- **Fix:** Reduce resolution to 720p if 1080p file is >200 MB
- **Fix:** Use more efficient codec (H.265 instead of H.264)

---

## Quick Reference Commands

```bash
# Start Functions app (Terminal 1)
cd dotnet/src/IncidentWarRoom.Functions && func start

# Check health
curl http://localhost:7071/api/health

# Trigger demo alert (Terminal 2)
curl -X POST http://localhost:7071/api/webhooks/alert \
  -H 'Content-Type: application/json' \
  -d @demo-alert-payload.json

# Stage anomaly (before demo)
bash demo/stage_anomaly.sh --vm-name gpu-training-vm --resource-group ai-dev-days-hackathon-eu

# Clean up after demo
bash demo/cleanup_demo.sh --vm-name gpu-training-vm --resource-group ai-dev-days-hackathon-eu
```

---

## Summary

This checklist ensures:
- ✅ Prerequisites verified (Azure auth, server running, Slack configured, VM staged)
- ✅ Recording setup prepared (software, windows, terminals, browser)
- ✅ All 6 demo segments captured in order with correct content
- ✅ Video exported in correct format and location
- ✅ Quality verified before submission

**Target:** Ready to record DEMO-02 in under 30 minutes of preparation + recording.
