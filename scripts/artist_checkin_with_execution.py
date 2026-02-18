"""
MAESTRO Artist Check-In Workflow with EXECUTION
Hour 4: Adding message sending capability
"""

import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path
import ollama
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Load contexts
def load_context(filename):
    path = Path(__file__).parent.parent / 'data' / filename
    with open(path, 'r') as f:
        return json.load(f)

# Load all artist profiles
def load_all_artists():
    artists_dir = Path(__file__).parent.parent / 'data' / 'artists'
    artists = []
    artist_files = []
    for file in artists_dir.glob('*.json'):
        with open(file, 'r') as f:
            artist_data = json.load(f)
            artists.append(artist_data)
            artist_files.append(file)
    return artists, artist_files

class MessageSender:
    """Handles actual message sending via different channels"""
    
    def __init__(self):
        self.email_address = os.getenv('EMAIL_ADDRESS')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.smtp_server = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('EMAIL_SMTP_PORT', '587'))
    
    def send_email(self, to_email, subject, message):
        """Send email via SMTP (handles both SSL and STARTTLS)"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message, 'plain'))
            
            # Port 465 uses SSL, port 587 uses STARTTLS
            if self.smtp_port == 465:
                # SSL connection
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                # STARTTLS connection (port 587)
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
            
            server.login(self.email_address, self.email_password)
            text = msg.as_string()
            server.sendmail(self.email_address, to_email, text)
            server.quit()
            
            return True, "Email sent successfully"
        except Exception as e:
            return False, f"Email failed: {str(e)}"
    
    def send_sms(self, to_phone, message):
        """Send SMS via Twilio (optional)"""
        try:
            # Uncomment if you set up Twilio
            # from twilio.rest import Client
            # client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
            # message = client.messages.create(
            #     body=message,
            #     from_=os.getenv('TWILIO_PHONE_NUMBER'),
            #     to=to_phone
            # )
            # return True, f"SMS sent: {message.sid}"
            
            return False, "SMS not configured (Twilio setup required)"
        except Exception as e:
            return False, f"SMS failed: {str(e)}"

class ArtistCheckinWorkflowWithExecution:
    def __init__(self):
        self.lr_context = load_context('lr_records_context.json')
        self.comm_profile = load_context('brett_communication_profile.json')
        self.artists, self.artist_files = load_all_artists()
        self.sender = MessageSender()
        
    def get_artist_name(self, artist):
        """Extract artist name from nested structure"""
        return artist.get('artist_info', {}).get('name', 'Unknown Artist')
    
    def get_artist_file(self, artist):
        """Get the file path for this artist"""
        artist_name = self.get_artist_name(artist)
        for i, a in enumerate(self.artists):
            if self.get_artist_name(a) == artist_name:
                return self.artist_files[i]
        return None
    
    def get_last_contact_date(self, artist):
        """Get most recent contact date"""
        history = artist.get('communication_history', [])
        if history:
            dates = [h.get('date') for h in history if h.get('date')]
            if dates:
                return max(dates)
        return None
    
    def analyze_artist_priority(self, artist):
        """BRIDGE analyzes artist and determines priority"""
        artist_name = self.get_artist_name(artist)
        last_contact = self.get_last_contact_date(artist)
        
        prompt = f"""You are BRIDGE, the Artist Relations Director for LRRecords.

ARTIST PROFILE:
{json.dumps(artist, indent=2)}

CURRENT DATE: {datetime.now().strftime('%B %d, %Y')}
LAST CONTACT: {last_contact if last_contact else 'Unknown'}

Analyze this artist's current status and determine:
1. Priority level (HIGH/MEDIUM/LOW) for check-in
2. Reason for this priority
3. Specific things to reference in check-in
4. Suggested timing for contact

