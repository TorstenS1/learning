# Comparison: ALIS Specification (`alis.md`) vs. Current Implementation

**Analysis Date:** 2025-11-27
**Source of Truth:** `alis.md` (Master Specification Document)

## 1. Data Models & Architecture

| Feature | `alis.md` Specification | Current Implementation | Status |
| :--- | :--- | :--- | :--- |
| **User Profile** | `stylePreference`, `complexityLevel`, `paceWPM`, `P2Enabled`, `P6Enabled`, `lastActiveGoalId` | `stylePreference`, `complexityLevel`, `paceWPM` | ⚠️ Missing: `P2Enabled`, `P6Enabled`, `lastActiveGoalId` |
| **Goal** | `name`, `fachgebiet`, `targetDate`, `bloomLevel`, `messMetrik`, `status` | `id`, `name` (implicit) | ⚠️ Missing: `targetDate`, `fachgebiet`, `bloomLevel`, `messMetrik`, `status` (only ID and name present) |
| **Logs** | `timestamp`, `eventType`, `conceptId`, `emotionFeedback`, `testScore`, `kognitiveDiskrepanz` | Not Implemented | ❌ Missing Logging System |
| **Architecture** | Hybrid Gemini LLM + Firestore | Structure exists, using simulations | ✅ Structure present, needs integration |

## 2. Workflow Gaps

| Phase | `alis.md` Specification | Current Implementation | Status |
| :--- | :--- | :--- | :--- |
| **P1** | SMART Goal Contract | Implemented | ✅ |
| **P2** | Vorwissenstest (Pre-test) | Not in graph | ❌ Missing Workflow Integration |
| **P3** | Path Creation & Expert Review | Implemented (UI supports skips) | ✅ |
| **P4** | Material Generation (Grounding) | Implemented (Grounding flag exists) | ✅ |
| **P5** | Learning Phase (Chat) | Implemented | ✅ |
| **P5.5** | Dynamic Remediation (Loop) | Implemented (Path Surgery) | ✅ |
| **P6** | Verständnisprüfung (Test) | Implemented (Generation only) | ⚠️ Scoring logic missing |
| **P7** | Adaption & Motivation (Automated) | Affective part in `process_chat` | ⚠️ Auto-progression logic based on test scores missing |

## 3. Agent Prompts

The prompts in `alis.md` are identical to those in `backend/agents/prompts.py`. We are good here.

## 4. Conclusion & Next Steps

The `alis.md` document is confirmed as the master specification and reinforces the findings from previous PDF analyses. The current implementation is a solid MVP for the "Happy Path" and "Remediation Loop," but significant gaps exist in data model richness, comprehensive logging, and automated workflow logic.

### Critical Gaps Identified 🔍

*   **Missing Data Fields**: User profile flags (`P2Enabled`, `P6Enabled`, `lastActiveGoalId`), Goal metadata (`targetDate`, `fachgebiet`, `bloomLevel`, `messMetrik`, `status`).
*   **Missing Logging**: The `/logs/` endpoint and structured logging for `emotionFeedback`, `testScore`, `kognitiveDiskrepanz` are absent.
*   **Missing Logic**: P2 workflow integration and P7 automated progression based on test scores are not fully implemented.

### Recommended Next Steps 🛠️

1.  **Address Data Model Gaps**: Update `backend/models/state.py` to include the missing fields from `alis.md`. This is foundational for subsequent features.
2.  **Implement Logging Service**: Develop the logging service to track user progress and feedback.
3.  **Enhance P7 Logic**: Implement the automated progression/remediation logic based on test scores.

