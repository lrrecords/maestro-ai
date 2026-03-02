"""
🤖 MAESTRO AUTOPILOT - Autonomous Artist Relations System
"""

import json
import os
import time
import schedule
from datetime import datetime, timedelta
from typing import Dict, List
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

from bridge_intelligence import BridgeIntelligence, HealthScorer, PatternDetector, Predictor

load_dotenv()

CONFIG_FILE = "data/autopilot_config.json"
ACTION_LOG_FILE = "data/autopilot_actions.log"
QUEUE_FILE = "data/autopilot_queue.json"

DEFAULT_CONFIG = {
    "enabled": True,
    "check_interval_minutes": 60,
    "daily_briefing": {
        "enabled": True,
        "time": "09:00",
        "send_email": True,
        "email_recipient": os.getenv("EMAIL_ADDRESS")
    },
    "auto_checkins": {
        "enabled": True,
        "health_threshold": 50,
        "days_since_contact_threshold": 30,
        "require_approval": True,
        "max_per_day": 3
    },
    "critical_alerts": {
        "enabled": True,
        "health_threshold": 40,
        "send_email": True
    },
    "momentum_alerts": {
        "enabled": True,
        "send_email": False
    },
    "rate_limits": {
        "max_emails_per_hour": 5,
        "max_emails_per_day": 20
    }
}

