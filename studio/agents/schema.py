# studio/agents/schema.py
# Single source of truth for all STUDIO agent form schemas.
# All field identifiers use "key" to match agent FIELDS definitions in code.
# Be sure to update both backend agent and this schema if fields change!

STUDIO_AGENT_SCHEMAS = {

    "client": {
        "title": "CLIENT",
        "description": "Client relationship management, onboarding, and communication.",
        "fields": [
            {"name": "client_name",       "label": "Client Name",       "type": "text",     "required": True,  "placeholder": "e.g. Jordan Blake"},
            {"name": "contact_person",    "label": "Contact Person",    "type": "text",     "required": True,  "placeholder": "e.g. Alex Smith"},
            {"name": "email",             "label": "Email Address",     "type": "text",     "required": True,  "placeholder": "e.g. alex@example.com"},
            {"name": "phone",             "label": "Phone",             "type": "text",     "required": False, "placeholder": "Optional"},
            {"name": "company_label",     "label": "Company / Label",   "type": "text",     "required": False, "placeholder": "Optional"},
            {"name": "relationship_type", "label": "Relationship Type", "type": "select",   "required": True,
             "options": ["artist", "label", "producer", "publisher", "manager", "other"]},
            {"name": "budget",            "label": "Budget",            "type": "number",   "required": False, "placeholder": "e.g. 1200"},
            {"name": "notes",             "label": "Notes",             "type": "textarea", "required": False, "placeholder": "Special requirements or history"},
        ],
    },

    "session": {
        "title": "SESSION",
        "description": "Session planning, scheduling, and resource allocation.",
        "fields": [
            {"name": "session_name",  "label": "Session Name",    "type": "text",     "required": True,  "placeholder": "e.g. Jordan Blake — Tracking Day 1"},
            {"name": "artist",        "label": "Artist",          "type": "text",     "required": True,  "placeholder": "e.g. Jordan Blake"},
            {"name": "session_date",  "label": "Session Date",    "type": "text",     "required": True,  "placeholder": "e.g. 2026-04-12"},
            {"name": "start_time",    "label": "Start Time",      "type": "text",     "required": False, "placeholder": "e.g. 10:00"},
            {"name": "end_time",      "label": "End Time",        "type": "text",     "required": False, "placeholder": "e.g. 18:00"},
            {"name": "room",          "label": "Room",            "type": "text",     "required": False, "placeholder": "e.g. Studio A"},
            {"name": "engineer",      "label": "Engineer",        "type": "text",     "required": False, "placeholder": "e.g. Brett"},
            {"name": "session_type",  "label": "Session Type",    "type": "select",   "required": False,
             "options": ["tracking", "overdubs", "mixing", "mastering", "editing", "rehearsal", "other"]},
            {"name": "status",        "label": "Status",          "type": "select",   "required": False,
             "options": ["tentative", "booked", "completed", "cancelled"]},
            {"name": "notes",         "label": "Notes",           "type": "textarea", "required": False, "placeholder": "Goals, equipment needs, special requests"},
        ],
    },

    "sound": {
        "title": "SOUND",
        "description": "Catalogue management, sync licensing, and rights tracking.",
        "fields": [
            {"name": "track_title",    "label": "Track Title",    "type": "text",     "required": True,  "placeholder": "e.g. Midnight Signal"},
            {"name": "artist",         "label": "Artist",         "type": "text",     "required": True,  "placeholder": "e.g. Jordan Blake"},
            {"name": "album",          "label": "Album / EP",     "type": "text",     "required": False, "placeholder": "e.g. Debut EP"},
            {"name": "isrc",           "label": "ISRC",           "type": "text",     "required": False, "placeholder": "e.g. GB-ABC-26-00001"},
            {"name": "genre",          "label": "Genre",          "type": "text",     "required": False, "placeholder": "e.g. Indie Rock"},
            {"name": "bpm",            "label": "BPM",            "type": "number",   "required": False, "placeholder": "e.g. 120"},
            {"name": "key",            "label": "Key",            "type": "text",     "required": False, "placeholder": "e.g. C minor"},
            {"name": "duration",       "label": "Duration",       "type": "text",     "required": False, "placeholder": "e.g. 3:42"},
            {"name": "rights_owner",   "label": "Rights Owner",   "type": "text",     "required": False, "placeholder": "e.g. Jordan Blake Music Ltd"},
            {"name": "sync_status",    "label": "Sync Status",    "type": "select",   "required": False,
             "options": ["available", "in_negotiation", "licensed", "not_available"]},
            {"name": "notes",          "label": "Notes",          "type": "textarea", "required": False, "placeholder": "Placement history, restrictions, stems available"},
        ],
    },

    "signal": {
        "title": "SIGNAL",
        "description": "Studio marketing, social content, and brand positioning.",
        "fields": [
            {"name": "track_or_project", "label": "Track / Project",  "type": "text",     "required": True,  "placeholder": "e.g. Midnight Signal EP"},
            {"name": "key_message",      "label": "Key Message",      "type": "textarea", "required": True,  "placeholder": "What is the core story or hook to communicate?"},
            {"name": "target_audience",  "label": "Target Audience",  "type": "text",     "required": False, "placeholder": "e.g. 18–34 indie fans, UK/US"},
            {"name": "channels",         "label": "Channels",         "type": "text",     "required": False, "placeholder": "e.g. Instagram, TikTok, Spotify"},
            {"name": "tone",             "label": "Tone",             "type": "select",   "required": False,
             "options": ["professional", "casual", "hype", "intimate", "editorial"]},
            {"name": "release_date",     "label": "Release Date",     "type": "text",     "required": False, "placeholder": "e.g. 2026-05-01"},
            {"name": "budget",           "label": "Marketing Budget", "type": "number",   "required": False, "placeholder": "e.g. 500"},
            {"name": "notes",            "label": "Notes",            "type": "textarea", "required": False, "placeholder": "Campaign history, prior posts, brand notes"},
        ],
    },

    "craft": {
        "title": "CRAFT",
        "description": "Internal tooling and workflow automation.",
        "fields": [
            {"name": "tool_name",     "label": "Tool / Script Name", "type": "text",     "required": True,  "placeholder": "e.g. Invoice Generator"},
            {"name": "purpose",       "label": "Purpose",            "type": "textarea", "required": True,  "placeholder": "What problem does this tool solve?"},
            {"name": "trigger",       "label": "Trigger",            "type": "select",   "required": False,
             "options": ["manual", "scheduled", "webhook", "event-driven", "other"]},
            {"name": "owner",         "label": "Owner",              "type": "text",     "required": False, "placeholder": "e.g. Brett"},
            {"name": "stack",         "label": "Tech Stack",         "type": "text",     "required": False, "placeholder": "e.g. Python, n8n, Flask"},
            {"name": "status",        "label": "Status",             "type": "select",   "required": False,
             "options": ["idea", "in_progress", "active", "deprecated"]},
            {"name": "notes",         "label": "Notes",              "type": "textarea", "required": False, "placeholder": "Links, dependencies, known issues"},
        ],
    },

    "rate": {
        "title": "RATE",
        "description": "Pricing strategy, quote generation, and contracts.",
        "fields": [
            {"name": "client",            "label": "Client Name",      "type": "text",   "required": True,  "placeholder": "e.g. Jordan Blake"},
            {"name": "project_type",      "label": "Project Type",     "type": "select", "required": True,
             "options": ["tracking", "mixing", "mastering", "production", "full_album", "ep", "single", "sync", "other"]},
            {"name": "session_days",      "label": "Session Days",     "type": "number", "required": False, "placeholder": "e.g. 3"},
            {"name": "hours_per_day",     "label": "Hours / Day",      "type": "number", "required": False, "placeholder": "e.g. 8"},
            {"name": "num_tracks",        "label": "No. of Tracks",    "type": "number", "required": False, "placeholder": "e.g. 12"},
            {"name": "includes_mix",      "label": "Includes Mix",     "type": "select", "required": False,
             "options": ["yes", "no"]},
            {"name": "includes_master",   "label": "Includes Master",  "type": "select", "required": False,
             "options": ["yes", "no"]},
            {"name": "currency",          "label": "Currency",         "type": "select", "required": False,
             "options": ["GBP", "USD", "EUR", "AUD", "CAD"]},
            {"name": "discount_percent",  "label": "Discount %",       "type": "number", "required": False, "placeholder": "e.g. 10"},
            {"name": "notes",             "label": "Notes",            "type": "textarea", "required": False, "placeholder": "Special terms, rush fees, travel, etc."},
        ],
    },

    "mix": {
        "title": "MIX",
        "description": "Strategy synthesiser — coordinates all studio agents.",
        "fields": [
            {"name": "artist",        "label": "Artist / Project",  "type": "text",     "required": True,  "placeholder": "e.g. Jordan Blake"},
            {"name": "goal",          "label": "Primary Goal",      "type": "textarea", "required": True,  "placeholder": "e.g. Plan a 3-day tracking session, generate a quote, and prep marketing for debut EP release"},
            {"name": "timeframe",     "label": "Timeframe",         "type": "text",     "required": False, "placeholder": "e.g. Sessions start 2026-04-12"},
            {"name": "budget",        "label": "Budget",            "type": "number",   "required": False, "placeholder": "e.g. 5000"},
            {"name": "agents",        "label": "Agents to Include", "type": "text",     "required": False, "placeholder": "e.g. session, rate, signal — or leave blank for all"},
            {"name": "notes",         "label": "Notes",             "type": "textarea", "required": False, "placeholder": "Any context MIX should factor in"},
        ],
    },

    "ask_ai": {
        "title": "ASK_AI",
        "description": "Ask any question—get AI-powered studio, business, or music answers.",
        "fields": [
            {
                "name": "question",
                "label": "Your Question",
                "type": "textarea",
                "required": True,
                "placeholder": "Type any studio, music, or business question here…"
            },
            {
                "name": "context_notes",
                "label": "Context (optional)",
                "type": "textarea",
                "required": False,
                "placeholder": "Tell us what this relates to (project, artist, session…)"
            },
            {
                "name": "answer_style",
                "label": "Answer Style",
                "type": "select",
                "options": [
                    "concise",
                    "detailed",
                    "step_by_step",
                    "creative",
                    "industry_best_practices"
                ],
                "required": False
            }
        ],
    },
}