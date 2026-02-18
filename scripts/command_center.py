"""
MAESTRO Command Center
Your mission control for LRRecords artist relations
"""

import json
import ollama
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

class CommandCenter:
    def __init__(self):
        self.artists = []
        self.artist_files = []
        self.load_artists()
        
    def load_artists(self):
        """Load all artist profiles"""
        artists_dir = Path(__file__).parent.parent / 'data' / 'artists'
        for file in artists_dir.glob('*.json'):
            with open(file, 'r') as f:
                artist_data = json.load(f)
                self.artists.append(artist_data)
                self.artist_files.append(file)
    
    def get_artist_name(self, artist):
        """Extract artist name"""
        return artist.get('artist_info', {}).get('name', 'Unknown Artist')
    
    def get_last_interaction(self, artist):
        """Get date of last interaction"""
        history = artist.get('communication_history', [])
        if history:
            dates = [h.get('date') for h in history if h.get('date')]
            if dates:
                return max(dates)
        return None
    
    def days_since_contact(self, last_contact):
        """Calculate days since last contact"""
        if not last_contact:
            return 999  # No contact ever
        try:
            last_date = datetime.strptime(last_contact, '%Y-%m-%d')
            return (datetime.now() - last_date).days
        except:
            return 999
    
    def get_pending_followups(self):
        """Get all artists with pending follow-ups"""
        followups = []
        
        for artist in self.artists:
            history = artist.get('communication_history', [])
            
            for entry in history:
                if entry.get('follow_up_needed', False):
                    followups.append({
                        'artist': self.get_artist_name(artist),
                        'priority': entry.get('priority', 'MEDIUM'),
                        'follow_up_by': entry.get('follow_up_by', 'No deadline'),
                        'action': entry.get('suggested_follow_up', 'No action specified'),
                        'date': entry.get('date', 'Unknown'),
                        'sentiment': entry.get('sentiment', 'NEUTRAL')
                    })
        
        # Sort by priority
        priority_order = {'HIGH': 0, 'URGENT': 0, 'MEDIUM': 1, 'LOW': 2, 'NEUTRAL': 1, 'POSITIVE': 2, 'NEGATIVE': 0}
        followups.sort(key=lambda x: priority_order.get(x['priority'], 1))
        
        return followups
    
    def get_recent_activity(self, days=7):
        """Get recent communications"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent = []
        
        for artist in self.artists:
            history = artist.get('communication_history', [])
            artist_name = self.get_artist_name(artist)
            
            for entry in history:
                try:
                    entry_date = datetime.strptime(entry.get('date', ''), '%Y-%m-%d')
                    if entry_date >= cutoff_date:
                        recent.append({
                            'artist': artist_name,
                            'date': entry.get('date'),
                            'type': entry.get('type', 'MESSAGE'),
                            'channel': entry.get('channel', 'Unknown'),
                            'topic': entry.get('topic', 'Unknown'),
                            'sentiment': entry.get('sentiment')
                        })
                except:
                    continue
        
        recent.sort(key=lambda x: x['date'], reverse=True)
        return recent
    
    def get_action_items(self):
        """Get all pending action items across all artists"""
        actions = []
        
        for artist in self.artists:
            history = artist.get('communication_history', [])
            artist_name = self.get_artist_name(artist)
            
            for entry in history:
                if entry.get('type') == 'RESPONSE_RECEIVED':
                    action_items = entry.get('action_items', [])
                    for action in action_items:
                        actions.append({
                            'artist': artist_name,
                            'action': action,
                            'priority': entry.get('priority', 'MEDIUM'),
                            'date_received': entry.get('date', 'Unknown')
                        })
        
        return actions
    
    def get_artist_health(self):
        """Analyze which artists need attention"""
        health = []
        
        for artist in self.artists:
            artist_name = self.get_artist_name(artist)
            last_contact = self.get_last_interaction(artist)
            days_since = self.days_since_contact(last_contact)
            
            # Determine health status
            if days_since > 60:
                status = "🔴 CRITICAL"
            elif days_since > 30:
                status = "🟡 WARNING"
            elif days_since > 14:
                status = "🟢 OK"
            else:
                status = "✅ RECENT"
            
            health.append({
                'artist': artist_name,
                'last_contact': last_contact or 'Never',
                'days_since': days_since if days_since < 999 else 'Never',
                'status': status,
                'projects': len(artist.get('current_projects', []))
            })
        
        health.sort(key=lambda x: x['days_since'] if isinstance(x['days_since'], int) else 999, reverse=True)
        return health
    
    def display_summary(self):
        """Display summary stats"""
        print("\n" + "=" * 80)
        print("🎛️  MAESTRO COMMAND CENTER")
        print("=" * 80)
        
        # Overall stats
        total_artists = len(self.artists)
        followups = self.get_pending_followups()
        high_priority = [f for f in followups if f['priority'] in ['HIGH', 'URGENT']]
        actions = self.get_action_items()
        
        print(f"\n📊 OVERVIEW:")
        print(f"   Total Artists: {total_artists}")
        print(f"   Pending Follow-ups: {len(followups)}")
        print(f"   High Priority: {len(high_priority)}")
        print(f"   Total Action Items: {len(actions)}")
    
    def display_high_priority_alerts(self):
        """Display urgent items"""
        followups = self.get_pending_followups()
        high_priority = [f for f in followups if f['priority'] in ['HIGH', 'URGENT']]
        
        if high_priority:
            print("\n" + "=" * 80)
            print("🚨 HIGH PRIORITY ALERTS")
            print("=" * 80)
            
            for item in high_priority:
                print(f"\n🔥 {item['artist']}")
                print(f"   Priority: {item['priority']}")
                print(f"   Follow-up by: {item['follow_up_by']}")
                print(f"   Action: {item['action']}")
                print(f"   Sentiment: {item['sentiment']}")
        else:
            print("\n✅ No high priority alerts!")
    
    def display_followups(self):
        """Display all pending follow-ups"""
        followups = self.get_pending_followups()
        
        if followups:
            print("\n" + "=" * 80)
            print("📋 PENDING FOLLOW-UPS")
            print("=" * 80)
            
            for item in followups:
                priority_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(item['priority'], "⚪")
                print(f"\n{priority_emoji} {item['artist']} - {item['priority']}")
                print(f"   Deadline: {item['follow_up_by']}")
                print(f"   Action: {item['action']}")
        else:
            print("\n✅ No pending follow-ups!")
    
    def display_recent_activity(self):
        """Display recent communications"""
        recent = self.get_recent_activity(days=7)
        
        print("\n" + "=" * 80)
        print("📅 RECENT ACTIVITY (Last 7 Days)")
        print("=" * 80)
        
        if recent:
            for item in recent[:10]:  # Show top 10
                sentiment_emoji = {
                    "POSITIVE": "😊",
                    "NEGATIVE": "😟",
                    "NEUTRAL": "😐",
                    "URGENT": "🚨"
                }.get(item.get('sentiment'), "📝")
                
                print(f"\n{sentiment_emoji} {item['date']} - {item['artist']}")
                print(f"   {item['channel']}: {item['topic']}")
        else:
            print("\n⚠️ No recent activity in the last 7 days")
    
    def display_action_items(self):
        """Display all action items"""
        actions = self.get_action_items()
        
        if actions:
            print("\n" + "=" * 80)
            print("✅ ACTION ITEMS")
            print("=" * 80)
            
            for item in actions:
                priority_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(item['priority'], "⚪")
                print(f"\n{priority_emoji} {item['artist']}")
                print(f"   → {item['action']}")
                print(f"   (From: {item['date_received']})")
        else:
            print("\n✅ No pending action items!")
    
    def display_artist_health(self):
        """Display artist relationship health"""
        health = self.get_artist_health()
        
        print("\n" + "=" * 80)
        print("💚 ARTIST RELATIONSHIP HEALTH")
        print("=" * 80)
        
        for item in health:
            print(f"\n{item['status']} {item['artist']}")
            print(f"   Last Contact: {item['last_contact']} ({item['days_since']} days ago)")
            print(f"   Active Projects: {item['projects']}")
    
    def display_menu(self):
        """Display interactive menu"""
        print("\n" + "=" * 80)
        print("📋 COMMAND CENTER OPTIONS")
        print("=" * 80)
        print("  [1] Show Summary Dashboard")
        print("  [2] Show High Priority Alerts Only")
        print("  [3] Show All Follow-ups")
        print("  [4] Show Recent Activity")
        print("  [5] Show Action Items")
        print("  [6] Show Artist Health")
        print("  [7] Full Report (Everything)")
        print("  [R] Refresh Data")
        print("  [Q] Quit")
        
        return input("\nSelect option: ").strip().lower()
    
    def run_full_report(self):
        """Display complete dashboard"""
        self.display_summary()
        self.display_high_priority_alerts()
        self.display_followups()
        self.display_recent_activity()
        self.display_action_items()
        self.display_artist_health()
        print("\n" + "=" * 80)
    
    def run_interactive(self):
        """Interactive command center"""
        while True:
            choice = self.display_menu()
            
            if choice == '1':
                self.display_summary()
            elif choice == '2':
                self.display_high_priority_alerts()
            elif choice == '3':
                self.display_followups()
            elif choice == '4':
                self.display_recent_activity()
            elif choice == '5':
                self.display_action_items()
            elif choice == '6':
                self.display_artist_health()
            elif choice == '7':
                self.run_full_report()
            elif choice == 'r':
                print("\n🔄 Refreshing data...")
                self.load_artists()
                print("✅ Data refreshed!")
            elif choice == 'q':
                print("\n👋 Closing Command Center...")
                break
            else:
                print("\n❌ Invalid option. Try again.")

if __name__ == "__main__":
    center = CommandCenter()
    center.run_interactive()