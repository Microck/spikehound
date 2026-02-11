# Phase 5 Plan 05-03 Summary: Demo Script and Recording Checklist

## Status

**Status:** Completed ✅
**Date:** 2026-02-11
**Duration:** ~10 minutes

## What Was Built

### 1. Timecoded Demo Script (`demo/script.md`)

Created a precise 2-minute demo script with 6 timed segments:

| Time | Segment | Duration | Key Points |
|---|---|---|---|
| 0:00 | Introduction | 10s | Project name, 3 prize categories |
| 0:10 | Architecture Overview | 20s | Show docs/architecture.png, explain 6 agents |
| 0:30 | Staged Anomaly | 15s | Azure VM, $12 vs $450, 36x spike |
| 0:45 | Trigger Investigation | 15s | `curl` webhook, show server logs |
| 1:00 | Multi-Agent Outputs | 20s | Slack message, read all fields |
| 1:20 | Human Approval | 20s | Click Approve, show approval logs |
| 1:40 | Remediation Execution | 20s | Follow-up Slack, VM stopped, $450/day savings |

**Features:**
- Exact one-liners to say during each segment
- Demo payload file embedded (ready for copy-paste)
- Pre-flight requirements (Azure auth, server running, Slack configured, VM staged)
- Conclusion summary: "Potential savings $13,500/month"

### 2. Recording Checklist (`demo/recording_checklist.md`)

Created comprehensive recording guide:

**Pre-Flight Checklist:**
- Environment setup (Azure CLI, server, Slack, demo VM)
- Recording preparation (software, terminals, browser, payload file)

**Per-Segment Checklist:**
- 6 segments match the script timecodes
- Each segment has specific verification points
- Expected one-liners to capture on video

**Post-Flight Checklist:**
- Video export verification (format, duration, resolution, size)
- Quality check (audio, text readability, diagram clarity)
- File placement (correct path: `demo/video.mp4`)

**Troubleshooting Section:**
- Common issues and fixes for terminal visibility, Slack buttons, VM status updates, file size

**Quick Reference Commands:**
- All necessary commands in one place (start server, health check, trigger alert, stage/cleanup)

## Verification

### Must-Haves

| Truth | Status | Evidence |
|---|---|---|
| A timecoded demo script exists and matches the staged scenario and system outputs | ✅ VERIFIED | `demo/script.md` contains 6 segments with exact timecodes matching `demo/scenario.md` flow |
| A recording checklist exists to produce a 2-minute end-to-end video (video recorded manually later) | ✅ VERIFIED | `demo/recording_checklist.md` includes pre-flight, per-segment, post-flight checklists |

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `demo/script.md` | Timecoded demo script | ✅ VERIFIED | 179 lines, 6 segments with timecodes 0:00-2:00 |
| `demo/recording_checklist.md` | Recording checklist (video is recorded manually later) | ✅ VERIFIED | 326 lines, comprehensive pre/post-flight checks |

## Key Links

| From | To | Via | Status | Details |
|---|---|---|---|
| `demo/script.md` | `demo/recording_checklist.md` | Recording checklist | ✅ WIRED | Script references checklist for segment-by-segment verification |
| `demo/script.md` | `demo/scenario.md` | Scenario reference | ✅ WIRED | Script timecodes align with scenario stages |

## Dependencies

**Depends on:** 05-01, 05-02 (Wave 1)
- ✅ 05-01 complete: Scenario documentation and staging scripts
- ✅ 05-02 complete: README and architecture diagram

## Success Criteria

**DEMO-02 met:** ✅ Ready to record DEMO-02 quickly: script + checklist exist (recording itself is manual)

- Demo script is timecoded to fit exactly 2:00 minutes
- Recording checklist is actionable and includes troubleshooting
- Both files are consistent with the staged scenario and system architecture
- No manual recording is required to use the checklist (the checklist enables manual recording later)

## Issues

None. All tasks completed successfully.

## Next Steps

- Phase 5 is complete. All 3 plans executed:
  - 05-01: Staged demo scenario ✅
  - 05-02: README and architecture diagram ✅
  - 05-03: Demo script and recording checklist ✅
- Run Phase 5 verification
- Update STATE.md and ROADMAP.md to mark Phase 5 Complete
- Total project progress: 18/18 plans (100%)

---

_Completed: 2026-02-11_
_Executor: Claude (gsd-executor)_
