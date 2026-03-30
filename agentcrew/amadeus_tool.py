"""
Amadeus travel tool for CrewAI agents.
Covers flights, hotels, airport search and travel recommendations.
Requires AMADEUS_API_KEY and AMADEUS_API_SECRET env vars.
"""
import json
import os
from typing import Optional, Type
from pydantic import BaseModel, Field

try:
    from amadeus import Client, ResponseError
    from crewai.tools import BaseTool
except ImportError:
    raise ImportError("amadeus and crewai are required: pip install amadeus crewai")

AMADEUS_API_KEY = os.environ.get("AMADEUS_API_KEY", "")
AMADEUS_API_SECRET = os.environ.get("AMADEUS_API_SECRET", "")


def _client():
    return Client(client_id=AMADEUS_API_KEY, client_secret=AMADEUS_API_SECRET)


# ── Flight Search ─────────────────────────────────────────────────────────────

class FlightSearchInput(BaseModel):
    origin: str = Field(..., description="IATA airport code for origin. E.g. 'LHR', 'JFK', 'DXB'")
    destination: str = Field(..., description="IATA airport code for destination.")
    departure_date: str = Field(..., description="Departure date in YYYY-MM-DD format.")
    adults: Optional[int] = Field(1, description="Number of adult passengers.")
    return_date: Optional[str] = Field(None, description="Return date for round trips (YYYY-MM-DD). Leave empty for one-way.")
    max_results: Optional[int] = Field(5, description="Max number of results to return.")


class FlightSearchTool(BaseTool):
    name: str = "Flight Search (Amadeus)"
    description: str = (
        "Search for available flights between two airports. "
        "Returns price, airline, duration, stops and booking class. "
        "Use IATA codes for airports (e.g. LHR, JFK, DXB, SYD)."
    )
    args_schema: Type[BaseModel] = FlightSearchInput

    def _run(self, origin: str, destination: str, departure_date: str,
             adults: int = 1, return_date: str = None, max_results: int = 5) -> str:
        if not AMADEUS_API_KEY:
            return "AMADEUS_API_KEY not configured."
        try:
            amadeus = _client()
            params = dict(
                originLocationCode=origin.upper(),
                destinationLocationCode=destination.upper(),
                departureDate=departure_date,
                adults=adults,
                max=max_results,
            )
            if return_date:
                params["returnDate"] = return_date

            response = amadeus.shopping.flight_offers_search.get(**params)
            offers = response.data[:max_results]

            if not offers:
                return f"No flights found from {origin} to {destination} on {departure_date}."

            lines = [f"Flights from {origin.upper()} → {destination.upper()} on {departure_date}\n"]
            for i, offer in enumerate(offers, 1):
                price = offer["price"]["grandTotal"]
                currency = offer["price"]["currency"]
                itinerary = offer["itineraries"][0]
                duration = itinerary["duration"].replace("PT", "").lower()
                segments = itinerary["segments"]
                stops = len(segments) - 1
                airline = segments[0]["carrierCode"]
                dep = segments[0]["departure"]["at"][:16]
                arr = segments[-1]["arrival"]["at"][:16]
                lines.append(
                    f"{i}. {airline} | {dep} → {arr} | {duration} | "
                    f"{stops} stop(s) | {currency} {price}"
                )
            return "\n".join(lines)

        except ResponseError as exc:
            return f"Amadeus API error: {exc}"
        except Exception as exc:
            return f"Flight search failed: {exc}"


# ── Hotel Search ──────────────────────────────────────────────────────────────

class HotelSearchInput(BaseModel):
    city_code: str = Field(..., description="IATA city code. E.g. 'LON', 'NYC', 'DXB', 'PAR'")
    check_in: str = Field(..., description="Check-in date (YYYY-MM-DD)")
    check_out: str = Field(..., description="Check-out date (YYYY-MM-DD)")
    adults: Optional[int] = Field(1, description="Number of adult guests.")
    max_results: Optional[int] = Field(5, description="Max results to return.")


class HotelSearchTool(BaseTool):
    name: str = "Hotel Search (Amadeus)"
    description: str = (
        "Search for available hotels in a city. "
        "Returns hotel name, rating, price per night and availability. "
        "Use IATA city codes (e.g. LON for London, NYC for New York, DXB for Dubai)."
    )
    args_schema: Type[BaseModel] = HotelSearchInput

    def _run(self, city_code: str, check_in: str, check_out: str,
             adults: int = 1, max_results: int = 5) -> str:
        if not AMADEUS_API_KEY:
            return "AMADEUS_API_KEY not configured."
        try:
            amadeus = _client()

            # Step 1: get hotel IDs in city
            hotels_resp = amadeus.reference_data.locations.hotels.by_city.get(
                cityCode=city_code.upper()
            )
            hotel_ids = [h["hotelId"] for h in hotels_resp.data[:20]]
            if not hotel_ids:
                return f"No hotels found in {city_code}."

            # Step 2: get offers
            offers_resp = amadeus.shopping.hotel_offers_search.get(
                hotelIds=",".join(hotel_ids),
                checkInDate=check_in,
                checkOutDate=check_out,
                adults=adults,
            )
            offers = offers_resp.data[:max_results]

            if not offers:
                return f"No availability found in {city_code} for {check_in} to {check_out}."

            lines = [f"Hotels in {city_code.upper()} | {check_in} → {check_out}\n"]
            for i, item in enumerate(offers, 1):
                hotel = item.get("hotel", {})
                name = hotel.get("name", "Unknown")
                rating = hotel.get("rating", "N/A")
                offer = item.get("offers", [{}])[0]
                price = offer.get("price", {}).get("total", "N/A")
                currency = offer.get("price", {}).get("currency", "")
                room = offer.get("room", {}).get("typeEstimated", {}).get("category", "")
                lines.append(f"{i}. {name} | ⭐ {rating} | {room} | {currency} {price}/stay")

            return "\n".join(lines)

        except ResponseError as exc:
            return f"Amadeus API error: {exc}"
        except Exception as exc:
            return f"Hotel search failed: {exc}"


# ── Airport Search ────────────────────────────────────────────────────────────

class AirportSearchInput(BaseModel):
    keyword: str = Field(..., description="City or airport name to look up IATA code for.")


class AirportSearchTool(BaseTool):
    name: str = "Airport/City Code Lookup (Amadeus)"
    description: str = "Look up IATA airport or city codes by name. Use before searching flights or hotels."
    args_schema: Type[BaseModel] = AirportSearchInput

    def _run(self, keyword: str) -> str:
        if not AMADEUS_API_KEY:
            return "AMADEUS_API_KEY not configured."
        try:
            amadeus = _client()
            response = amadeus.reference_data.locations.get(
                keyword=keyword, subType="AIRPORT,CITY"
            )
            results = response.data[:8]
            if not results:
                return f"No IATA codes found for: {keyword}"
            lines = [f"IATA codes for '{keyword}':"]
            for r in results:
                lines.append(
                    f"  {r['iataCode']} — {r['name']} ({r.get('address', {}).get('countryCode', '')})"
                )
            return "\n".join(lines)
        except Exception as exc:
            return f"Airport lookup failed: {exc}"
