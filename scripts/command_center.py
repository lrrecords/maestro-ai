"""
🎛️ MAESTRO COMMAND CENTER 2.0
Mission Control Dashboard with BRIDGE Intelligence Integration

Now powered by 5-layer AI intelligence system
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List
import sys

# Import BRIDGE Intelligence
from bridge_intelligence import (
    BridgeIntelligence,
    HealthScorer,
    PatternDetector,
    Predictor,
    LearningMemory
)

# ============================================================================
# CONFIGURATION
# ============================================================================

ARTIST_FOLDER = "data/artists"

# ============================================================================
# DATA LOADING
# ============================================================================

def load_all_artists() -> List[Dict]:
    """Load all artist profiles"""
    artists = []
    for filename in os.listdir(ARTIST_FOLDER):
        if filename.endswith(".json"):
            filepath = os.path.join(ARTIST_FOLDER, filename)
            with open(filepath, "r") as f:
                artists.append(json.load(f))
    return artists


def get_pending_followups(artists: List[Dict]) -> List[Dict]:
    """Extract all pending follow-ups across roster"""
    followups = []
    
    for artist_data in artists:
        artist_name = artist_data["artist_info"]["name"]
        comm_history = artist_data.get("communication_history", [])
        
        for comm in comm_history:
            if comm.get("follow_up_needed") and comm.get("follow_up_date"):
                followup_date = datetime.fromisoformat(comm["follow_up_date"])
                days_until = (followup_date - datetime.now()).days
                
                followups.append({
                    "artist": artist_name,
                    "date": comm["follow_up_date"],
                    "days_until": days_until,
                    "reason": comm.get("follow_up_reason", "Check-in"),
                    "original_date": comm["date"]
                })
    
    # Sort by urgency
    return sorted(followups, key=lambda x: x["days_until"])


def get_all_action_items(artists: List[Dict]) -> List[Dict]:
    """Extract all open action items"""
    action_items = []
    
    for artist_data in artists:
        artist_name = artist_data["artist_info"]["name"]
        items = artist_data.get("open_action_items", [])
        
        for item in items:
            due_date = item.get("due_date")
            if due_date:
                due = datetime.fromisoformat(due_date)
                days_until = (due - datetime.now()).days
                is_overdue = days_until < 0
            else:
                days_until = None
                is_overdue = False
            
            action_items.append({
                "artist": artist_name,
                "description": item.get("description", "No description"),
                "assigned_to": item.get("assigned_to", "Unknown"),
                "due_date": due_date,
                "days_until": days_until,
                "is_overdue": is_overdue
            })
    
    # Sort: overdue first, then by due date
    return sorted(action_items, key=lambda x: (not x["is_overdue"], x["days_until"] if x["days_until"] is not None else 999))


def get_recent_activity(artists: List[Dict], days: int = 7) -> List[Dict]:
    """Get recent communication activity"""
    activities = []
    cutoff_date = datetime.now() - timedelta(days=days)
    
    for artist_data in artists:
        artist_name = artist_data["artist_info"]["name"]
        comm_history = artist_data.get("communication_history", [])
        
        for comm in comm_history:
            comm_date = datetime.fromisoformat(comm["date"])
            if comm_date >= cutoff_date:
                activities.append({
                    "artist": artist_name,
                    "date": comm["date"],
                    "type": comm.get("type", "Unknown"),
                    "channel": comm.get("channel", "Unknown"),
                    "sentiment": comm.get("sentiment", "N/A")
                })
    
    return sorted(activities, key=lambda x: x["date"], reverse=True)


# ============================================================================
# DISPLAY FUNCTIONS
# ============================================================================

def print_header():
    """Print dashboard header"""
    print("\n" + "="*70)
    print("🎛️  MAESTRO COMMAND CENTER 2.0 - BRIDGE INTELLIGENCE INTEGRATED")
    print("="*70)
    print(f"📅 {datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')}")
    print("="*70 + "\n")


def print_bridge_briefing(briefing: Dict):
    """Display BRIDGE daily briefing at top of dashboard"""
    print("🌉 BRIDGE DAILY BRIEFING")
    print("-" * 70)
    
    summary = briefing["roster_summary"]
    
    # Roster health overview
    print(f"\n📊 ROSTER HEALTH:")
    print(f"   Total Artists: {summary['total_artists']}")
    
    health_bar = ""
    if summary['healthy'] > 0:
        health_bar += "🟢" * summary['healthy']
    if summary['at_risk'] > 0:
        health_bar += "🟡" * summary['at_risk']
    if summary['critical'] > 0:
        health_bar += "🔴" * summary['critical']
    
    print(f"   {health_bar}")
    print(f"   🟢 Healthy: {summary['healthy']}  |  🟡 At Risk: {summary['at_risk']}  |  🔴 Critical: {summary['critical']}")
    
    # Critical alerts
    if briefing["critical_artists"]:
        print(f"\n🚨 CRITICAL ATTENTION NEEDED:")
        for artist in briefing["critical_artists"]:
            print(f"   • {artist['name']}: {artist['health_status']} ({artist['health_score']}/100)")
    
    # At risk
    if briefing["at_risk_artists"]:
        print(f"\n⚠️  AT RISK:")
        for artist in briefing["at_risk_artists"][:3]:  # Top 3
            print(f"   • {artist['name']}: {artist['health_status']} ({artist['health_score']}/100)")
    
    # Top opportunities
    if briefing["opportunities"]:
        print(f"\n✨ OPPORTUNITIES:")
        for opp in briefing["opportunities"][:2]:  # Top 2
            print(f"   • {opp['artist']}: {opp['opportunity']}")
            print(f"     → {opp['action']}")
    
    # Top predictions
    if briefing["predictions"]:
        print(f"\n🔮 TOP PREDICTIONS:")
        for pred in briefing["predictions"][:3]:  # Top 3
            conf_emoji = {"HIGH": "🎯", "MEDIUM": "🤔", "LOW": "💭"}
            print(f"   {conf_emoji.get(pred['confidence'], '💭')} {pred['artist']}: {pred['prediction']}")
            print(f"     → {pred['action']}")
    
    print()


def print_health_summary(artists: List[Dict], bridge: BridgeIntelligence):
    """Display artist health scores"""
    print("\n💚 ARTIST HEALTH OVERVIEW")
    print("-" * 70)
    
    # Calculate health for all artists
    health_data = []
    for artist_data in artists:
        name = artist_data["artist_info"]["name"]
        score, status, _ = HealthScorer.calculate_health(artist_data)
        health_data.append({
            "name": name,
            "score": score,
            "status": status
        })
    
    # Sort by health score (lowest first = needs attention)
    health_data.sort(key=lambda x: x["score"])
    
    for artist in health_data:
        status_color = artist["status"]
        bar_length = int(artist["score"] / 5)  # 20 chars max
        bar = "█" * bar_length + "░" * (20 - bar_length)
        print(f"   {status_color} {artist['name']:20} [{bar}] {artist['score']}/100")
    
    print()


def print_followups(followups: List[Dict]):
    """Display pending follow-ups"""
    print("\n📅 PENDING FOLLOW-UPS")
    print("-" * 70)
    
    if not followups:
        print("   ✅ No pending follow-ups\n")
        return
    
    overdue = [f for f in followups if f["days_until"] < 0]
    upcoming = [f for f in followups if f["days_until"] >= 0]
    
    if overdue:
        print("   🚨 OVERDUE:")
        for f in overdue:
            print(f"      • {f['artist']}: {f['reason']} ({abs(f['days_until'])} days overdue)")
    
    if upcoming:
        print("   📆 UPCOMING:")
        for f in upcoming[:5]:  # Show next 5
            if f["days_until"] == 0:
                urgency = "TODAY"
            elif f["days_until"] == 1:
                urgency = "TOMORROW"
            else:
                urgency = f"in {f['days_until']} days"
            print(f"      • {f['artist']}: {f['reason']} ({urgency})")
    
    print()


def print_action_items(action_items: List[Dict]):
    """Display open action items"""
    print("\n✅ ACTION ITEMS")
    print("-" * 70)
    
    if not action_items:
        print("   🎉 No open action items\n")
        return
    
    overdue = [a for a in action_items if a["is_overdue"]]
    upcoming = [a for a in action_items if not a["is_overdue"]]
    
    if overdue:
        print("   🚨 OVERDUE:")
        for item in overdue:
            print(f"      • [{item['assigned_to']}] {item['artist']}: {item['description']}")
            print(f"        ({abs(item['days_until'])} days overdue)")
    
    if upcoming:
        print("   📋 OPEN:")
        for item in upcoming[:5]:  # Show next 5
            due_text = f"Due in {item['days_until']} days" if item["days_until"] else "No due date"
            print(f"      • [{item['assigned_to']}] {item['artist']}: {item['description']}")
            print(f"        ({due_text})")
    
    print()


def print_recent_activity(activities: List[Dict]):
    """Display recent activity"""
    print("\n📊 RECENT ACTIVITY (Last 7 Days)")
    print("-" * 70)
    
    if not activities:
        print("   No recent activity\n")
        return
    
    for activity in activities[:10]:  # Show last 10
        date = datetime.fromisoformat(activity["date"]).strftime("%b %d")
        sentiment_emoji = {
            "POSITIVE": "😊",
            "NEUTRAL": "😐",
            "NEGATIVE": "😟",
            "N/A": "📧"
        }
        emoji = sentiment_emoji.get(activity["sentiment"], "📧")
        
        print(f"   {emoji} {date} - {activity['artist']}: {activity['type']} via {activity['channel']}")
    
    print()


def print_menu():
    """Display interactive menu"""
    print("\n" + "="*70)
    print("🎮 ACTIONS")
    print("="*70)
    print("   [1] 📊 Analyze Artist (Deep Intelligence)")
    print("   [2] 📧 Generate Check-In Message")
    print("   [3] 🔄 Refresh Dashboard")
    print("   [4] 🌉 Full BRIDGE Briefing")
    print("   [5] 📈 Artist Health Details")
    print("   [6] 🧠 View Learning Insights")
    print("   [Q] Quit")
    print("="*70)


def show_artist_analysis(bridge: BridgeIntelligence, artist_name: str):
    """Show detailed BRIDGE analysis for an artist"""
    print(f"\n{'='*70}")
    print(f"🌉 BRIDGE INTELLIGENCE: {artist_name}")
    print(f"{'='*70}")
    
    analysis = bridge.analyze_artist(artist_name)
    
    if "error" in analysis:
        print(f"\n❌ {analysis['error']}\n")
        return
    
    # Health breakdown
    health = analysis["health"]
    print(f"\n📊 HEALTH: {health['status']} ({health['score']}/100)")
    print("\nBreakdown:")
    for category, data in health["breakdown"].items():
        score_bar = "█" * int(data['score'] / 10) + "░" * (10 - int(data['score'] / 10))
        print(f"  • {category.capitalize():20} [{score_bar}] {data['detail']}")
    
    # Patterns
    if analysis["patterns"]:
        print(f"\n🔍 DETECTED PATTERNS:")
        for pattern in analysis["patterns"]:
            severity_emoji = {
                "HIGH": "🚨",
                "MEDIUM": "⚠️",
                "OPPORTUNITY": "✨",
                "POSITIVE": "✅"
            }.get(pattern["severity"], "ℹ️")
            print(f"\n  {severity_emoji} {pattern['type']}")
            print(f"     {pattern['signal']}")
            print(f"     → Action: {pattern['action']}")
    
    # Predictions
    if analysis["predictions"]:
        print(f"\n🔮 PREDICTIONS:")
        for pred in analysis["predictions"]:
            conf_emoji = {"HIGH": "🎯", "MEDIUM": "🤔", "LOW": "💭"}
            print(f"\n  {conf_emoji.get(pred['confidence'], '💭')} {pred['prediction']} ({pred['confidence']} confidence)")
            print(f"     Why: {pred['reasoning']}")
            print(f"     → Action: {pred['suggested_action']}")
    
    # Learning insights
    recs = analysis["learned_recommendations"]
    print(f"\n🧠 LEARNED INSIGHTS:")
    print(f"  • Best channel: {recs['best_channel']}")
    print(f"  • Best message type: {recs['best_message_type']}")
    print(f"  • Avg response time: {recs['avg_response_time']}")
    
    if recs["successful_tactics"]:
        print(f"  • What works: {', '.join(recs['successful_tactics'][:3])}")
    if recs["avoid_tactics"]:
        print(f"  • Avoid: {', '.join(recs['avoid_tactics'][:2])}")
    
    print()


def show_crafted_message(bridge: BridgeIntelligence, artist_name: str):
    """Generate and show context-aware message"""
    print(f"\n{'='*70}")
    print(f"📧 CONTEXT-AWARE MESSAGE: {artist_name}")
    print(f"{'='*70}\n")
    
    print("Analyzing artist context and crafting message...\n")
    
    message = bridge.craft_check_in(artist_name)
    
    print("="*70)
    print(message)
    print("="*70)
    
    print("\n💡 This message was crafted based on:")
    print("   • Artist's communication style")
    print("   • Current relationship health")
    print("   • Detected patterns")
    print("   • Predictive intelligence")
    print("   • What's worked before")
    
    print()


def show_full_briefing(bridge: BridgeIntelligence):
    """Show comprehensive BRIDGE briefing"""
    briefing = bridge.daily_briefing()
    
    print(f"\n{'='*70}")
    print(f"🌉 FULL BRIDGE INTELLIGENCE BRIEFING")
    print(f"{'='*70}")
    print(f"📅 {briefing['date']}\n")
    
    summary = briefing["roster_summary"]
    print(f"📊 ROSTER SUMMARY:")
    print(f"   Total Artists: {summary['total_artists']}")
    print(f"   🟢 Healthy: {summary['healthy']}")
    print(f"   🟡 At Risk: {summary['at_risk']}")
    print(f"   🔴 Critical: {summary['critical']}\n")
    
    if briefing["critical_artists"]:
        print(f"🚨 CRITICAL ATTENTION ({len(briefing['critical_artists'])} artists):")
        for artist in briefing["critical_artists"]:
            print(f"   • {artist['name']}: {artist['health_status']} ({artist['health_score']}/100)")
        print()
    
    if briefing["at_risk_artists"]:
        print(f"⚠️  AT RISK ({len(briefing['at_risk_artists'])} artists):")
        for artist in briefing["at_risk_artists"]:
            print(f"   • {artist['name']}: {artist['health_status']} ({artist['health_score']}/100)")
        print()
    
    if briefing["opportunities"]:
        print(f"✨ OPPORTUNITIES ({len(briefing['opportunities'])}):")
        for opp in briefing["opportunities"]:
            print(f"\n   • {opp['artist']}")
            print(f"     Signal: {opp['opportunity']}")
            print(f"     → {opp['action']}")
        print()
    
    if briefing["predictions"]:
        print(f"🔮 PREDICTIONS ({len(briefing['predictions'])}):")
        for pred in briefing["predictions"]:
            conf_emoji = {"HIGH": "🎯", "MEDIUM": "🤔", "LOW": "💭"}
            print(f"\n   {conf_emoji.get(pred['confidence'], '💭')} {pred['artist']}: {pred['prediction']}")
            print(f"     → {pred['action']}")
        print()


def show_health_details(artists: List[Dict], bridge: BridgeIntelligence):
    """Show detailed health breakdown for all artists"""
    print(f"\n{'='*70}")
    print(f"📈 DETAILED HEALTH ANALYSIS")
    print(f"{'='*70}\n")
    
    for artist_data in artists:
        name = artist_data["artist_info"]["name"]
        score, status, breakdown = HealthScorer.calculate_health(artist_data)
        
        print(f"\n{status} {name} ({score}/100)")
        print("-" * 50)
        
        for category, data in breakdown.items():
            penalty_text = f"-{data['penalty']:.1f}" if data['penalty'] > 0 else "✓"
            print(f"  {category.capitalize():20} {penalty_text:>6}  |  {data['detail']}")
    
    print()


def show_learning_insights(artists: List[Dict]):
    """Show what BRIDGE has learned about each artist"""
    print(f"\n{'='*70}")
    print(f"🧠 LEARNING INSIGHTS - What Works With Each Artist")
    print(f"{'='*70}\n")
    
    for artist_data in artists:
        name = artist_data["artist_info"]["name"]
        recs = LearningMemory.get_recommendations(name)
        
        print(f"\n{name}")
        print("-" * 50)
        print(f"  Best Channel: {recs['best_channel']}")
        print(f"  Best Message Type: {recs['best_message_type']}")
        print(f"  Avg Response Time: {recs['avg_response_time']}")
        
        if recs["successful_tactics"]:
            print(f"  ✅ Works: {', '.join(recs['successful_tactics'][:3])}")
        if recs["avoid_tactics"]:
            print(f"  ❌ Avoid: {', '.join(recs['avoid_tactics'][:2])}")
    
    print()


# ============================================================================
# MAIN DASHBOARD
# ============================================================================

def run_dashboard():
    """Main dashboard loop"""
    
    # Initialize BRIDGE
    bridge = BridgeIntelligence()
    
    while True:
        # Load fresh data
        artists = load_all_artists()
        followups = get_pending_followups(artists)
        action_items = get_all_action_items(artists)
        recent = get_recent_activity(artists)
        
        # Get BRIDGE briefing
        briefing = bridge.daily_briefing()
        
        # Display dashboard
        print_header()
        print_bridge_briefing(briefing)
        print_health_summary(artists, bridge)
        print_followups(followups)
        print_action_items(action_items)
        print_recent_activity(recent)
        print_menu()
        
        # Get user input
        choice = input("\n👉 Select action: ").strip().lower()
        
        if choice == "q":
            print("\n👋 Closing command center. Stay sharp! 🎵\n")
            break
        
        elif choice == "1":
            # Analyze artist
            print("\nAvailable artists:")
            for i, artist_data in enumerate(artists, 1):
                print(f"   [{i}] {artist_data['artist_info']['name']}")
            
            artist_choice = input("\n👉 Select artist number: ").strip()
            try:
                idx = int(artist_choice) - 1
                if 0 <= idx < len(artists):
                    artist_name = artists[idx]["artist_info"]["name"]
                    show_artist_analysis(bridge, artist_name)
                    input("\nPress Enter to continue...")
                else:
                    print("Invalid selection")
            except ValueError:
                print("Invalid input")
        
        elif choice == "2":
            # Generate message
            print("\nAvailable artists:")
            for i, artist_data in enumerate(artists, 1):
                print(f"   [{i}] {artist_data['artist_info']['name']}")
            
            artist_choice = input("\n👉 Select artist number: ").strip()
            try:
                idx = int(artist_choice) - 1
                if 0 <= idx < len(artists):
                    artist_name = artists[idx]["artist_info"]["name"]
                    show_crafted_message(bridge, artist_name)
                    input("\nPress Enter to continue...")
                else:
                    print("Invalid selection")
            except ValueError:
                print("Invalid input")
        
        elif choice == "3":
            # Refresh (loop continues)
            print("\n🔄 Refreshing dashboard...\n")
            continue
        
        elif choice == "4":
            # Full briefing
            show_full_briefing(bridge)
            input("\nPress Enter to continue...")
        
        elif choice == "5":
            # Health details
            show_health_details(artists, bridge)
            input("\nPress Enter to continue...")
        
        elif choice == "6":
            # Learning insights
            show_learning_insights(artists)
            input("\nPress Enter to continue...")
        
        else:
            print("\n❌ Invalid choice. Try again.")
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        run_dashboard()
    except KeyboardInterrupt:
        print("\n\n👋 Command center closed. 🎵\n")