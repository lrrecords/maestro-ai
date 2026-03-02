"""
🌉 BRIDGE - Artist Relations Intelligence Director
Multi-layered AI system for artist relationship management

Layers:
1. Health Scoring - Quantifies relationship health
2. Pattern Detection - Spots trends in communication
3. Context-Aware Messaging - Tailors communication per artist
4. Predictive Intelligence - Forecasts needs before they're urgent  
5. Learning Memory - Remembers what works over time
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import ollama
from collections import defaultdict

# ============================================================================
# CONFIGURATION
# ============================================================================

ARTIST_FOLDER = "data/artists"
LEARNING_FILE = "data/bridge_learnings.json"
CONTEXT_FILE = "data/lr_records_context.json"
COMM_PROFILE = "data/brett_communication_profile.json"

# Health scoring weights
WEIGHTS = {
    "recency": 0.35,
    "sentiment": 0.25,
    "responsiveness": 0.20,
    "project_momentum": 0.15,
    "open_loops": 0.05
}

# ============================================================================
# LAYER 1: HEALTH SCORING SYSTEM
# ============================================================================

class HealthScorer:
    """Quantifies artist relationship health (0-100 score)"""
    
    @staticmethod
    def calculate_health(artist_data: Dict) -> Tuple[int, str, Dict]:
        """
        Returns: (score, status_label, breakdown)
        """
        score = 100
        breakdown = {}
        
        # 1. RECENCY SCORE (35% weight)
        recency_score, recency_penalty = HealthScorer._score_recency(artist_data)
        score -= recency_penalty
        breakdown["recency"] = {
            "score": recency_score,
            "penalty": recency_penalty,
            "detail": HealthScorer._get_recency_detail(artist_data)
        }
        
        # 2. SENTIMENT SCORE (25% weight)
        sentiment_score, sentiment_penalty = HealthScorer._score_sentiment(artist_data)
        score -= sentiment_penalty
        breakdown["sentiment"] = {
            "score": sentiment_score,
            "penalty": sentiment_penalty,
            "detail": HealthScorer._get_sentiment_detail(artist_data)
        }
        
        # 3. RESPONSIVENESS SCORE (20% weight)
        response_score, response_penalty = HealthScorer._score_responsiveness(artist_data)
        score -= response_penalty
        breakdown["responsiveness"] = {
            "score": response_score,
            "penalty": response_penalty,
            "detail": HealthScorer._get_responsiveness_detail(artist_data)
        }
        
        # 4. PROJECT MOMENTUM SCORE (15% weight)
        momentum_score, momentum_penalty = HealthScorer._score_momentum(artist_data)
        score -= momentum_penalty
        breakdown["momentum"] = {
            "score": momentum_score,
            "penalty": momentum_penalty,
            "detail": HealthScorer._get_momentum_detail(artist_data)
        }
        
        # 5. OPEN LOOPS SCORE (5% weight)
        loops_score, loops_penalty = HealthScorer._score_open_loops(artist_data)
        score -= loops_penalty
        breakdown["open_loops"] = {
            "score": loops_score,
            "penalty": loops_penalty,
            "detail": f"{len(artist_data.get('open_action_items', []))} open items"
        }
        
        final_score = max(0, min(100, score))
        status = HealthScorer._get_status_label(final_score)
        
        return final_score, status, breakdown
    
    @staticmethod
    def _score_recency(artist_data: Dict) -> Tuple[int, float]:
        """How recently did we contact them?"""
        last_contact = artist_data.get("last_contact_date")
        
        if not last_contact:
            return 0, 35.0  # Maximum penalty
        
        days_ago = (datetime.now() - datetime.fromisoformat(last_contact)).days
        
        if days_ago <= 14:
            return 100, 0
        elif days_ago <= 30:
            penalty = (days_ago - 14) * 1.0  # 1 point per day
            return 85, penalty
        elif days_ago <= 60:
            penalty = 16 + (days_ago - 30) * 0.5
            return 60, penalty
        else:
            penalty = 31 + (days_ago - 60) * 0.3
            return 30, min(penalty, 35)
    
    @staticmethod
    def _score_sentiment(artist_data: Dict) -> Tuple[int, float]:
        """Analyze sentiment trend"""
        comm_history = artist_data.get("communication_history", [])
        
        if not comm_history:
            return 75, 0  # Neutral if no history
        
        # Get last 5 interactions with sentiment
        recent = [c for c in comm_history[-5:] if c.get("sentiment")]
        
        if not recent:
            return 75, 0
        
        sentiment_scores = {
            "POSITIVE": 100,
            "NEUTRAL": 70,
            "NEGATIVE": 30
        }
        
        avg_score = sum(sentiment_scores.get(c["sentiment"], 70) for c in recent) / len(recent)
        
        # Check for declining trend
        if len(recent) >= 3:
            first_half = sum(sentiment_scores.get(c["sentiment"], 70) for c in recent[:len(recent)//2])
            second_half = sum(sentiment_scores.get(c["sentiment"], 70) for c in recent[len(recent)//2:])
            
            if second_half < first_half - 20:  # Declining
                penalty = 15.0
            elif avg_score < 50:  # Consistently negative
                penalty = 25.0
            elif avg_score < 70:  # Neutral/mixed
                penalty = 10.0
            else:
                penalty = 0
        else:
            penalty = (100 - avg_score) * 0.25
        
        return int(avg_score), penalty
    
    @staticmethod
    def _score_responsiveness(artist_data: Dict) -> Tuple[int, float]:
        """How responsive are they?"""
        comm_history = artist_data.get("communication_history", [])
        
        # Count outreach vs response ratio
        outreach_count = len([c for c in comm_history if c.get("type") in ["CHECK_IN", "EMAIL_SENT"]])
        response_count = len([c for c in comm_history if c.get("type") == "RESPONSE_RECEIVED"])
        
        if outreach_count == 0:
            return 75, 0
        
        response_rate = response_count / outreach_count
        
        if response_rate >= 0.8:
            return 100, 0
        elif response_rate >= 0.6:
            return 85, 3.0
        elif response_rate >= 0.4:
            return 65, 7.0
        elif response_rate >= 0.2:
            return 40, 12.0
        else:
            return 20, 20.0
    
    @staticmethod
    def _score_momentum(artist_data: Dict) -> Tuple[int, float]:
        """Are projects moving or stalled?"""
        projects = artist_data.get("current_projects", [])
        
        if not projects:
            return 60, 6.0  # Slight penalty for no projects
        
        stalled = sum(1 for p in projects if p.get("status") in ["STALLED", "DELAYED"])
        active = sum(1 for p in projects if p.get("status") in ["ACTIVE", "IN_PROGRESS"])
        
        if stalled > active:
            return 40, 15.0
        elif active > 0:
            return 90, 0
        else:
            return 60, 6.0
    
    @staticmethod
    def _score_open_loops(artist_data: Dict) -> Tuple[int, float]:
        """How many unresolved action items?"""
        open_items = len(artist_data.get("open_action_items", []))
        
        penalty = min(open_items * 1.5, 5.0)
        score = max(0, 100 - (open_items * 15))
        
        return score, penalty
    
    @staticmethod
    def _get_status_label(score: int) -> str:
        if score >= 80:
            return "🟢 HEALTHY"
        elif score >= 60:
            return "🟡 NEEDS ATTENTION"
        elif score >= 40:
            return "🟠 AT RISK"
        else:
            return "🔴 CRITICAL"
    
    @staticmethod
    def _get_recency_detail(artist_data: Dict) -> str:
        last_contact = artist_data.get("last_contact_date")
        if not last_contact:
            return "Never contacted"
        days = (datetime.now() - datetime.fromisoformat(last_contact)).days
        return f"{days} days ago"
    
    @staticmethod
    def _get_sentiment_detail(artist_data: Dict) -> str:
        comm_history = artist_data.get("communication_history", [])
        recent = [c for c in comm_history[-3:] if c.get("sentiment")]
        if not recent:
            return "No sentiment data"
        sentiments = [c["sentiment"] for c in recent]
        return f"Recent: {' → '.join(sentiments)}"
    
    @staticmethod
    def _get_responsiveness_detail(artist_data: Dict) -> str:
        comm_history = artist_data.get("communication_history", [])
        outreach = len([c for c in comm_history if c.get("type") in ["CHECK_IN", "EMAIL_SENT"]])
        responses = len([c for c in comm_history if c.get("type") == "RESPONSE_RECEIVED"])
        if outreach == 0:
            return "No outreach yet"
        rate = (responses / outreach) * 100
        return f"{rate:.0f}% response rate ({responses}/{outreach})"
    
    @staticmethod
    def _get_momentum_detail(artist_data: Dict) -> str:
        projects = artist_data.get("current_projects", [])
        if not projects:
            return "No active projects"
        active = sum(1 for p in projects if p.get("status") in ["ACTIVE", "IN_PROGRESS"])
        stalled = sum(1 for p in projects if p.get("status") in ["STALLED", "DELAYED"])
        return f"{active} active, {stalled} stalled"


# ============================================================================
# LAYER 2: PATTERN DETECTION ENGINE
# ============================================================================

class PatternDetector:
    """Spots trends and patterns in artist communication"""
    
    @staticmethod
    def detect_patterns(artist_data: Dict) -> List[Dict]:
        patterns = []
        
        # Pattern 1: Engagement decline
        if PatternDetector._is_engagement_declining(artist_data):
            patterns.append({
                "type": "ENGAGEMENT_DECLINE",
                "severity": "MEDIUM",
                "signal": PatternDetector._describe_engagement_decline(artist_data),
                "action": "Consider switching communication channel or scheduling a call"
            })
        
        # Pattern 2: Momentum building
        if PatternDetector._is_momentum_building(artist_data):
            patterns.append({
                "type": "MOMENTUM_BUILDING",
                "severity": "OPPORTUNITY",
                "signal": PatternDetector._describe_momentum_building(artist_data),
                "action": "Capitalize: propose next release timeline or collaboration"
            })
        
        # Pattern 3: Stalled commitment
        if PatternDetector._has_stalled_commitment(artist_data):
            patterns.append({
                "type": "STALLED_COMMITMENT",
                "severity": "HIGH",
                "signal": PatternDetector._describe_stalled_commitment(artist_data),
                "action": "Gentle nudge with specific reference to what was promised"
            })
        
        # Pattern 4: Radio silence after positive
        if PatternDetector._is_radio_silence_after_positive(artist_data):
            patterns.append({
                "type": "RADIO_SILENCE",
                "severity": "MEDIUM",
                "signal": "Positive interaction followed by 20+ days silence",
                "action": "Low-pressure check-in: 'Hope all's well, no pressure'"
            })
        
        # Pattern 5: Consistent engagement
        if PatternDetector._is_consistently_engaged(artist_data):
            patterns.append({
                "type": "HEALTHY_RHYTHM",
                "severity": "POSITIVE",
                "signal": "Consistent, positive engagement pattern",
                "action": "Maintain current cadence, consider level-up conversation"
            })
        
        return patterns
    
    @staticmethod
    def _is_engagement_declining(artist_data: Dict) -> bool:
        comm_history = artist_data.get("communication_history", [])
        if len(comm_history) < 4:
            return False
        
        responses = [c for c in comm_history if c.get("type") == "RESPONSE_RECEIVED"]
        if len(responses) < 3:
            return False
        
        # Check if response times are increasing
        recent_3 = responses[-3:]
        dates = [datetime.fromisoformat(r["date"]) for r in recent_3]
        
        # Simple heuristic: if gaps are increasing
        if len(dates) >= 3:
            gap1 = (dates[1] - dates[0]).days
            gap2 = (dates[2] - dates[1]).days
            return gap2 > gap1 * 1.5
        
        return False
    
    @staticmethod
    def _describe_engagement_decline(artist_data: Dict) -> str:
        return "Response time increasing, engagement dropping"
    
    @staticmethod
    def _is_momentum_building(artist_data: Dict) -> bool:
        comm_history = artist_data.get("communication_history", [])
        recent = [c for c in comm_history[-3:] if c.get("sentiment")]
        
        if len(recent) < 3:
            return False
        
        # All recent interactions positive?
        return all(c["sentiment"] == "POSITIVE" for c in recent)
    
    @staticmethod
    def _describe_momentum_building(artist_data: Dict) -> str:
        return "3+ consecutive positive interactions, project energy high"
    
    @staticmethod
    def _has_stalled_commitment(artist_data: Dict) -> bool:
        action_items = artist_data.get("open_action_items", [])
        
        for item in action_items:
            if item.get("assigned_to") == "ARTIST":
                due_date = item.get("due_date")
                if due_date:
                    due = datetime.fromisoformat(due_date)
                    if datetime.now() > due + timedelta(days=7):
                        return True
        return False
    
    @staticmethod
    def _describe_stalled_commitment(artist_data: Dict) -> str:
        overdue_items = []
        for item in artist_data.get("open_action_items", []):
            if item.get("assigned_to") == "ARTIST":
                due_date = item.get("due_date")
                if due_date:
                    due = datetime.fromisoformat(due_date)
                    if datetime.now() > due:
                        days_overdue = (datetime.now() - due).days
                        overdue_items.append(f"{item['description']} ({days_overdue}d overdue)")
        
        return "; ".join(overdue_items[:2])
    
    @staticmethod
    def _is_radio_silence_after_positive(artist_data: Dict) -> bool:
        comm_history = artist_data.get("communication_history", [])
        if len(comm_history) < 2:
            return False
        
        last = comm_history[-1]
        if last.get("sentiment") == "POSITIVE":
            date = datetime.fromisoformat(last["date"])
            if (datetime.now() - date).days > 20:
                return True
        return False
    
    @staticmethod
    def _is_consistently_engaged(artist_data: Dict) -> bool:
        comm_history = artist_data.get("communication_history", [])
        if len(comm_history) < 5:
            return False
        
        responses = [c for c in comm_history if c.get("type") == "RESPONSE_RECEIVED"]
        if len(responses) < 3:
            return False
        
        # Check response rate
        outreach = len([c for c in comm_history if c.get("type") in ["CHECK_IN", "EMAIL_SENT"]])
        if outreach == 0:
            return False
        
        response_rate = len(responses) / outreach
        
        # Check sentiment
        sentiments = [c.get("sentiment") for c in responses[-5:] if c.get("sentiment")]
        positive_rate = sentiments.count("POSITIVE") / len(sentiments) if sentiments else 0
        
        return response_rate >= 0.7 and positive_rate >= 0.6


# ============================================================================
# LAYER 3: CONTEXT-AWARE MESSAGING
# ============================================================================

class MessageCrafter:
    """Tailors communication per artist personality and context"""
    
    @staticmethod
    def craft_message(artist_data: Dict, context: str, comm_profile: Dict) -> str:
        """
        Generates context-aware message using Ollama
        """
        artist_name = artist_data["artist_info"]["name"]
        comm_style = artist_data["artist_info"].get("communication_style", "BALANCED")
        
        # Build rich context
        health_score, health_status, _ = HealthScorer.calculate_health(artist_data)
        patterns = PatternDetector.detect_patterns(artist_data)
        
        # Get recent context
        last_contact = artist_data.get("last_contact_date")
        days_ago = "never" if not last_contact else f"{(datetime.now() - datetime.fromisoformat(last_contact)).days} days ago"
        
        recent_sentiment = "No history"
        comm_history = artist_data.get("communication_history", [])
        if comm_history:
            recent = [c.get("sentiment") for c in comm_history[-3:] if c.get("sentiment")]
            if recent:
                recent_sentiment = " → ".join(recent)
        
        # Build pattern context
        pattern_context = "\n".join([
            f"- {p['type']}: {p['signal']}"
            for p in patterns
        ]) if patterns else "No significant patterns detected"
        
        # Construct AI prompt
        prompt = f"""You are BRIDGE, Brett Caporn's AI Artist Relations Director for LRRecords.

