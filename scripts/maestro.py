#!/usr/bin/env python3
"""
MAESTRO AI - Orchestrator
LRRecords

Commands:
    artists                    List roster
    vinyl   "Artist Name"      Release checklist        (VINYL)
    echo    "Artist Name"      2-week content plan      (ECHO)
    atlas   "Artist Name"      Analytics report         (ATLAS)
    forge   "Artist Name"      Automation specs         (FORGE)
    sage    "Artist Name"      Weekly action plan       (SAGE)
    bridge  "Artist Name"      Artist relationship      (BRIDGE)
    bridge  --all              Full roster briefing
    full    "Artist Name"      VINYL+ECHO+ATLAS+FORGE+SAGE
    report                     Health dashboard (all artists)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import os
import json
from datetime import datetime, timezone
from colorama import Fore, Style, init

init(autoreset=False)

# ── Path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent))

BASE_DIR = Path(__file__).resolve().parent.parent

# Allow private/local data dir override (keeps public repo demo-safe)
DATA_DIR = Path(os.getenv("MAESTRO_DATA_DIR", str(BASE_DIR / "data")))
if not DATA_DIR.is_absolute():
    DATA_DIR = (BASE_DIR / DATA_DIR).resolve()

ARTISTS_DIR = DATA_DIR / "artists"

# ── Class-based agents ────────────────────────────────────────────────────────
from agents.vinyl import VinylAgent
from agents.echo  import EchoAgent

# ── Function-based agents ─────────────────────────────────────────────────────
try:
    from agents import forge as _forge
    FORGE_OK = True
except ImportError:
    FORGE_OK = False

try:
    from agents import sage as _sage
    SAGE_OK = True
except ImportError:
    SAGE_OK = False

try:
    from agents import bridge as _bridge
    BRIDGE_OK = True
except ImportError:
    BRIDGE_OK = False


# ── Artist discovery ──────────────────────────────────────────────────────────

def load_artist(query: str) -> tuple[dict, str] | None:
    if not ARTISTS_DIR.exists():
        print("ERROR  data/artists/ folder not found.")
        return None

    query_lower = query.lower().strip()

    for path in sorted(ARTISTS_DIR.glob("*.json")):
        slug = path.stem
        with open(path, encoding="utf-8") as f:
            profile = json.load(f)
        name = profile.get("artist_info", {}).get("name", "").lower()
        if query_lower == slug or query_lower in name or query_lower in slug:
            return profile, slug

    return None


def load_all_artists() -> list[tuple[dict, str]]:
    artists = []
    if not ARTISTS_DIR.exists():
        return artists
    for path in sorted(ARTISTS_DIR.glob("*.json")):
        with open(path, encoding="utf-8") as f:
            profile = json.load(f)
        artists.append((profile, path.stem))
    return artists


def print_roster():
    artists = load_all_artists()
    if not artists:
        print("\n  No artists found in data/artists/\n")
        return
    print(f"\n  MAESTRO AI - Artist Roster  ({len(artists)} artists)\n")
    print(f"  {'NAME':<28} {'GENRE':<22} NEXT RELEASE")
    print(f"  {'-'*28} {'-'*22} {'-'*20}")
    for profile, slug in artists:
        name    = profile.get("artist_info",      {}).get("name",          slug)
        genre   = profile.get("musical_identity", {}).get("primary_genre", "-")
        release = profile.get("upcoming_release", {}).get("title",         "-")
        print(f"  {name:<28} {genre:<22} {release}")
    print()


# ── Manifest writer ───────────────────────────────────────────────────────────

def write_manifest(run_id: str, artist_slug: str, commands_run: list[str]):
    manifest_dir = DATA_DIR / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)

    agent_folders = {
        "vinyl":  DATA_DIR / "vinyl",
        "echo":   DATA_DIR / "echo",
        "atlas":  DATA_DIR / "atlas",
        "forge":  DATA_DIR / "forge",
        "sage":   DATA_DIR / "sage",
        "bridge": DATA_DIR / "bridge",
    }

    outputs = {}
    for agent_name, folder in agent_folders.items():
        if folder.exists():
            matches = sorted(
                folder.glob(f"{artist_slug}*.json"),
                key=lambda f: f.stat().st_mtime,
                reverse=True,
            )
            if matches:
                outputs[agent_name] = str(matches[0].relative_to(BASE_DIR))

    manifest = {
        "run_id":       run_id,
        "artist_slug":  artist_slug,
        "commands_run": commands_run,
        "outputs":      outputs,
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
    }

    path = manifest_dir / f"{artist_slug}_{run_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"\n  Manifest saved -> {path.relative_to(BASE_DIR)}")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _print_error(exc: Exception) -> None:
    """Print an exception message with consistent indentation.

    Multi-line messages (e.g. the Ollama timeout guidance) are indented so
    every line lines up with the first, keeping the terminal output readable.
    """
    lines = str(exc).splitlines()
    print(f"  ERROR: {lines[0]}")
    for line in lines[1:]:
        print(f"         {line}")


# ── Agent runners ─────────────────────────────────────────────────────────────

def run_vinyl(artist_data: dict, slug: str):
    print("\n[VINYL] Initializing...")
    try:
        agent = VinylAgent()
        print("  Generating release checklist...")
        checklist, saved = agent.generate_checklist(artist_data)
        print(agent.format_display(checklist))
        print(f"  Saved -> {saved}")
        return checklist
    except Exception as e:
        _print_error(e)
        return None


def run_echo(artist_data: dict, slug: str):
    print("\n[ECHO] Initializing...")
    try:
        agent = EchoAgent()
        print("  Generating 2-week content plan...")
        plan, saved = agent.generate_content_plan(artist_data)
        print(agent.format_display(plan))
        print(f"  Saved -> {saved}")
        return plan
    except Exception as e:
        _print_error(e)
        return None


def run_atlas(artist_data: dict, slug: str):
    print("\n[ATLAS] Initializing...")
    try:
        from agents.atlas import Atlas

        artist_info      = artist_data.get("artist_info", {})
        musical_identity = artist_data.get("musical_identity", {})
        atlas_artist = {
            "name":  artist_info.get("name", "Unknown"),
            "genre": musical_identity.get("primary_genre", ""),
        }

        agent  = Atlas(atlas_artist)
        report = agent.run()

        if not report:
            print("  WARNING: No data returned - add CSVs to data/metrics/")
            return None

        agent.display(report)

        out_dir = DATA_DIR / "atlas"
        out_dir.mkdir(parents=True, exist_ok=True)
        ts       = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        out_path = out_dir / f"{slug}_{ts}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"  Saved -> {out_path.relative_to(BASE_DIR)}")
        return report

    except Exception as e:
        _print_error(e)
        return None


def run_forge(artist_data: dict, slug: str):
    if not FORGE_OK:
        print("\n[FORGE] ERROR: agents/forge.py not found.")
        print("  Create scripts/agents/forge.py to enable this agent.")
        return None
    print("\n[FORGE] Initializing...")
    try:
        return _forge.run(artist_data, slug)
    except Exception as e:
        _print_error(e)
        return None


def run_sage(artist_data: dict, slug: str):
    if not SAGE_OK:
        print("\n[SAGE] ERROR: agents/sage.py not found.")
        print("  Create scripts/agents/sage.py to enable this agent.")
        return None
    print("\n[SAGE] Initializing...")
    try:
        return _sage.run(artist_data, slug)
    except Exception as e:
        _print_error(e)
        return None


def run_bridge(artist_data: dict, slug: str):
    if not BRIDGE_OK:
        print("\n[BRIDGE] ERROR: agents/bridge.py not found.")
        print("  Create scripts/agents/bridge.py to enable this agent.")
        return None
    print("\n[BRIDGE] Initializing...")
    try:
        return _bridge.run(artist_data, slug)
    except Exception as e:
        _print_error(e)
        return None


def run_bridge_all(artists: list[tuple[dict, str]]):
    if not BRIDGE_OK:
        print("\n[BRIDGE] ERROR: agents/bridge.py not found.")
        return None
    try:
        return _bridge.run_roster_briefing(artists)
    except Exception as e:
        _print_error(e)
        return None


def run_report():
    """Print a colour-coded health dashboard for all artists."""
    artists_dir = DATA_DIR / "artists"
    bridge_dir  = DATA_DIR / "bridge"

    artist_files = sorted(artists_dir.glob("*.json"))

    if not artist_files:
        print(f"{Fore.YELLOW}  No artist profiles found in {artists_dir}{Style.RESET_ALL}")
        return

    rows = []

    for artist_file in artist_files:
        slug = artist_file.stem

        # Display name
        try:
            with open(artist_file, "r", encoding="utf-8") as f:
                profile = json.load(f)
            name = (
                profile.get("artist_info", {}).get("name")
                or slug.replace("_", " ").title()
            )
        except Exception:
            name = slug.replace("_", " ").title()

        # Latest BRIDGE snapshot
        bridge_files = sorted(bridge_dir.glob(f"{slug}_*.json"), reverse=True)

        if not bridge_files:
            rows.append({
                "name":    name,
                "slug":    slug,
                "score":   None,
                "band":    "NO DATA",
                "trend":   "-",
                "days":    None,
                "summary": "No BRIDGE snapshot found.",
            })
            continue

        try:
            with open(bridge_files[0], "r", encoding="utf-8") as f:
                bridge = json.load(f)
        except Exception as e:
            rows.append({
                "name":    name,
                "slug":    slug,
                "score":   None,
                "band":    "ERROR",
                "trend":   "-",
                "days":    None,
                "summary": str(e),
            })
            continue

        # Nested field mapping — matches actual BRIDGE JSON structure
        health  = bridge.get("health",           {})
        pattern = bridge.get("pattern_analysis", {})

        rows.append({
            "name":    name,
            "slug":    slug,
            "score":   health.get("score"),
            "band":    health.get("status",  "Unknown"),
            "trend":   pattern.get("trend",  "-"),
            "days":    bridge.get("days_since_contact"),
            "summary": pattern.get("summary", ""),
        })

    # Sort: lowest score first, no-data at bottom
    rows.sort(key=lambda r: (
        r["score"] is None,
        r["score"] if r["score"] is not None else 999
    ))

    # Render
    W   = 74
    now = datetime.now(timezone.utc).strftime("%d %b %Y  %H:%M UTC")

    print(f"\n{Fore.CYAN}{'=' * W}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  MAESTRO AI  -  ARTIST HEALTH DASHBOARD{now:>{W - 40}}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * W}{Style.RESET_ALL}")
    print(f"  {'ARTIST':<26}  {'SCORE':>7}  {'STATUS':<13}{'TREND':<14}LAST CONTACT")
    print(f"  {'-'*26}  {'-'*7}  {'-'*13}{'-'*14}{'-'*12}")

    for row in rows:
        score = row["score"]
        days  = row["days"]

        days_str = f"{days}d ago" if isinstance(days, (int, float)) else "Unknown"
        trend    = (row["trend"] or "-")[:13]

        if score is None:
            colour    = Fore.WHITE
            score_str = "     N/A"
            band_str  = row["band"]
        elif score >= 70:
            colour    = Fore.GREEN
            score_str = f"  {score:>3}/100"
            band_str  = "Good"
        elif score >= 40:
            colour    = Fore.YELLOW
            score_str = f"  {score:>3}/100"
            band_str  = "Monitor"
        else:
            colour    = Fore.RED
            score_str = f"  {score:>3}/100"
            band_str  = "Critical"

        print(
            f"  {colour}"
            f"{row['name'][:26]:<26}  "
            f"{score_str}  "
            f"{band_str:<13}"
            f"{trend:<14}"
            f"{days_str}"
            f"{Style.RESET_ALL}"
        )

    # Footer
    print(f"{Fore.CYAN}{'=' * W}{Style.RESET_ALL}")

    critical = sum(1 for r in rows if r["score"] is not None and r["score"] <  40)
    monitor  = sum(1 for r in rows if r["score"] is not None and 40 <= r["score"] < 70)
    good     = sum(1 for r in rows if r["score"] is not None and r["score"] >= 70)
    no_data  = sum(1 for r in rows if r["score"] is None)

    parts = []
    if critical: parts.append(f"{Fore.RED}{critical} Critical{Style.RESET_ALL}")
    if monitor:  parts.append(f"{Fore.YELLOW}{monitor} Monitor{Style.RESET_ALL}")
    if good:     parts.append(f"{Fore.GREEN}{good} Good{Style.RESET_ALL}")
    if no_data:  parts.append(f"{Fore.WHITE}{no_data} No Data{Style.RESET_ALL}")

    summary = "  ·  ".join(parts)
    print(f"  {len(rows)} artist(s) on roster  ·  {summary}\n")


# ── CLI ───────────────────────────────────────────────────────────────────────

BANNER = """
==================================================
      MAESTRO AI  -  LRRecords Orchestrator
