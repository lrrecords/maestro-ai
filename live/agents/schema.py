"""
LIVE agent context schemas used by the dashboard Run modal.
"""

LIVE_AGENT_SCHEMAS: dict[str, dict] = {
    "book": {
        "title": "BOOK",
        "description": "Venues, holds, deal negotiation, contract tracking.",
        "fields": [
            {"name": "artist", "label": "Artist", "type": "text", "required": True, "placeholder": "Example Artist"},
            {"name": "territory", "label": "Territory", "type": "text", "placeholder": "UK / Europe / US"},
            {"name": "dates", "label": "Target dates (comma-separated)", "type": "text", "placeholder": "2026-04-02, 2026-04-05"},
            {"name": "capacity", "label": "Min venue capacity", "type": "number", "placeholder": "250"},
            {"name": "deal_type", "label": "Deal type", "type": "select", "options": ["flat", "versus", "guarantee"]},
            {"name": "notes", "label": "Notes", "type": "textarea", "placeholder": "Constraints, dream venues, supports..."},
        ],
    },
    "merch": {
        "title": "MERCH",
        "description": "Merchandise planning, inventory, and settlement.",
        "fields": [
            {"name": "artist", "label": "Artist", "type": "text", "required": True},
            {"name": "expected_attendance", "label": "Expected attendance", "type": "number", "placeholder": "300"},
            {"name": "show_dates", "label": "Show dates (comma-separated)", "type": "text"},
            {"name": "price_points", "label": "Price points (comma-separated)", "type": "text", "placeholder": "10, 25, 40"},
            {"name": "existing_inventory", "label": "Existing inventory (free text)", "type": "textarea", "placeholder": "T-shirts: 40, Hoodies: 20, Vinyl: 15"},
        ],
    },
    "promo": {
        "title": "PROMO",
        "description": "Marketing and promotional strategy.",
        "fields": [
            {"name": "artist", "label": "Artist", "type": "text", "required": True},
            {"name": "cities", "label": "Cities (comma-separated)", "type": "text"},
            {"name": "show_dates", "label": "Show dates (comma-separated)", "type": "text"},
            {"name": "target_audience", "label": "Target audience", "type": "text", "placeholder": "Fans of X / genre / scene"},
            {"name": "budget", "label": "Budget", "type": "number", "placeholder": "500"},
            {"name": "platforms", "label": "Platforms (comma-separated)", "type": "text", "placeholder": "instagram, tiktok"},
        ],
    },
    "route": {
        "title": "ROUTE",
        "description": "Tour routing and travel optimisation.",
        "fields": [
            {"name": "home_city", "label": "Home city", "type": "text", "placeholder": "London"},
            {"name": "cities", "label": "Cities (comma-separated)", "type": "text", "placeholder": "London, Manchester, Glasgow"},
            {"name": "start_date", "label": "Start date", "type": "text", "placeholder": "2026-04-02"},
            {"name": "end_date", "label": "End date", "type": "text", "placeholder": "2026-04-15"},
            {"name": "transport_mode", "label": "Transport", "type": "select", "options": ["van", "bus", "train", "fly", "mixed"]},
            {"name": "max_drive_hours", "label": "Max drive hours/day", "type": "number", "placeholder": "6"},
        ],
    },
    "settle": {
        "title": "SETTLE",
        "description": "Financial settlement and reconciliation.",
        "fields": [
            {"name": "currency", "label": "Currency", "type": "select", "options": ["GBP", "USD", "EUR"]},
            {"name": "gross_box_office", "label": "Gross box office", "type": "number", "placeholder": "2500"},
            {"name": "deal_memo", "label": "Deal memo (free text)", "type": "textarea", "placeholder": "Guarantee, splits, merch cuts..."},
            {"name": "expenses", "label": "Expenses (free text)", "type": "textarea", "placeholder": "Crew, fuel, hotel, per diems..."},
        ],
    },
    "rider": {
        "title": "RIDER",
        "description": "Technical and hospitality rider management.",
        "fields": [
            {"name": "artist", "label": "Artist", "type": "text", "required": True},
            {"name": "venue_specs", "label": "Venue specs", "type": "textarea", "placeholder": "PA, stage size, load-in, FOH position..."},
            {"name": "stage_plot", "label": "Stage plot / inputs", "type": "textarea", "placeholder": "Kick, Snare, OH L/R, Vox, DI..."},
            {"name": "hospitality_requirements", "label": "Hospitality", "type": "textarea", "placeholder": "Water, towels, meals, green room..."},
        ],
    },
    "tour": {
        "title": "TOUR",
        "description": "Strategy synthesiser — coordinates all LIVE agents.",
        "fields": [
            {"name": "artist", "label": "Artist", "type": "text", "required": True},
            {"name": "objective", "label": "Objective", "type": "text", "placeholder": "Build audience / profit / support release"},
            {"name": "territory", "label": "Territory", "type": "text", "placeholder": "UK"},
            {"name": "date_window", "label": "Date window", "type": "text", "placeholder": "2026-04-01 to 2026-04-30"},
            {"name": "constraints", "label": "Constraints", "type": "textarea", "placeholder": "No Mondays, avoid long drives, budget cap..."},
        ],
    },
}