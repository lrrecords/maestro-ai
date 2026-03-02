# scripts/maestro.py
# MAESTRO Orchestrator — routes commands to specialist agents

import sys
import json
from pathlib import Path

# Ensure the scripts/ directory is on the path so agents/ sub-package is found
sys.path.insert(0, str(Path(__file__).parent))

from agents.vinyl import VinylAgent
from agents.echo import EchoAgent


# ── Artist loader ────────────────────────────────────────────────

def load_artist(query: str):
    """Load artist data by name or file slug"""
    artists_dir = Path("data/artists")
    if not artists_dir.exists():
        print("❌ data/artists/ not found.")
        return None

    slug = query.lower().replace(" ", "_")

    for artist_file in artists_dir.glob("*.json"):
        # Match by filename
        if slug in artist_file.stem.lower():
            with open(artist_file, encoding="utf-8") as f:
                return json.load(f)
        # Match by name field inside the JSON
        with open(artist_file, encoding="utf-8") as f:
            data = json.load(f)
        name_slug = data.get("artist_info", {}).get("name", "").lower().replace(" ", "_")
        if slug in name_slug:
            return data

    return None


def list_artists():
    artists_dir = Path("data/artists")
    result = []
    for f in artists_dir.glob("*.json"):
        with open(f, encoding="utf-8") as fp:
            data = json.load(fp)
        result.append(data.get("artist_info", {}).get("name", f.stem))
    return result


# ── Agent runners ────────────────────────────────────────────────

def run_vinyl(artist_data):
    print("\n🎵  VINYL initializing...")
    try:
        agent = VinylAgent()
        print("🔄  Generating release checklist...")
        checklist, saved = agent.generate_checklist(artist_data)
        print(agent.format_display(checklist))
        print(f"💾  Saved → {saved}")
        return checklist
    except Exception as e:
        print(f"❌  VINYL error: {e}")
        return None


def run_echo(artist_data):
    print("\n📣  ECHO initializing...")
    try:
        agent = EchoAgent()
        print("🔄  Generating 2-week content plan...")
        plan, saved = agent.generate_content_plan(artist_data)
        print(agent.format_display(plan))
        print(f"💾  Saved → {saved}")
        return plan
    except Exception as e:
        print(f"❌  ECHO error: {e}")
        return None


def run_atlas(artist_data):
    print("\n📊  ATLAS initializing...")
    try:
        from agents.atlas import Atlas

        artist_info = artist_data.get("artist_info", {})
        musical_identity = artist_data.get("musical_identity", {})
        atlas_artist = {
            "name": artist_info.get("name", "Unknown"),
            "genre": musical_identity.get("primary_genre", ""),
        }

        agent = Atlas(atlas_artist)
        report = agent.run()
        if not report:
            return None

        agent.display(report)
        out_dir = Path("data/atlas")
        out_dir.mkdir(parents=True, exist_ok=True)
        slug = atlas_artist["name"].lower().replace(" ", "_")
        out_path = out_dir / f"{slug}_atlas_report.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"💾  Saved → {out_path}")
        return report
    except Exception as e:
        print(f"❌  ATLAS error: {e}")
        return None


# ── CLI ──────────────────────────────────────────────────────────

BANNER = """
╔══════════════════════════════════════════════════╗
║        🎶   MAESTRO AI — ORCHESTRATOR   🎶        ║
╚══════════════════════════════════════════════════╝"""

USAGE = """
Commands:
  vinyl   <artist>   Generate release checklist  (VINYL agent)
  echo    <artist>   Generate 2-week content plan (ECHO agent)
    atlas   <artist>   Generate analytics report    (ATLAS agent)
  full    <artist>   Run VINYL + ECHO together
  artists            List all artists in roster

Examples:
  python scripts\\maestro.py vinyl "Brendananis Monster"
  python scripts\\maestro.py echo "Jerry Mane"
    python scripts\\maestro.py atlas "Jerry Mane"
  python scripts\\maestro.py full "Brendananis Monster"
  python scripts\\maestro.py artists
"""


def main():
    print(BANNER)

    if len(sys.argv) < 2:
        print(USAGE)
        return

    command = sys.argv[1].lower()

    # List roster
    if command == "artists":
        artists = list_artists()
        print("\n📋  Current Roster:")
        for a in artists:
            print(f"  •  {a}")
        print()
        return

    # All other commands need an artist name
    if len(sys.argv) < 3:
        print(f"\n⚠️   '{command}' requires an artist name.")
        print("    Run:  python scripts\\maestro.py artists\n")
        return

    query = sys.argv[2]
    print(f"\n🔍  Loading artist: {query}")
    artist_data = load_artist(query)

    if not artist_data:
        print(f"\n❌  Artist '{query}' not found.")
        print("    Run:  python scripts\\maestro.py artists\n")
        return

    name = artist_data.get("artist_info", {}).get("name", query)
    print(f"✅  Loaded: {name}")

    if command == "vinyl":
        run_vinyl(artist_data)

    elif command == "echo":
        run_echo(artist_data)

    elif command == "atlas":
        run_atlas(artist_data)

    elif command == "full":
        checklist = run_vinyl(artist_data)
        plan = run_echo(artist_data)
        report = run_atlas(artist_data)

        vinyl_phases = len(checklist.get("phases", [])) if checklist else 0
        echo_days = len(
            [d for d in (plan.get("content_plan", []) if plan else []) if d.get("posts")]
        )
        atlas_records = report.get("record_count") if report else None

        print("\n" + "=" * 62)
        print("✅  MAESTRO FULL RUN COMPLETE")
        print("=" * 62)
        print(f"  🎵  VINYL  →  {vinyl_phases} phases generated")
        print(f"  📣  ECHO   →  {echo_days} active posting days planned")
        if atlas_records is not None:
            print(f"  📊  ATLAS  →  {atlas_records:,} records analysed")
        else:
            print(f"  📊  ATLAS  →  no data (add CSVs to data/metrics/)")
        print(f"  💾  Data   →  data/vinyl/  data/echo/  data/atlas/")
        print("=" * 62 + "\n")

    else:
        print(f"\n❌  Unknown command: '{command}'")
        print(USAGE)


if __name__ == "__main__":
    main()