class AutopilotEngine:
    def __init__(self):
        self.config = self._load_config()
        self.bridge = BridgeIntelligence()
        self.action_queue = self._load_queue()
        self.email_count = {"hour": 0, "day": 0, "last_reset": datetime.now()}
        print("🤖 MAESTRO AUTOPILOT initializing...")
        self._log_action("SYSTEM", "Autopilot engine started")
    
    def _load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        os.makedirs("data", exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        return DEFAULT_CONFIG
    
    def _load_queue(self):
        if os.path.exists(QUEUE_FILE):
            with open(QUEUE_FILE, "r") as f:
                return json.load(f)
        return []
    
    def _save_queue(self):
        with open(QUEUE_FILE, "w") as f:
            json.dump(self.action_queue, f, indent=2)
    
    def _log_action(self, action_type, description, artist=None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{action_type}]"
        if artist:
            log_entry += f" [{artist}]"
        log_entry += f" {description}\n"
        os.makedirs("data", exist_ok=True)
        with open(ACTION_LOG_FILE, "a") as f:
            f.write(log_entry)
        print(f"📝 {log_entry.strip()}")
    
    def _reset_rate_limits(self):
        now = datetime.now()
        if (now - self.email_count["last_reset"]).seconds >= 3600:
            self.email_count["hour"] = 0
            self.email_count["last_reset"] = now
        if now.date() != self.email_count["last_reset"].date():
            self.email_count["day"] = 0
            self.email_count["last_reset"] = now
    
    def _can_send_email(self):
        self._reset_rate_limits()
        hour_limit = self.config["rate_limits"]["max_emails_per_hour"]
        day_limit = self.config["rate_limits"]["max_emails_per_day"]
        return (self.email_count["hour"] < hour_limit and self.email_count["day"] < day_limit)
    
    def _increment_email_count(self):
        self.email_count["hour"] += 1
        self.email_count["day"] += 1
    
    def _send_email(self, subject, body, recipient=None):
        if not self._can_send_email():
            self._log_action("EMAIL_BLOCKED", "Rate limit reached")
            return False
        try:
            recipient = recipient or os.getenv("EMAIL_ADDRESS")
            msg = MIMEMultipart()
            msg["From"] = os.getenv("EMAIL_ADDRESS")
            msg["To"] = recipient
            msg["Subject"] = f"🤖 MAESTRO: {subject}"
            msg.attach(MIMEText(body, "plain"))
            server = smtplib.SMTP_SSL(
                os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com"),
                int(os.getenv("EMAIL_SMTP_PORT", 465))
            )
            server.login(os.getenv("EMAIL_ADDRESS"), os.getenv("EMAIL_PASSWORD"))
            server.send_message(msg)
            server.quit()
            self._increment_email_count()
            self._log_action("EMAIL_SENT", f"Sent: {subject}")
            return True
        except Exception as e:
            self._log_action("EMAIL_FAILED", f"Error: {e}")
            return False
    
    def daily_briefing_task(self):
        if not self.config["daily_briefing"]["enabled"]:
            return
        self._log_action("BRIEFING", "Generating daily briefing")
        briefing = self.bridge.daily_briefing()
        email_body = self._format_briefing_email(briefing)
        if self.config["daily_briefing"]["send_email"]:
            subject = f"Daily Briefing - {briefing['date']}"
            self._send_email(subject, email_body)
        briefing_file = f"data/briefings/briefing_{briefing['date']}.txt"
        os.makedirs("data/briefings", exist_ok=True)
        with open(briefing_file, "w", encoding='utf-8') as f:
            f.write(email_body)
        self._log_action("BRIEFING", f"Saved to {briefing_file}")
    
    def monitor_artist_health_task(self):
        if not self.config["auto_checkins"]["enabled"]:
            return
        artists = self.bridge.load_all_artists()
        actions_taken = 0
        max_actions = self.config["auto_checkins"]["max_per_day"]
        for artist_data in artists:
            if actions_taken >= max_actions:
                break
            artist_name = artist_data["artist_info"]["name"]
            health_score, health_status, _ = HealthScorer.calculate_health(artist_data)
            health_threshold = self.config["auto_checkins"]["health_threshold"]
            if health_score < health_threshold:
                last_contact = artist_data.get("last_contact_date")
                days_ago = (datetime.now() - datetime.fromisoformat(last_contact)).days if last_contact else 999
                days_threshold = self.config["auto_checkins"]["days_since_contact_threshold"]
                if days_ago >= days_threshold:
                    self._log_action("HEALTH_ALERT", f"{artist_name} health: {health_score}/100, {days_ago} days since contact", artist_name)
                    self._queue_auto_checkin(artist_data, health_score, days_ago)
                    actions_taken += 1
    
    def check_critical_alerts_task(self):
        if not self.config["critical_alerts"]["enabled"]:
            return
        artists = self.bridge.load_all_artists()
        critical_threshold = self.config["critical_alerts"]["health_threshold"]
        critical_artists = []
        for artist_data in artists:
            artist_name = artist_data["artist_info"]["name"]
            health_score, health_status, _ = HealthScorer.calculate_health(artist_data)
            if health_score < critical_threshold:
                critical_artists.append({"name": artist_name, "health_score": health_score, "status": health_status})
        if critical_artists and self.config["critical_alerts"]["send_email"]:
            alert_body = "🚨 CRITICAL ARTIST HEALTH ALERT\n\n"
            alert_body += f"{len(critical_artists)} artist(s) need immediate attention:\n\n"
            for artist in critical_artists:
                alert_body += f"• {artist['name']}: {artist['status']} ({artist['health_score']}/100)\n"
            alert_body += "\n👉 Open Command Center for details."
            self._send_email("CRITICAL ALERT - Artist Health", alert_body)
            self._log_action("CRITICAL_ALERT", f"{len(critical_artists)} artists critical")
    
    def check_momentum_opportunities_task(self):
        if not self.config["momentum_alerts"]["enabled"]:
            return
        artists = self.bridge.load_all_artists()
        opportunities = []
        for artist_data in artists:
            artist_name = artist_data["artist_info"]["name"]
            predictions = Predictor.predict_needs(artist_data)
            momentum_predictions = [p for p in predictions if p["prediction"] == "MOMENTUM_WINDOW"]
            if momentum_predictions:
                opportunities.append({"artist": artist_name, "prediction": momentum_predictions[0]})
        if opportunities:
            self._log_action("MOMENTUM", f"{len(opportunities)} momentum opportunities detected")
            if self.config["momentum_alerts"]["send_email"]:
                alert_body = "✨ MOMENTUM OPPORTUNITIES DETECTED\n\n"
                for opp in opportunities:
                    alert_body += f"• {opp['artist']}\n  {opp['prediction']['reasoning']}\n  → {opp['prediction']['suggested_action']}\n\n"
                self._send_email("Momentum Opportunities", alert_body)
    
    def _queue_auto_checkin(self, artist_data, health_score, days_since_contact):
        artist_name = artist_data["artist_info"]["name"]
        context = f"Artist health at {health_score}/100, no contact for {days_since_contact} days"
        message = self.bridge.craft_check_in(artist_name, context)
        action = {
            "id": f"checkin_{artist_name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "type": "AUTO_CHECKIN",
            "artist": artist_name,
            "artist_email": artist_data["artist_info"].get("email"),
            "message": message,
            "context": {"health_score": health_score, "days_since_contact": days_since_contact, "reason": "Health below threshold"},
            "created_at": datetime.now().isoformat(),
            "status": "PENDING_APPROVAL" if self.config["auto_checkins"]["require_approval"] else "APPROVED",
            "executed_at": None
        }
        self.action_queue.append(action)
        self._save_queue()
        self._log_action("QUEUE_ADD", f"Check-in queued for {artist_name}", artist_name)
    
    def process_queue(self):
        executed_count = 0
        for action in self.action_queue[:]:
            if action["status"] == "APPROVED" and action["executed_at"] is None:
                if action["type"] == "AUTO_CHECKIN":
                    success = self._send_checkin_email(action)
                    if success:
                        action["executed_at"] = datetime.now().isoformat()
                        action["status"] = "EXECUTED"
                        executed_count += 1
                    else:
                        action["status"] = "FAILED"
        self._save_queue()
        if executed_count > 0:
            self._log_action("QUEUE_PROCESS", f"Executed {executed_count} actions")
    
    def _send_checkin_email(self, action):
        try:
            artist_name = action["artist"]
            artist_email = action["artist_email"]
            message = action["message"]
            if not artist_email:
                self._log_action("EMAIL_FAILED", f"No email for {artist_name}", artist_name)
                return False
            msg = MIMEMultipart()
            msg["From"] = os.getenv("EMAIL_ADDRESS")
            msg["To"] = artist_email
            msg["Subject"] = "Checking in"
            msg.attach(MIMEText(message, "plain"))
            server = smtplib.SMTP_SSL(os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com"), int(os.getenv("EMAIL_SMTP_PORT", 465)))
            server.login(os.getenv("EMAIL_ADDRESS"), os.getenv("EMAIL_PASSWORD"))
            server.send_message(msg)
            server.quit()
            self._increment_email_count()
            self._log_action("CHECKIN_SENT", f"Auto check-in sent to {artist_name}", artist_name)
            self._update_artist_last_contact(artist_name, message)
            return True
        except Exception as e:
            self._log_action("EMAIL_FAILED", f"Error: {e}")
            return False
    
    def _update_artist_last_contact(self, artist_name, message):
        artist_data = self.bridge.load_artist(artist_name)
        if not artist_data:
            return
        artist_data["last_contact_date"] = datetime.now().isoformat()
        if "communication_history" not in artist_data:
            artist_data["communication_history"] = []
        artist_data["communication_history"].append({
            "date": datetime.now().isoformat(),
            "type": "AUTO_CHECKIN",
            "channel": "Email",
            "message": message,
            "sent_by": "AUTOPILOT"
        })
        filename = artist_name.lower().replace(" ", "_") + ".json"
        filepath = os.path.join("data/artists", filename)
        with open(filepath, "w", encoding='utf-8') as f:
            json.dump(artist_data, f, indent=2)
    
    def _format_briefing_email(self, briefing):
        body = f"🌉 MAESTRO DAILY BRIEFING\n{'='*60}\n📅 {briefing['date']}\n\n"
        summary = briefing["roster_summary"]
        body += f"📊 ROSTER HEALTH:\n   Total: {summary['total_artists']} artists\n"
        body += f"   🟢 Healthy: {summary['healthy']}\n   🟡 At Risk: {summary['at_risk']}\n   🔴 Critical: {summary['critical']}\n\n"
        if briefing["critical_artists"]:
            body += f"🚨 CRITICAL ATTENTION:\n"
            for artist in briefing["critical_artists"]:
                body += f"   • {artist['name']}: {artist['health_score']}/100\n"
            body += "\n"
        if briefing["at_risk_artists"]:
            body += f"⚠️  AT RISK:\n"
            for artist in briefing["at_risk_artists"][:3]:
                body += f"   • {artist['name']}: {artist['health_score']}/100\n"
            body += "\n"
        if briefing["opportunities"]:
            body += f"✨ OPPORTUNITIES:\n"
            for opp in briefing["opportunities"][:3]:
                body += f"   • {opp['artist']}: {opp['opportunity']}\n     → {opp['action']}\n"
            body += "\n"
        if briefing["predictions"]:
            body += f"🔮 PREDICTIONS:\n"
            for pred in briefing["predictions"][:3]:
                body += f"   • {pred['artist']}: {pred['prediction']}\n     → {pred['action']}\n"
            body += "\n"
        body += f"{'='*60}\n👉 Open Command Center for details.\n"
        return body
    
    def run(self):
        if not self.config["enabled"]:
            print("⚠️  Autopilot is disabled")
            return
        if self.config["daily_briefing"]["enabled"]:
            briefing_time = self.config["daily_briefing"]["time"]
            schedule.every().day.at(briefing_time).do(self.daily_briefing_task)
            print(f"📅 Daily briefing scheduled for {briefing_time}")
        check_interval = self.config["check_interval_minutes"]
        schedule.every(check_interval).minutes.do(self.monitor_artist_health_task)
        schedule.every(check_interval).minutes.do(self.check_critical_alerts_task)
        schedule.every(check_interval).minutes.do(self.check_momentum_opportunities_task)
        schedule.every(5).minutes.do(self.process_queue)
        print(f"🔄 Health monitoring every {check_interval} minutes")
        print(f"🤖 Autopilot running... (Ctrl+C to stop)\n")
        self.monitor_artist_health_task()
        self.check_critical_alerts_task()
        while True:
            schedule.run_pending()
            time.sleep(60)

def view_queue():
    if not os.path.exists(QUEUE_FILE):
        print("\n📭 Action queue is empty\n")
        return
    with open(QUEUE_FILE, "r") as f:
        queue = json.load(f)
    if not queue:
        print("\n📭 Action queue is empty\n")
        return
    print(f"\n{'='*70}\n📋 AUTOPILOT ACTION QUEUE ({len(queue)} items)\n{'='*70}\n")
    pending = [a for a in queue if a["status"] == "PENDING_APPROVAL"]
    approved = [a for a in queue if a["status"] == "APPROVED" and not a["executed_at"]]
    executed = [a for a in queue if a["status"] == "EXECUTED"]
    if pending:
        print(f"⏳ PENDING APPROVAL ({len(pending)}):")
        for i, action in enumerate(pending, 1):
            print(f"\n   [{i}] {action['type']} - {action['artist']}")
            print(f"       Created: {action['created_at']}")
            print(f"       Reason: {action['context'].get('reason', 'N/A')}")
            if action["type"] == "AUTO_CHECKIN":
                print(f"       Health: {action['context']['health_score']}/100")
                print(f"       Preview: {action['message'][:100]}...")
        print()
    if approved:
        print(f"✅ APPROVED ({len(approved)}):")
        for action in approved:
            print(f"   • {action['artist']}: {action['type']}")
        print()
    if executed:
        print(f"📧 EXECUTED ({len(executed)}):")
        for action in executed[-5:]:
            print(f"   • {action['artist']}: {action['type']} at {action['executed_at']}")
        print()
    if pending:
        print("="*70 + "\n[A] Approve all | [R] Reject all | [#] Approve specific | [Q] Quit\n" + "="*70)
        choice = input("\n👉 Action: ").strip().lower()
        if choice == "a":
            for action in pending:
                action["status"] = "APPROVED"
            with open(QUEUE_FILE, "w") as f:
                json.dump(queue, f, indent=2)
            print(f"\n✅ Approved {len(pending)} actions\n")
        elif choice == "r":
            for action in pending:
                action["status"] = "REJECTED"
            with open(QUEUE_FILE, "w") as f:
                json.dump(queue, f, indent=2)
            print(f"\n❌ Rejected {len(pending)} actions\n")

def main():
    import sys
    if len(sys.argv) < 2:
        print("\n🤖 MAESTRO AUTOPILOT\n" + "="*60)
        print("Usage:\n  python maestro_autopilot.py run\n  python maestro_autopilot.py queue\n  python maestro_autopilot.py test\n  python maestro_autopilot.py briefing\n")
        return
    command = sys.argv[1].lower()
    if command == "run":
        engine = AutopilotEngine()
        try:
            engine.run()
        except KeyboardInterrupt:
            print("\n\n🛑 Autopilot stopped\n")
    elif command == "queue":
        view_queue()
    elif command == "test":
        print("\n🧪 Testing autopilot systems...\n")
        engine = AutopilotEngine()
        print("✅ Engine initialized\n✅ BRIDGE intelligence loaded\n✅ Configuration loaded\n✅ Action queue loaded\n")
        print("🎯 Running test checks...")
        engine.monitor_artist_health_task()
        engine.check_critical_alerts_task()
        print("\n✅ All systems operational\n")
    elif command == "briefing":
        engine = AutopilotEngine()
        print("\n📧 Sending test briefing...\n")
        engine.daily_briefing_task()
        print("✅ Briefing complete\n")
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()