=================================================="""

USAGE = """
Commands:
  artists                    List all artists in roster
  report                     Health dashboard (all artists)

  vinyl   "Artist Name"      Release checklist         (VINYL)
  echo    "Artist Name"      2-week content plan        (ECHO)
  atlas   "Artist Name"      Analytics report           (ATLAS)
  forge   "Artist Name"      Automation specs           (FORGE)
  sage    "Artist Name"      Weekly action plan         (SAGE)
  bridge  "Artist Name"      Artist relationship health (BRIDGE)

  sage    --all              Weekly plan for all artists
  bridge  --all              Full roster relationship briefing

  full    "Artist Name"      VINYL > ECHO > ATLAS > FORGE > SAGE

Examples:
  python scripts\\maestro.py report
  python scripts\\maestro.py artists
  python scripts\\maestro.py bridge "Brendananis Monster"
  python scripts\\maestro.py full "Brendananis Monster"
  python scripts\\maestro.py sage --all
  python scripts\\maestro.py bridge --all
"""


def main():
    print(BANNER)

    if len(sys.argv) < 2:
        print(USAGE)
        return

    command = sys.argv[1].lower()
    has_arg = len(sys.argv) >= 3
    arg     = sys.argv[2] if has_arg else ""

    # ── artists ────────────────────────────────────────────────────────────────
    if command == "artists":
        print_roster()
        return

    # ── report ─────────────────────────────────────────────────────────────────
    if command == "report":
        run_report()
        return

    # ── sage --all ─────────────────────────────────────────────────────────────
    if command == "sage" and arg == "--all":
        if not SAGE_OK:
            print("\nERROR: agents/sage.py not found.\n")
            return
        artists = load_all_artists()
        if not artists:
            print("\n  No artists found.\n")
            return
        print(f"\n[SAGE] Full Roster Run  ({len(artists)} artists)\n")
        for i, (profile, slug) in enumerate(artists, 1):
            name = profile.get("artist_info", {}).get("name", slug)
            print(f"[{i}/{len(artists)}] {name}")
            _sage.run(profile, slug)
            print()
        print("COMPLETE: SAGE roster run finished.\n")
        return

    # ── bridge --all ───────────────────────────────────────────────────────────
    if command == "bridge" and arg == "--all":
        if not BRIDGE_OK:
            print("\nERROR: agents/bridge.py not found.\n")
            return
        artists = load_all_artists()
        if not artists:
            print("\n  No artists found.\n")
            return
        print(f"\n[BRIDGE] Roster Briefing  ({len(artists)} artists)\n")
        run_bridge_all(artists)
        print()
        return

    # ── all other commands need an artist name ─────────────────────────────────
    if not has_arg:
        print(f"\n  WARNING: '{command}' requires an artist name.")
        print(f'  Example: python scripts\\maestro.py {command} "Brendananis Monster"\n')
        return

    print(f"\n  Loading: {arg}")
    result = load_artist(arg)

    if not result:
        print(f"\n  ERROR: Artist '{arg}' not found.")
        print("  Run: python scripts\\maestro.py artists\n")
        return

    artist_data, slug = result
    name = artist_data.get("artist_info", {}).get("name", arg)
    print(f"  Loaded: {name}  [{slug}]")

    # ── single agent commands ──────────────────────────────────────────────────
    if command == "vinyl":
        run_vinyl(artist_data, slug)

    elif command == "echo":
        run_echo(artist_data, slug)

    elif command == "atlas":
        run_atlas(artist_data, slug)

    elif command == "forge":
        run_forge(artist_data, slug)

    elif command == "sage":
        run_sage(artist_data, slug)

    elif command == "bridge":
        run_bridge(artist_data, slug)

    elif command == "checkin":
        from checkin import run as run_checkin
        run_checkin(sys.argv[2:])

    # ── full pipeline ──────────────────────────────────────────────────────────
    elif command == "full":
        run_id  = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        divider = "-" * 52

        print(f"\n  MAESTRO - Full Pipeline - {name}")
        print(f"  {divider}")
        print(f"  Order: VINYL > ECHO > ATLAS > FORGE > SAGE")
        print(f"  Tip: run bridge \"{name}\" first for richer output")
        print(f"  {divider}")

        checklist = run_vinyl(artist_data, slug)
        plan      = run_echo(artist_data,  slug)
        report    = run_atlas(artist_data, slug)
        auto_spec = run_forge(artist_data, slug)
        weekly    = run_sage(artist_data,  slug)

        vinyl_phases = 0
        if isinstance(checklist, dict):
            vinyl_phases = len(checklist.get("phases", []))

        echo_days = 0
        if isinstance(plan, dict):
            echo_days = len(
                [d for d in plan.get("content_plan", []) if d.get("posts")]
            )

        print(f"\n  {divider}")
        print(f"  COMPLETE - {name}  [{run_id}]")
        print(f"  {divider}")
        print(f"  VINYL  -> {vinyl_phases} release phases")
        print(f"  ECHO   -> {echo_days} active posting days")
        print(f"  ATLAS  -> {'report saved' if report    else 'no metrics data'}")
        print(f"  FORGE  -> {'automation specs saved' if auto_spec else 'error - check agents/forge.py'}")
        print(f"  SAGE   -> {'weekly plan saved' if weekly    else 'error - check agents/sage.py'}")
        print(f"  {divider}")

        write_manifest(run_id, slug, ["vinyl", "echo", "atlas", "forge", "sage"])
        print()

    else:
        print(f"\n  ERROR: Unknown command '{command}'")
        print(USAGE)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()