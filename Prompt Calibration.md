Prompt Calibration  
For maestro-ai, HARNESS_ENGINEERING_WORKFLOW.md serves as the root instructions file. Root instructions should define the operating frame, not every possible move. Both agents and humans should follow this guidance.

-Keep In The Root File (HARNESS_ENGINEERING_WORKFLOW.md)  
- repository purpose and scope  
- startup path (e.g., ./init.sh or start_maestro_session.ps1)  
- verification path (e.g., python test_agents.py)  
- non-negotiable constraints  
- required state artifacts (feature_list.json, claude-progress.md, etc.)  
- end-of-session rules

Move Out Of The Root File  
- long historical edge cases  
- topic-specific implementation details  
- local architecture notes that belong near the code  
- examples that only apply to one subsystem

Working Rule  
The root file (HARNESS_ENGINEERING_WORKFLOW.md) should help a fresh session orient itself quickly. If the file is becoming a dumping ground for every past failure, split the detail into smaller documents (e.g., session_handoff.md, Clean State Checklist.md) and link to them instead.