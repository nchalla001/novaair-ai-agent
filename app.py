from fastapi import FastAPI, HTTPException

app = FastAPI()

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

@app.get("/bookings/{booking_id}")
def get_booking(booking_id: str):
    booking = bookings.get(booking_id)

    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")

    return booking