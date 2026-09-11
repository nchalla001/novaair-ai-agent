from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from knowledge_base import retrieve_policy
import uuid
import re

app = FastAPI()

class BookingRequest(BaseModel):
    passenger: str
    flight: str
    status: str


bookings = {
    "NA123": {
        "passenger": "Marcus",
        "flight": "NV101",
        "status": "CANCELLED"
    },
    "NA456": {
        "passenger": "Livia",
        "flight": "NV202",
        "status": "CONFIRMED"
    }
}

@app.post("/bookings")
def create_booking(booking: BookingRequest):
    booking_id = f"NA-{uuid.uuid4()}"
    bookings[booking_id] = booking.model_dump()
    return {
    "booking_id": booking_id,
    **booking.model_dump()
}
@app.get("/bookings/{booking_id}")
def get_booking(booking_id: str):
    booking = bookings.get(booking_id)

    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")

    return booking

def decide_tool(action: str):
    if action == "get_booking":
        return "GET /bookings/{booking_id}"

    if action == "create_booking":
        return "POST /bookings"

    return "UNKNOWN"
allowed_actions = {
    "get_booking",
    "create_booking"
}

def is_action_allowed(action: str):
    return action in allowed_actions

def route_request(message: str):
    message = message.lower()

    if any(word in message for word in [
        "baggage",
        "luggage",
        "carry-on",
        "refund policy",
        "cancellation policy"
    ]):
        return "RAG"

    if "booking" in message and any(word in message for word in [
        "status",
        "show",
        "find",
        "lookup",
        "check"
    ]):
        return "TOOL"

    return "UNSUPPORTED"


def handle_request(message: str):
    route = route_request(message)

    if route == "RAG":
        return retrieve_policy(message)

    if route == "TOOL":
        booking_match = re.search(r"\bNA\d+\b", message.upper())

        if booking_match is None:
            return "Please provide a valid NovaAir booking reference."

        booking_id = booking_match.group()
        return get_booking(booking_id)

    return "This request is outside the supported NovaAir scope."

