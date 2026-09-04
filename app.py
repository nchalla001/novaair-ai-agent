from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid

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
