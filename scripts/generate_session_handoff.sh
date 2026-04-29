#!/bin/bash
# Script to generate a draft session_handoff.md based on recent changes

git diff --name-only HEAD~1 > changed_files.txt

echo "Session Handoff" > session_handoff.md

echo "\nVerified Now" >> session_handoff.md
echo "What is currently working:" >> session_handoff.md
echo "What verification actually ran (e.g., python test_agents.py):" >> session_handoff.md

echo "\nChanged This Session" >> session_handoff.md
echo "Code or behavior added:" >> session_handoff.md
cat changed_files.txt >> session_handoff.md
echo "Infrastructure or harness changes:" >> session_handoff.md

echo "\nBroken Or Unverified" >> session_handoff.md
echo "Known defect:" >> session_handoff.md
echo "Unverified path:" >> session_handoff.md
echo "Risk for the next session:" >> session_handoff.md

echo "\nNext Best Step" >> session_handoff.md
echo "Highest-priority unfinished feature:" >> session_handoff.md
echo "Why it is next:" >> session_handoff.md
echo "What counts as passing:" >> session_handoff.md
echo "What must not change during that step:" >> session_handoff.md

echo "\nCommands" >> session_handoff.md
echo "Startup: ./init.sh (or start_maestro_session.ps1)" >> session_handoff.md
echo "Verification: python test_agents.py" >> session_handoff.md
echo "Focused debug command:" >> session_handoff.md

echo "---" >> session_handoff.md
echo "Reminder: Update feature_list.json and claude-progress.md at the end of each session for continuity." >> session_handoff.md

rm changed_files.txt
