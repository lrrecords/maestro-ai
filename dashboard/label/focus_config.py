# Example config for FOCUS brief data sources
FOCUS_DATA_SOURCES = [
    {
        "name": "approvals",
        "loader": "crews.base_crew.get_pending_approvals",
        "summary_key": "approvals"
    },
    {
        "name": "missions",
        "path": "data/missions/missions.json",
        "summary_key": "missions"
    },
    {
        "name": "upcoming_shows",
        "path": "live/data/shows.json",
        "summary_key": "upcoming_shows"
    },
    # Add more sources here (e.g., CRM, analytics)
]
