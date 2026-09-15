from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from knowledge_base import retrieve_policy, model
from sentence_transformers import util
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

intent_examples = {
    "POLICY_QUESTION": [
        "What is the baggage policy?",
        "My suitcase never arrived. What should I do?",
        "What are the cancellation rules?",
        "Can I get a refund?",
        "What happens if my checked bag is delayed?",
    ],

    "BOOKING_LOOKUP": [
        "Check booking NA123",
        "Show me my booking status",
        "Can you tell me about my reservation?",
        "What is happening with NA456?",
    ],

    "UNSUPPORTED": [
        "Who was Augustus?",
        "Tell me a joke",
        "What is the weather today?",
    ]
}

intent_texts = []
intent_labels = []

for intent, examples in intent_examples.items():
    for example in examples:
        intent_texts.append(example)
        intent_labels.append(intent)

intent_embeddings = model.encode(
    intent_texts,
    convert_to_tensor=True
)
def classify_intent(message: str):
    message_embedding = model.encode(
        message,
        convert_to_tensor=True
    )

    scores = util.cos_sim(
        message_embedding,
        intent_embeddings
    )[0]

    best_match_index = scores.argmax().item()
    best_match_score = scores[best_match_index].item()

    if best_match_score < 0.30:
        return "UNSUPPORTED"

    return intent_labels[best_match_index]
def route_request(message: str):
    intent = classify_intent(message)

    if intent == "POLICY_QUESTION":
        return "RAG"

    if intent == "BOOKING_LOOKUP":
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

        try:
            return get_booking(booking_id)

        except HTTPException as error:
            if error.status_code == 404:
                return f"I couldn't find booking {booking_id}. Please verify the booking reference and try again."

            raise error

        except TimeoutError:
         return "The booking service is temporarily unavailable. Please try again shortly or contact customer service."

    return "This request is outside the supported NovaAir scope."




