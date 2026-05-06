from core.base_agent import BaseAgent
import os
from urllib.parse import quote_plus


# OpenRouteService client setup
try:
    import openrouteservice
except ImportError:
    openrouteservice = None

def get_ors_client():
    api_key = os.getenv("ORS_API_KEY")
    if not api_key or not openrouteservice:
        return None
    return openrouteservice.Client(key=api_key)

def get_distance_and_duration(from_city, to_city, from_state=None, to_state=None, from_country=None, to_country=None):
    if not from_city or not to_city or from_city == to_city or not openrouteservice:
        return 0, 0.0

    ors = get_ors_client()
    if not ors:
        return None, None
    try:
        # Compose full location strings
        from_full = ", ".join([v for v in [from_city, from_state, from_country] if v])
        to_full = ", ".join([v for v in [to_city, to_state, to_country] if v])
        # Geocode cities to coordinates
        geocode = ors.pelias_search
        from_res = geocode(text=from_full)
        to_res = geocode(text=to_full)
        from_coords = from_res['features'][0]['geometry']['coordinates']
        to_coords = to_res['features'][0]['geometry']['coordinates']
        # Get route
        route = ors.directions(
            coordinates=[from_coords, to_coords],
            profile='driving-car',
            format='geojson'
        )
        summary = route['features'][0]['properties']['summary']
        distance_km = summary['distance'] / 1000.0  # meters to km
        duration_hr = summary['duration'] / 3600.0  # seconds to hours
        return distance_km, duration_hr
    except Exception as e:
        print(f"OpenRouteService API error: {e}")
    return None, None

def build_osm_route_url(home_city, cities, home_state=None, home_country=None, states=None, countries=None):
    # Compose full location strings
    points = []
    if home_city:
        home_full = ", ".join([v for v in [home_city, home_state, home_country] if v])
        points.append(home_full)
    for idx, c in enumerate(cities):
        state = states[idx] if states and idx < len(states) else None
        country = countries[idx] if countries and idx < len(countries) else None
        city_full = ", ".join([v for v in [c, state, country] if v])
        if city_full and city_full != points[0]:
            points.append(city_full)
    if len(points) < 2:
        return ""
    quoted_points = [quote_plus(pt) for pt in points]
    url = "https://www.openstreetmap.org/directions?engine=fossgis_osrm_car&route=" + "%3B".join(quoted_points)
    return url

def patch_route_with_real_distance(structured, context):
    total_km = 0
    total_hours = 0.0
    route_plan = structured.get("route_plan", [])
    states = context.get("states")
    countries = context.get("countries")
    for idx, leg in enumerate(route_plan):
        from_city = leg.get("travel_from", "")
        to_city = leg.get("travel_to", "")
        from_state = states[idx] if states and idx < len(states) else None
        to_state = states[idx+1] if states and idx+1 < len(states) else None
        from_country = countries[idx] if countries and idx < len(countries) else None
        to_country = countries[idx+1] if countries and idx+1 < len(countries) else None
        if from_city and to_city and from_city != to_city:
            distance_km, duration_hr = get_distance_and_duration(from_city, to_city, from_state, to_state, from_country, to_country)
            if distance_km is not None:
                # Always overwrite with API value, ignore LLM guess
                leg["km"] = round(distance_km)
                leg["notes"] = (leg.get("notes", "") + " | Distance/time set via OpenRouteService").strip()
                total_km += distance_km
                if duration_hr:
                    total_hours += duration_hr
                leg["travel_time_hr"] = round(duration_hr, 2) if duration_hr else 0
            else:
                leg["notes"] = (leg.get("notes", "") + " | OpenRouteService lookup failed").strip()
        # If not a valid leg, do not use LLM's km at all
        # (skip adding to total_km)
    structured["total_km"] = round(total_km)
    structured["estimated_travel_time_hr"] = round(total_hours, 2)
    home_city = context.get("home_city") or ""
    home_state = context.get("home_state")
    home_country = context.get("home_country")
    cities_order = [step["city"] for step in structured.get("route_plan", [])]
    structured["route_url"] = build_osm_route_url(home_city, cities_order, home_state, home_country, states, countries)
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