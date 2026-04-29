Coding Agent Startup Flow  
Use this at the beginning of every session (agent or human) after initialization is complete.

Fixed Startup Template  
- Run pwd and confirm the repository root.  
- Read claude-progress.md.  
- Read feature_list.json.  
- Review recent commits with git log --oneline -5.  
- Run ./init.sh (or start_maestro_session.ps1 on Windows).  
- Run python test_agents.py for baseline verification.  
- If the baseline is broken, fix that first.  
- Select the highest-priority unfinished feature.  
- Work only on that feature until it is verified or explicitly blocked.

Why This Order Matters  
- pwd prevents accidental work in the wrong directory.  
- progress and feature files recover durable state before new edits begin.  
- recent commits explain what changed most recently.  
- init.sh/start_maestro_session.ps1 standardizes startup instead of relying on memory.  
- baseline verification (python test_agents.py) catches broken starting states before new work hides them.

End-Of-Session Mirror  
The same session should end by:  
- recording progress in claude-progress.md  
- updating feature state in feature_list.json  
- writing a handoff in session_handoff.md if needed  
- committing safe work  
- leaving a clean restart path (see Clean State Checklist.md)