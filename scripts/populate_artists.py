import csv
import json
import os
import sys
from datetime import datetime

# Adjust path to run from project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTISTS_DIR = os.path.join(BASE_DIR, "data", "artists")


def name_to_filename(name):
    """Convert 'DJ Snake Eyes' → 'dj_snake_eyes.json'"""
    return (
        name.lower()
        .replace(" ", "_")
        .replace("'", "")
        .replace("-", "_")
        .replace(".", "")
        + ".json"
    )


def parse_list_field(value, delimiter=";"):
    """Split semicolon-separated fields into a list"""
    if not value or not value.strip():
        return []
    return [item.strip() for item in value.split(delimiter) if item.strip()]


def create_artist_profile(row):
    """Convert a CSV row dict into a full MAESTRO artist JSON profile"""
    name = row.get("name", "").strip()

    profile = {
        "artist_info": {
            "name": name,
            "email": row.get("email", "").strip(),
            "phone": row.get("phone", "").strip(),
            "instagram": row.get("instagram", "").strip(),
            "genre": row.get("genre", "").strip(),
            "label_status": row.get("label_status", "signed").strip(),
            "priority_level": row.get("priority_level", "medium").strip(),
            "preferred_contact_method": row.get("preferred_contact_method", "Email").strip(),
            "bio": row.get("bio", "").strip(),
            "date_added": datetime.now().strftime("%Y-%m-%d"),
        },
        "current_projects": parse_list_field(row.get("current_projects", "")),
        "goals": parse_list_field(row.get("goals", "")),
        "notes": row.get("notes", "").strip(),
        "communication_history": [],
        "action_items": [],
        "health_score": None,
        "last_contact": None,
        "follow_up_needed": False,
    }

    return profile


def generate_template(output_path):
    """Generate a blank CSV template with one example row"""
    headers = [
        "name",
        "email",
        "phone",
        "instagram",
        "genre",
        "label_status",
        "priority_level",
        "preferred_contact_method",
        "bio",
        "current_projects",
        "goals",
        "notes",
    ]

    example = {
        "name": "Example Artist",
        "email": "artist@gmail.com",
        "phone": "0400 000 000",
        "instagram": "@exampleartist",
        "genre": "Hip-Hop",
        "label_status": "signed",          # signed / unsigned / distributed
        "priority_level": "high",          # high / medium / low
        "preferred_contact_method": "Email", # Email / Instagram / Phone / SMS
        "bio": "Brief artist bio or background notes here.",
        "current_projects": "Debut album recording; Single drop March 2026",  # semicolon-separated
        "goals": "Release album by mid-2026; Hit 10k Instagram followers",     # semicolon-separated
        "notes": "Met at BIGSOUND 2025. Responsive via Instagram DM.",
    }

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerow(example)

    print(f"\n📋 Template created: {output_path}")
    print("   → Fill in your artists (one per row)")
    print("   → Use semicolons (;) to separate multiple projects or goals")
    print(f"   → Then run: python scripts/populate_artists.py import {output_path}\n")


def import_from_csv(csv_path):
    """Read CSV and generate JSON profiles for all artists"""
    os.makedirs(ARTISTS_DIR, exist_ok=True)

    if not os.path.exists(csv_path):
        print(f"❌ File not found: {csv_path}")
        sys.exit(1)

    created = []
    skipped = []
    errors = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"\n🎵 MAESTRO Artist Import")
    print(f"   Found {len(rows)} rows in CSV...\n")

    for i, row in enumerate(rows, 1):
        name = row.get("name", "").strip()

        if not name or name.lower() == "example artist":
            print(f"   Row {i}: Skipping (no name or example row)")
            continue

        filename = name_to_filename(name)
        filepath = os.path.join(ARTISTS_DIR, filename)

        if os.path.exists(filepath):
            print(f"   ⚠️  {name} → already exists, skipping ({filename})")
            skipped.append(name)
            continue

        try:
            profile = create_artist_profile(row)
            with open(filepath, "w", encoding="utf-8") as jf:
                json.dump(profile, jf, indent=2)
            print(f"   ✅ {name} → {filename}")
            created.append(name)
        except Exception as e:
            print(f"   ❌ {name} → ERROR: {e}")
            errors.append(name)

    # Summary
    print(f"\n{'='*45}")
    print(f"✅ Created:  {len(created)} artist profiles")
    print(f"⚠️  Skipped:  {len(skipped)} (already existed)")
    if errors:
        print(f"❌ Errors:   {len(errors)}")
    print(f"📁 Saved to: {ARTISTS_DIR}")
    print(f"{'='*45}\n")

    if created:
        print("New artists added:")
        for a in created:
            print(f"  • {a}")
        print()


def list_artists():
    """Quick overview of all current artist profiles"""
    if not os.path.exists(ARTISTS_DIR):
        print("No artists directory found.")
        return

    files = [f for f in os.listdir(ARTISTS_DIR) if f.endswith(".json")]
    print(f"\n🎵 {len(files)} artists in MAESTRO:\n")

    for fname in sorted(files):
        fpath = os.path.join(ARTISTS_DIR, fname)
        with open(fpath, "r") as f:
            data = json.load(f)
        info = data.get("artist_info", {})
        name = info.get("name", fname)
        genre = info.get("genre", "Unknown genre")
        priority = info.get("priority_level", "?")
        status = info.get("label_status", "?")
        projects = len(data.get("current_projects", []))
        history = len(data.get("communication_history", []))
        print(
            f"  [{priority.upper():6}] {name:<25} | {genre:<15} | "
            f"{status:<12} | {projects} projects | {history} comms"
        )
    print()


# ─── CLI Entry Point ───────────────────────────────────────────────────────────

USAGE = """
MAESTRO Artist Population Tool
===============================
Commands:
  python scripts/populate_artists.py template              → Generate blank CSV template
  python scripts/populate_artists.py template <output.csv> → Template to custom filename
  python scripts/populate_artists.py import <file.csv>     → Import artists from CSV
  python scripts/populate_artists.py list                  → List all current artists
"""

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(USAGE)
        sys.exit(0)

    command = sys.argv[1].lower()

    if command == "template":
        output = sys.argv[2] if len(sys.argv) > 2 else "artist_import_template.csv"
        generate_template(output)

    elif command == "import":
        if len(sys.argv) < 3:
            print("❌ Usage: python scripts/populate_artists.py import <file.csv>")
            sys.exit(1)
        import_from_csv(sys.argv[2])

    elif command == "list":
        list_artists()

    else:
        print(f"❌ Unknown command: '{command}'")
        print(USAGE)