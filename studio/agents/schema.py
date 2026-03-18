# studio/agents/schema.py
# Single source of truth for all STUDIO agent form schemas.
# All field identifiers use "key" to match agent FIELDS definitions.

STUDIO_AGENT_SCHEMAS = {

    "client": {
        "title": "CLIENT",
        "description": "Client relationship management, onboarding, and communication.",
        "fields": [
            {"key": "client_name",       "label": "Client Name",       "type": "text",     "required": True,  "placeholder": "e.g. Jordan Blake"},
            {"key": "contact_person",    "label": "Contact Person",    "type": "text",     "required": True,  "placeholder": "e.g. Alex Smith"},
            {"key": "email",             "label": "Email Address",     "type": "text",     "required": True,  "placeholder": "e.g. alex@example.com"},
            {"key": "phone",             "label": "Phone",             "type": "text",     "required": False, "placeholder": "Optional"},
            {"key": "company_label",     "label": "Company / Label",   "type": "text",     "required": False, "placeholder": "Optional"},
            {"key": "relationship_type", "label": "Relationship Type", "type": "select",   "required": True,
             "options": ["artist", "label", "producer", "publisher", "manager", "other"]},
            {"key": "budget",            "label": "Budget",            "type": "number",   "required": False, "placeholder": "e.g. 1200"},
            {"key": "notes",             "label": "Notes",             "type": "textarea", "required": False, "placeholder": "Special requirements or history"},
        ],
    },

    "session": {
        "title": "SESSION",
        "description": "Session planning, scheduling, and resource allocation.",
        "fields": [
            {"key": "session_name",  "label": "Session Name",   "type": "text",     "required": True,  "placeholder": "e.g. Jordan Blake — Tracking Day 1"},
            {"key": "artist",        "label": "Artist",         "type": "text",     "required": True,  "placeholder": "e.g. Jordan Blake"},
            {"key": "session_date",  "label": "Session Date",   "type": "text",     "required": True,  "placeholder": "e.g. 2026-04-12"},
            {"key": "start_time",    "label": "Start Time",     "type": "text",     "required": False, "placeholder": "e.g. 10:00"},
            {"key": "end_time",      "label": "End Time",       "type": "text",     "required": False, "placeholder": "e.g. 18:00"},
            {"key": "room",          "label": "Room",           "type": "text",     "required": False, "placeholder": "e.g. Studio A"},
            {"key": "engineer",      "label": "Engineer",       "type": "text",     "required": False, "placeholder": "e.g. Brett"},
            {"key": "session_type",  "label": "Session Type",  "type": "select",   "required": False,
             "options": ["tracking", "overdubs", "mixing", "mastering", "editing", "rehearsal", "other"]},
            {"key": "status",        "label": "Status",         "type": "select",   "required": False,
             "options": ["tentative", "booked", "confirmed", "completed", "cancelled"]},
            {"key": "notes",         "label": "Notes",          "type": "textarea", "required": False, "placeholder": "Goals, equipment needs, special requests"},
        ],
    },

    "sound": {
        "title": "SOUND",
        "description": "Catalogue management, sync licensing, and rights tracking.",
        "fields": [
            {"key": "track_title",    "label": "Track Title",    "type": "text",     "required": True,  "placeholder": "e.g. Midnight Signal"},
            {"key": "artist",         "label": "Artist",         "type": "text",     "required": True,  "placeholder": "e.g. Jordan Blake"},
            {"key": "album",          "label": "Album / EP",     "type": "text",     "required": False, "placeholder": "e.g. Debut EP"},
            {"key": "isrc",           "label": "ISRC",           "type": "text",     "required": False, "placeholder": "e.g. GB-ABC-26-00001"},
            {"key": "genre",          "label": "Genre",          "type": "text",     "required": False, "placeholder": "e.g. Indie Rock"},
            {"key": "bpm",            "label": "BPM",            "type": "number",   "required": False, "placeholder": "e.g. 120"},
            {"key": "key",            "label": "Key",            "type": "text",     "required": False, "placeholder": "e.g. C minor"},
            {"key": "duration",       "label": "Duration",       "type": "text",     "required": False, "placeholder": "e.g. 3:42"},
            {"key": "rights_owner",   "label": "Rights Owner",   "type": "text",     "required": False, "placeholder": "e.g. Jordan Blake Music Ltd"},
            {"key": "sync_status",    "label": "Sync Status",    "type": "select",   "required": False,
             "options": ["available", "in_negotiation", "licensed", "not_available"]},
            {"key": "notes",          "label": "Notes",          "type": "textarea", "required": False, "placeholder": "Placement history, restrictions, stems available"},
        ],
    },

    "signal": {
        "title": "SIGNAL",
        "description": "Studio marketing, social content, and brand positioning.",
        "fields": [
            {"key": "track_or_project", "label": "Track / Project",  "type": "text",     "required": True,  "placeholder": "e.g. Midnight Signal EP"},
            {"key": "key_message",      "label": "Key Message",      "type": "textarea", "required": True,  "placeholder": "What is the core story or hook to communicate?"},
            {"key": "target_audience",  "label": "Target Audience",  "type": "text",     "required": False, "placeholder": "e.g. 18–34 indie fans, UK/US"},
            {"key": "channels",         "label": "Channels",         "type": "text",     "required": False, "placeholder": "e.g. Instagram, TikTok, Spotify"},
            {"key": "tone",             "label": "Tone",             "type": "select",   "required": False,
             "options": ["professional", "casual", "hype", "intimate", "editorial"]},
            {"key": "release_date",     "label": "Release Date",     "type": "text",     "required": False, "placeholder": "e.g. 2026-05-01"},
            {"key": "budget",           "label": "Marketing Budget", "type": "number",   "required": False, "placeholder": "e.g. 500"},
            {"key": "notes",            "label": "Notes",            "type": "textarea", "required": False, "placeholder": "Campaign history, prior posts, brand notes"},
        ],
    },

    "craft": {
        "title": "CRAFT",
        "description": "Internal tooling and workflow automation.",
        "fields": [
            {"key": "tool_name",     "label": "Tool / Script Name", "type": "text",     "required": True,  "placeholder": "e.g. Invoice Generator"},
            {"key": "purpose",       "label": "Purpose",            "type": "textarea", "required": True,  "placeholder": "What problem does this tool solve?"},
            {"key": "trigger",       "label": "Trigger",            "type": "select",   "required": False,
             "options": ["manual", "scheduled", "webhook", "event-driven", "other"]},
            {"key": "owner",         "label": "Owner",              "type": "text",     "required": False, "placeholder": "e.g. Brett"},
            {"key": "stack",         "label": "Tech Stack",         "type": "text",     "required": False, "placeholder": "e.g. Python, n8n, Flask"},
            {"key": "status",        "label": "Status",             "type": "select",   "required": False,
             "options": ["idea", "in_progress", "active", "deprecated"]},
            {"key": "notes",         "label": "Notes",              "type": "textarea", "required": False, "placeholder": "Links, dependencies, known issues"},
        ],
    },

    "rate": {
        "title": "RATE",
        "description": "Pricing strategy, quote generation, and contracts.",
        "fields": [
            {"key": "client",            "label": "Client Name",      "type": "text",   "required": True,  "placeholder": "e.g. Jordan Blake"},
            {"key": "project_type",      "label": "Project Type",     "type": "select", "required": True,
             "options": ["tracking", "mixing", "mastering", "production", "full_album", "ep", "single", "sync", "other"]},
            {"key": "session_days",      "label": "Session Days",     "type": "number", "required": False, "placeholder": "e.g. 3"},
            {"key": "hours_per_day",     "label": "Hours / Day",      "type": "number", "required": False, "placeholder": "e.g. 8"},
            {"key": "num_tracks",        "label": "No. of Tracks",    "type": "number", "required": False, "placeholder": "e.g. 12"},
            {"key": "includes_mix",      "label": "Includes Mix",     "type": "select", "required": False,
             "options": ["yes", "no"]},
            {"key": "includes_master",   "label": "Includes Master",  "type": "select", "required": False,
             "options": ["yes", "no"]},
            {"key": "currency",          "label": "Currency",         "type": "select", "required": False,
             "options": ["GBP", "USD", "EUR", "AUD", "CAD"]},
            {"key": "discount_percent",  "label": "Discount %",       "type": "number", "required": False, "placeholder": "e.g. 10"},
            {"key": "notes",             "label": "Notes",            "type": "textarea","required": False, "placeholder": "Special terms, rush fees, travel, etc."},
        ],
    },

    "mix": {
        "title": "MIX",
        "description": "Strategy synthesiser — coordinates all studio agents.",
        "fields": [
            {"key": "artist",        "label": "Artist / Project",  "type": "text",     "required": True,  "placeholder": "e.g. Jordan Blake"},
            {"key": "goal",          "label": "Primary Goal",      "type": "textarea", "required": True,  "placeholder": "e.g. Plan a 3-day tracking session, generate a quote, and prep marketing for debut EP release"},
            {"key": "timeframe",     "label": "Timeframe",         "type": "text",     "required": False, "placeholder": "e.g. Sessions start 2026-04-12"},
            {"key": "budget",        "label": "Budget",            "type": "number",   "required": False, "placeholder": "e.g. 5000"},
            {"key": "agents",        "label": "Agents to Include", "type": "text",     "required": False, "placeholder": "e.g. session, rate, signal — or leave blank for all"},
            {"key": "notes",         "label": "Notes",             "type": "textarea", "required": False, "placeholder": "Any context MIX should factor in"},
        ],
    },

}