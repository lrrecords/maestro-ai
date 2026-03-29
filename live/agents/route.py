from core.base_agent import BaseAgent
import os
from urllib.parse import quote_plus

# Google Maps client setup
try:
    import googlemaps
except ImportError:
    googlemaps = None

def get_gmaps_client():
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key or not googlemaps:
        return None
    return googlemaps.Client(key=api_key)

def get_distance_and_duration(from_city, to_city):
    if not from_city or not to_city or from_city == to_city or not googlemaps:
        return 0, 0.0

    gmaps = get_gmaps_client()
    if not gmaps:
        return None, None
    try:
        directions_result = gmaps.directions(
            from_city, to_city, mode="driving", units="metric"
        )
        if directions_result and "legs" in directions_result[0]:
            leg = directions_result[0]["legs"][0]
            distance_km = leg["distance"]["value"] / 1000.0  # meters to km
            duration_hr = leg["duration"]["value"] / 3600.0  # seconds to hours
            return distance_km, duration_hr
    except Exception as e:
        print(f"Google Maps API error: {e}")
    return None, None

def build_google_maps_route_url(home_city, cities):
    points = [home_city] + [c for c in cities if c and c != home_city]
    if len(points) < 2:
        return ""
    quoted_points = [quote_plus(pt) for pt in points]
    url = "https://www.google.com/maps/dir/" + "/".join(quoted_points)
    return url

def patch_route_with_real_distance(structured, context):
    total_km = 0
    total_hours = 0.0
    route_plan = structured.get("route_plan", [])
    for idx, leg in enumerate(route_plan):
        from_city = leg.get("travel_from", "")
        to_city = leg.get("travel_to", "")
        if from_city and to_city and from_city != to_city:
            distance_km, duration_hr = get_distance_and_duration(from_city, to_city)
            if distance_km is not None:
                leg["km"] = round(distance_km)
                leg["notes"] = (leg.get("notes", "") + " | Verified via Google Maps").strip()
                total_km += distance_km
                if duration_hr:
                    total_hours += duration_hr
                leg["travel_time_hr"] = round(duration_hr, 2) if duration_hr else 0
            else:
                try:
                    total_km += float(leg.get("km", 0))
                except Exception:
                    pass
        else:
            try:
                total_km += float(leg.get("km", 0))
            except Exception:
                pass
    structured["total_km"] = round(total_km)
    structured["estimated_travel_time_hr"] = round(total_hours, 2)
    home_city = context.get("home_city") or ""
    cities_order = [step["city"] for step in structured.get("route_plan", [])]
    structured["route_url"] = build_google_maps_route_url(home_city, cities_order)
    return structured

# ------------- AGENT --------------
class RouteAgent(BaseAgent):
    department = "live"
    name = "ROUTE"
    description = "Tour routing and travel optimisation."

    FIELDS = [
        {"key": "cities",         "label": "Cities",          "type": "tags",   "placeholder": "e.g. London, Manchester, Glasgow", "required": True},
        {"key": "home_city",      "label": "Home City",       "type": "text",   "placeholder": "e.g. London",                     "required": True},
        {"key": "start_date",     "label": "Start Date",      "type": "text",   "placeholder": "e.g. 2026-04-01"},
        {"key": "end_date",       "label": "End Date",        "type": "text",   "placeholder": "e.g. 2026-04-30"},
        {"key": "transport_mode", "label": "Transport Mode",  "type": "select", "options": ["van", "fly", "train", "mixed"]},
    ]

    def run(self, context: dict) -> dict:
        prompt = self.build_prompt(context)
        try:
            llm_result = self.llm(prompt)
            structured = self.parse_json(llm_result)
            structured = patch_route_with_real_distance(structured, context)
        except Exception as e:
            return {
                "agent": self.name,
                "department": self.department,
                "status": "error",
                "message": f"ROUTE LLM/API error: {str(e)}",
                "context": context,
            }
        return {
            "agent": self.name,
            "department": self.department,
            "status": "complete",
            "message": llm_result,
            "data": structured,
            "context": context,
        }

    def build_prompt(self, context: dict) -> str:
        cities = ", ".join(context.get("cities", [])) if isinstance(context.get("cities"), list) else str(context.get("cities", ""))
        home_city = context.get("home_city", "[home city]")
        start_date = context.get("start_date", "[start]")
        end_date = context.get("end_date", "[end]")
        transport = context.get("transport_mode", "van")
        return (
            f"You are an expert tour manager. Given these requirements, optimize a music tour route:\n"
            f"- Cities to visit (in any order): {cities}\n"
            f"- Home city: {home_city}\n"
            f"- Start date: {start_date}\n"
            f"- End date: {end_date}\n"
            f"- Transport: {transport}\n"
            "\n"
            "Respond ONLY with strict JSON in this schema (all fields always present—arrays, never null, no prose):\n"
            "{\n"
            "  \"route_plan\": [\n"
            "    {\n"
            "      \"date\": \"YYYY-MM-DD\",\n"
            "      \"city\": string,\n"
            "      \"travel_from\": string,\n"
            "      \"travel_to\": string,\n"
            "      \"km\": number,\n"
            "      \"transport_mode\": string,\n"
            "      \"notes\": string\n"
            "    }\n"
            "  ],\n"
            "  \"total_km\": number,\n"
            "  \"estimated_travel_time_hr\": number,\n"
            "  \"overall_notes\": string\n"
            "}\n"
            "Rules:\n"
            "- Start at home_city, end at last city.\n"
            "- Visit all cities between start_date and end_date, 1 show per city per day, in sensible order.\n"
            "- Optimize for routing based on mode (no zig-zags, reduce backtracking).\n"
            "- In `route_plan`, for each leg give: date, city, travel_from, travel_to, km (estimate), travel_mode, and notes.\n"
            "- All arrays must be present, use empty arrays/strings for unknowns (never null or missing).\n"
            "- JSON only. No code blocks, markdown, or explanations."
        )