ARTIST CONTEXT:
- Name: {artist_name}
- Communication Style: {comm_style}
- Last Contact: {days_ago}
- Relationship Health: {health_status} ({health_score}/100)
- Recent Sentiment: {recent_sentiment}

DETECTED PATTERNS:
{pattern_context}

BRETT'S COMMUNICATION PROFILE:
{json.dumps(comm_profile, indent=2)}

SITUATION:
{context}

TASK: Craft a check-in message that:
1. Matches {artist_name}'s communication style ({comm_style})
2. References specific context (not generic "how are you")
3. Has clear purpose
4. Feels authentic to Brett's voice
5. Is concise (2-4 sentences max)

COMMUNICATION STYLE GUIDELINES:
- HIGH_TOUCH: Warm, supportive, frequent check-ins expected
- AUTONOMOUS: Respect their space, check in only with clear purpose
- COLLABORATIVE: Share ideas, opportunities, creative sparks
- TRANSACTIONAL: Business-first, efficient, clear next steps
- BALANCED: Mix of personal + professional

Write ONLY the message body. No subject line. No signatures."""

        try:
            response = ollama.chat(
                model="llama3.1:8b",
                messages=[{"role": "user", "content": prompt}]
            )
            return response["message"]["content"].strip()
        except Exception as e:
            return f"[Error generating message: {e}]"


# ============================================================================
# LAYER 4: PREDICTIVE INTELLIGENCE
# ============================================================================

class Predictor:
    """Forecasts artist needs before they become urgent"""
    
    @staticmethod
    def predict_needs(artist_data: Dict) -> List[Dict]:
        predictions = []
        
        # Prediction 1: Creative block likely
        if Predictor._likely_creative_block(artist_data):
            predictions.append({
                "prediction": "CREATIVE_BLOCK_LIKELY",
                "confidence": "MEDIUM",
                "reasoning": Predictor._explain_creative_block(artist_data),
                "suggested_action": "Send inspiration: playlist, beat pack, or collab opportunity"
            })
        
        # Prediction 2: Release momentum window
        if Predictor._release_momentum_window(artist_data):
            predictions.append({
                "prediction": "MOMENTUM_WINDOW",
                "confidence": "HIGH",
                "reasoning": "Recent positive engagement + project progress",
                "suggested_action": "Propose fast-follow release to capitalize on energy"
            })
        
        # Prediction 3: Relationship at risk
        if Predictor._relationship_at_risk(artist_data):
            predictions.append({
                "prediction": "RELATIONSHIP_AT_RISK",
                "confidence": "HIGH",
                "reasoning": Predictor._explain_relationship_risk(artist_data),
                "suggested_action": "Priority check-in call (not email) to rebuild connection"
            })
        
        # Prediction 4: Ready for level-up conversation
        if Predictor._ready_for_levelup(artist_data):
            predictions.append({
                "prediction": "READY_FOR_GROWTH_CONVERSATION",
                "confidence": "MEDIUM",
                "reasoning": "Consistent positive momentum, project completion rate high",
                "suggested_action": "Schedule strategic conversation: next phase, bigger goals"
            })
        
        return predictions
    
    @staticmethod
    def _likely_creative_block(artist_data: Dict) -> bool:
        projects = artist_data.get("current_projects", [])
        
        # No projects for 45+ days?
        if not projects:
            last_contact = artist_data.get("last_contact_date")
            if last_contact:
                days = (datetime.now() - datetime.fromisoformat(last_contact)).days
                return days > 45
        
        # All projects stalled?
        if projects:
            stalled_count = sum(1 for p in projects if p.get("status") in ["STALLED", "DELAYED"])
            return stalled_count == len(projects) and len(projects) > 0
        
        return False
    
    @staticmethod
    def _explain_creative_block(artist_data: Dict) -> str:
        projects = artist_data.get("current_projects", [])
        if not projects:
            return "No project activity for 45+ days"
        return "All projects stalled, creative momentum stopped"
    
    @staticmethod
    def _release_momentum_window(artist_data: Dict) -> bool:
        # Positive sentiment + active project?
        comm_history = artist_data.get("communication_history", [])
        recent_positive = any(
            c.get("sentiment") == "POSITIVE" 
            for c in comm_history[-3:] 
            if c.get("sentiment")
        )
        
        projects = artist_data.get("current_projects", [])
        active_projects = any(
            p.get("status") in ["ACTIVE", "IN_PROGRESS"]
            for p in projects
        )
        
        return recent_positive and active_projects
    
    @staticmethod
    def _relationship_at_risk(artist_data: Dict) -> bool:
        health_score, _, _ = HealthScorer.calculate_health(artist_data)
        return health_score < 50
    
    @staticmethod
    def _explain_relationship_risk(artist_data: Dict) -> str:
        health_score, _, breakdown = HealthScorer.calculate_health(artist_data)
        
        issues = []
        if breakdown["recency"]["penalty"] > 15:
            issues.append(f"Long silence ({breakdown['recency']['detail']})")
        if breakdown["sentiment"]["penalty"] > 10:
            issues.append(f"Sentiment declining ({breakdown['sentiment']['detail']})")
        if breakdown["responsiveness"]["penalty"] > 10:
            issues.append(f"Low responsiveness ({breakdown['responsiveness']['detail']})")
        
        return "; ".join(issues) if issues else f"Health score: {health_score}"
    
    @staticmethod
    def _ready_for_levelup(artist_data: Dict) -> bool:
        health_score, _, _ = HealthScorer.calculate_health(artist_data)
        
        if health_score < 75:
            return False
        
        # Check for consistent positive engagement
        comm_history = artist_data.get("communication_history", [])
        recent_sentiments = [
            c.get("sentiment") 
            for c in comm_history[-5:] 
            if c.get("sentiment")
        ]
        
        if len(recent_sentiments) < 4:
            return False
        
        positive_rate = recent_sentiments.count("POSITIVE") / len(recent_sentiments)
        return positive_rate >= 0.75


# ============================================================================
# LAYER 5: LEARNING MEMORY SYSTEM
# ============================================================================

class LearningMemory:
    """Remembers what works with each artist over time"""
    
    @staticmethod
    def load_learnings() -> Dict:
        if os.path.exists(LEARNING_FILE):
            with open(LEARNING_FILE, "r") as f:
                return json.load(f)
        return {}
    
    @staticmethod
    def save_learnings(learnings: Dict):
        with open(LEARNING_FILE, "w") as f:
            json.dump(learnings, f, indent=2)
    
    @staticmethod
    def record_interaction(artist_name: str, interaction_data: Dict):
        """
        Record what happened in an interaction for learning
        
        interaction_data format:
        {
            "channel": "email" | "instagram" | "phone",
            "message_type": "check_in" | "opportunity" | "creative" | "business",
            "response_received": bool,
            "response_time_hours": int,
            "sentiment": "POSITIVE" | "NEUTRAL" | "NEGATIVE",
            "resulted_in_action": bool
        }
        """
        learnings = LearningMemory.load_learnings()
        
        artist_key = artist_name.lower().replace(" ", "_")
        
        if artist_key not in learnings:
            learnings[artist_key] = {
                "response_rate_by_channel": defaultdict(lambda: {"sent": 0, "responded": 0}),
                "response_rate_by_type": defaultdict(lambda: {"sent": 0, "responded": 0}),
                "avg_response_time_hours": [],
                "successful_tactics": [],
                "unsuccessful_tactics": []
            }
        
        artist_learning = learnings[artist_key]
        
        # Update channel stats
        channel = interaction_data["channel"]
        if channel not in artist_learning["response_rate_by_channel"]:
            artist_learning["response_rate_by_channel"][channel] = {"sent": 0, "responded": 0}
        
        artist_learning["response_rate_by_channel"][channel]["sent"] += 1
        if interaction_data["response_received"]:
            artist_learning["response_rate_by_channel"][channel]["responded"] += 1
        
        # Update message type stats
        msg_type = interaction_data["message_type"]
        if msg_type not in artist_learning["response_rate_by_type"]:
            artist_learning["response_rate_by_type"][msg_type] = {"sent": 0, "responded": 0}
        
        artist_learning["response_rate_by_type"][msg_type]["sent"] += 1
        if interaction_data["response_received"]:
            artist_learning["response_rate_by_type"][msg_type]["responded"] += 1
        
        # Track response time
        if interaction_data["response_received"] and interaction_data.get("response_time_hours"):
            artist_learning["avg_response_time_hours"].append(interaction_data["response_time_hours"])
            # Keep only last 20 interactions
            artist_learning["avg_response_time_hours"] = artist_learning["avg_response_time_hours"][-20:]
        
        # Track tactics
        tactic_desc = f"{msg_type} via {channel}"
        if interaction_data["response_received"] and interaction_data["sentiment"] == "POSITIVE":
            if tactic_desc not in artist_learning["successful_tactics"]:
                artist_learning["successful_tactics"].append(tactic_desc)
        elif not interaction_data["response_received"]:
            if tactic_desc not in artist_learning["unsuccessful_tactics"]:
                artist_learning["unsuccessful_tactics"].append(tactic_desc)
        
        LearningMemory.save_learnings(learnings)
    
    @staticmethod
    def get_recommendations(artist_name: str) -> Dict:
        """Get learned recommendations for this artist"""
        learnings = LearningMemory.load_learnings()
        artist_key = artist_name.lower().replace(" ", "_")
        
        if artist_key not in learnings:
            return {
                "best_channel": "Email (default)",
                "best_message_type": "Unknown (no data)",
                "avg_response_time": "Unknown",
                "successful_tactics": [],
                "avoid_tactics": []
            }
        
        artist_learning = learnings[artist_key]
        
        # Calculate best channel
        best_channel = "Email"
        best_rate = 0
        for channel, stats in artist_learning["response_rate_by_channel"].items():
            if stats["sent"] > 0:
                rate = stats["responded"] / stats["sent"]
                if rate > best_rate:
                    best_rate = rate
                    best_channel = channel
        
        # Calculate best message type
        best_type = "check_in"
        best_type_rate = 0
        for msg_type, stats in artist_learning["response_rate_by_type"].items():
            if stats["sent"] > 0:
                rate = stats["responded"] / stats["sent"]
                if rate > best_type_rate:
                    best_type_rate = rate
                    best_type = msg_type
        
        # Average response time
        avg_time = "Unknown"
        if artist_learning["avg_response_time_hours"]:
            avg_hours = sum(artist_learning["avg_response_time_hours"]) / len(artist_learning["avg_response_time_hours"])
            if avg_hours < 24:
                avg_time = f"{avg_hours:.1f} hours"
            else:
                avg_time = f"{avg_hours/24:.1f} days"
        
        return {
            "best_channel": f"{best_channel} ({best_rate*100:.0f}% response rate)",
            "best_message_type": f"{best_type} ({best_type_rate*100:.0f}% response rate)",
            "avg_response_time": avg_time,
            "successful_tactics": artist_learning["successful_tactics"][-5:],
            "avoid_tactics": artist_learning["unsuccessful_tactics"][-3:]
        }


# ============================================================================
# MAIN BRIDGE INTELLIGENCE ORCHESTRATOR
# ============================================================================

class BridgeIntelligence:
    """Main orchestrator for all 5 intelligence layers"""
    
    def __init__(self):
        self.health_scorer = HealthScorer()
        self.pattern_detector = PatternDetector()
        self.message_crafter = MessageCrafter()
        self.predictor = Predictor()
        self.learning_memory = LearningMemory()
        
        # Load context
        self.context = self._load_context()
        self.comm_profile = self._load_comm_profile()
    
    def _load_context(self) -> Dict:
        if os.path.exists(CONTEXT_FILE):
            with open(CONTEXT_FILE, "r") as f:
                return json.load(f)
        return {}
    
    def _load_comm_profile(self) -> Dict:
        if os.path.exists(COMM_PROFILE):
            with open(COMM_PROFILE, "r") as f:
                return json.load(f)
        return {}
    
    def load_artist(self, artist_name: str) -> Optional[Dict]:
        """Load artist data by name"""
        for filename in os.listdir(ARTIST_FOLDER):
            if filename.endswith(".json"):
                filepath = os.path.join(ARTIST_FOLDER, filename)
                with open(filepath, "r") as f:
                    data = json.load(f)
                    if data["artist_info"]["name"].lower() == artist_name.lower():
                        return data
        return None
    
    def load_all_artists(self) -> List[Dict]:
        """Load all artist profiles"""
        artists = []
        for filename in os.listdir(ARTIST_FOLDER):
            if filename.endswith(".json"):
                filepath = os.path.join(ARTIST_FOLDER, filename)
                with open(filepath, "r") as f:
                    artists.append(json.load(f))
        return artists
    
    def analyze_artist(self, artist_name: str) -> Dict:
        """Full analysis of a single artist"""
        artist_data = self.load_artist(artist_name)
        
        if not artist_data:
            return {"error": f"Artist '{artist_name}' not found"}
        
        # Run all 5 layers
        health_score, health_status, health_breakdown = self.health_scorer.calculate_health(artist_data)
        patterns = self.pattern_detector.detect_patterns(artist_data)
        predictions = self.predictor.predict_needs(artist_data)
        recommendations = self.learning_memory.get_recommendations(artist_name)
        
        return {
            "artist": artist_name,
            "health": {
                "score": health_score,
                "status": health_status,
                "breakdown": health_breakdown
            },
            "patterns": patterns,
            "predictions": predictions,
            "learned_recommendations": recommendations
        }
    
    def daily_briefing(self) -> Dict:
        """Generate daily briefing across all artists"""
        artists = self.load_all_artists()
        
        critical_artists = []
        at_risk_artists = []
        healthy_artists = []
        opportunities = []
        all_predictions = []
        
        for artist_data in artists:
            artist_name = artist_data["artist_info"]["name"]
            health_score, health_status, _ = self.health_scorer.calculate_health(artist_data)
            patterns = self.pattern_detector.detect_patterns(artist_data)
            predictions = self.predictor.predict_needs(artist_data)
            
            artist_summary = {
                "name": artist_name,
                "health_score": health_score,
                "health_status": health_status
            }
            
            if health_score < 40:
                critical_artists.append(artist_summary)
            elif health_score < 60:
                at_risk_artists.append(artist_summary)
            else:
                healthy_artists.append(artist_summary)
            
            # Collect opportunities
            opportunity_patterns = [p for p in patterns if p["severity"] == "OPPORTUNITY"]
            for pattern in opportunity_patterns:
                opportunities.append({
                    "artist": artist_name,
                    "opportunity": pattern["signal"],
                    "action": pattern["action"]
                })
            
            # Collect predictions
            for pred in predictions:
                all_predictions.append({
                    "artist": artist_name,
                    "prediction": pred["prediction"],
                    "confidence": pred["confidence"],
                    "action": pred["suggested_action"]
                })
        
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "roster_summary": {
                "total_artists": len(artists),
                "critical": len(critical_artists),
                "at_risk": len(at_risk_artists),
                "healthy": len(healthy_artists)
            },
            "critical_artists": critical_artists,
            "at_risk_artists": at_risk_artists,
            "opportunities": opportunities,
            "predictions": all_predictions
        }
    
    def craft_check_in(self, artist_name: str, context: str = None) -> str:
        """Generate context-aware check-in message"""
        artist_data = self.load_artist(artist_name)
        
        if not artist_data:
            return f"Error: Artist '{artist_name}' not found"
        
        if not context:
            # Auto-generate context based on analysis
            analysis = self.analyze_artist(artist_name)
            patterns = analysis.get("patterns", [])
            predictions = analysis.get("predictions", [])
            
            context_parts = []
            if patterns:
                context_parts.append(f"Pattern detected: {patterns[0]['signal']}")
            if predictions:
                context_parts.append(f"Prediction: {predictions[0]['reasoning']}")
            
            context = " | ".join(context_parts) if context_parts else "General check-in"
        
        return self.message_crafter.craft_message(artist_data, context, self.comm_profile)


# ============================================================================
# CLI INTERFACE
# ============================================================================

def print_health_report(analysis: Dict):
    """Pretty print health analysis"""
    print(f"\n{'='*60}")
    print(f"🌉 BRIDGE INTELLIGENCE REPORT: {analysis['artist']}")
    print(f"{'='*60}")
    
    health = analysis["health"]
    print(f"\n📊 HEALTH STATUS: {health['status']} ({health['score']}/100)")
    print(f"\nBreakdown:")
    for category, data in health["breakdown"].items():
        print(f"  • {category.capitalize():20} {data['detail']}")
    
    if analysis["patterns"]:
        print(f"\n🔍 DETECTED PATTERNS:")
        for pattern in analysis["patterns"]:
            severity_emoji = {
                "HIGH": "🚨",
                "MEDIUM": "⚠️",
                "OPPORTUNITY": "✨",
                "POSITIVE": "✅"
            }.get(pattern["severity"], "ℹ️")
            print(f"  {severity_emoji} {pattern['type']}")
            print(f"     Signal: {pattern['signal']}")
            print(f"     Action: {pattern['action']}\n")
    
    if analysis["predictions"]:
        print(f"\n🔮 PREDICTIONS:")
        for pred in analysis["predictions"]:
            conf_emoji = {"HIGH": "🎯", "MEDIUM": "🤔", "LOW": "💭"}
            print(f"  {conf_emoji.get(pred['confidence'], '💭')} {pred['prediction']} ({pred['confidence']} confidence)")
            print(f"     Why: {pred['reasoning']}")
            print(f"     Action: {pred['suggested_action']}\n")
    
    recs = analysis["learned_recommendations"]
    print(f"\n🧠 LEARNED RECOMMENDATIONS:")
    print(f"  • Best channel: {recs['best_channel']}")
    print(f"  • Best message type: {recs['best_message_type']}")
    print(f"  • Avg response time: {recs['avg_response_time']}")
    
    if recs["successful_tactics"]:
        print(f"  • What works: {', '.join(recs['successful_tactics'])}")
    if recs["avoid_tactics"]:
        print(f"  • What doesn't: {', '.join(recs['avoid_tactics'])}")


def print_daily_briefing(briefing: Dict):
    """Pretty print daily briefing"""
    print(f"\n{'='*60}")
    print(f"🌉 BRIDGE DAILY BRIEFING - {briefing['date']}")
    print(f"{'='*60}")
    
    summary = briefing["roster_summary"]
    print(f"\n📊 ROSTER OVERVIEW:")
    print(f"  Total Artists: {summary['total_artists']}")
    print(f"  🟢 Healthy: {summary['healthy']}")
    print(f"  🟡 At Risk: {summary['at_risk']}")
    print(f"  🔴 Critical: {summary['critical']}")
    
    if briefing["critical_artists"]:
        print(f"\n🚨 CRITICAL ATTENTION NEEDED:")
        for artist in briefing["critical_artists"]:
            print(f"  • {artist['name']}: {artist['health_status']} ({artist['health_score']}/100)")
    
    if briefing["at_risk_artists"]:
        print(f"\n⚠️  AT RISK:")
        for artist in briefing["at_risk_artists"]:
            print(f"  • {artist['name']}: {artist['health_status']} ({artist['health_score']}/100)")
    
    if briefing["opportunities"]:
        print(f"\n✨ OPPORTUNITIES:")
        for opp in briefing["opportunities"]:
            print(f"  • {opp['artist']}: {opp['opportunity']}")
            print(f"    → {opp['action']}\n")
    
    if briefing["predictions"]:
        print(f"\n🔮 PREDICTIONS:")
        for pred in briefing["predictions"][:5]:  # Top 5
            print(f"  • {pred['artist']}: {pred['prediction']}")
            print(f"    → {pred['action']}\n")


def main():
    """CLI interface for BRIDGE Intelligence"""
    import sys
    
    bridge = BridgeIntelligence()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python bridge_intelligence.py briefing")
        print("  python bridge_intelligence.py analyze <artist_name>")
        print("  python bridge_intelligence.py message <artist_name>")
        return
    
    command = sys.argv[1].lower()
    
    if command == "briefing":
        briefing = bridge.daily_briefing()
        print_daily_briefing(briefing)
    
    elif command == "analyze":
        if len(sys.argv) < 3:
            print("Error: Provide artist name")
            return
        
        artist_name = " ".join(sys.argv[2:])
        analysis = bridge.analyze_artist(artist_name)
        
        if "error" in analysis:
            print(f"Error: {analysis['error']}")
        else:
            print_health_report(analysis)
    
    elif command == "message":
        if len(sys.argv) < 3:
            print("Error: Provide artist name")
            return
        
        artist_name = " ".join(sys.argv[2:])
        message = bridge.craft_check_in(artist_name)
        
        print(f"\n{'='*60}")
        print(f"📧 SUGGESTED MESSAGE FOR {artist_name}")
        print(f"{'='*60}\n")
        print(message)
        print()
    
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()