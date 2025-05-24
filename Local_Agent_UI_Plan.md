# Local Agent Web UI & User-Driven PII Review Plan

## Motivation
To maximize privacy, transparency, and user control, the local agent will provide a web-based UI (running on localhost) for reviewing and confirming PII masking decisions. This approach ensures:
- All data stays on the user's machine
- Users can see and override what is masked
- The system is flexible and works for any site/app

## High-Level Workflow
1. **User opens the local web UI** (e.g., http://localhost:5000)
2. **User enters the target URL** and clicks "Create Application Map"
3. **Agent scans the site, runs PII detection, and builds the application map**
4. **Web UI displays detected PII and all fields (page-wise):**
    - User can approve/reject detected PII
    - User can search and manually select additional fields to mask
5. **User clicks "Confirm Application Map"**
    - Only then is the final, masked map saved and used for downstream processing

## Recording User Feedback for ML Training
- When users flag, approve, or reject fields for masking, **these actions (field names, types, and masking decisions) are recorded as metadata** for future ML model training.
- **No actual user data or field values are saved or sent out.** Only the information about which fields were selected or masked is stored.
- This metadata is kept in the local agent and can be sent (with user consent) to the web app for improving the ML model.
- This ensures user privacy: **no sensitive content or PII values ever leave the user's system—only anonymized feedback and selections.**

## Future Extensibility
- The UI and backend API should be modular for easy extension
- In production, the UI can be wrapped in Electron or replaced with a native app if needed
- The same review/override flow can be integrated with the main web app in the future

## User Warning & Limitations
**Important:**
- The system uses automated PII detection (Presidio, regex, etc.) and user review to mask sensitive data.
- If any PII is missed by both the automated scan and user selection, it may be included in the final application map and could be sent to the web app or LLM.
- **The end user is responsible for reviewing and confirming all sensitive fields.**
- The current system is an MVP and may not catch all PII. Use with caution for sensitive or regulated data.
- **User feedback and masking actions are recorded for ML training, but no actual user data or field values are ever saved or sent out.**

## Notes for Future Development
- Add a feedback mechanism for users to report missed PII or false positives
- Consider logging masking decisions (with user consent) for future ML model training
- Explore more advanced UI/UX for large or complex application maps
- Plan for installer/native app packaging after MVP validation

---

**Summary:**
- Local agent will use a local web UI for PII review and confirmation
- User-driven masking is required for maximum privacy and flexibility
- User is responsible for confirming all sensitive fields before finalizing the application map
- User feedback (field selections, masking actions) is recorded for ML training, but no user data/values are ever saved or sent out
- Future improvements will focus on automation, feedback, and packaging 