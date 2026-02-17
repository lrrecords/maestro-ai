"""
BRIDGE Automation - Artist Health Check
No LLM needed - pure business logic
Outputs JSON for n8n workflows
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
ARTISTS_DIR = BASE_DIR / "data" / "artists"
CONTEXT_FILE = BASE_DIR / "data" / "lr_records_context.json"

print(f"DEBUG: Looking for context file at: {CONTEXT_FILE}", file=sys.stderr)
print(f"DEBUG: File exists? {CONTEXT_FILE.exists()}", file=sys.stderr)

def load_json(filepath):
    """Load JSON file safely"""
    try:
        print(f"DEBUG: Attempting to load {filepath}", file=sys.stderr)
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"DEBUG: Successfully loaded {filepath}", file=sys.stderr)
            return data
    except FileNotFoundError:
        print(f"DEBUG: File not found: {filepath}", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"DEBUG: JSON decode error in {filepath}: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"DEBUG: Unexpected error loading {filepath}: {e}", file=sys.stderr)
        return None

def load_artists():
    """Load all artist profiles"""
    print("DEBUG: Loading artists...", file=sys.stderr)
    artists = []
    
    # Load from main context file
    context = load_json(CONTEXT_FILE)
    if context and 'artists' in context:
        artists = context['artists']
        print(f"DEBUG: Loaded {len(artists)} artists from context file", file=sys.stderr)
    else:
        print("DEBUG: No artists found in context file", file=sys.stderr)
    
    # If artist directory exists, override with individual files
    if ARTISTS_DIR.exists():
        print(f"DEBUG: Artists directory exists: {ARTISTS_DIR}", file=sys.stderr)
        for artist_file in ARTISTS_DIR.glob("*.json"):
            artist_data = load_json(artist_file)
            if artist_data and 'name' in artist_data:
                artist_name = artist_data['name']
                existing_index = next((i for i, a in enumerate(artists) if a.get('name') == artist_name), None)
                if existing_index is not None:
                    artists[existing_index] = artist_data
                else:
                    artists.append(artist_data)
    else:
        print(f"DEBUG: Artists directory does not exist: {ARTISTS_DIR}", file=sys.stderr)
    
    print(f"DEBUG: Total artists loaded: {len(artists)}", file=sys.stderr)
    return artists

def calculate_days_since_contact(last_contact_str):
    """Calculate days since last contact"""
    if not last_contact_str:
        return 999
    
    try:
        last_contact = datetime.strptime(last_contact_str, "%Y-%m-%d")
        days = (datetime.now() - last_contact).days
        return days
    except Exception as e:
        print(f"DEBUG: Error parsing date {last_contact_str}: {e}", file=sys.stderr)
        return 999

def analyze_artist_health(artist):
    """Analyze if artist needs attention"""
    name = artist.get('name', 'Unknown')
    status = artist.get('status', 'unknown')
    last_contact = artist.get('last_contact', None)
    current_project = artist.get('current_project', None)
    relationship_status = artist.get('relationship_status', 'unknown')
    
    needs_attention = False
    reason = []
    priority = "low"
    
    days_since_contact = calculate_days_since_contact(last_contact)
    
    # Rule 1: No contact in 30+ days
    if days_since_contact > 30:
        needs_attention = True
        reason.append(f"No contact in {days_since_contact} days")
        priority = "high"
    elif days_since_contact > 14:
        needs_attention = True
        reason.append(f"It's been {days_since_contact} days since last contact")
        priority = "medium"
    
    # Rule 2: Relationship status needs attention
    if relationship_status == 'needs_attention':
        needs_attention = True
        reason.append("Relationship status flagged as 'needs attention'")
        if priority != "high":
            priority = "medium"
    
    # Rule 3: Status indicates attention needed
    if status.lower() in ['inactive', 'needs attention', 'at risk']:
        needs_attention = True
        reason.append(f"Status: {status}")
        if priority != "high":
            priority = "medium"
    
    return {
        "name": name,
        "needs_attention": needs_attention,
        "priority": priority,
        "days_since_contact": days_since_contact,
        "last_contact": last_contact,
        "reasons": reason,
        "current_project": current_project,
        "status": status,
        "relationship_status": relationship_status,
        "notes": artist.get('notes', '')
    }

def draft_check_in_message(artist_analysis):
    """Draft a check-in message based on artist situation"""
    name = artist_analysis['name']
    days = artist_analysis['days_since_contact']
    current_project = artist_analysis['current_project']
    
    if 'needs attention' in artist_analysis.get('relationship_status', '').lower():
        message = f"Hey {name}! 👋\n\n"
        message += f"Just checking in - how's everything going?\n\n"
        if current_project:
            message += f"How's the {current_project} coming along?\n\n"
        message += f"Let me know if you need anything or just want to catch up.\n\n"
        message += f"Brett"
    
    elif days > 30:
        message = f"Hey {name}! 👋\n\n"
        message += f"Been a minute since we connected! How's everything going with your music?\n\n"
        if current_project:
            message += f"Still working on {current_project}? Would love to hear how it's progressing.\n\n"
        else:
            message += f"Any new tracks in the works? Would love to hear what you're up to.\n\n"
        message += f"Brett"
    
    elif days > 14:
        message = f"Hey {name}! 👋\n\n"
        message += f"Just checking in - how's everything going?\n\n"
        if current_project:
            message += f"How's the {current_project} coming along?\n\n"
        message += f"Let me know if you need anything.\n\n"
        message += f"Brett"
    
    else:
        message = f"Hey {name}! 👋\n\n"
        message += f"Hope you're doing well! Just wanted to touch base.\n\n"
        message += f"Anything exciting happening on your end?\n\n"
        message += f"Brett"
    
    return message

def health_check():
    """Run full artist health check"""
    print("DEBUG: Starting health check...", file=sys.stderr)
    artists = load_artists()
    
    if not artists:
        return {
            "timestamp": datetime.now().isoformat(),
            "error": "No artists found",
            "artists_analyzed": 0,
            "artists_needing_attention": []
        }
    
    results = []
    
    for artist in artists:
        print(f"DEBUG: Analyzing {artist.get('name', 'Unknown')}", file=sys.stderr)
        analysis = analyze_artist_health(artist)
        
        if analysis['needs_attention']:
            analysis['draft_message'] = draft_check_in_message(analysis)
            results.append(analysis)
    
    priority_order = {"high": 0, "medium": 1, "low": 2}
    results.sort(key=lambda x: priority_order.get(x['priority'], 3))
    
    output = {
        "timestamp": datetime.now().isoformat(),
        "artists_analyzed": len(artists),
        "artists_needing_attention": len(results),
        "alerts": results
    }
    
    print("DEBUG: Health check complete", file=sys.stderr)
    return output

def main():
    """Main entry point"""
    print(f"DEBUG: Script started with args: {sys.argv}", file=sys.stderr)
    
    if "--health-check" in sys.argv:
        result = health_check()
        print(json.dumps(result, indent=2))
    
    elif "--test" in sys.argv:
        result = health_check()
        print("\n🎵 BRIDGE AUTOMATION - ARTIST HEALTH CHECK\n")
        print(f"Timestamp: {result['timestamp']}")
        print(f"Artists Analyzed: {result['artists_analyzed']}")
        print(f"Need Attention: {result['artists_needing_attention']}\n")
        
        if result.get('error'):
            print(f"❌ Error: {result['error']}")
        elif result['artists_needing_attention'] > 0:
            print("⚠️  ALERTS:\n")
            for alert in result['alerts']:
                print(f"{'='*60}")
                print(f"Artist: {alert['name']}")
                print(f"Priority: {alert['priority'].upper()}")
                print(f"Days Since Contact: {alert['days_since_contact']}")
                print(f"Reasons: {', '.join(alert['reasons'])}")
                print(f"\n📝 Draft Message:\n{alert['draft_message']}")
                print(f"{'='*60}\n")
        else:
            print("✅ All artists are in good contact!")
    
    else:
        print("Usage:")
        print("  --health-check    Output JSON for automation")
        print("  --test            Pretty formatted test output")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FATAL ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