Return ONLY valid JSON:
{{
    "priority": "HIGH|MEDIUM|LOW",
    "reason": "why this priority",
    "reference_points": ["point1", "point2"],
    "suggested_timing": "when to reach out",
    "urgency_score": 1-10
}}"""

        response = ollama.chat(
            model='llama3.1:8b',
            messages=[{'role': 'user', 'content': prompt}],
            format='json'
        )
        
        return json.loads(response['message']['content'])
    
    def draft_checkin_message(self, artist, analysis):
        """BRIDGE drafts personalized check-in in Brett's voice"""
        artist_name = self.get_artist_name(artist)
        current_projects = artist.get('current_projects', [])
        
        prompt = f"""You are BRIDGE, drafting a check-in message for Brett Caporn (LRRecords owner).

ARTIST: {artist_name}
CURRENT PROJECTS: {json.dumps(current_projects, indent=2)}
ANALYSIS: {json.dumps(analysis, indent=2)}

BRETT'S COMMUNICATION STYLE:
- Direct, friendly, action-oriented
- High energy, celebrates wins
- Uses casual language ("Yo!", "How's it going?", "Pumped!")
- Keeps it real and authentic
- Shows genuine interest
- Uses Australian slang naturally
- SHORT messages (2-3 sentences max)

Draft a check-in message for {artist_name}.

Return ONLY valid JSON:
{{
    "message": "the full message text (2-3 sentences)",
    "tone": "description of tone used",
    "suggested_subject": "if email, otherwise null"
}}"""

        response = ollama.chat(
            model='llama3.1:8b',
            messages=[{'role': 'user', 'content': prompt}],
            format='json'
        )
        
        return json.loads(response['message']['content'])
    
    def log_interaction(self, artist, channel, message, outcome):
        """Log the interaction to artist's communication_history"""
        artist_file = self.get_artist_file(artist)
        if not artist_file:
            print("⚠️ Could not find artist file to log interaction")
            return
        
        # Create new communication entry
        new_entry = {
            "date": datetime.now().strftime('%Y-%m-%d'),
            "channel": channel,
            "topic": "Check-in via MAESTRO",
            "message_sent": message,
            "outcome": outcome,
            "follow_up_needed": False,
            "automated": True
        }
        
        # Add to artist profile
        if 'communication_history' not in artist:
            artist['communication_history'] = []
        
        artist['communication_history'].append(new_entry)
        
        # Save back to file
        with open(artist_file, 'w') as f:
            json.dump(artist, f, indent=2)
        
        print(f"✅ Logged interaction to {artist_file.name}")
    
    def interactive_review(self, artist, analysis, draft):
        """Interactive review and sending interface"""
        artist_name = self.get_artist_name(artist)
        artist_info = artist.get('artist_info', {})
        preferred_contact = artist_info.get('preferred_contact_method', 'Unknown')
        
        print("\n" + "=" * 70)
        print(f"📧 READY TO SEND: {artist_name}")
        print("=" * 70)
        print(f"Priority: {analysis['priority']} ({analysis['urgency_score']}/10)")
        print(f"Preferred Contact: {preferred_contact}")
        print(f"\n💬 MESSAGE:")
        print("-" * 70)
        print(draft['message'])
        print("-" * 70)
        
        if draft.get('suggested_subject'):
            print(f"Subject: {draft['suggested_subject']}")
        
        print("\n📋 OPTIONS:")
        print("  [1] Send Email")
        print("  [2] Send SMS (if configured)")
        print("  [3] Copy for Manual DM (Instagram/WhatsApp)")
        print("  [4] Edit Message")
        print("  [5] Skip (don't send)")
        print("  [Q] Quit workflow")
        
        choice = input("\nYour choice: ").strip().lower()
        
        if choice == '1':
            # Send email
            email = input(f"Enter {artist_name}'s email address: ").strip()
            if email:
                subject = draft.get('suggested_subject', f"Quick check-in - {artist_name}")
                success, result = self.sender.send_email(email, subject, draft['message'])
                
                if success:
                    print(f"\n✅ {result}")
                    self.log_interaction(artist, "Email", draft['message'], "Sent successfully")
                    return True
                else:
                    print(f"\n❌ {result}")
                    return False
        
        elif choice == '2':
            # Send SMS
            phone = input(f"Enter {artist_name}'s phone number (with country code): ").strip()
            if phone:
                success, result = self.sender.send_sms(phone, draft['message'])
                print(f"\n{'✅' if success else '❌'} {result}")
                
                if success:
                    self.log_interaction(artist, "SMS", draft['message'], "Sent successfully")
                return success
        
        elif choice == '3':
            # Copy for manual DM
            print("\n📋 MESSAGE COPIED TO CLIPBOARD (copy manually):")
            print("-" * 70)
            print(draft['message'])
            print("-" * 70)
            
            sent = input("\nDid you send this message? (y/n): ").strip().lower()
            if sent == 'y':
                channel = input("Channel used (Instagram/WhatsApp/Other): ").strip()
                self.log_interaction(artist, channel, draft['message'], "Sent manually")
                return True
        
        elif choice == '4':
            # Edit message
            print("\n✏️ EDIT MESSAGE:")
            print("(Current message shown above, enter new version)")
            new_message = input("\nNew message: ").strip()
            if new_message:
                draft['message'] = new_message
                return self.interactive_review(artist, analysis, draft)  # Re-show with edit
        
        elif choice == '5':
            # Skip
            print(f"\n⏭️ Skipped {artist_name}")
            return False
        
        elif choice == 'q':
            print("\n👋 Exiting workflow...")
            return None  # Signal to quit
        
        return False
    
    def run_full_workflow(self):
        """Run complete workflow with execution"""
        print("🎵 MAESTRO Artist Check-In Workflow (WITH EXECUTION)")
        print("=" * 70)
        print(f"Analyzing {len(self.artists)} artists...\n")
        
        results = []
        
        # Step 1: Analyze all artists
        for artist in self.artists:
            artist_name = self.get_artist_name(artist)
            print(f"Analyzing: {artist_name}...")
            
            try:
                analysis = self.analyze_artist_priority(artist)
                draft = self.draft_checkin_message(artist, analysis)
                
                results.append({
                    'artist': artist,
                    'analysis': analysis,
                    'draft': draft
                })
                
                print(f"  Priority: {analysis['priority']} (Score: {analysis['urgency_score']}/10)\n")
                
            except Exception as e:
                print(f"  ❌ Error: {e}\n")
                continue
        
        # Sort by priority
        results.sort(key=lambda x: x['analysis']['urgency_score'], reverse=True)
        
        # Step 2: Interactive review and sending
        print("\n" + "=" * 70)
        print("📤 INTERACTIVE SENDING")
        print("=" * 70)
        
        sent_count = 0
        
        for result in results:
            outcome = self.interactive_review(
                result['artist'],
                result['analysis'],
                result['draft']
            )
            
            if outcome is None:  # User quit
                break
            elif outcome:
                sent_count += 1
        
        print("\n" + "=" * 70)
        print(f"✅ Workflow complete! Sent {sent_count} messages.")
        print("=" * 70)

# Main execution
if __name__ == "__main__":
    print("🚀 Starting MAESTRO Artist Relations Workflow with EXECUTION...\n")
    
    # Check for .env file
    if not Path('.env').exists():
        print("⚠️ WARNING: No .env file found!")
        print("Email sending will fail without credentials.")
        print("Create .env file with EMAIL_ADDRESS and EMAIL_PASSWORD")
        print("\nContinuing anyway...\n")
    
    workflow = ArtistCheckinWorkflowWithExecution()
    workflow.run_full_workflow()