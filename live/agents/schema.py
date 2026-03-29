"""
LIVE agent context schemas used by the dashboard Run modal.
(Standardised fields and types to exactly match all LIVE agents.)
"""

LIVE_AGENT_SCHEMAS: dict[str, dict] = {
    "book": {
        "title": "BOOK",
        "description": "Venues, holds, deal negotiation, contract tracking.",
        "fields": [
            {"name": "artist",    "label": "Artist",        "type": "text",   "required": True, "placeholder": "Example Artist"},
            {"name": "territory", "label": "Territory",     "type": "text",   "placeholder": "UK / Europe / US"},
            {"name": "dates",     "label": "Target Dates",  "type": "tags",   "placeholder": "2026-04-02, 2026-04-05"},
            {"name": "capacity",  "label": "Min. Capacity", "type": "number", "placeholder": "250"},
            {"name": "deal_type", "label": "Deal Type",     "type": "select", "options": ["flat", "versus", "guarantee"]},
            {"name": "notes",     "label": "Notes",         "type": "textarea", "placeholder": "Constraints, dream venues, supports..."},
        ],
    },
    "merch": {
        "title": "MERCH",
        "description": "Merchandise planning, inventory, and settlement.",
        "fields": [
            {"name": "artist",              "label": "Artist",              "type": "text",     "required": True, "placeholder": "e.g. Bicep"},
            {"name": "expected_attendance", "label": "Expected Attendance", "type": "number",   "placeholder": "300"},
            {"name": "show_dates",          "label": "Show Dates",          "type": "tags",     "placeholder": "2026-04-02, 2026-04-15"},
            {"name": "price_points",        "label": "Price Points",        "type": "text",     "placeholder": "10, 25, 40"},
            {"name": "existing_inventory",  "label": "Existing Inventory",  "type": "textarea", "placeholder": "T-shirts: 40, Hoodies: 20, Vinyl: 15"},
        ],
    },
    "promo": {
    "title": "PROMO",
    "description": "Marketing and promotional strategy.",
    "fields": [
        {"name": "artist",           "label": "Artist",           "type": "text",    "required": True, "placeholder": "e.g. Bicep"},
        {"name": "cities",           "label": "Cities",           "type": "tags",    "placeholder": "London, Manchester, Glasgow"},
        {"name": "show_dates",       "label": "Show Dates",       "type": "tags",    "placeholder": "2026-04-02, 2026-04-15"},
        {"name": "target_audience",  "label": "Target Audience",  "type": "text",    "placeholder": "Fans of X / genre / scene"},
        {"name": "budget",           "label": "Budget",           "type": "number",  "placeholder": "500"},
        {"name": "platforms",        "label": "Platforms",        "type": "tags",    "placeholder": "instagram, tiktok"},
        {"name": "objectives",       "label": "Objectives",       "type": "textarea","placeholder": "Sell out first three dates, grow mailing list, etc."},
    ],
},
    "route": {
        "title": "ROUTE",
        "description": "Tour routing and travel optimisation.",
        "fields": [
            {"name": "home_city",      "label": "Home City",      "type": "text",   "placeholder": "London", "required": True},
            {"name": "cities",         "label": "Cities",         "type": "tags",   "placeholder": "London, Manchester, Glasgow", "required": True},
            {"name": "start_date",     "label": "Start Date",     "type": "text",   "placeholder": "2026-04-02"},
            {"name": "end_date",       "label": "End Date",       "type": "text",   "placeholder": "2026-04-15"},
            {"name": "transport_mode", "label": "Transport",      "type": "select", "options": ["van", "bus", "train", "fly", "mixed"]},
            {"name": "max_drive_hours","label": "Max drive hours/day", "type": "number", "placeholder": "6"},
        ],
    },
    "settle": {
        "title": "SETTLE",
        "description": "Financial settlement and reconciliation.",
        "fields": [
            {"name": "currency",           "label": "Currency",             "type": "select",   "options": ["GBP", "USD", "EUR"]},
            {"name": "gross_box_office",   "label": "Gross Box Office",     "type": "number",   "placeholder": "2500"},
            {"name": "deal_memo",          "label": "Deal Memo",            "type": "textarea", "placeholder": "Guarantee, splits, merch cuts..."},
            {"name": "expenses",           "label": "Deductible Expenses",  "type": "number",   "placeholder": "1500"},
        ],
    },
    "rider": {
        "title": "RIDER",
        "description": "Technical and hospitality rider management.",
        "fields": [
            {"name": "artist",                      "label": "Artist",                "type": "text",     "required": True, "placeholder": "e.g. Bicep"},
            {"name": "show_dates",                  "label": "Show Dates",            "type": "tags",     "placeholder": "e.g. 2026-04-02"},
            {"name": "stage_plot",                  "label": "Stage Plot Notes",      "type": "textarea", "placeholder": "e.g. 2x CDJs, 1x DJM mixer, monitors L/R"},
            {"name": "hospitality_requirements",    "label": "Hospitality Notes",     "type": "textarea", "placeholder": "e.g. Vegan catering, 2 private dressing rooms"},
            {"name": "guest_list",                  "label": "Guest List",            "type": "textarea", "placeholder": "Per show: City and names, e.g. Perth: Jason M, Randy L"},
            {"name": "security_notes",              "label": "Security Notes",        "type": "textarea", "placeholder": "Afterparty protocols, anonymity, meet-and-greet"},
            {"name": "logistics_notes",             "label": "Logistics Notes",       "type": "textarea", "placeholder": "Parking for van, load-in, hotel near venue"},
        ],
    },
    "tour": {
        "title": "TOUR",
        "description": "Strategy synthesiser — coordinates all LIVE agents.",
        "fields": [
            {"name": "artist",      "label": "Artist",       "type": "text",     "required": True, "placeholder": "e.g. Bicep"},
            {"name": "territory",   "label": "Territory",    "type": "text",     "placeholder": "UK"},
            {"name": "start_date",  "label": "Start Date",   "type": "text",     "placeholder": "2026-04-01"},
            {"name": "end_date",    "label": "End Date",     "type": "text",     "placeholder": "2026-04-30"},
            {"name": "show_count",  "label": "Target Shows", "type": "number",   "placeholder": "10"},
            {"name": "notes",       "label": "Notes",        "type": "textarea", "placeholder": "Constraints, priorities, any context"},
        ],
    },
}