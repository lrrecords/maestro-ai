# MAESTRO Project Structure

## Current Structure

maestro-ai/
├── scripts/               # Main executable scripts
│   ├── maestro_with_context.py      (v0.4 - basic)
│   ├── maestro_with_memory.py       (v0.5 - enhanced)
│   └── bridge_artist_intelligence.py (artist management)
│
├── agents/                # Individual agent modules (coming soon)
│   ├── bridge.py         # Artist Relations Director
│   ├── vinyl.py          # Music Operations Manager
│   ├── echo.py           # Content & Marketing Chief
│   ├── atlas.py          # Business Intelligence Officer
│   ├── forge.py          # Development & Automation Engineer
│   └── sage.py           # Personal Assistant & Life Manager
│
├── data/                  # Business data and context
│   ├── lr_records_context.json
│   ├── brett_communication_profile.json
│   ├── maestro_commands_reference.md
│   ├── maestro_build_progress.md
│   ├── FULL_CONTEXT_HANDOFF.md
│   │
│   ├── artists/          # Artist profiles
│   │   ├── brendananis_monster.json
│   │   └── jerry_mane.json
│   │
│   └── ai_conversations/ # Chat history and memory
│       ├── claude_maestro_full_build_dec15.txt
│       └── memory_index.json
│
├── memory/                # Long-term memory system (planned)
│   ├── embeddings/       # Vector embeddings for semantic search
│   ├── conversations/    # Processed conversation archives
│   └── knowledge_base/   # Extracted insights and patterns
│
├── workflows/             # Automation workflows (planned)
│   ├── n8n/             # n8n workflow JSONs
│   ├── artist_checkin/  # Artist relationship workflows
│   ├── content/         # Content creation workflows
│   └── release/         # Release coordination workflows
│
├── docs/                  # Documentation
│   ├── user_guide.md
│   ├── api_reference.md
│   ├── product_roadmap.md
│   └── customer_onboarding.md
│
├── tests/                 # Unit tests (future)
│
├── venv/                  # Python virtual environment
│
├── .gitignore            # Git ignore rules
├── README.md             # Project overview
├── LICENSE               # License file
├── requirements.txt      # Python dependencies
└── PROJECT_STRUCTURE.md  # This file

## Planned Additions

### Phase 1: Execution Layer (Week 1)
- `workflows/n8n/` - Workflow automation configs
- `scripts/automations.py` - Automation orchestrator

### Phase 2: Database (Month 1)
- `database/` - PostgreSQL schema and migrations
- `scripts/db_manager.py` - Database utilities

### Phase 3: Web Interface (Quarter 1)
- `frontend/` - React/Vue web interface
- `backend/` - FastAPI server
- `api/` - REST API endpoints

### Phase 4: Multi-Label (Quarter 2)
- `templates/` - Multi-tenant templates
- `config/` - Per-label configuration