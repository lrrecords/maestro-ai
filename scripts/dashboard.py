import json
import os
from pathlib import Path
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama for colored terminal output
init()

# --- CONFIGURATION ---
BASE_DIR = Path.cwd()
ARTISTS_DIR = BASE_DIR / "data" / "artists"
BRIDGE_DIR = BASE_DIR / "data" / "bridge"

def load_artist_profile(json_path):
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def get_latest_bridge_data(slug):
    if not BRIDGE_DIR.exists(): return None
    files = sorted(BRIDGE_DIR.glob(f"{slug}_*.json"), reverse=True)
    if not files: return None
    
    try:
        with open(files[0], "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None

def print_dashboard():
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"   MAESTRO AI  -  WEEKLY ARTIST DASHBOARD")
    print(f"{'='*60}{Style.RESET_ALL}\n")

    if not ARTISTS_DIR.exists():
        print(f"{Fore.RED}No artists directory found at {ARTISTS_DIR}{Style.RESET_ALL}")
        return

    artists = sorted(list(ARTISTS_DIR.glob("*.json")))
    
    if not artists:
        print(f"{Fore.YELLOW}No artist profiles found.{Style.RESET_ALL}")
        return

    print(f"{Fore.WHITE}{'ARTIST':<25} {'HEALTH':<10} {'TREND':<10} {'STATUS'}{Style.RESET_ALL}")
    print(f"{'-'*60}")

    for artist_file in artists:
        profile = load_artist_profile(artist_file)
        if not profile: continue
        
        name = profile.get("name", "Unknown")
        slug = profile.get("slug", artist_file.stem)
        
        bridge_data = get_latest_bridge_data(slug)
        
        if bridge_data:
            score = bridge_data.get("health_score", 0)
            trend = bridge_data.get("health_trend", "unknown")
            summary = bridge_data.get("summary", "No summary")
            
            # Color coding based on score
            if score < 40:
                score_str = f"{Fore.RED}{score}/100{Style.RESET_ALL}"
                status = f"{Fore.RED}CRITICAL{Style.RESET_ALL}"
            elif score < 70:
                score_str = f"{Fore.YELLOW}{score}/100{Style.RESET_ALL}"
                status = f"{Fore.YELLOW}Monitor{Style.RESET_ALL}"
            else:
                score_str = f"{Fore.GREEN}{score}/100{Style.RESET_ALL}"
                status = f"{Fore.GREEN}Good{Style.RESET_ALL}"
        else:
            score_str = f"{Fore.WHITE}--/100{Style.RESET_ALL}"
            trend = "--"
            status = f"{Fore.WHITE}No Data{Style.RESET_ALL}"

        print(f"{name:<25} {score_str:<20} {trend:<10} {status}")

    print(f"\n{'-'*60}")
    print(f"Run {Fore.CYAN}python scripts/maestro.py checkin \"Name\"{Style.RESET_ALL} to draft emails.")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    print_dashboard()